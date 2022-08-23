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

def register(environment):
    setObj = restsh.DictObject(
        { 'create': bCreate
        })
    setObj.description = 'Functions for working with sets'

    environment.setVariable('set', setObj)
