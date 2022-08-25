from typing import cast, List
import sys
import os
from . import terminal
from .environment import Environment, EvaluationError, Cell
from .token import Token
from .reader import read, EndOfFile, UntokenizableError
from .parser import parse, ParseError, EndOfTokens, statement
from . import tableParser
from .evaluate import Eval

def printable(value:Eval) -> bool:
    if isinstance(value, Cell):
        return value.value.interactivePrint
    else:
        return value.interactivePrint
    

def repLoop(environment:Environment) -> Eval:
    parser = parse
    tokens:List[Token] = []

    if environment.ngParser:
        tparser = tableParser.Parser(statement)
        tparser.printTransitionTable()
        parser = tparser.parse

    while environment.loop:
        previousTokens = tokens
        tokens = []
        exprs = []

        terminal.setTitle(environment.output, 'restsh')

        try:
            try:
                tokens = read(environment, previousTokens)
                #print('tokenized: %s' % tokens)
            except EndOfFile:
                environment.loop = False
            except UntokenizableError as ex:
                environment.print(ex.message)

            if tokens:
                try:
                    #print('parsing')
                    exprs = parser(tokens)
                    tokens = []
                    #print('expression: %s' % exprs)
                except ParseError as ex:
                    terminal.setForeground(environment.output, 'red')
                    environment.print(
                        'parse error, expected one of: %s' % \
                        ', '.join([token.__name__ for token in set(ex.tokens)]))
                    terminal.reset(environment.output)
                    tokens = []
                except EndOfTokens:
                    #print('END OF TOKENS')
                    if previousTokens == tokens:
                        terminal.setForeground(environment.output, 'red')
                        environment.print('parse error')
                        terminal.reset(environment.output)
                        tokens = []
                    else:
                        continue
            
            if exprs:
                try:
                    #print('expressions: %s' % exprs)
                    for expr in exprs:
                        terminal.setTitle(environment.output, repr(expr)[:30])
                        result = expr.evaluate(environment)
                        # TODO: Just have a way to turn this off
                        if environment.input.isatty() and environment.output.isatty() and printable(expr):
                            terminal.setForeground(environment.output, environment.getVariable('*resultcolor').value)
                            environment.print('%s' % str(result))
                            terminal.reset(environment.output)
                        environment.lastResult = result
                except EvaluationError:
                    pass
                except Exception as ex:
                    terminal.setForeground(environment.output, 'red')
                    environment.print('INTERNAL INTERPRETER ERROR: %s' % str(ex))
                    terminal.reset(environment.output)
                    if environment.debugErrors:
                        raise
                    
        except KeyboardInterrupt:
            print('')


    return cast(Eval, environment.lastResult)


