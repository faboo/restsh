from typing import cast, Union, Dict, Callable, Tuple, List, Optional, Any
from urllib import request
from .environment import Environment, Cell
from .evaluate import dereference, wrap, DictObject, Builtin, String, Eval

def bGet(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    headers = \
        { 'User-Agent': 'restsh/1.0'
        } # TODO

    req = request.Request(
        url,
        headers=headers,
        method='GET')

    print('request:\n', req.__dict__)

    with request.urlopen(req) as response:
        status = response.status
        reason = response.reason
        text = response.read().decode('utf-8')

    status = status // 100
    
    if status not in (1, 2):
        environment.error('HTTP GET failed: '+reason)

    print('status:\n', status)
    print('reason:\n', reason)

    return wrap(text)


def bPost(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    data = cast(String, dereference(args['data'])).getValue()
    headers = \
        { 'User-Agent': 'restsh/1.0'
        } # TODO

    req = request.Request(
        url,
        headers=headers,
        data=data.encode('utf-8'),
        method='POST')

    print('request:\n', req.__dict__)

    with request.urlopen(req) as response:
        status = response.status
        reason = response.reason
        text = response.read().decode('utf-8')

    status = status // 100
    
    if status not in (1, 2):
        environment.error('HTTP POST failed: '+reason)

    print('status:\n', status)
    print('reason:\n', reason)

    return wrap(text)


def register(environment:Environment):
    httpObj = DictObject(
        { 'get': Builtin('get', bGet, {'url': 'string'})
        , 'post': Builtin('post', bPost, {'url': 'string', 'data': 'string'})
        })
    environment.setVariable('http', httpObj)
