from typing import Dict, Any, Optional
import os
import uuid
from urllib import request
from urllib.parse import urlunparse
import time
import yaml
import json
import re

class UnsupportedProtocol(Exception):
    def __init__(self, protocol:str) -> None:
        super().__init__('Unsupported '+protocol)
        self.protocol = protocol


class Service:
    @staticmethod
    def loadService(filename:str) -> 'Service':
        contents = {}

        try:
            with open(filename, encoding='utf-8') as file:
                contents = yaml.safe_load(file.read())
        except FileNotFoundError:
            filename = os.path.expanduser('~/.restsh/'+filename)
            with open(filename, encoding='utf-8') as file:
                contents = yaml.safe_load(file.read())

        if contents['protocol'] in ('http', 'https'):
            return HttpService(contents)
        if contents['protocol'] == 'amqp':
            return AmqpService(contents)
        raise UnsupportedProtocol(contents['protocol'])

    def __init__(self, definition:dict) -> None:
        self.host:str = definition.get('host', 'localhost')
        self.protocol:str = definition['protocol']
        self.authType:Optional[str] = None
        self.authData:Optional[str] = None
        self.callDef:Dict[str, dict] = { }

        if 'authentication' in definition:
            self.authType = definition['authentication'].get('type')
            self.authData = definition['authentication'].get('data')

        for call in definition['call']:
            self.createCall(call)

    def setAuthentication(self, auth:str) -> None:
        self.authData = auth


    def fillTemplate(self, template:str, parameters:dict, arguments:dict) -> str:
        string = template

        for param in parameters.keys():
            arg = arguments.get(param, '')
            string = re.sub(r'(?<!\$)\$' + param + r'\$(?!\$)', str(arg), string)

        #print('filled template: ', string)
        return string


    def fillCall(self, callDef, templ) -> None:
        for key in templ:
            if key not in callDef:
                callDef[key] = templ[key]
            elif isinstance(templ[key], dict):
                self.fillCall(callDef[key], templ[key])


    def createCall(self, definition:dict) -> None:
        self.fillCall(
            definition,
            { 'timeout': 60
            , 'params': {}
            , 'response': 
                { 'type': 'text'
                , 'transform': None
                , 'error': None
                }
            })

        self.callDef[definition['name']] = definition


    def setHost(self, host:str) -> None:
        self.host = host

    def has(self, name:str) -> bool:
        return name in self.callDef

    def describe(self, name:str) -> Dict[str, str]:
        return self.callDef[name].get('params', {})

    def getResponseTransform(self, name:str) -> Optional[str]:
        return self.callDef[name]['response']['transform']

    def getErrorTransform(self, name:str) -> Optional[str]:
        return self.callDef[name]['response']['error']

    def needsAuth(self, call:str) -> bool:
        return self.authType is not None \
            and self.callDef[call].get('authenticated', True)
    
    def call(self, name:str, arguments:dict) -> Any:
        return None



class HttpService(Service):
    def addAuth(self, headers:dict) -> None:
        if self.authType is not None and self.authData is not None:
            if self.authType.startswith('cookie'):
                (_, cookie) = self.authType.split(':')
                headers['set-cookie'] = '%s=%s' % (cookie, self.authData)
            else:
                # TODO: basic auth?
                headers['authorization'] = self.authType+' '+self.authData


    def call(self, name:str, arguments:dict) -> Any:
        call = self.callDef[name]
        timeout = call['timeout']
        params = self.describe(name)
        path = call.get('path', '/')
        method = call.get('method', 'GET')
        query = call.get('query', None)
        fragment = call.get('fragment', None)
        responseType = call['response']['type']
        data = call.get('body', None)
        headers = \
            { 'User-Agent': 'restsh/1.0'
            }
        status = 0
        text = ''
        result = ''

        if self.needsAuth(name):
            self.addAuth(headers)

        path = self.fillTemplate(path, params, arguments)
        print('path is\n', path)

        if query is not None:
            query = self.fillTemplate(query, params, arguments)

        if fragment is not None:
            fragment = self.fillTemplate(fragment, params, arguments)

        if data is not None:
            data = self.fillTemplate(data, params, arguments)
        print('data is\n', data)


        req = request.Request(
            urlunparse(
                ( self.protocol
                , self.host
                , path
                , ''
                , query
                , fragment
                )),
            data=data.encode('utf-8') if data is not None else None,
            headers=headers,
            method=method)
        
        print('request:\n', req.__dict__)

        with request.urlopen(req, timeout=timeout) as response:

            status = response.status
            headers = response.headers
            text = response.read()

        if responseType == 'json':
            result = json.loads(text)
        elif responseType == 'text':
            result = text
        else:
            result = ''

        return \
            { 'response': result
            , 'status': status
            , 'headers': dict(headers.items())
            }


class AmqpService(Service):
    def addAuth(self, auth:dict) -> None:
        if self.authType == 'basic' and self.authData is not None:
            user, password = self.authData.split(':')
            auth['userid'] = user
            auth['password'] = password


    def call(self, name:str, arguments:dict) -> Any:
        import amqp #pylint: disable=import-outside-toplevel
        startTime = time.monotonic()
        replyQueue = 'REPLY_restsh_'+str(uuid.uuid1())
        call = self.callDef[name]
        timeout = call['timeout']
        params = self.describe(name)
        queue = call.get('queue', None)
        responseType = call['response']['type']
        data = call.get('body', '')
        connConf:dict = {}
        text = ''
        result = ''

        if data is not None:
            data = self.fillTemplate(data, params, arguments)

        if self.needsAuth(name):
            self.addAuth(connConf)

        with amqp.Connection(
                self.host,
                confirm_publish=True,
                **connConf
                ) as conn:
            response = None
            chan = conn.channel()

            chan.queue_declare(replyQueue, auto_delete=True)

            print('publishing message: ', str(data))
            chan.basic_publish(
                amqp.Message(data, reply_to=replyQueue),
                routing_key=queue)

            while not response:
                print('waiting')
                response = chan.basic_get(queue=replyQueue)
                time.sleep(0.10)
                if (time.monotonic() - startTime) > timeout:
                    raise Exception('Call timed out after %s seconds' % timeout)

            print('response')
            text = response.body.decode('utf-8')

            chan.close()

        if responseType == 'json':
            result = json.loads(text)
        elif responseType == 'text':
            result = text
        else:
            result = ''

        return \
            { 'response': result
            }


