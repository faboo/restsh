from typing import cast, Union, Dict, Any
from datetime import datetime, timezone
import dateutil.parser as dateparser
import dateutil.tz
from ..moduleUtils import builtin
from ..environment import Environment, Cell
from ..evaluate import dereference, wrap, DictObject, String, Constant, Eval

class Time(Constant):
    def __init__(self, time:datetime) -> None:
        super().__init__()
        self.time = time
    
    def getValue(self) -> Any:
        return self.time
        
    def __repr__(self) -> str:
        return '<%s>' % self.time
        
    def __str__(self) -> str:
        return self.time.isoformat()

    def toPython(self) -> Any:
        return str(self.time)

    def isType(self, typeDesc:str) -> bool:
        return super().isType(typeDesc) or typeDesc == 'time'


@builtin('now', [], 'Returns a new Time object with the current time and date.')
def bNow(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    return Time(datetime.now(timezone.utc))


@builtin('show', [('time', 'time'), ('tz', 'string')], 'Convert a Time to a string in ISO format.')
def bShow(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()
    tzstr = cast(String, dereference(args['tz'])).getValue()

    time = time.astimezone(dateutil.tz.gettz(tzstr))

    return wrap(time.isoformat())


@builtin('showhttp', [('time', 'time'), ('tz', 'string')], 'Convert a Time to a string in HTTP format.')
def bShowhttp(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()
    tzstr = cast(String, dereference(args['tz'])).getValue()

    time = time.astimezone(dateutil.tz.gettz(tzstr))

    # TODO: This should use the en_US for the RFC-correct day and month names
    # TODO: I don't think this is quite correct (because of 0 padding)
    return wrap(time.strftime('%a, %d %b %Y %H:%M:%S %Z'))


@builtin('parse', [('str', 'string')], 'Generically parse a date/time string.')
def bParse(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    string = cast(String, dereference(args['str'])).getValue()

    time = dateparser.parse(string)
    if time.tzinfo is None:
        time = time.replace(tzinfo=timezone.utc)
    else:
        time = time.astimezone(timezone.utc)

    return Time(time)


@builtin('timestamp', [('time', 'time')], 'Convert a Time to a Unix timestamp.')
def bTimestamp(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    time = cast(Time, dereference(args['time'])).getValue()

    return wrap(time.timestamp())


@builtin(
    'lt',
    [('left', 'time'), ('right', 'time')],
    'Returns true if the \'left\' argument is before (less than) the \'right\'.')
def bLt(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    left = cast(Time, dereference(args['left'])).getValue()
    right = cast(Time, dereference(args['right'])).getValue()

    return wrap(left < right)


@builtin(
    'gt',
    [('left', 'time'), ('right', 'time')],
    'Returns true if the \'left\' argument is after (greater than) the \'right\'.')
def bGt(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:
    left = cast(Time, dereference(args['left'])).getValue()
    right = cast(Time, dereference(args['right'])).getValue()

    return wrap(left > right)


def register(environment:Environment):
    timeObj = DictObject(
        { 'now': bNow
        , 'show': bShow
        , 'showhttp': bShowhttp
        , 'parse': bParse
        , 'timestamp': bTimestamp
        , 'lt': bLt
        , 'gt': bGt
        })
    timeObj.description = 'Functions to create and manipulate Time.'
    environment.setVariable('time', timeObj)
