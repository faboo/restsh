import sys
import os.path
from typing import Dict, Any, Optional, TextIO
from .service import Service
from . import terminal

class EvaluationError(Exception):
    pass

class Cell:
    def __init__(self, value:Any) -> None:
        self.value:Any = value.value if isinstance(value, Cell) else value

    def set(self, value:Any) -> None:
        if isinstance(value, Cell):
            value = value.value
        self.value = value

    def toPython(self) -> Any:
        if hasattr(self.value, 'toPython'):
            return self.value.toPython()
        else:
            return None

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return repr(self.value)

class Environment:
    def __init__(self, base:Optional['Environment']=None) -> None:
        #print('environment: %s (base? %s)' % (id(self), base is not None))
        self.base = base
        self.globals = False
        self.loop:bool = True
        self.ngParser:bool = False
        self.debugErrors:bool = False
        self.variables:Dict[str,Any] = {}
        self.services:Dict[str,Service] = {}
        self.lastError:Optional[Any] = None
        self.input:TextIO = sys.stdin
        self.output:TextIO = sys.stdout

        if base is not None:
            self.services = base.services

    def print(self, string:str, end='\n') -> None:
        print(string, end=end, file=self.output)

    def error(self, string) -> None:
        terminal.setForeground(self.output, 'red')
        self.print('error: %s' % string)
        terminal.reset(self.output)
        self.lastError = string
        raise EvaluationError(string)

    @property
    def homedir(self) -> str:
        return os.path.expanduser('~/.restsh/')

    @property
    def interactive(self) -> bool:
        return terminal.istty(self.input) # TODO: AND output?
        

    @property
    def lastResult(self) -> Any:
        return self.getVariable('__result')

    @lastResult.setter
    def lastResult(self, result:Any) -> None:
        self.setVariable('__result', result)

    def isVariable(self, name:str) -> bool:
        return name in self.variables

    def setVariable(self, name:str, value:Any) -> Cell:
        if name not in self.variables:
            if self.base and self.base.isVariable(name):
                self.variables[name] = self.base.variables[name]
            else:
                self.variables[name] = Cell(None)
        self.variables[name].set(value)
        return self.variables[name]

    def getVariable(self, name:str) -> Cell:
        if name not in self.variables:
            if self.base:
                return self.base.getVariable(name)
            else:
                self.error('Undefined variable: \'%s\'' % name)
        return self.variables[name]

    def getVariableValue(self, name:str) -> Any:
        return self.getVariable(name).value

