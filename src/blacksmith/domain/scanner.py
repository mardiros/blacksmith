"""
Scanning Resources
==================

Convenient method to fillout an blacksmith registry.

::

  import blacksmith
  blacksmith.scan('mypkg.resources', 'other.resources')
"""
import importlib
import pkgutil


def scan(*modules: str):
    """
    Collect all resources to fillout the registry.

    Basically, it import modules containins :func:`blacksmith.register` calls.

    """
    for mod in modules:
        mod = importlib.import_module(mod)
        for loader, submod, _is_pkg in pkgutil.walk_packages(
            path=mod.__path__,
            prefix=mod.__name__ + ".",
        ):
            loader.find_module(submod).load_module(submod)
