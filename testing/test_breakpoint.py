import sys
import textwrap

import pytest

import pdbpp

from .test_pdb import PdbTest, check, set_trace_via_module


@pytest.fixture(autouse=True)
def hijack_breakpointhook(monkeypatch):
    """helper to hijack breakpoint() calls for tests"""
    from functools import partial

    breakpointhook = partial(set_trace_via_module, cleanup=False)
    monkeypatch.setattr("sys.breakpointhook", breakpointhook)
    yield

    pdbpp.cleanup()


def test_breakpoint():
    def fn():
        breakpoint()
        a = 1
        return a

    if sys.version_info >= (3, 13):
        expected = """
            [NUM] > .*fn()
            -> breakpoint()
               5 frames hidden .*
            # n
            [NUM] > .*fn()
            -> a = 1
               5 frames hidden .*
            # c
            """
    else:
        expected = """
            [NUM] > .*fn()
            -> a = 1
               5 frames hidden .*
            # c
            """

    check(fn, expected)


def test_breakpoint_remembers_previous_state():
    def fn():
        a = 1
        breakpoint()
        a = 2
        breakpoint()
        a = 3
        breakpoint()
        a = 4
        return a

    if sys.version_info >= (3, 13):
        expected = """
            [NUM] > .*fn()
            -> breakpoint()
               5 frames hidden .*
            # display a
            # c
            [NUM] > .*fn()
            -> breakpoint()
               5 frames hidden .*
            a: 1 --> 2
            # c
            [NUM] > .*fn()
            -> breakpoint()
               5 frames hidden .*
            a: 2 --> 3
            # c
            """
    else:
        expected = """
            [NUM] > .*fn()
            -> a = 2
               5 frames hidden .*
            # display a
            # c
            [NUM] > .*fn()
            -> a = 3
               5 frames hidden .*
            a: 1 --> 2
            # c
            [NUM] > .*fn()
            -> a = 4
               5 frames hidden .*
            a: 2 --> 3
            # c
            """

    check(fn, expected)
