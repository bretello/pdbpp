import os.path
from sysconfig import get_path

from setuptools import setup

readme_path = os.path.join(os.path.dirname(__file__), "README.rst")
changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG")

with open(readme_path, encoding="utf-8") as fh:
    readme = fh.read()
with open(changelog_path, encoding="utf-8") as fh:
    changelog = fh.read()

long_description = readme + "\n\n" + changelog

setup(
    name="pdbpp",
    use_scm_version=True,
    author="Antonio Cuni",
    author_email="anto.cuni@gmail.com",
    package_dir={"": "src"},
    url="https://github.com/pdbpp/pdbpp",
    project_urls={
        "Bug Tracker": "https://github.com/pdbpp/pdbpp/issues",
        "Source Code": "https://github.com/pdbpp/pdbpp",
    },
    license="BSD",
    platforms=["unix", "linux", "osx", "cygwin", "win32"],
    description="pdb++, a drop-in replacement for pdb",
    long_description=long_description,
    keywords=["pdb", "debugger", "tab", "color", "completion"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python",
        "Topic :: Utilities",
        "Topic :: Software Development :: Debuggers",
    ],
    install_requires=[
        "fancycompleter @ git+https://github.com/bretello/fancycompleter@0.10.5",  # noqa: E501
        "pygments",
    ],
    extras_require={
        "testing": [
            "pytest",
            "pytest-cov",
            "ipython",
            "pexpect",
        ],
    },
    setup_requires=["setuptools_scm"],
    data_files=[
        (
            os.path.relpath(get_path("purelib"), get_path("data")),
            ["pdbpp_hijack_pdb.pth"],
        ),
    ],
)
