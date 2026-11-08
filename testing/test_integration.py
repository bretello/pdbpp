import glob
import importlib
import logging
import re
import subprocess
import sys
import sysconfig
from os import spawnl
from pathlib import Path
from shutil import which
from textwrap import dedent

import pexpect
import pytest

log = logging.getLogger(__name__)


class PexpectLog:
    """Capture full pexpect child output and print it on failure.

    pexpect's default error output only shows the last 100 chars of
    ``before``/``buffer``, making debugging difficult. This wraps the child
    to collect everything and dump it when a TIMEOUT/EOF is raised.
    """

    def __init__(self, child, name="child"):
        self.child = child
        self.name = name
        self.logfile = child.logfile

    def __enter__(self):
        return self.child

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, (pexpect.TIMEOUT, pexpect.EOF)):
            output = self.child.before or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            print(f"\n--- {self.name} full output before failure ---\n{output}\n--- end ---")
        return False


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

    with PexpectLog(child, "test_integration"):
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
        if sys.version_info >= (3, 15):
            # pdb uses pyrepl as its input console (GH-145378), which does
            # not complete an empty stem on tab, but indents instead.
            # Complete the file name with a non-empty stem.
            child.send(b"test_f\t")
            child.expect(b"ile\x1b\\[0m\\.\x1b\\[0mpy\x1b\\[0m:")
        elif sys.version_info < (3, 14):
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

    child = testdir.spawn(
        f"{sys.executable} -m IPython --colors=nocolor --simple-prompt",
        expect_timeout=1,
    )
    with PexpectLog(child, "test_ipython"):
        child.sendline("%debug raise ValueError('my_value_error')")
        child.sendline("up")
        child.expect_exact("ipdb++> ")
        child.sendline("c")
        child.expect_exact("ValueError: my_value_error")
        child.expect_exact("In [2]: ")
        child.sendeof()
        child.sendline("y")
        assert child.wait() == 0


def test_hijacking():
    """make sure that _pdbpp_path_hack is one of the first items in sys.path"""

    spec = importlib.util.find_spec("pdbpp")
    if spec is None or spec.origin is None:
        return False

    package_path = Path(spec.origin).parent

    if package_path.parts[-1] == "src":
        # editable install
        path_entry = sys.path[2]
    elif package_path.parts[-1] == "site-packages":
        # full install
        path_entry = sys.path[1]
    else:
        pytest.fail("Unknown install location/method?")

    stdlib_path = sysconfig.get_path("stdlib")

    path_hack_found = False
    for path_entry in sys.path:
        if "_pdbpp_path_hack" in path_entry:
            path_hack_found = True

        if path_entry != stdlib_path:
            continue

        if path_hack_found:
            break

        pytest.fail("stdlib path is not hijacked")


def test_editable_install_pth(tmp_path):
    """Make sure that running `pip install -e .` installs the .pth and .start files for pdb hijacking"""

    has_uv = which("uv")
    if has_uv:  # uv is faster in creating venvs
        venv_command = f"uv venv --python={sys.executable} --seed {tmp_path}"  # seed the env with pip
    else:
        venv_command = f"{sys.executable} -m venv {tmp_path}"

    subprocess.check_call(venv_command.split())

    python = tmp_path / "bin/python"

    pdbpp_root = Path(__file__).parent.parent

    install_command = f"pip install --no-deps -e {pdbpp_root}"
    if has_uv:
        install_command = f"uv {install_command} --python={python}"
    else:
        install_command = f"{python} -m {install_command}"

    subprocess.check_call(install_command.split())

    pths: list[Path] = list(
        glob.glob((tmp_path / "lib/*/site-packages/__editable__.pdbpp*.pth").as_posix())
    )

    assert len(pths) == 1

    editable_pth = Path(pths[0])
    pth_contents = editable_pth.read_text()

    assert pth_contents.splitlines()[0] == (pdbpp_root / "src").resolve().as_posix()
    assert (
        "import pdbpp_utils.__hacks__; pdbpp_utils.__hacks__.hijack_pdb()"
        in pth_contents
    )
    assert (
        editable_pth.with_suffix(".start").read_text()
        == (pdbpp_root / "pdbpp.start").read_text()
    )
