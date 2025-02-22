import os
import re
from ..moduleUtils import builtin
from ..evaluate import wrap, Eval, DictObject, ServiceObject, Builtin, Array
from ..repl import repLoop

def flattenable(value:Eval) -> bool:
    return not isinstance(value, (ServiceObject, Builtin))

def flatten(value:Eval) -> str:
    if isinstance(value, (Builtin, ServiceObject)):
        return value.name
    elif isinstance(value, Array):
        elements = [flatten(elm.value) for elm in value.elements]
        return '[ %s ]' % ', '.join(elements)
    elif isinstance(value, DictObject):
        #pylint: disable=protected-access
        kvps = {key: flatten(val.value) for key, val in value._properties.items()}
        return '{ %s }' % ', '.join(f'{key}: {val}' for key, val in kvps.items())
    elif isinstance(value, str):
        return value.toJson()
    else:
        return repr(value)

def legalSymbol(sym:str) -> bool:
    return bool(re.match('[_a-zA-Z][_a-zA-Z0-9]*$', sym))

@builtin('save',
    [('name', '?string')],
    'Save the current session. Saves to the current session if no name is provided.')
def bSave(environment, args):
    if 'name' in args:
        name = args['name'].toPython()
        sessionObj.get('current', environment).set(wrap(name))
    else:
        name = sessionObj.get('current', environment).toPython()

    filename = environment.homedir+name+'.sess'

    os.makedirs(environment.homedir, exist_ok=True)

    while not environment.globals and environment.base is not None:
        environment = environment.base

    with open(filename, 'w', encoding='utf-8') as file:
        file.write("# Maybe don't edit this file ;-)\n")
        # import services
        for service in environment.services:
            line = f'import {service}\n'
            file.write(line)

        # write variables
        for var, value in environment.variables.items():
            value = value.value

            if legalSymbol(var) and flattenable(value):
                line = f'let {var} = {flatten(value)}\n'
                file.write(line)


@builtin('open', [('name', 'string')], 'Load a saved session. Loads the current session if no name is provided.')
def bOpen(environment, args):
    name = args['name'].toPython()
    filename = environment.homedir+name+'.sess'
    originalInput = environment.input

    sessionObj.get('current', environment).set(wrap(name))

    try:
        with open(filename, encoding='utf-8') as file:
            environment.input = file
            repLoop(environment)
    #pylint: disable=bare-except
    except:
        pass

    environment.input = originalInput
    environment.loop = True


@builtin('clear', [], 'Clear the current session of new definitions and services.')
def bClear(environment, args):
    environment.variables = { }
    environment.services = { }


sessionObj = DictObject(
    { 'current': wrap('')
    , 'save': bSave
    , 'open': bOpen
    , 'clear': bClear
    })

def register(environment):
    sessionObj.description = 'Session management'

    environment.setVariable('session', sessionObj)
