import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.validate_mount import validate_mount

@pytest.mark.parametrize("lv, dev_info, expected", [
    # 1. Properly mounted volume
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "/mnt/data1"}]},
        True
    ),
    # 2. Exists but not mounted
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "/wrong"}]},
        False
    ),
    # 3. Exists, no mount section
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True},
        False
    ),
    # 4. Not exists
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": False},
        False
    ),
    # 5. Invalid mountpoint (not absolute path)
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "mnt/data1", "filesystem": "xfs"},
        {"is_exists": True, "mount": [{"target": "mnt/data1"}]},
        AnsibleFilterError
    ),
    # 6. Invalid filesystem type
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "ntfs"},
        {"is_exists": True, "mount": [{"target": "/mnt/data1"}]},
        AnsibleFilterError
    ),
    # 7. dev_info is not a dict
    (
        {"name": "data1", "vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
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
        {"vg": "data", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True},
        AnsibleFilterError
    ),
    # 10. missing 'vg'
    (
        {"name": "data1", "size": "100g", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True},
        AnsibleFilterError
    ),
    # 11. missing 'size'
    (
        {"name": "data1", "vg": "data", "mountpoint": "/mnt/data1", "filesystem": "xfs"},
        {"is_exists": True},
        AnsibleFilterError
    ),
])

def test_validate_mount(lv, dev_info, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            validate_mount(lv, dev_info)
    else:
        assert validate_mount(lv, dev_info) is expected
