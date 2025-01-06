import glob
import os

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = "lint", "tests"
nox.options.default_venv_backend = "uv"
locations = "src", "testing"


@nox.session(
    python=[
        "3.9",
        "3.10",
        "3.11",
        "3.12",
        "3.13",
        "pypy3.8",
        "pypy3.9",
        "pypy3.10",
    ]
)
def tests(session: nox.Session) -> None:
    session.install(".[testing]")
    session.run(
        "pytest",
        "--cov-config=pyproject.toml",
        *session.posargs,
        env={"COVERAGE_FILE": f".coverage.{session.python}"},
    )


@nox.session
def lint(session: nox.Session) -> None:
    session.install(
        "ruff",
        # "mypy",
    )
    session.install("-e", ".[testing]")

    session.run("ruff", "check", "src", "testing")
    # session.run("python", "-m", "mypy")


@nox.session
def build(session: nox.Session) -> None:
    session.install("build", "setuptools", "twine")
    session.run("python", "-m", "build")
    dists = glob.glob("dist/*")
    session.run("twine", "check", *dists, silent=True)


@nox.session
def dev(session: nox.Session) -> None:
    """Sets up a python development environment for the project."""
    args = session.posargs or ("venv",)
    venv_dir = os.fsdecode(os.path.abspath(args[0]))

    session.log(f"Setting up virtual environment in {venv_dir}")
    session.install("virtualenv")
    session.run("virtualenv", venv_dir, silent=True)

    python = os.path.join(venv_dir, "bin/python")
    session.run(python, "-m", "pip", "install", "-e", ".[testing]", external=True)
