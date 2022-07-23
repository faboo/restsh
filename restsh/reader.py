from typing import Tuple, Optional, List
import sys
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


def readTokens(line:str) -> List[Token]:
    tokens = []

    line = line.lstrip()

    while line:
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

