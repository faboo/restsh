from typing import cast, Union, Dict, Callable, Tuple, List, Optional, Any
import io
import os
import sys
import re
import json
import base64
from .environment import Environment, Cell
from .evaluate import dereference, wrap, Eval, Builtin, Array, Function, ServiceObject, Object, String, Boolean \
    , Integer, Float, Null, Constant
from .repl import repLoop

builtins:Dict[
        str,
        Tuple[
            Callable[[Environment, Dict[str,Union[Eval, Cell]]], Union[Eval, Cell]],
            dict,
            Optional[str]
        ]
    ] = { }

def add(
        name:str,
        args:Dict[str,str],
        desc:Optional[str]=None,
        retwrap:Optional[Callable[[Any], Union[Eval, Cell]]]=None
        ) -> Any:
    def wrapper(func:Callable[[Any, Any], Any]
            ) -> Callable[[Environment, Dict[str,Union[Eval, Cell]]], Union[Eval, Cell]]:
        def run(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:

            try:
                result = func(environment, {key: dereference(arg) for key, arg in args.items()})

                if retwrap:
                    return retwrap(result)
                else:
                    return wrap(result)
            except Exception as ex:
                environment.error("%s: %s" % (ex.__class__.__name__, ' '.join(ex.args)))
                return wrap(None)

        builtins[name] = (run, args, desc)

        return run

    return wrapper


@add(
    'size',
    {'of': 'any'},
    'Returns the number of elements in an array, object, or string, or the number of parameters to a function')
def bSize(environment:Environment, args:Dict[str,Eval]) -> Any:
    value = args['of']

    if isinstance(value, Array):
        return len(cast(Array, value).elements)
    elif isinstance(value, Function):
        return len(value.parameters(environment))
    elif isinstance(value, ServiceObject):
        return len(environment.services[cast(ServiceObject, value).name].callDef)
    elif isinstance(value, Object):
        return len(cast(Object, value).properties)
    elif isinstance(value, String):
        return len(cast(String, value).getValue())
    else:
        return environment.getVariable('null')


@add('eval', {'code': 'string'}, 'Evaluate a string as a restsh command')
def bEval(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['code']
    env = Environment(environment)

    if not isinstance(value, String):
        environment.error('Cannot eval non-string: %s' % value)

    env.input = io.StringIO(initial_value=cast(String, value).getValue())

    return repLoop(env)


@add('type', {'of': 'any'}, 'Get the type of a value')
def bType(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['of']

    if isinstance(value, Constant):
        typeName = value.__class__.__name__.lower()
    elif isinstance(value, Function):
        typeName = 'function'
    elif isinstance(value, Array):
        typeName = 'array'
    elif isinstance(value, Object):
        typeName = 'object'

    return wrap(typeName)
    

@add('map', {'arr': 'array', 'fn': 'function[item,index]'})
def bMap(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    array = cast(Array, args['arr'])
    func = cast(Function, args['fn'])
    result:List[Eval] = []
    index = 0

    for expr in array.elements:
        elm = func.call(environment, {'item': dereference(expr), 'index': wrap(index)})
        result.append(dereference(elm))
        index += 1

    return Array(result)


@add('filter', {'arr': 'array', 'fn': 'function[item,index]'})
def bFilter(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    array = cast(Array, args['arr'])
    func = cast(Function, args['fn'])
    result:List[Eval] = []
    index = 0

    for expr in array.elements:
        keep = func.call(environment, {'item': dereference(expr), 'index': wrap(index)})
        
        if Boolean.truthy(keep).getValue():
            result.append(dereference(expr))
        index += 1

    return Array(result)


@add('reduce', {'arr': 'array', 'fn': 'function[accum,item,index]'}, 'Reduce left-to-right')
def bReduce(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    array = cast(Array, args['arr'])
    func = cast(Function, args['fn'])
    accum:Union[Eval,Cell] = args['base']
    index = 0

    for item in array.elements:
        accum = func.call(
            environment,
            { 'accum': dereference(accum)
            , 'item': dereference(item)
            , 'index': wrap(index)
            })

        index += 1
    
    return accum


@add('rreduce', {'arr': 'array', 'fn': 'function[accum,item,index]'}, 'Reduce right-to-left')
def bRreduce(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    array = cast(Array, args['arr'])
    func = cast(Function, args['fn'])
    accum:Union[Eval,Cell] = args['base']
    index = 0

    for item in reversed(array.elements):
        accum = func.call(
            environment,
            { 'accum': dereference(accum)
            , 'item': dereference(item)
            , 'index': wrap(index)
            })

        index += 1
    
    return accum


@add('string', {'value': 'any'}, 'Convert a value into a string')
def bString(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['value']

    if isinstance(value, String):
        return value
    else:
        return String(repr(value))


@add('boolean', {'value': 'any'})
def bBoolean(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['value']

    if isinstance(value, Boolean):
        return value
    else:
        return Boolean.truthy(value)


@add('integer', {'value': 'any'})
def bInteger(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['value']

    if isinstance(value, Integer):
        return value
    elif isinstance(value, String):
        try:
            return Integer(int(cast(String, value).getValue()))
        except: #pylint: disable=bare-except
            return Integer(0)
    elif isinstance(value, Boolean):
        return Integer(int(cast(Boolean, value).getValue()))
    elif isinstance(value, Float):
        return Integer(int(cast(Float, value).getValue()))
    else:
        return Integer(0)


@add('sh', {'cmd': 'string'})
def bSh(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    cmd = args['cmd']

    try:
        cmdStr = cast(String, cmd).getValue()
        output = os.popen(cmdStr)
        return String(output.read())
    except Exception as ex:
        environment.error(str(ex))
        return Null()


@add('grep', {'text': 'string', 'for': 'string', 'case': '?boolean'}, 'Search text for a regular expression')
def bGrep(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    text = cast(String, args['text']).getValue()
    forStr = cast(String, args['for']).getValue()
    caseIns = args.get('case')
    regexargs = {}

    if caseIns is None or cast(Boolean, caseIns).getValue() is False:
        regexargs = { 'flags': re.IGNORECASE }

    return Boolean(re.search(forStr, text, **regexargs) is not None)


@add('split', {'text': 'string', 'on': 'string'}, 'Split a string on a regular expression')
def bSplit(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    text = cast(String, args['text']).getValue()
    onStr = cast(String, args['on']).getValue()

    return Array([String(string) for string in re.split(onStr, text)])


@add('join', {'with': 'string', 'arr': 'array'}, 'Join the elements of an array into a string')
def bJoin(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    text = cast(String, args['with']).getValue()
    array = cast(Array, args['arr']).elements

    return wrap(text.join([str(elm) for elm in array]))


@add('tojson', {'val': 'any'}, 'Convert ')
def bTojson(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    val = args['val']
    return String(json.dumps(val.toPython()))


@add('parsejson', {'str': 'string'})
def bParsejson(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    string = cast(String, args['str']).getValue()
    return wrap(json.loads(string))


@add('b64encode', {'text': 'string'}, 'Encode a string as base-64')
def bB64encode(environment:Environment, args:Dict[str,Eval]) -> Any:
    string = cast(String, args['text']).getValue()
    return base64.b64encode(string.encode('utf-8')).decode('utf-8')


@add('b64decode', {'b64': 'string'}, 'Decode a base-64 as a string')
def bB64decode(environment:Environment, args:Dict[str,Eval]) -> Any:
    b64 = cast(String, args['b64']).getValue()
    return base64.b64decode(b64).decode('utf-8')


@add('print', {'text': 'string'})
def bPrint(environment:Environment, args:Dict[str,Eval]) -> Any:
    text = cast(String, args['text']).getValue()
    return environment.print(text)


@add('get', {'obj': 'object', 'name': 'string'}, 'Get a property of an object by name')
def bGet(environment:Environment, args:Dict[str,Eval]) -> Any:
    name = cast(String, args['name']).getValue()
    obj = cast(Object, args['obj'])

    return obj.get(name, environment)

def bSet(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    cell = args['var']
    value = args['value']

    if isinstance(cell, String):
        cell = environment.setVariable(cell.getValue(), value)
    elif isinstance(cell, Cell):
        cell.set(value)
    else:
        environment.error('var must be either a string, or variable')

    return cell

builtins['set'] = (bSet, {'var': 'any', 'value': 'any'}, 'Set or define a variable')

@add('source', {'file': 'string'})
def bSource(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    filename = cast(String, args['file']).getValue()

    with open(os.path.expanduser(filename), 'r', encoding='utf-8') as rsource:
        environment.input = rsource
        try:
            repLoop(environment)
            return environment.lastResult
        finally:
            environment.input = sys.stdin
            environment.loop = True


def register(environment:Environment):
    for name, (builtin, params, description) in builtins.items():
        environment.setVariable(
            name,
            Builtin(name, builtin, params, description))

