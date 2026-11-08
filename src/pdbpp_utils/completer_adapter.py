"""Adapter for fancycompleter.

As of python>=3.15 (see https://github.com/python/cpython/pull/130473),
[fancycompleter](https://github.com/bretello/fancycompleter) has been
integrated in the interpreter. This module provides an adapter to ensure
compatibility with the standalone fancycompleter module in python<=3.14
and the bundled fancycompleter in `_pyrepl` in 3.15+.

`ConfigurableClass` class from fancycompleter https://github.com/bretello/fancycompleter/blob/0.11.0/fancycompleter/__init__.py#L139
has been vendored in this module from fancycompleter to ensure compatibility
in 3.15 as it has been dropped from _pyrepl.fancycompleter.
"""

from __future__ import annotations

import contextlib
import os.path
import re
import sys

__all__ = [
    "Color",
    "ConfigurableClass",
    "clean_matches",
    "commonprefix",
    "get_completer",
    "readline_module",
    "restore",
    "setup",
    "uses_pyrepl",
]

REMOVE_ESCAPE_SEQS = re.compile(r"\x1b\[[\d;]*m")


def _execfile(filename, namespace):
    with open(filename) as f:
        code = compile(f.read(), filename, "exec")
        exec(code, namespace)


class ConfigurableClass:
    """Load a ``Config`` class from ``~/{config_filename}``, if any.

    Vendored from fancycompleter, so that it is also available with the
    stdlib completer on Python >= 3.15.
    """

    DefaultConfig = None
    config_filename = None

    def get_config(self, Config):
        if Config is not None:
            return Config()

        # try to load config from the ~/filename file
        filename = f"~/{self.config_filename}"
        rcfile = os.path.normpath(os.path.expanduser(filename))
        if not os.path.exists(rcfile):
            if self.DefaultConfig is None:
                raise ValueError("DefaultConfig cannot be None")

            return self.DefaultConfig()

        namespace = {}
        try:
            _execfile(rcfile, namespace)
        except Exception as exc:
            import traceback

            sys.stderr.write(f"** error when importing {filename}: {exc!r} **\n")
            traceback.print_tb(sys.exc_info()[2])
            if self.DefaultConfig is None:
                raise ValueError("DefaultConfig cannot be None") from None

            return self.DefaultConfig()

        try:
            Config = namespace["Config"]
        except KeyError:
            if self.DefaultConfig is None:
                raise ValueError("DefaultConfig cannot be None") from None

            return self.DefaultConfig()

        try:
            return Config()
        except Exception as exc:
            err = f"error when setting up Config from {filename}: {exc}"
            tb = sys.exc_info()[2]
            if tb and tb.tb_next:
                tb = tb.tb_next
                err_fname = tb.tb_frame.f_code.co_filename
                err_lnum = tb.tb_lineno
                err += f" ({err_fname}:{err_lnum})"
            sys.stderr.write(f"** {err} **\n")

        if self.DefaultConfig is None:
            raise ValueError("DefaultConfig cannot be None")

        return self.DefaultConfig()


if sys.version_info >= (3, 15):
    from _pyrepl import fancycompleter as _stdlib_fancycompleter
    from _pyrepl import readline as _pyrepl_readline

    class Color:
        """Mirror of fancycompleter's Color."""

        black = "30"
        darkred = "31"
        darkgreen = "32"
        brown = "33"
        darkblue = "34"
        purple = "35"
        teal = "36"
        lightgray = "37"
        darkgray = "30;01"
        red = "31;01"
        green = "32;01"
        yellow = "33;01"
        blue = "34;01"
        fuchsia = "35;01"
        turquoise = "36;01"
        white = "37;01"

        @classmethod
        def set(cls, color, string):
            with contextlib.suppress(AttributeError):
                color = getattr(cls, color)
            return f"\x1b[{color}m{string}\x1b[00m"

    def get_completer(namespace):
        return _stdlib_fancycompleter.Completer(namespace)

    def setup(completer, complete):
        """Install ``complete`` as readline completer, return the old one."""
        old_completer = _pyrepl_readline.get_completer()
        _pyrepl_readline.parse_and_bind("tab: complete")
        _pyrepl_readline.set_completer(complete)
        return old_completer

    def restore(completer, old_completer):
        _pyrepl_readline.set_completer(old_completer)

    def readline_module(completer):
        return _pyrepl_readline

    def uses_pyrepl(completer):
        return True

    def commonprefix(names):
        return _stdlib_fancycompleter.commonprefix(names)

    def clean_matches(matches):
        # The stdlib completer colorizes matches using _colorize.
        return [REMOVE_ESCAPE_SEQS.sub("", x) for x in matches]

else:
    import fancycompleter
    from fancycompleter import Color, Completer  # noqa: F401

    def get_completer(namespace):
        return Completer(namespace)

    def setup(completer, complete):
        """Install ``complete`` as readline completer, return the old one."""
        readline = completer.config.readline
        old_completer = readline.get_completer()
        if fancycompleter.has_libedit(completer.config):
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        readline.set_completer(complete)
        return old_completer

    def restore(completer, old_completer):
        completer.config.readline.set_completer(old_completer)

    def readline_module(completer):
        return completer.config.readline

    def uses_pyrepl(completer):
        return completer.config.readline != sys.modules["readline"]

    def commonprefix(names):
        return fancycompleter.commonprefix(names)

    def clean_matches(matches):
        # Strip ANSI escape sequences, so that colorized matches from the
        # standalone package can be deduped against pdb's plain matches.
        return [REMOVE_ESCAPE_SEQS.sub("", x) for x in matches]
