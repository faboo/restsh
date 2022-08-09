from typing import Any, Dict
import os
import re
from .environment import Environment, Cell

LeaderHelp = """
REST Shell

Use the "help" command to get help, and "exit" to exit the shell.
""".strip()

GeneralHelp = """
Below are the currently defined variables and operators. You can get additional help about each of them like so:

$ help [variable]
""".strip()

def printWrapped(env:Environment, text:str) -> None:
    width = os.get_terminal_size().columns

    for fullLine in text.split('\n'):
        toPrint = ''

        for word in fullLine.split(' '):
            word += ' '
            word = word.replace('\t', '  ')

            if (len(toPrint) + len(word)) > width:
                env.print(toPrint)
                toPrint = ''
            toPrint += word

        env.print(toPrint)


def environment(env:Environment) -> None:
    sym = re.compile('[_a-zA-Z][_a-zA-Z0-9]*$')
    op = re.compile('[-+*/|&^$@?~]+$')
    printWrapped(env, GeneralHelp)
    env.print('\nVariables:')
    printWrapped(
        env,
        ', '.join(var for var in env.variables if sym.match(var))
        )
    env.print('\nOperators:')
    printWrapped(
        env,
        ', '.join(var for var in env.variables if op.match(var))
        )


def article(word:str) -> str:
    if word[0] in 'aeiou':
        return 'an '+word
    else:
        return 'a '+word


def typeName(variable:Any) -> str:
    translate = \
        { 'builtin': 'function'
        , 'servicecall': 'function'
        , 'serviceobject': 'object'
        , 'dictobject': 'object'
        }
    name = variable.__class__.__name__.lower()

    name = translate.get(name, name)

    return name


def function(env:Environment, func:Any) -> None:
    params:Dict[str,str] = func.parameters(env)
    description = 'It takes %s arguments:\n' % len(params)

    for param, ptype in params.items():
        description += '\t%s: %s\n' % (param, ptype)

    printWrapped(env, description)


def object(env:Environment, obj:Any) -> None:
    service = hasattr(obj, 'name') and obj.name in env.services
    properties = {**env.services[obj.name].callDef, **obj.methods} \
        if service \
        else obj.properties
    description = 'It has %s properties:\n' % len(properties)

    for param, value in properties.items():
        value = value.value if isinstance(value, Cell) else value
        if service:
            description += '\t%s: %s\n' % \
                ( param
                , 'function'
                )
        else:
            description += '\t%s: %s\n' % \
                ( param
                , typeName(value)
                )

    printWrapped(env, description)
    

def variable(env:Environment, keyword:str) -> None:
    value = env.getVariableValue(keyword)
    typeStr = typeName(value)

    if typeStr != 'null':
        typeStr = article(typeStr)
    
    printWrapped(env, '%s is %s\n' % (keyword, typeStr))

    if typeStr == 'a function':
        function(env, value)
    elif typeStr == 'an object':
        object(env, value)


def value(env:Environment, name:str, value:Any) -> None:
    value = value.value if isinstance(value, Cell) else value
    typeStr = typeName(value)

    if typeStr != 'null':
        typeStr = article(typeStr)
    
    printWrapped(env, '%s is %s\n' % (name, typeStr))

    if typeStr == 'a function':
        function(env, value)
    elif typeStr == 'an object':
        object(env, value)


