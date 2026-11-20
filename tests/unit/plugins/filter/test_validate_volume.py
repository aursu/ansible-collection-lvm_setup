import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.validate_volume import validate_volume

# dev_info for an LV that does not exist yet, and for one that exists with XFS.
ABSENT = {"is_exists": False}
PRESENT_XFS = {"is_exists": True, "blkid": {"type": "xfs"}}


def lvm_state(lvs=()):
    # One VG over two PVs: 1000 MiB free on the first, 2000 MiB on the second.
    return {
        "vg": [{"vg_name": "data", "vg_free": "3000.00m"}],
        "pv": [
            {"pv_name": "/dev/nvme0n1p4", "vg_name": "data", "pv_free": "1000.00m"},
            {"pv_name": "/dev/nvme1n1p1", "vg_name": "data", "pv_free": "2000.00m"},
        ],
        "lv": list(lvs),
    }


def volume(**extra):
    return {"name": "docker", "vg": "data", "size": "1500m", "filesystem": "xfs", **extra}


def test_unpinned_volume_uses_group_free_space():
    assert validate_volume(volume(), lvm_state(), ABSENT)["action"] == "create"


def test_pinned_volume_counts_only_its_pvs():
    # 1500 MiB fits the VG (3000) but not the named PV (1000).
    with pytest.raises(AnsibleFilterError, match=r"\(1000\.00 MiB\) on physical volume\(s\) /dev/nvme0n1p4"):
        validate_volume(volume(pvs=["/dev/nvme0n1p4"]), lvm_state(), ABSENT)


def test_pinned_volume_fits_on_its_pv():
    assert validate_volume(volume(pvs=["/dev/nvme1n1p1"]), lvm_state(), ABSENT)["action"] == "create"


def test_pv_outside_the_group_is_rejected():
    with pytest.raises(AnsibleFilterError, match="/dev/sdz1 not part of volume group 'data'"):
        validate_volume(volume(pvs=["/dev/sdz1"]), lvm_state(), ABSENT)


def test_pv_outside_the_group_is_rejected_for_an_existing_volume():
    existing = lvm_state([{"lv_name": "docker", "vg_name": "data", "lv_size": "1500.00m"}])
    with pytest.raises(AnsibleFilterError, match="not part of volume group"):
        validate_volume(volume(pvs=["/dev/sdz1"]), existing, PRESENT_XFS)


def test_existing_pinned_volume_is_skipped():
    existing = lvm_state([{"lv_name": "docker", "vg_name": "data", "lv_size": "1500.00m"}])
    assert validate_volume(volume(pvs=["/dev/nvme0n1p4"]), existing, PRESENT_XFS)["action"] == "skip"


@pytest.mark.parametrize("pvs, message", [
    ("/dev/nvme0n1p4", "non-empty list"),
    ([], "non-empty list"),
    (["nvme0n1p4"], "must be an absolute path"),
    (["/dev/nvme0n1p4", "/dev/nvme0n1p4"], "more than once"),
])
def test_malformed_pvs_are_rejected(pvs, message):
    with pytest.raises(AnsibleFilterError, match=message):
        validate_volume(volume(pvs=pvs), lvm_state(), ABSENT)
