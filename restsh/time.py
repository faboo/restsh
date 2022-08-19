from typing import cast, Union, Dict, Callable, Tuple, List, Optional, Any
from datetime import datetime, timezone
import dateutil.parser as dateparser
import dateutil.tz
from .environment import Environment, Cell
from .evaluate import dereference, wrap, DictObject, Builtin, String, Constant, Eval

class Time(Constant):
    def __init__(self, time:datetime) -> None:
        super().__init__()
        self.time = time
    
    def getValue(self) -> Any:
        return self.time
        
    def __repr__(self) -> str:
        return '<%s>' % self.time

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'time'


def bNow(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    return Time(datetime.now(timezone.utc))


def bShow(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()
    tzstr = cast(String, dereference(args['tz'])).getValue()

    time = time.astimezone(dateutil.tz.gettz(tzstr))

    return wrap(time.isoformat())


def bShowhttp(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()
    tzstr = cast(String, dereference(args['tz'])).getValue()

    time = time.astimezone(dateutil.tz.gettz(tzstr))

    # TODO: This should use the en_US for the RFC-correct day and month names
    # TODO: I don't think this is quite correct (because of 0 padding)
    return wrap(time.strftime('%a, %d %b %Y %H:%M:%S %Z'))


def bParse(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    string = cast(String, dereference(args['str'])).getValue()

    time = dateparser.parse(string)
    if time.tzinfo is None:
        time = time.replace(tzinfo=timezone.utc)
    else:
        time = time.astimezone(dateutil.tz.gettz(tzstr))

    return Time(time)


def bTimestamp(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()

    return wrap(time.timestamp())


def bLt(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    left = cast(Time, dereference(args['left'])).getValue()
    right = cast(Time, dereference(args['right'])).getValue()

    return wrap(left < right)


def bGt(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    left = cast(Time, dereference(args['left'])).getValue()
    right = cast(Time, dereference(args['right'])).getValue()

    return wrap(left > right)


def register(environment:Environment):
    timeObj = DictObject(
        { 'now': Builtin('now', bNow, {}, 'Returns a new Time object with the current time and date.')
        , 'parse': Builtin('parse', bParse, {'str': 'string'}, 'Generically parse a date/time string.')
        , 'show': Builtin('show',
            bShow,
            {'time': 'time', 'tz': 'string'},
            'Convert a Time to a string in ISO format.')
        , 'showhttp': Builtin('showhttp',
            bShowhttp,
            {'time': 'time', 'tz': 'string'},
            'Convert a Time to a string in HTTP request format.')
        , 'timestamp': Builtin('timestamp',
            bTimestamp,
            {'time': 'time'},
            'Convert a Time to a Unix timestamp.')
        , 'lt': Builtin('lt', bLt, {'left': 'time', 'right': 'time'})
        , 'gt': Builtin('gt', bGt, {'left': 'time', 'right': 'time'})
        })
    timeObj.description = 'Functions to create and manipulate Time.'
    environment.setVariable('time', timeObj)
