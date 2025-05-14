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
    cmdclass={"build_py": build_py_with_pth_file},
    platforms=[
        "unix",
        "linux",
        "osx",
        "cygwin",
        "win32",
    ],
)
