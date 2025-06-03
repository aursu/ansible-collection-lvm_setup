import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.validate_mount import validate_mount

# Unit tests
test_lv_base = {
    "name": "data1",
    "vg": "data",
    "size": "100g"
}

@pytest.mark.parametrize("lv_mod, dev_info, expected", [
    # 1. Properly mounted volume
    (
        {"mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "/mnt/data1"}]},
        True
    ),
    # 2. Exists but not mounted
    (
        {"mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "/wrong"}]},
        False
    ),
    # 3. Exists, no mount section
    (
        {"mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True},
        False
    ),
    # 4. Not exists
    (
        {"mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": False},
        False
    ),
    # 5. Invalid mountpoint (not absolute path)
    (
        {"mountpoint": "mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "mnt/data1"}]},
        AnsibleFilterError
    ),
    # 6. Invalid filesystem type
    (
        {"mountpoint": "/mnt/data1", "filesystem": "ntfs"},
        {"is_exists": True, "mount": [{"target": "/mnt/data1"}]},
        AnsibleFilterError
    ),
    # 7. dev_info is not a dict
    (
        {"mountpoint": "/mnt/data1", "filesystem": "xfs"},
        "not-a-dict",
        AnsibleFilterError
    ),
    # 8. lv is not a dict
    (
        "not-a-dict",
        {"is_exists": True},
        AnsibleFilterError
    ),
    # 9. missing 'name'
    (
        {"vg": "data", "size": "100g"},
        {"is_exists": True},
        AnsibleFilterError
    ),
    # 10. missing 'vg'
    (
        {"name": "data1", "size": "100g"},
        {"is_exists": True},
        AnsibleFilterError
    ),
    # 11. missing 'size'
    (
        {"name": "data1", "vg": "data"},
        {"is_exists": True},
        AnsibleFilterError
    ),
])

def test_validate_mount(lv_mod, dev_info, expected):
    lv = dict(test_lv_base)

    if isinstance(lv_mod, dict):
        lv.update(lv_mod)
    else:
        lv = lv_mod

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            validate_mount(lv, dev_info)
    else:
        assert validate_mount(lv, dev_info) is expected
