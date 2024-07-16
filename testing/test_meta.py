import pytest

import pdbpp


def test_mod_attributeerror():
    with pytest.raises(AttributeError) as excinfo:
        pdbpp.doesnotexist  # noqa: B018
    assert str(excinfo.value) == "module 'pdbpp' has no attribute 'doesnotexist'"
