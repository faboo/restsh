import sys
from . import terminal

showDebug = False

def debug(*strings:list[str]) -> None:
    if showDebug:
        terminal.setBackground(sys.stdout, 'purple')
        print('   ', end='')
        terminal.reset(sys.stdout)
        print('', *strings)
