"""
Convenient method to fillout an blacksmith registry.

::

  import blacksmith
  blacksmith.scan('mypkg.resources', 'other.resources')
"""

import importlib
import pkgutil


def scan(*modules: str) -> None:
    """
    Collect all resources to fillout the registry.

    Basically, it import modules registered using :func:`blacksmith.register`.

    :raises TypeError: malformed module name
    :raises ModuleNotFoundError: unknown package name
    :raises AttributeError: argument is a module, not a package.
    """
    for modname in modules:
        if modname.startswith("."):
            raise ValueError(f"{modname}: Relative package unsupported")
        mod = importlib.import_module(modname)
        if hasattr(mod, "__path__"):  # it means it is a __init__.py.
            for _loader, submod, _is_pkg in pkgutil.walk_packages(
                path=mod.__path__,
                prefix=mod.__name__ + ".",
            ):
                importlib.import_module(submod)
