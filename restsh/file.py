from .moduleUtils import builtin
from .evaluate import DictObject, wrap
from .environment import EvaluationError

@builtin('read', {'file': 'string'}, 'Read a text file into a string')
def bRead(environment, args):
    filename = args['file'].toPython()

    try:
        with open(filename, 'r') as file:
            contents = '\n'.join(file.readlines())
    except FileNotFoundError:
        raise EvaluationError(f'File not found: {filename}')

    return wrap(contents)


def register(environment):
    # Setting up an object to contain the functions your module creates is useful, but not required.
    mod = DictObject(
        { 'read': bRead
        })
    mod.description = 'Functions for working with files'

    environment.setVariable('file', mod)
