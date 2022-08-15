import argparse
import sys
import os
from .environment import Environment
from .repl import repLoop
from .evaluate import Null, Boolean
from . import builtins
from . import operators
from . import http
from . import describe
from . import parser

def setupArguments(args:list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='restsh',
        description='REST and RPC processing shell.')
    parser.add_argument('--environment', '-e', action='append', default=[])
    parser.add_argument('--skip-rc', '-s', action='store_true', default=False)
    parser.add_argument('--ng-parser', action='store_true', default=False)
    parser.add_argument('--debug-errors', action='store_true', default=False)
    parser.add_argument('--version', action='store_true', default=False)
    parser.add_argument('script', nargs='?')

    return parser.parse_args()


def readHistory() -> None:
    try:
        import readline #pylint: disable=import-outside-toplevel
        historyName = os.path.expanduser('~/.restsh_history')
        readline.read_history_file(historyName)
        readline.set_history_length(100)
    except: #pylint: disable=bare-except
        pass


def writeHistory() -> None:
    try:
        import readline #pylint: disable=import-outside-toplevel
        historyName = os.path.expanduser('~/.restsh_history')
        readline.write_history_file(historyName)
    except: #pylint: disable=bare-except
        pass


def printVersion() -> None:
    print("REST Shell v1.0")
    sys.exit(1)


def main(args:list=None):
    arguments = setupArguments(args or sys.argv[1:])
    historyName = os.path.expanduser('~/.restsh_history')
    rcfile = os.path.expanduser('~/.restshrc')

    if arguments.version:
        printVersion()

    # ensure the history file exists
    with open(historyName, mode='a', encoding='utf-8') as history:
        print('', file=history)

    environment = Environment()

    environment.ngParser = arguments.ng_parser
    environment.debugErrors = arguments.debug_errors

    environment.setVariable('__result', Null())
    environment.setVariable('null', Null())
    environment.setVariable('true', Boolean(True))
    environment.setVariable('false', Boolean(False))
    environment.setVariable('*prompt', '$ ')
    environment.setVariable('*continue', '.  ')
    environment.setVariable('*resultcolor', 'green')

    builtins.register(environment)
    operators.register(environment)
    http.register(environment)

    if not arguments.skip_rc and os.path.exists(rcfile):
        with open(rcfile, 'r', encoding='utf-8') as rsource:
            environment.input = rsource
            repLoop(environment)
            environment.input = sys.stdin
            environment.loop = True

    for envFile in arguments.environment:
        with open(envFile, 'r', encoding='utf-8') as env:
            environment.input = env
            repLoop(environment)
            environment.input = sys.stdin
            environment.loop = True

    if arguments.script:
        with open(arguments.script, 'r', encoding='utf-8') as script:
            environment.input = script
            repLoop(environment)

    else:
        try:
            readHistory()
            describe.printWrapped(environment, describe.LeaderHelp)
            repLoop(environment)
        finally:
            writeHistory()
            environment.print('')

    return 0

if __name__ == "__main__":
    sys.exit(main())
