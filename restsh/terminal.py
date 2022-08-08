import os
from .environment import Environment

def istty(func):
    def wrap(environment:Environment, *args):
        if not environment.output.isatty():
            return

        func(environment, *args)

    return wrap
            

class Foreground:
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    orange = '\033[33m'
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'
    lightgrey = '\033[37m'
    darkgrey = '\033[90m'
    lightred = '\033[91m'
    lightgreen = '\033[92m'
    yellow = '\033[93m'
    lightblue = '\033[94m'
    pink = '\033[95m'
    lightcyan = '\033[96m'
 
class Background:
    black = '\033[40m'
    red = '\033[41m'
    green = '\033[42m'
    orange = '\033[43m'
    blue = '\033[44m'
    purple = '\033[45m'
    cyan = '\033[46m'
    lightgrey = '\033[47m'
    


@istty
def reset(environment:Environment) -> None:
    environment.output.write('\033[0m')


@istty
def setForeground(environment:Environment, string:str) -> None:
    environment.output.write(getattr(Foreground, string))


@istty
def setBackground(environment:Environment, string:str) -> None:
    environment.output.write(getattr(Background, string))


