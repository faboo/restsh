from typing import cast, Any
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
    allVars = {**cast(Environment, env.base).variables, **env.variables}
    syms = [var for var in allVars if sym.match(var)]
    var = [var for var in syms if not env.getVariableValue(var).isType('function')]
    func = [var for var in syms if env.getVariableValue(var).isType('function')]
    printWrapped(env, GeneralHelp)
    env.print('\nVariables:')
    printWrapped(
        env,
        ', '.join(var)
        )
    env.print('\nFunctions:')
    printWrapped(
        env,
        ', '.join(func)
        )
    env.print('\nOperators:')
    printWrapped(
        env,
        ', '.join(var for var in allVars if op.match(var))
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
    params:dict[str,str] = func.parameters(env)

    if params:
        description = 'It takes %s arguments:\n' % len(params)

        for param, ptype in params.items():
            if ptype[0] == '?':
                ptype = ptype[1:] + ' (optional)'
            description += '\t%s: %s\n' % (param, ptype)

        printWrapped(env, description)
    else:
        printWrapped(env, 'It takes no arguments.')


def object(env:Environment, obj:Any) -> None:
    service = hasattr(obj, 'name') and obj.name in env.services
    properties = [*env.services[obj.name].callDef.keys(),  *obj.methods.keys()] \
        if service \
        else obj.properties
    description = 'It has %s properties:\n' % len(properties)

    for prop in properties:
        value = obj.get(prop, env)
        value = value.value if isinstance(value, Cell) else value
        if service:
            description += '\t%s: %s\n' % \
                ( prop
                , 'function'
                )
        else:
            description += '\t%s: %s\n' % \
                ( prop
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

    if hasattr(value, 'description') and value.description is not None:
        printWrapped(env, value.description+'\n')

    if typeStr == 'a function':
        function(env, value)
    elif typeStr == 'an object':
        object(env, value)


