from typing import cast, Union, Dict, Callable, Tuple, List, Optional, Any
import io
import os
import json
from .environment import Environment, Cell
from .evaluate import dereference, wrap, Eval, Builtin, Array, Function, ServiceObject, DictObject, String, Boolean \
    , Integer, Null
from .repl import repLoop

builtins:Dict[
        str,
        Tuple[ Callable[[Environment, Dict[str,Eval]], Union[Eval, Cell]], dict]
        ] = { }

def add(name:str, args:Dict[str,str], retwrap:Optional[Callable[[Any], Union[Eval, Cell]]]=None
        ) -> Any:
    def wrapper(func:Callable[[Any, Any], Any]
            ) -> Callable[[Environment, Dict[str,Eval]], Union[Eval, Cell]]:
        def run(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:

            result = func(environment, {key: dereference(arg) for key, arg in args.items()})

            if retwrap:
                return retwrap(result)
            else:
                return wrap(result)

        builtins[name] = (run, args)

        return run

    return wrapper


@add('size', {'of': 'collection'})
def bSize(environment:Environment, args:Dict[str,Eval]) -> Any:
    value = args['of']

    if isinstance(value, Array):
        return len(cast(Array, value).elements)
    elif isinstance(value, Function):
        return 1
    elif isinstance(value, ServiceObject):
        return len(environment.services[cast(ServiceObject, value).name].callDef)
    elif isinstance(value, DictObject):
        return len(cast(DictObject, value).properties)
    else:
        return environment.getVariable('null')


@add('eval', {'code': 'string'})
def bEval(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    value = args['code']
    env = Environment(environment)

    if not isinstance(value, String):
        environment.error('Cannot eval non-string: %s' % value)

    env.input = io.StringIO(initial_value=cast(String, value).getValue())

    return repLoop(env)
    

@add('map', {'arr': 'array', 'fn': 'function(arr,fn)'})
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


@add('filter', {'arr': 'array', 'fn': 'function(arr,fn)'})
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


@add('string', {'value': 'any'})
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


@add('tojson', {'val': 'any'})
def bTojson(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    val = args['val']
    return String(json.dumps(val.toPython()))


@add('parsejson', {'str': 'string'})
def bParsejson(environment:Environment, args:Dict[str,Eval]) -> Union[Eval, Cell]:
    string = cast(String, args['str']).getValue()
    return wrap(json.loads(string))


def bSet(environment:Environment, args:Dict[str,Union[Cell,Eval]]) -> Union[Eval, Cell]:
    cell = args['var']
    value = args['value']

    cell.set(value)
    return cell

builtins['set'] = (bSet, {'var': 'cell', 'value': 'any'})



def register(environment:Environment):
    for name, (builtin, params) in builtins.items():
        environment.setVariable(
            name,
            Builtin(name, builtin, params))

