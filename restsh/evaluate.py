from typing import cast, Union, Dict, Any, List, Callable, Optional
from .environment import Environment, Cell, EvaluationError
from .token import Sym, Eq, LParen, RParen, LAngle, RAngle, LBrace, RBrace, LBracket, RBracket \
    , Comma, Colon, SemiColon, Bang, Dot, BSlash \
    , Str, Flt, Int, Let, Imp, Help, Ext, Try
from .service import Service, UnsupportedProtocol
from . import describe


class Eval:
    #@staticmethod
    #def parse() -> 'Eval':
    #    return Eval()

    def evaluate(self, environment:Environment) -> Union['Eval', Cell]:
        return self

    @property
    def interactivePrint(self) -> bool:
        return True

    def isType(self, typeDesc:str) -> bool:
        return typeDesc == 'any'

    def toPython(self) -> Any:
        return repr(self)

    def equal(self, other:'Eval') -> bool:
        return id(self) == id(other)


def dereference(value:Union[Eval, Cell]) -> Eval:
    return value.value if isinstance(value, Cell) else value


def wrap(value:Any) -> Eval:
    if isinstance(value, Eval):
        return value
    elif isinstance(value, Cell):
        return value.value
    elif value is None:
        return Null()
    elif isinstance(value, str):
        return String(value)
    elif isinstance(value, bool):
        return Boolean(value)
    elif isinstance(value, float):
        return Float(value)
    elif isinstance(value, int):
        return Integer(value)
    elif isinstance(value, list):
        return Array.fromPython(value)
    elif isinstance(value, dict):
        return DictObject.fromPython(value)
    else:
        raise EvaluationError('Unsupported native value: %s (%s)' % (value, value.__class__))


class Variable(Eval):
    def __init__(self, name:str) -> None:
        self.name:str = name

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def parse(sym:Sym) -> Eval:
        return Variable(sym.text)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        return environment.getVariable(self.name)


class ElementList(Eval):
    def __init__(self, elements:List[Eval]) -> None:
        self.elements:List[Eval] = elements

    def __repr__(self) -> str:
        return ', '.join('%s' % repr(elm) for elm in self.elements)

    @staticmethod
    def parse(elm:Eval=None, _:Comma=None, elmList:Union['ElementList',Eval]=None) -> Eval:
        elements:List[Eval] = []

        if isinstance(elmList, ElementList):
            elements = list(elmList.elements)
        elif isinstance(elmList, Eval):
            elements.insert(0, elmList)

        if isinstance(elm, Eval):
            elements.insert(0, elm)

        return ElementList(elements)


class Object(Eval):
    def get(self, name:str, environment:Environment) -> Union[Eval, Cell]:
        return self


class Array(Eval):
    def __init__(self, elements:List[Eval]) -> None:
        self.evaluated = False
        self.elements:List[Cell] = [Cell(elm) for elm in elements]

    def __repr__(self) -> str:
        return '[ %s ]' % (', '.join('%s' % repr(elm) for elm in self.elements))

    @staticmethod
    def fromPython(lst:list) -> Eval:
        array = Array([wrap(elm) for elm in lst])
        array.evaluated = True
        return array

    def toPython(self) -> Any:
        return [elm.toPython() for elm in self.elements]

    @staticmethod
    def parse(_:LAngle, elements:ElementList, __:RAngle) -> Eval:
        return Array(elements.elements)

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc.startswith('array') \
            or typeDesc.startswith('collection')

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        if self.evaluated:
            return self
        
        elements = \
            [ dereference(elm.value.evaluate(environment))
              for elm in self.elements
            ]
        array = Array(elements)
        array.evaluated = True

        return array


    def get(self, index:int, environment:Environment) -> Union[Eval, Cell]:
        if index < 0 or index >= len(self.elements):
            environment.error('No element at index %s' % index)

        return self.elements[index]


class ParamList(Eval):
    def __init__(self, params:List[str]) -> None:
        self.params:List[str] = params

    def __repr__(self) -> str:
        return ', '.join(self.params)

    @staticmethod
    def parse(param:Sym=None, _:Comma=None, paramList:Union['ParamList',Sym]=None) -> Eval:
        params:List[str] = []

        if isinstance(paramList, ParamList):
            params = list(paramList.params)
        elif isinstance(paramList, Sym):
            params.insert(0, paramList.text)

        if isinstance(param, Sym):
            params.insert(0, param.text)

        return ParamList(params)


