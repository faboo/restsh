import sys
from . import terminal

ShowDebug = False

def debug(*strings:str) -> None:
    if ShowDebug:
        terminal.setBackground(sys.stdout, 'purple')
        print('   ', end='')
        terminal.reset(sys.stdout)
        print('', *strings)
