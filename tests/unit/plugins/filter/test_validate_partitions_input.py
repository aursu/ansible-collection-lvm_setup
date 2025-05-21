import pytest
from plugins.filter.validate_partitions import validate_partitions_input
from ansible.errors import AnsibleFilterError

def test_valid_partitions_without_gaps():
    partitions = {
        '/dev/sda': [
            {'num': 1, 'size': '100g'},
            {'num': 2, 'size': '10240m'},
            {'num': 3}
        ]
    }
    assert validate_partitions_input(partitions) is True

def test_valid_partitions_with_gaps_allowed():
    partitions = {
        '/dev/sda': [
            {'num': 1, 'size': '2t'},
            {'num': 3}
        ]
    }
    assert validate_partitions_input(partitions, allow_gaps=True) is True

def test_invalid_structure_not_a_dict():
    with pytest.raises(AnsibleFilterError, match="Expected 'partitions' to be a dictionary."):
        validate_partitions_input(['not', 'a', 'dict'])

def test_invalid_entries_not_list():
    with pytest.raises(AnsibleFilterError, match="Expected a list of partitions for device '/dev/sda'"):
        validate_partitions_input({'/dev/sda': 'notalist'})

def test_missing_num_field():
    partitions = {
        '/dev/sda': [
            {'size': '500G'}
        ]
    }
    with pytest.raises(AnsibleFilterError, match="Missing 'num' field in partition"):
        validate_partitions_input(partitions)

def test_num_not_integer():
    partitions = {
        '/dev/sda': [
            {'num': 'one'}
        ]
    }
    with pytest.raises(AnsibleFilterError, match="'num' must be an integer"):
        validate_partitions_input(partitions)

def test_duplicate_partition_num():
    partitions = {
        '/dev/sda': [
            {'num': 1, 'size': '100g'},
            {'num': 1}
        ]
    }
    with pytest.raises(AnsibleFilterError, match="Duplicate partition number 1 on disk '/dev/sda'"):
        validate_partitions_input(partitions)

def test_partition_numbers_have_gaps():
    partitions = {
        '/dev/sda': [
            {'num': 1, 'size': '100g'},
            {'num': 3, 'size': '100g'},
            {'num': 4}
        ]
    }
    with pytest.raises(AnsibleFilterError, match="Partition numbers on disk '/dev/sda' have gaps"):
        validate_partitions_input(partitions, allow_gaps=False)
