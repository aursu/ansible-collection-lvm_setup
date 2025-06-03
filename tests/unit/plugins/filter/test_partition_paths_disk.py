import pytest
from ansible_collections.aursu.lvm_setup.plugins.filter.partition_paths_disk import partition_paths_disk

def test_partition_paths():
    parts = [{"num": 1, "size": "200g"}, {"num": 2}]
    result = partition_paths_disk("/dev/sda", parts)
    assert result == ["/dev/sda1", "/dev/sda2"]

    result = partition_paths_disk("/dev/nvme0n1", parts)
    assert result == ["/dev/nvme0n1p1", "/dev/nvme0n1p2"]
