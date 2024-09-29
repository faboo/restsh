from typing import Any
import os.path
import importlib
import importlib.util
import sys
from .environment import Environment

def importModule(name:str, environment:Environment) -> None:
    shortname = name+'.py'
    homename = environment.homedir+shortname
    moduleName = 'dynrestsh'+name

    if os.path.exists(shortname):
        pathname = os.path.normpath(shortname)
    elif os.path.exists(homename):
        pathname = homename
    else:
        raise FileNotFoundError(shortname)

    spec = importlib.util.spec_from_file_location(moduleName, pathname)

    if spec is None:
        raise FileNotFoundError(shortname)

    module:Any = importlib.util.module_from_spec(spec)
    sys.modules[moduleName] = module
    if spec.loader is not None:
        spec.loader.exec_module(module)

    module.register(environment)

