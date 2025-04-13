import os.path

from setuptools import setup
from setuptools.command.build_py import build_py

readme_path = os.path.join(os.path.dirname(__file__), "README.rst")
changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG")

with open(readme_path, encoding="utf-8") as fh:
    readme = fh.read()
with open(changelog_path, encoding="utf-8") as fh:
    changelog = fh.read()

long_description = readme + "\n\n" + changelog


class build_py_with_pth_file(build_py):
    """Include the .pth file for this project, in the generated wheel."""

    pth_file = "pdbpp_hijack_pdb.pth"

    def run(self):
        super().run()

        self.copy_file(
            self.pth_file,
            os.path.join(self.build_lib, self.pth_file),
            preserve_mode=0,
        )


setup(
    name="pdbpp",
    use_scm_version=True,
    author="Antonio Cuni",
    author_email="anto.cuni@gmail.com",
    maintainer="bretello",
    maintainer_email="bretello@distruzione.org",
    package_dir={"": "src"},
    url="https://github.com/bretello/pdbpp",
    project_urls={
        "Bug Tracker": "https://github.com/bretello/pdbpp/issues",
        "Source Code": "https://github.com/bretello/pdbpp",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python",
        "Topic :: Utilities",
        "Topic :: Software Development :: Debuggers",
    ],
    install_requires=[
        "fancycompleter>=0.11.0",
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
    cmdclass={"build_py": build_py_with_pth_file},
)
