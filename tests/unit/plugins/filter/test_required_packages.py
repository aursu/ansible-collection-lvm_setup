import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.required_packages import required_packages

BASE = ["lvm2"]
BY_FS = {"xfs": "xfsprogs", "ext4": "e2fsprogs", "btrfs": "btrfs-progs"}


def volume(name, **extra):
    return {"name": name, "vg": "data", "size": "1g", **extra}


def test_base_packages_alone_when_no_volume_has_a_filesystem():
    assert required_packages([volume("raw")], BASE, BY_FS) == ["lvm2"]


def test_filesystems_in_declaration_order_without_duplicates():
    volumes = [volume("a", filesystem="xfs"), volume("b", filesystem="ext4"),
               volume("c", filesystem="xfs"), volume("d")]
    assert required_packages(volumes, BASE, BY_FS) == ["lvm2", "xfsprogs", "e2fsprogs"]


def test_only_requested_filesystems_are_installed():
    assert "btrfs-progs" not in required_packages([volume("a", filesystem="xfs")], BASE, BY_FS)


def test_a_filesystem_may_map_to_several_packages_or_none():
    by_fs = {"xfs": ["xfsprogs", "xfsdump"], "ext4": []}
    volumes = [volume("a", filesystem="xfs"), volume("b", filesystem="ext4")]
    assert required_packages(volumes, BASE, by_fs) == ["lvm2", "xfsprogs", "xfsdump"]


def test_a_package_shared_by_base_and_filesystem_appears_once():
    assert required_packages([volume("a", filesystem="xfs")], ["lvm2", "xfsprogs"], BY_FS) == ["lvm2", "xfsprogs"]


def test_base_may_be_a_single_name():
    assert required_packages([], "lvm2", BY_FS) == ["lvm2"]


def test_unsupported_filesystem_fails_with_the_collection_message():
    with pytest.raises(AnsibleFilterError, match="Unsupported filesystem 'zfs'"):
        required_packages([volume("a", filesystem="zfs")], BASE, BY_FS)


def test_supported_but_unmapped_filesystem_fails():
    with pytest.raises(AnsibleFilterError, match="No package is mapped for filesystem 'ext4'"):
        required_packages([volume("a", filesystem="ext4")], BASE, {"xfs": "xfsprogs"})


@pytest.mark.parametrize("volumes, base, by_fs, message", [
    ({"a": 1}, BASE, BY_FS, "'volumes' to be a list"),
    (["not a dict"], BASE, BY_FS, "must be a dictionary"),
    ([], BASE, ["xfsprogs"], "'filesystem_packages' to be a dict"),
    ([], [""], BY_FS, "'base_packages' must be a package name"),
    ([], BASE, {"xfs": 42}, r"'filesystem_packages\['xfs'\]' must be a package name"),
])
def test_malformed_input_is_rejected(volumes, base, by_fs, message):
    with pytest.raises(AnsibleFilterError, match=message):
        required_packages(volumes, base, by_fs)
