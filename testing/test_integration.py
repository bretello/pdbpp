import re
import sys
from os import spawnl
from textwrap import dedent

import pexpect
import pytest

from .conftest import skip_with_missing_pth_file


def test_integration(pytester, readline_param):
    with (pytester.path / "test_file.py").open("w") as fh:
        fh.write(
            dedent("""
            print('before')
            breakpoint()
            print('after')
        """)
        )

    child: pexpect.spawn = pytester.spawn(
        f"{sys.executable} test_file.py", expect_timeout=1
    )
    prompt = "(Pdb++) "

    child.expect_exact("before")
    if sys.version_info >= (3, 13):
        child.expect_exact("breakpoint")
    child.expect_exact(prompt)

    # Completes help as unique (coming from pdb and fancycompleter).
    child.send("hel\t")
    if sys.version_info >= (3, 13):
        child.expect_exact("help")
    else:
        child.expect_exact("\x1b[1@h\x1b[1@e\x1b[1@l\x1b[1@p")

    child.sendline()
    child.expect_exact("Documented commands")
    child.expect_exact(prompt)

    # Completes breakpoints via pdb, should not contain "\t" from
    # fancycompleter.
    child.send(b"b \t")
    if sys.version_info < (3, 14):
        child.expect(b"b.*test_file.py:")
    else:
        child.expect_exact("\x1b[0mb test_file\x1b[0m.\x1b[0mpy\x1b[0m:")

    child.sendline()
    child.sendline("c")
    child.expect("after")
    child.expect(pexpect.EOF)


def test_ipython(testdir):
    """Test integration when used with IPython.

    - `up` used to crash due to conflicting `hidden_frames` attribute/method.
    """
    pytest.importorskip("IPython")
    skip_with_missing_pth_file()

    child = testdir.spawn(
        f"{sys.executable} -m IPython --colors=nocolor --simple-prompt",
        expect_timeout=1,
    )
    child.sendline("%debug raise ValueError('my_value_error')")
    child.sendline("up")
    child.expect_exact("ipdb++> ")
    child.sendline("c")
    child.expect_exact("ValueError: my_value_error")
    child.expect_exact("In [2]: ")
    child.sendeof()
    child.sendline("y")
    assert child.wait() == 0
