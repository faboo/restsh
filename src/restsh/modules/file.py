from ..moduleUtils import builtin
from ..evaluate import DictObject, wrap
from ..environment import EvaluationError

@builtin('read', [('file', 'string')], 'Read a text file into a string')
def bRead(environment, args):
    filename = args['file'].toPython()

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            contents = '\n'.join(file.readlines())
    except FileNotFoundError:
        #pylint: disable=raise-missing-from
        raise EvaluationError(f'File not found: {filename}')

    return wrap(contents)


@builtin('write', [('file', 'string'), ('text', 'string')], 'Write a string to a file')
def bWrite(environment, args):
    filename = args['file'].toPython()
    text = args['text'].toPython()

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)


@builtin('append', [('file', 'string'), ('text', 'string')], 'Write a string to a file')
def bAppend(environment, args):
    filename = args['file'].toPython()
    text = args['text'].toPython()

    with open(filename, 'a', encoding='utf-8') as file:
        file.write(text)


def register(environment):
    # Setting up an object to contain the functions your module creates is useful, but not required.
    mod = DictObject(
        { 'read': bRead
        , 'write': bWrite
        , 'append': bAppend
        })
    mod.description = 'Functions for working with files'

    environment.setVariable('file', mod)
