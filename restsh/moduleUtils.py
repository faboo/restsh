from typing import Dict, Optional, Any, Union, Callable
from .environment import Environment, Cell
from .evaluate import Builtin, Eval, dereference, wrap

def builtin(
        name:str,
        params:list[tuple[str,str]],
        desc:Optional[str]=None
        ) -> Any:
    def wrapper(func:Callable[[Any, Any], Any]) -> Builtin:
        def run(environment:Environment, args:Dict[str,Union[Eval, Cell]]) -> Union[Eval, Cell]:

            try:
                result = func(environment, {key: dereference(arg) for key, arg in args.items()})

                return wrap(result)
            except Exception as ex:
                environment.error("%s: %s" % (ex.__class__.__name__, ' '.join(ex.args)))
                return wrap(None)

        return Builtin(name, run, params, desc)

    return wrapper

