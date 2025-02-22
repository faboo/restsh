from typing import cast, List
import traceback
from . import terminal
from .environment import Environment, EvaluationError, Cell
from .token import Token
from .reader import read, EndOfFile, UntokenizableError
from .parser import parse, ParseError, PartialParseError, EndOfTokens
from .evaluate import Eval
from .debug import debug

def printable(value:Eval) -> bool:
    if isinstance(value, Cell):
        return value.value.interactivePrint
    else:
        return value.interactivePrint
    

def repLoop(environment:Environment) -> Eval:
    parser = parse
    tokens:List[Token] = []

    while environment.loop:
        previousTokens = tokens
        tokens = []
        exprs = []

        terminal.setTitle(environment.output, 'restsh')

        try:
            try:
                tokens = read(environment, previousTokens)
                debug('tokenized: %s' % tokens)
            except EndOfFile:
                if previousTokens and environment.interactive:
                    previousTokens = []
                    environment.print('')
                else:
                    environment.loop = False
            except UntokenizableError as ex:
                environment.print(ex.message)

            if tokens:
                try:
                    exprs = parser(tokens)
                    tokens = []
                except PartialParseError:
                    #print('Got PartialParseError')
                    pass
                except ParseError as ex:
                    if ex.endOfTokens:
                        #print('ParseError end of tokens True')
                        if previousTokens == tokens:
                            terminal.setForeground(environment.output, 'red')
                            environment.print('parse error')
                            terminal.reset(environment.output)
                            tokens = []
                        else:
                            continue
                    else:
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
                            environment.print('%s' % repr(result))
                            terminal.reset(environment.output)
                        environment.lastResult = result
                except EvaluationError as ex:
                    if environment.debugErrors:
                        terminal.setForeground(environment.output, 'red')
                        traceback.print_exception(ex)
                        terminal.reset(environment.output)
                except Exception as ex:
                    terminal.setForeground(environment.output, 'red')
                    environment.print('INTERNAL INTERPRETER ERROR: %s' % str(ex))
                    terminal.reset(environment.output)
                    if environment.debugErrors:
                        raise
                    
        except KeyboardInterrupt:
            print('')


    return cast(Eval, environment.lastResult)


