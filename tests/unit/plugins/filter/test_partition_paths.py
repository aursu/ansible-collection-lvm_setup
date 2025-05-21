import pytest
from ansible.errors import AnsibleFilterError
from plugins.filter.validate_partitions import (
    partition_path,
    partition_paths,
    partition_paths_all
)

def test_partition_path_for_sata():
    assert partition_path("/dev/sda", 1) == "/dev/sda1"
    assert partition_path("/dev/sdb", 5) == "/dev/sdb5"

def test_partition_path_for_nvme():
    assert partition_path("/dev/nvme0n1", 1) == "/dev/nvme0n1p1"
    assert partition_path("/dev/nvme1n1", 10) == "/dev/nvme1n1p10"

def test_partition_paths():
    parts = [{"num": 1}, {"num": 2}]
    result = partition_paths("/dev/sda", parts)
    assert result == ["/dev/sda1", "/dev/sda2"]

    result = partition_paths("/dev/nvme0n1", parts)
    assert result == ["/dev/nvme0n1p1", "/dev/nvme0n1p2"]

def test_partition_paths_all_valid():
    partitions = {
        "/dev/sda": [{"num": 1, "size": "100g"}, {"num": 2}],
        "/dev/nvme0n1": [{"num": 1}]
    }
    result = partition_paths_all(partitions)
    assert result == "/dev/sda1,/dev/sda2,/dev/nvme0n1p1"

def test_partition_paths_all_invalid_input():
    with pytest.raises(AnsibleFilterError, match="Expected 'partitions' to be a dictionary."):
        partition_paths_all("not a dict")