class Function(Object):
    def get(self, name:str, environment:Environment) -> Union[Eval, Cell]:
        result = self
        if name == 'parameters':
            result = self
        else:
            environment.error('%s has no member %s' % (self, name))

        return result

    def parameters(self, environment:Environment) -> Dict[str, str]:
        return {}

    def call(self, environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
        return self

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc.startswith('function')


class Builtin(Function):
    def __init__(self,
            name:str,
            func:Callable[[Environment, Dict[str, Union[Eval, Cell]]], Union[Eval, Cell]],
            params:Dict[str,str]) -> None:
        self.name = name
        self.func = func
        self.params = params

    def __repr__(self) -> str:
        return 'builtin[%s]' % self.name

    def parameters(self, environment:Environment) -> Dict[str, str]:
        return self.params

    def call(self, environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
        return self.func(environment, args)


class Closure(Function):
    def __init__(self, params:List[str], expr:Eval) -> None:
        self.params:List[str] = params
        self.expression:Eval = expr
        self.environment:Optional[Environment] = None
        self.evaluated = False

    def __repr__(self) -> str:
        return '\\ %s . %s' % \
            ( ', '.join(self.params)
            , repr(self.expression)
            )

    @staticmethod
    def parse(_:BSlash, params:ParamList, __:Dot, expr:Eval) -> Eval:
        return Closure(params.params, expr)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        if not self.evaluated:
            self.environment = environment
            self.evaluated = True
        return self

    def parameters(self, environment:Environment) -> Dict[str, str]:
        return { param: 'any' for param in self.params }

    def call(self, _:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
        if self.environment is None:
            _.error('Function not evaluated!')
        environment = Environment(self.environment)

        for param in self.params:
            environment.setVariable(param, args[param])

        return self.expression.evaluate(environment)


class ServiceCall(Function):
    def __init__(self, service:str, call:str) -> None:
        self.service:str = service
        self.name:str = call

    def __repr__(self) -> str:
        return 'ServiceCall[%s.%s]' % (self.service, self.name)

    def parameters(self, environment:Environment) -> Dict[str, str]:
        service = environment.services[self.service]
        return service.describe(self.name)

    def buildTransformEnv(self, environment:Environment, response:dict) -> Environment:
        env = Environment(environment)
        for key, value in response.items():
            env.setVariable(key, wrap(value))
        return env

    def call(self, environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
        service = environment.services[self.service]
        args = \
            { key: cast(Constant, dereference(arg)) #.getValue()
              for key, arg in args.items()
            }

        try:
            bEval = cast(Builtin, dereference(environment.getVariable('eval')))
            response = service.call(self.name, args)
            respTrans = service.getResponseTransform(self.name)
            errorTrans = service.getErrorTransform(self.name)

            if errorTrans:
                error = bEval.func(
                    self.buildTransformEnv(environment, response),
                    { 'code': wrap(errorTrans) })
                if isinstance(error, Boolean) and error.getValue():
                    environment.error('remote call failed')

            if respTrans:
                result = bEval.func(
                    self.buildTransformEnv(environment, response),
                    { 'code': wrap(respTrans) })
            else:
                result = wrap(response['response'])
        except Exception as ex:
            environment.error('Error in remote call: %s' % repr(ex))

        return result


class Block(Eval):
    def __init__(self, exprs:List[Eval]) -> None:
        self.expressions = exprs

    def __repr__(self) -> str:
        return '; '.join([repr(expr) for expr in self.expressions])

    @staticmethod
    def parse(left:Eval, _:SemiColon, right:Eval) -> Eval:
        exprs:List[Eval] = []

        if isinstance(left, Block):
            exprs = left.expressions
        else:
            exprs.append(left)

        exprs.append(right)

        return Block(exprs)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        for expr in self.expressions:
            result = expr.evaluate(environment)

        return result


class Arg(Eval):
    def __init__(self, param:str, arg:Eval) -> None:
        self.param:str = param
        self.arg:Eval = arg

    def __repr__(self) -> str:
        return '%s: %s' % (self.param, repr(self.arg))

    @staticmethod
    def parse(param:Str, _:Colon, arg:Eval) -> Eval:
        return Arg(param.text, arg)


class ArgList(Eval):
    def __init__(self, args:Dict[str,Eval]) -> None:
        self.args:Dict[str,Eval] = args

    def __repr__(self) -> str:
        return ', '.join('%s: %s' % (key, repr(arg)) for key, arg in self.args.items())

    @staticmethod
    def parse(arg:Arg=None, _:Comma=None, argList:Union['ArgList',Arg]=None) -> Eval:
        args:Dict[str,Eval] = {}

        if isinstance(argList, ArgList):
            args = { **args, **argList.args }
        elif isinstance(argList, Arg):
            args[cast(Arg, args).param] = argList.arg

        if isinstance(arg, Arg):
            args[arg.param] = arg.arg

        return ArgList(args)


class ServiceObject(Object):
    def __init__(self, name:str) -> None:
        self.calls:Dict[str,ServiceCall] = {}
        self.name:str = name
        self.methods:Dict[str,Builtin] = \
            { 'setHost': Builtin('setHost', self.setHost, {'host': 'string'})
            , 'setAuthentication': Builtin('setAuthentication', self.setAuthentication, {'auth': 'string'})
            }

    def __repr__(self) -> str:
        return 'Service[%s]' % self.name

    def setHost(self, environment:Environment, args:Dict[str, Union[Eval, Cell]]) -> Union[Eval, Cell]:
        host = cast(String, args['host'])
        print('Setting host', host)
        environment.services[self.name].setHost(host.getValue())
        return self

    def setAuthentication(self, environment:Environment, args:Dict[str, Union[Eval, Cell]]) -> Union[Eval, Cell]:
        auth = cast(String, dereference(args['auth']))
        environment.services[self.name].setAuthentication(auth.getValue())
        return self

    def toPython(self) -> Any:
        return {}

    def get(self, name:str, environment:Environment) -> Union[Eval, Cell]:
        service = environment.services[self.name]

        if service.has(name):
            if name not in self.calls:
                self.calls[name] = ServiceCall(self.name, name)
            return self.calls[name]
        else:
            if name not in self.methods:
                environment.error('%s has no defined call named %s' % (self.name, name))
            return self.methods[name]


class DictObject(Object):
    def __init__(self, props:Dict[str, Eval]) -> None:
        self.evaluated = False
        self.properties:Dict[str, Cell] = \
            { prop: Cell(value)
              for prop, value in props.items()
            }

    def __repr__(self) -> str:
        return '{ %s\n}' % ', '.join('%s: %s\n' % (prop, repr(value)) for prop, value in self.properties.items())

    @staticmethod
    def parse(_:LBrace, argList:ArgList, __:RBrace) -> Eval:
        return DictObject(argList.args)

    @staticmethod
    def fromPython(dct:dict) -> Eval:
        obj = DictObject(
            { prop: wrap(value)
              for prop, value in dct.items()
            })
        obj.evaluated = True

        return obj

    def toPython(self) -> Any:
        return \
            { prop: value.toPython()
              for prop, value
              in self.properties.items()
            }

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        if self.evaluated:
            return self

        obj = DictObject(
            { prop: dereference(value.value.evaluate(environment))
              for prop, value in self.properties.items()
            })
        obj.evaluated = True
        return obj

    def get(self, name:str, environment:Environment) -> Union[Eval, Cell]:
        return self.properties[name]


class ObjectRef(Eval):
    def __init__(self, obj:Eval, referent:str) -> None:
        self.obj:Eval = obj
        self.referent:str = referent

    def __repr__(self) -> str:
        return '%s.%s' % (str(self.obj), self.referent)

    @staticmethod
    def parse(obj:Eval, _:Dot, referent:Sym) -> Eval:
        return ObjectRef(obj, referent.text)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        obj = dereference(self.obj.evaluate(environment))
        if not isinstance(obj, Object):
            environment.error('%s is not an object' % str(obj))
        
        return cast(Object, obj).get(self.referent, environment)


class Define(Eval):
    def __init__(self, name:str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return 'let %s' % self.name

    @property
    def interactivePrint(self) -> bool:
        return False

    @staticmethod
    def parse(_:Let, var:Variable) -> Eval:
        return Define(var.name)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        environment.setVariable(self.name, Null())
        return environment.getVariable(self.name)


class Constant(Eval):
    def getValue(self) -> Any:
        return None

    def toPython(self) -> Any:
        return self.getValue()

    def equal(self, other:Eval) -> bool:
        return isinstance(other, self.__class__) and self.getValue() == cast(Constant, other).getValue()


class Null(Constant):
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return 'null'

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'null'


class String(Constant):
    def __init__(self, string:str) -> None:
        self.value = string

    def __repr__(self) -> str:
        return '"%s"' % self.value.replace('\n', '\\n')

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def parse(string:Str) -> Eval:
        return String(string.text[1:-1])

    def getValue(self) -> Any:
        return self.value

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'string'


class Integer(Constant):
    def __init__(self, integer:int) -> None:
        self.value = integer

    def __repr__(self) -> str:
        return str(self.value)

    @staticmethod
    def parse(integer:Int) -> Eval:
        return Integer(int(integer.text))

    def getValue(self) -> Any:
        return self.value

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'integer'


class Float(Constant):
    def __init__(self, number:float) -> None:
        self.value = number

    def __repr__(self) -> str:
        return str(self.value)

    @staticmethod
    def parse(number:Flt) -> Eval:
        return Float(float(number.text))

    def getValue(self) -> Any:
        return self.value

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'float'


class Boolean(Constant):
    def __init__(self, boolean:bool) -> None:
        self.value = boolean

    def __repr__(self) -> str:
        return 'true' if self.value else 'false'

    def getValue(self) -> Any:
        return self.value

    @staticmethod
    def truthy(value:Union[Eval,Cell]) -> 'Boolean':
        expr = dereference(value)
        result = Boolean(False)

        if isinstance(expr, Boolean):
            result = expr
        elif isinstance(expr, Integer):
            result = Boolean(expr.getValue() != 0)
        elif isinstance(expr, Array):
            result = Boolean(len(expr.elements) != 0)
        else:
            result = Boolean(not isinstance(expr, Null))

        return result

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'boolean'


class Assignment(Eval):
    def __init__(self, lvalue:Eval, rvalue:Eval) -> None:
        self.lvalue = lvalue
        self.rvalue = rvalue

    def __repr__(self) -> str:
        return '%s = %s' % (self.lvalue, self.rvalue)

    @property
    def interactivePrint(self) -> bool:
        return False

    @staticmethod
    def parse(lvalue:Eval, _:Eq, rvalue:Eval) -> Eval:
        return Assignment(lvalue, rvalue)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        cell = cast(Cell, self.lvalue.evaluate(environment))
        value = self.rvalue.evaluate(environment)
        cell.set(value)
        return value


class Import(Eval):
    def __init__(self, name:str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return 'import %s' % self.name

    @property
    def interactivePrint(self) -> bool:
        return False

    @staticmethod
    def parse(_:Imp, name:Str) -> Eval:
        return Import(name.text)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        filename = self.name.replace('.', '/') + '.yaml'
        service = ServiceObject(self.name)

        try:
            environment.services[self.name] = Service.loadService(filename)
            environment.setVariable(self.name, service)
        except UnsupportedProtocol as ex:
            environment.error('Unsupport protocol "%s"' % ex.protocol)

        return service


class Describe(Eval):
    def __init__(self, keyword:str=None) -> None:
        self.keyword = keyword

    def __repr__(self) -> str:
        return 'help %s' % self.keyword

    @property
    def interactivePrint(self) -> bool:
        return False

    @staticmethod
    def parse(_:Help, keyword:Optional[Sym]=None) -> Eval:
        return Describe(keyword.text if keyword else None)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        if self.keyword is None:
            describe.environment(environment)
        elif environment.isVariable(self.keyword):
            describe.variable(environment, self.keyword)
        else:
            environment.error('%s is not defined' % self.keyword)

        return self


class Exit(Eval):
    def __repr__(self) -> str:
        return 'exit'

    @property
    def interactivePrint(self) -> bool:
        return False

    @staticmethod
    def parse(_:Ext) -> Eval:
        return Exit()

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        environment.loop = False
        return self


class TryException(Eval):
    def __init__(self, expr:Eval) -> None:
        self.expr = expr

    def __repr__(self) -> str:
        return 'try %s' % self.expr

    @staticmethod
    def parse(_:Try, expr:Eval) -> Eval:
        return TryException(expr)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        try:
            result = self.expr.evaluate(environment)
        except EvaluationError:
            result = Null()

        return result


class Call(Eval):
    def __init__(self, func:Eval, args:Dict[str,Eval]) -> None:
        self.func:Eval = func
        self.args:Dict[str,Eval] = args
        
    
    def __repr__(self) -> str:
        return '%s(%s)' % (
            repr(self.func),
            ', '.join('%s: %s' % (key, repr(self.args[key])) for key in self.args.keys())
            )

    @staticmethod
    def parse(func:Eval, _:LParen, args:ArgList, __:RParen) -> Eval:
        return Call(func, args.args)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        args = \
            { key: arg.evaluate(environment)
              for key, arg in self.args.items()
            }
        func = dereference(self.func.evaluate(environment))

        if not isinstance(func, Function):
            environment.error('%s is not a function' % func)

        params = cast(Function, func).parameters(environment)

        for param in params:
            if param not in args:
                environment.error('Missing argument %s should be %s' % \
                    ( param
                    , describe.article(params[param])
                    ))
            if params[param] == 'cell':
                if not isinstance(args[param], Cell):
                    environment.error('Parameter %s should be a variable or other cell not %s, %s' % \
                        ( param
                        , args[param]
                        , describe.article(
                            describe.typeName(args[param]))
                        ))
                    
            elif not dereference(args[param]).isType(params[param]):
                environment.error('Parameter %s should be %s not %s, %s' % \
                    ( param
                    , describe.article(params[param])
                    , args[param]
                    , describe.article(
                        describe.typeName(args[param]))
                    ))

        return cast(Function, func).call(environment, args)


class OpCall(Call):
    def __init__(self, op:Eval, left:Eval, right:Eval) -> None:
        super().__init__(
            op, 
            { 'left': left
            , 'right': right
            })

        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return '%s %s %s' % (
            repr(self.left),
            repr(self.op),
            repr(self.right)
            )

    @staticmethod
    def parse(left:Eval, op:Eval, right:Eval) -> Eval: #type:ignore
        return OpCall(op, left, right)


class Subscript(Eval):
    def __init__(self, array:Eval, sub:Eval) -> None:
        self.array = array
        self.subscript = sub

    @staticmethod
    def parse(array:Eval, _:LBracket, sub:Eval, __:RBracket) -> Eval:
        return Subscript(array, sub)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        array = dereference(self.array.evaluate(environment))

        if not isinstance(array, Array):
            environment.error('%s is not subscriptable' % array)

        sub = dereference(self.subscript.evaluate(environment))

        if not isinstance(sub, Integer):
            environment.error('%s cannot be used as a subscript' % sub)

        subValue = cast(Integer, sub).getValue()

        return cast(Array, array).get(subValue, environment)


class Group(Eval):
    def __init__(self, value:Eval) -> None:
        self.value = value

    def __repr__(self) -> str:
        return '(%s)' % repr(self.value)

    @staticmethod
    def parse(_:LParen, value:Eval, __:RParen) -> Eval:
        return Group(value)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        return self.value.evaluate(environment)


class Not(Eval):
    def __init__(self, value:Eval) -> None:
        self.value = value

    @staticmethod
    def parse(_:Bang, value:Eval) -> Eval:
        return Not(value)

    def evaluate(self, environment:Environment) -> Union[Eval, Cell]:
        value = dereference(self.value.evaluate(environment))

        if not isinstance(value, Boolean):
            environment.error('%s is not a boolean' % value)

        return Boolean(not cast(Boolean, value).getValue())

