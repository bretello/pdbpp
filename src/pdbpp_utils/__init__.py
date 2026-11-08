try:
    from ._version import __version__
except ImportError:
    __version__ = "dev"


from . import completer_adapter
