from typing import cast, Union, Dict, Callable, Tuple, Optional, Any
from ..environment import Environment, Cell, EvaluationError
from ..evaluate import wrap, dereference, Eval, Builtin, Boolean, Constant

operators:Dict[
        str,
        Tuple[
            Callable[[Environment, Dict[str,Union[Eval, Cell]]], Union[Eval, Cell]],
            Tuple[str, str]
            ]
        ] = { }


def add(name:str, args:Tuple[str,str], retwrap:Optional[Callable[[Any], Union[Eval, Cell]]]=None
        ) -> Any:
    def wrapper(func:Callable[[Any, Any], Any]
            ) -> Callable[[Environment, Dict[str,Union[Eval, Cell]]], Union[Eval, Cell]]:
        def run(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
            left = dereference(args['left'])
            right = dereference(args['right'])

            try:
                result = func(cast(Constant, left).getValue(), cast(Constant, right).getValue())

                if retwrap:
                    return retwrap(result)
                else:
                    return wrap(result)
            except EvaluationError:
                raise
            except Exception as ex:
                environment.error("%s: %s" % (ex.__class__.__name__, ' '.join(ex.args)))
                return wrap(None)

        operators[name] = (run, args)

        return run

    return wrapper


def bEqual(environment:Environment, args:Dict[str,Union[Cell, Eval]]) -> Union[Eval, Cell]:
    return Boolean(dereference(args['left']).equal(dereference(args['right'])))
operators['=='] = (bEqual, ('any', 'any'))


def bNotEqual(environment:Environment, args:Dict[str,Union[Cell, Eval]]) -> Union[Eval, Cell]:
    return Boolean(not dereference(args['left']).equal(dereference(args['right'])))
operators['~='] = (bEqual, ('any', 'any'))


@add('+', ('number', 'number'))
def bAdd(left:Union[int,float], right:Union[int,float]) -> Union[int,float]:
    return left + right


@add('-', ('number', 'number'))
def bMinus(left:Union[int,float], right:Union[int,float]) -> Union[int,float]:
    return left - right


@add('*', ('number', 'number'))
def bMultiply(left:Union[int,float], right:Union[int,float]) -> Union[int,float]:
    return left * right


@add('/', ('number', 'number'))
def bDivide(left:Union[int,float], right:Union[int,float]) -> Union[int,float]:
    return left / right


@add('<', ('number', 'number'))
def bLessThan(left:Union[int,float], right:Union[int,float]) -> bool:
    return left < right


@add('>', ('number', 'number'))
def bGreaterThan(left:Union[int,float], right:Union[int,float]) -> bool:
    return left > right


@add('||', ('boolean', 'boolean'))
def bOr(left:bool, right:bool) -> bool:
    return left or right


@add('&&', ('boolean', 'boolean'))
def bAnd(left:bool, right:bool) -> bool:
    return left and right


@add('|', ('string', 'string'))
def bConcat(left:str, right:str) -> str:
    return left + right


def register(environment:Environment):
    for name, (operator, (left, right)) in operators.items():
        environment.setVariable(
            name,
            Builtin(name, operator, [('left', left), ('right', right)]))


