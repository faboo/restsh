from ..moduleUtils import builtin
from ..evaluate import DictObject, wrap
from ..environment import EvaluationError

@builtin('read', {'file': 'string'}, 'Read a text file into a string')
def bRead(environment, args):
    filename = args['file'].toPython()

    try:
        with open(filename, 'r') as file:
            contents = '\n'.join(file.readlines())
    except FileNotFoundError:
        raise EvaluationError(f'File not found: {filename}')

    return wrap(contents)


@builtin('write', {'file': 'string', 'text': 'string'}, 'Write a string to a file')
def bWrite(environment, args):
    filename = args['file'].toPython()
    text = args['text'].toPython()

    with open(filename, 'w') as file:
        file.write(text)

    return None


@builtin('append', {'file': 'string', 'text': 'string'}, 'Write a string to a file')
def bAppend(environment, args):
    filename = args['file'].toPython()
    text = args['text'].toPython()

    with open(filename, 'a') as file:
        file.write(text)

    return None


def register(environment):
    # Setting up an object to contain the functions your module creates is useful, but not required.
    mod = DictObject(
        { 'read': bRead
        , 'write': bWrite
        , 'append': bAppend
        })
    mod.description = 'Functions for working with files'

    environment.setVariable('file', mod)
