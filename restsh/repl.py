from typing import cast, List
import sys
from .environment import Environment, EvaluationError, Cell
from .token import Token
from .reader import read, EndOfFile, UntokenizableError
from .parser import parse, ParseError, EndOfTokens
from .evaluate import Eval

def printable(value:Eval) -> bool:
    if isinstance(value, Cell):
        return value.value.interactivePrint
    else:
        return value.interactivePrint
    

def repLoop(environment:Environment) -> Eval:
    tokens:List[Token] = []

    while environment.loop:
        previousTokens = tokens
        tokens = []
        exprs = []

        try:
            tokens = read(environment, previousTokens)
            print('tokenized: %s' % tokens)
        except EndOfFile:
            environment.loop = False
        except UntokenizableError as ex:
            environment.print(ex.message)

        if tokens:
            try:
                #print('parsing')
                exprs = parse(tokens)
                tokens = []
                print('expression: %s' % exprs)
            except ParseError as ex:
                environment.print(
                    'parse error, expected one of: %s' % \
                    ', '.join([token.__name__ for token in set(ex.tokens)]))
            except EndOfTokens:
                print('END OF TOKENS')
                if previousTokens == tokens:
                    environment.print('parse error')
                    tokens = []
                else:
                    continue
        
        if exprs:
            try:
                print('expressions: %s' % exprs)
                for expr in exprs:
                    result = expr.evaluate(environment)
                    if environment.input == sys.stdin and printable(expr):
                        environment.print('%s' % str(result))
                    environment.lastResult = result
            except EvaluationError:
                pass


    return cast(Eval, environment.lastResult)


