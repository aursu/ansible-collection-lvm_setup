import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.validate_pvs import validate_pvs

def test_create_when_not_a_pv():
    lvm_info = {"pvs": []}
    paths = ["/dev/sda5"]
    result = validate_pvs(lvm_info, paths, "vg_main")
    assert result == [
        {"path": "/dev/sda5", "action": "create"}
    ]

def test_skip_when_pv_in_correct_vg():
    lvm_info = {
        "pvs": [
            {"pv_name": "/dev/sda5", "vg_name": "vg_main"}
        ]
    }
    paths = ["/dev/sda5"]
    result = validate_pvs(lvm_info, paths, "vg_main")
    assert result == [
        {"path": "/dev/sda5", "action": "skip"}
    ]

def test_add_when_pv_without_vg():
    lvm_info = {
        "pvs": [
            {"pv_name": "/dev/sda5", "vg_name": ""}
        ]
    }
    paths = ["/dev/sda5"]
    result = validate_pvs(lvm_info, paths, "vg_main")
    assert result == [
        {"path": "/dev/sda5", "action": "add"}
    ]

def test_add_when_pv_with_none_vg():
    lvm_info = {
        "pvs": [
            {"pv_name": "/dev/sda5", "vg_name": None}
        ]
    }
    paths = ["/dev/sda5"]
    result = validate_pvs(lvm_info, paths, "vg_main")
    assert result == [
        {"path": "/dev/sda5", "action": "add"}
    ]

def test_fail_when_pv_in_another_vg():
    lvm_info = {
        "pvs": [
            {"pv_name": "/dev/sda5", "vg_name": "other_vg"}
        ]
    }
    paths = ["/dev/sda5"]
    with pytest.raises(AnsibleFilterError, match="already part of another volume group: other_vg"):
        validate_pvs(lvm_info, paths, "vg_main")

def test_fail_on_missing_vg_name():
    lvm_info = {"pvs": []}
    paths = ["/dev/sda5"]
    with pytest.raises(AnsibleFilterError, match="must be provided"):
        validate_pvs(lvm_info, paths, "")

def test_fail_on_invalid_paths_type():
    lvm_info = {"pvs": []}
    with pytest.raises(AnsibleFilterError, match="Expected 'paths' to be a list."):
        validate_pvs(lvm_info, "/dev/sda5", "vg_main")

def test_fail_on_invalid_lvm_info_type():
    with pytest.raises(AnsibleFilterError, match="Expected 'lvm_info' to be a dictionary."):
        validate_pvs("invalid", ["/dev/sda5"], "vg_main")
