import pytest
from ansible.errors import AnsibleFilterError
from plugins.filter.utils import (
    to_mib,
    mib
)

def test_to_mib_with_valid_units():
    assert to_mib("512m") == 512.0
    assert to_mib("1g") == 1024.0
    assert to_mib("2g") == 2048.0
    assert to_mib("1t") == 1048576.0
    assert to_mib(1024) == 1024.0
    assert to_mib(512.5) == 512.5

def test_to_mib_with_invalid_unit():
    with pytest.raises(AnsibleFilterError, match="Unsupported or invalid size format"):
        to_mib("100x")

def test_to_mib_with_invalid_type():
    with pytest.raises(AnsibleFilterError, match="Invalid type for size"):
        to_mib(["not", "a", "string"])

def test_mib_with_numeric_input():
    assert mib(1024) == "1024MiB"
    assert mib(1000.0) == "1000MiB"
    assert mib(1000.0, align=24) == "1024MiB"

def test_mib_with_percentage_string():
    assert mib("100%") == "100%"

def test_mib_with_string_number():
    assert mib("1000") == "1000MiB"
    assert mib("1000", align=48) == "1048MiB"
