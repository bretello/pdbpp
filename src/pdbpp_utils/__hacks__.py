# This script is used by Python's site module.
# Doc: https://docs.python.org/3/library/site.html
# Code: https://github.com/blueyed/cpython/blob/1b293b600/Lib/site.py#L148-L187
#
# See `setup.py` for a similar setup for editable installs.


def hijack_pdb():
    """
    Add our "_pdbpp_path_hack" to the beginning of `sys.path` if:
    1. the environment variable PDBPP_HIJACK_PDB is trueish (as an int), defaults to 1.
       i.e. PDBPP_HIJACK_PDB=0 can be used to disable it.
    2. there is not another one already at the beginning
       (e.g. via a virtualenv using "include-system-site-packages")
    """
    import os
    import pathlib
    import sys

    _pdbpp_path = f"{os.path.sep}_pdbpp_path_hack"

    if int(os.getenv("PDBPP_HIJACK_PDB", 1)) and not sys.path[0].endswith(_pdbpp_path):
        sitedir = pathlib.Path(__file__).absolute().parents[1]
        sys.path.insert(0, (sitedir / "_pdbpp_path_hack").as_posix())
