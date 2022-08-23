import restsh

class Set(restsh.Constant):
    def __init__(self, elements):
        self.elements = set(elements)

    def getValue(self):
        return self.elements

    def __repr__(self):
        return '{%s}' % ', '.join(str(elm) for elm in self.elements)

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'set'

@restsh.builtin('create', {'from': 'array'}, 'Create a set from the elements of an array')
def bCreate(environment, args):
    array = args['from']

    return Set(array.toPython())


@restsh.builtin('array', {'set': 'set'}, 'Return the elements of a set as an array')
def bArray(environment, args):
    set = args['set']

    return restsh.Array([restsh.wrap(elm) for elm in set.elements])


# register() will be called with an Environment object when the module is loaded (or reloaded). 
def register(environment):
    # Setting up an object to contain the functions your module creates is useful, but not required.
    setObj = restsh.DictObject(
        { 'create': bCreate
        , 'array': bArray
        })
    setObj.description = 'Functions for working with sets'

    environment.setVariable('set', setObj)
