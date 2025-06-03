import pytest
from ansible_collections.aursu.lvm_setup.plugins.filter.partition_path import partition_path

def test_partition_path():
    part = {"num": 1, "size": "200g"}
    result = partition_path("/dev/sda", part)
    assert result == "/dev/sda1"

    part = {"num": 2}
    result = partition_path("/dev/nvme0n1", part)
    assert result == "/dev/nvme0n1p2"
