import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.partition_paths_system import partition_paths_system

def partition_paths_system():
    partitions = {
        "/dev/sda": [{"num": 1, "size": "100g"}, {"num": 2}],
        "/dev/nvme0n1": [{"num": 1}]
    }
    result = partition_paths_system(partitions)
    assert result == "/dev/sda1,/dev/sda2,/dev/nvme0n1p1"

def test_partition_paths_all_invalid_input():
    with pytest.raises(AnsibleFilterError, match="Expected 'partitions' to be a dictionary."):
        partition_paths_system("not a dictionary")
