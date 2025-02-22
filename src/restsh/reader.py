from typing import Tuple, Optional, List
import sys
import re
from .environment import Environment
from .token import Token, tokens

class UntokenizableError(Exception):
    def __init__(self, msg:str) -> None:
        super().__init__(msg)
        self.message = msg

class EndOfFile(Exception):
    pass


def readToken(line:str) -> Optional[Tuple[Token,str]]:
    for (token, exp) in tokens:
        match = exp.match(line)
        if match:
            text = match.group(0)
            line = line[len(text):]

            return (token(text), line.lstrip())

    return None


def tabCompleter(environment:Environment, text:str, state:int) -> Optional[str]:
    commands = ['help', 'exit', 'import', 'let']

    try:
        symre = '[_a-zA-Z][_a-zA-Z0-9]*'
        lastObjRef = re.search(f'({symre}(?:\\.{symre}|\\.)*)$', text)
        suggestions = []

        if not lastObjRef:
            suggestions = [key for key in environment.variables.keys() if re.match(symre, key)]
            suggestions = commands + suggestions
        else:
            syms = lastObjRef[0].split('.')

            if len(syms) == 1:
                suggestions = [key for key in environment.variables.keys() if re.match(symre, key)]
                suggestions = commands + suggestions
                suggestions = [sugg for sugg in suggestions if sugg.startswith(syms[0])]
            else:
                obj = environment.getVariableValue(syms[0])
                lastRef = syms[1]

                for ref in syms[1:-1]:
                    if ref:
                        obj = obj.get(ref, environment)
                        lastRef = ref

                prefix = '.'.join(syms[:-1])
                suggestions = [prefix+'.'+key for key in obj.properties if key.startswith(lastRef)]

    except Exception as ex:
        print('ex: %s' % ex)
    
    if state < len(suggestions):
        return suggestions[state]
    else:
        return None


def readTokens(line:str) -> List[Token]:
    tokens = []

    line = line.lstrip()

    while line:
        if line[0] == '#':
            break
            
        result = readToken(line)
        if not result:
            raise UntokenizableError('Unrecognized text: '+line[:20])

        token, line = result
        tokens.append(token)

    #print('Read tokens: ', tokens)

    return tokens
    

def read(environment:Environment, tokens:List[Token]) -> List[Token]:
    if environment.input == sys.stdin:
        if tokens:
            prompt = environment.getVariableValue('*continue')
        else:
            prompt = environment.getVariableValue('*prompt')
        try:
            line = input(prompt)
        except EOFError as ex:
            raise EndOfFile() from ex
        
    else:
        line = environment.input.readline()
        if not line:
            raise EndOfFile()
    #print('Read command: ', line)
    return tokens + readTokens(line)

