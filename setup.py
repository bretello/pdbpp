from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.editable_wheel import _encode_pth, _StaticPth, editable_wheel

if TYPE_CHECKING:
    from setuptools.command.editable_wheel import (
        Distribution,
        EditableStrategy,
        WheelFile,
    )

readme_path = Path(__file__).parent / "README.rst"
changelog_path = Path(__file__).parent / "CHANGELOG"

with open(readme_path, encoding="utf-8") as fh:
    readme = fh.read()
with open(changelog_path, encoding="utf-8") as fh:
    changelog = fh.read()

long_description = readme + "\n\n" + changelog


class CustomEditablePth(_StaticPth):
    """Inserts a custom module (path_hack_name) as the first element of sys.path"""

    def __init__(
        self, path_hack_name: str, dist: Distribution, name: str, src_dir: Path
    ) -> None:
        super().__init__(dist, name, [src_dir])
        self.path_hack = src_dir / path_hack_name

    def __call__(
        self, wheel: WheelFile, files: list[str], mapping: Mapping[str, str]
    ) -> None:
        assert all([p.resolve().exists() for p in self.path_entries]), (
            "module path does not exist"
        )

        path_hack = Path(__file__).with_name("pdbpp.pth").read_text()
        contents = _encode_pth(
            "\n".join(
                [
                    self.path_entries[0].resolve().as_posix(),
                    path_hack,
                ]
            ),
        )

        # include both .pth & .start
        wheel.writestr(f"__editable__.{self.name}.pth", contents)
        wheel.writestr(
            f"__editable__.{self.name}.start",
            Path(__file__).with_name("pdbpp.start").read_bytes(),
        )


class editable_install_with_startup_files(editable_wheel):
    """
    custom editable_wheel install so that `pip install -e .` also hijacks pdb with pdbpp
    """

    _path_hack_name: str = "_pdbpp_path_hack"  # must match name of module in `./src/`

    def _select_strategy(
        self,
        name: str,
        tag: str,
        build_lib: str | Path,
    ) -> EditableStrategy:
        # note: this requires src-layout
        src_dir = self.package_dir.get("", ".")

        src_dir = Path(self.project_dir, src_dir)
        return CustomEditablePth(
            self._path_hack_name,
            self.distribution,
            name,
            src_dir,
        )


class build_py_with_startup_files(build_py):
    """Include the .pth & .start files for this project, in the generated wheel."""

    includes_ = {"pdbpp.pth", "pdbpp.start"}

    def run(self):
        super().run()

        for include in self.includes_:
            self.copy_file(
                include,
                Path(self.build_lib, include),
                preserve_mode=0,
            )
            print(f"build_py_with_pth_file: include {include} in wheel")


setup(
    cmdclass={
        "editable_wheel": editable_install_with_startup_files,
        "build_py": build_py_with_startup_files,
    },
    platforms=[
        "unix",
        "linux",
        "osx",
        "cygwin",
        "win32",
    ],
)
