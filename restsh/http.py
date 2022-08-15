from typing import cast, Union, Dict, Callable, Tuple, List, Optional, Any
from urllib import request
from urllib.error import HTTPError
from .environment import Environment, Cell
from .evaluate import dereference, wrap, DictObject, Builtin, String, Eval

def bRequest(environment:Environment, method:str, url:str, data:Optional[str]) -> Union[Eval, Cell]:
    headers = \
        { 'User-Agent': 'restsh/1.0'
        } # TODO

    req = request.Request(
        url,
        headers=headers,
        data=data.encode('utf-8') if data is not None else data,
        method=method)

    print('request:\n', req.__dict__)

    try:
        with request.urlopen(req) as response:
            status = response.status
            reason = response.reason
            text = response.read().decode('utf-8')
    except HTTPError as ex:
        status = ex.status
        reason = ex.reason
        text = ex.read().decode('utf-8')
        print(text)

    status = status // 100
    
    if status not in (1, 2):
        environment.error(f'HTTP {method} failed: {status} {reason}')

    print('status:\n', status)
    print('reason:\n', reason)

    return wrap(text)

    

def bGet(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    return bRequest(environment, 'GET', url, None)


def bPost(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    data = cast(String, dereference(args['data'])).getValue()
    return bRequest(environment, 'POST', url, data)


def bHead(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    # TODO
    url = cast(String, dereference(args['url'])).getValue()
    headers = \
        { 'User-Agent': 'restsh/1.0'
        } # TODO

    req = request.Request(
        url,
        headers=headers,
        method='HEAD')

    print('request:\n', req.__dict__)

    with request.urlopen(req) as response:
        status = response.status
        reason = response.reason
        text = response.read().decode('utf-8')

    status = status // 100
    
    if status not in (1, 2):
        environment.error(f'HTTP POST failed: {status} {reason}')

    print('status:\n', status)
    print('reason:\n', reason)

    return wrap(text)


def bDelete(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    return bRequest(environment, 'DELETE', url, None)


def bOptions(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    url = cast(String, dereference(args['url'])).getValue()
    return bRequest(environment, 'OPTIONS', url, None)


def register(environment:Environment):
    httpObj = DictObject(
        { 'get': Builtin('get', bGet, {'url': 'string'})
        , 'post': Builtin('post', bPost, {'url': 'string', 'data': 'string'})
        , 'head': Builtin('head', bHead, {'url': 'string'})
        , 'delete': Builtin('delete', bHead, {'url': 'string'})
        , 'options': Builtin('options', bHead, {'url': 'string'})
        })
    environment.setVariable('http', httpObj)
