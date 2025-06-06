import sys
from readline import __doc__ as readline_doc
from textwrap import dedent

import pytest

from .conftest import skip_with_missing_pth_file

HAS_GNU_READLINE = "GNU readline" in readline_doc


@pytest.mark.xfail(sys.version_info >= (3, 13), reason="flaky")
def test_integration(testdir, readline_param):
    tmpdir = testdir.tmpdir

    f = tmpdir.ensure("test_file.py")
    f.write(
        dedent("""
        print('before')

        breakpoint()
        print('after')
    """)
    )

    if "pyrepl" not in readline_param:
        # Create empty pyrepl module to ignore any installed pyrepl.
        mocked_pyrepl = tmpdir.ensure("pyrepl.py")
        mocked_pyrepl.write("")

    child = testdir.spawn(f"{sys.executable} test_file.py", expect_timeout=1)
    child.expect_exact("\n(Pdb++) ")

    if "pyrepl" not in readline_param:
        # Remove it after startup to not interfere with completions.
        mocked_pyrepl.remove()

    if "pyrepl" in readline_param:
        child.expect_exact("\x1b[?12l\x1b[?25h")
        pdbpp_prompt = "\n(Pdb++) \x1b[?12l\x1b[?25h"
    else:
        pdbpp_prompt = "\n(Pdb++) "

    # Completes help as unique (coming from pdb and fancycompleter).
    child.send(b"hel\t")
    if "pyrepl" in readline_param:
        child.expect_exact(b"\x1b[1@h\x1b[1@e\x1b[1@l\x1b[1@p")
    else:
        if not HAS_GNU_READLINE:
            reason = dedent("""
            When using readline instead of pyrepl, this will fail under libedit.
            This is the case for uv python builds.
            See here: https://github.com/astral-sh/python-build-standalone/blob/cda1c64dd1b3b7e457d3cc5efc5ff6bf7229f5a3/docs/quirks.rst#use-of-libedit-on-linux
            """).strip()
            pytest.xfail(reason)
        child.expect_exact(b"help")

    child.sendline("")
    child.expect_exact("\r\nDocumented commands")
    child.expect_exact(pdbpp_prompt)

    # Completes breakpoints via pdb, should not contain "\t" from
    # fancycompleter.
    child.send(b"b \t")
    if "pyrepl" in readline_param:
        child.expect_exact(b"\x1b[1@b\x1b[1@ \x1b[?25ltest_file.py:\x1b[?12l\x1b[?25h")
    else:
        child.expect_exact(b"b test_file.py:")

    child.sendline("")
    if "pyrepl" in readline_param:
        child.expect_exact(
            b"\x1b[23D\r\n\r\x1b[?1l\x1b>*** Bad lineno: \r\n"
            b"\x1b[?1h\x1b=\x1b[?25l\x1b[1A\r\n(Pdb++) \x1b[?12l\x1b[?25h"
        )
    else:
        child.expect_exact(b"\r\n*** Bad lineno: \r\n(Pdb++) ")

    child.sendline("c")
    rest = child.read()

    if "pyrepl" in readline_param:
        expected = b"\x1b[1@c\x1b[9D\r\n\r\x1b[?1l\x1b>"
    else:
        expected = b"c\r\n"

    if sys.version_info >= (3, 13):
        expected += b"after\r\n"

    assert rest == expected


@pytest.mark.xfail(
    sys.version_info >= (3, 12),
    reason="ipython integration with 3.13 is preliminary"
    if sys.version_info >= (3, 13)
    else "flaky",
)
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
    child.expect_exact("\r\nipdb++> ")
    child.sendline("c")
    child.expect_exact("\r\nValueError: my_value_error\r\n")
    child.expect_exact("\r\nIn [2]: ")
    child.sendeof()
    child.sendline("y")
    assert child.wait() == 0
