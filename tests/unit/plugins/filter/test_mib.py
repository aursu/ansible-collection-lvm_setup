import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.module_utils.size_utils import to_mib

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
