import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.partition_paths import partition_paths

def test_partition_paths():
    parts = [{"num": 1}, {"num": 2}]
    result = partition_paths("/dev/sda", parts)
    assert result == ["/dev/sda1", "/dev/sda2"]

    result = partition_paths("/dev/nvme0n1", parts)
    assert result == ["/dev/nvme0n1p1", "/dev/nvme0n1p2"]
