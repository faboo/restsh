import argparse
import sys
import os
from typing import Optional
from .environment import Environment
from .repl import repLoop
from .reader import tabCompleter
from .evaluate import wrap, Null, Boolean
from .modules import builtins
from .modules import operators
from .modules import http
from .modules import time
from .modules import file
from .modules import session
from . import describe
from . import debug

def setupArguments(args:list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='restsh',
        description='REST and RPC processing shell.')
    parser.add_argument('--environment', '-e', action='append', default=[],
        help='A script to run before opening the prompt or running the main script')
    parser.add_argument('--skip-rc', '-s', action='store_true', default=False)
    #parser.add_argument('--ng-parser', action='store_true', default=False)
    parser.add_argument('--debug-internals', action='store_true', default=False,
        help='Turn on debugging info for the shell itself')
    parser.add_argument('--version', action='store_true', default=False,
        help='Print the restsh version and exit')
    parser.add_argument('script', nargs='?')
    parser.add_argument('scriptargs', nargs='*')

    return parser.parse_args()


def setupReadline(environment:Environment) -> None:
    try:
        import readline #pylint: disable=import-outside-toplevel
        historyName = os.path.expanduser('~/.restsh_history')
        readline.read_history_file(historyName)
        readline.set_history_length(100)
        readline.parse_and_bind("tab: menu-complete")
        readline.set_completer(lambda text, state: tabCompleter(environment, text, state))
        readline.set_completer_delims(" \t\n")
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
    print("Copyright (C) 2024 Raymond W. Wallace III")
    print("License GPLv2: GNU GPL version 2 <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>")
    print("")
    print("This is free software; you are free to change and redistribute it.")
    print("There is NO WARRANTY, to the extent permitted by law.")
    sys.exit(1)


def createBaseEnv(arguments:argparse.Namespace) -> Environment:
    environment = Environment()

    environment.setVariable('args', wrap(arguments.scriptargs))
    environment.setVariable('env', wrap({**os.environ}))
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
    time.register(environment)
    file.register(environment)
    session.register(environment)

    return environment


def main(args:Optional[list]=None):
    arguments = setupArguments(args or sys.argv[1:])
    historyName = os.path.expanduser('~/.restsh_history')
    rcfile = os.path.expanduser('~/.restshrc')

    if arguments.version:
        printVersion()

    # ensure the history file exists
    with open(historyName, mode='a', encoding='utf-8') as history:
        history.write('')

    # Base the global environment of a base environment.
    environment = Environment(createBaseEnv(arguments))
    environment.globals = True
    #environment.ngParser = arguments.ng_parser
    environment.debugErrors = arguments.debug_internals
    debug.ShowDebug = arguments.debug_internals


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
            setupReadline(environment)
            describe.printWrapped(environment, describe.LeaderHelp)
            repLoop(environment)
        finally:
            writeHistory()
            environment.print('')

    return 0

if __name__ == "__main__":
    sys.exit(main())
