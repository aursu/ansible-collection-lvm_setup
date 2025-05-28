import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.filter.validate_partitions import validate_partitions

def parted_info(partitions, size):
    return {
        "disk": {"size": size, "dev": "/dev/sda"},
        "partitions": partitions
    }

def test_missing_num_field():
    parted = parted_info([], 4096.0)
    parts = [{}]  # no 'num'
    with pytest.raises(AnsibleFilterError, match=r"missing 'num'"):
        validate_partitions(parted, parts)

def test_missing_disk_size():
    parted = {
        "disk": {},
        "partitions": []
    }
    parts = [{"num": 1, "size": 1024.0}]
    with pytest.raises(AnsibleFilterError, match=r"Missing 'size' field."):
        validate_partitions(parted, parts)

def test_existing_partition_with_matching_size():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 1024.0)
    requested = [{"num": 1, "size": 1024.0}]
    result = validate_partitions(parted, requested)
    assert result[0]["status"] == "ok"
    assert result[0]["action"] == "skip"
    assert result[0]["warning"] == ""

def test_existing_partition_with_size_mismatch():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 1024.0)
    requested = [{"num": 1, "size": 2048.0}]
    result = validate_partitions(parted, requested)
    assert result[0]["status"] == "ok"
    assert result[0]["action"] == "skip"
    assert result[0]["warning"] == "size mismatch"

def test_create_partition_with_enough_space():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 4096.0)
    requested = [{"num": 2, "size": 1024.0}]
    result = validate_partitions(parted, requested)
    assert result[0]["status"] == "ok"
    assert result[0]["action"] == "create"
    assert result[0]["part_start"] == "1025MiB"
    assert result[0]["part_end"] == "2048MiB"

def test_create_partition_without_size_at_end():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 4096.0)
    requested = [{"num": 2}]
    result = validate_partitions(parted, requested)
    assert result[0]["status"] == "ok"
    assert result[0]["action"] == "create"
    assert result[0]["part_end"] == "100%"

def test_create_partition_without_size_before_existing():
    parted = parted_info([
        {"num": 2, "begin": 1024.0, "end": 2048.0, "size": 1024.0}
    ], 4096.0)
    requested = [{"num": 1}]
    with pytest.raises(AnsibleFilterError, match=r"no 'size' specified and another partition 2"):
        validate_partitions(parted, requested)

def test_existing_partition_without_size_and_no_following():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 4096.0, "size": 4096.0}
    ], 4096.0)
    requested = [{"num": 1}]
    result = validate_partitions(parted, requested)
    assert result[0]["status"] == "ok"
    assert result[0]["action"] == "skip"
    assert result[0]["part_start"] == 0.0
    assert result[0]["part_end"] == 4096.0
    assert result[0]["warning"] == ""

def test_create_partition_without_enough_space():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0},
        {"num": 3, "begin": 2048.0, "end": 4096.0, "size": 2048.0}
    ], 4096.0)
    requested = [{"num": 2, "size": 2000.0}]
    with pytest.raises(AnsibleFilterError, match=r"exceeds available space"):
        validate_partitions(parted, requested)

def test_disk_label_from_parted_info():
    parted = {
        "disk": {"size": 4096.0, "dev": "/dev/sda", "table": "msdos"},
        "partitions": []
    }
    parts = [{"num": 1, "size": 1024.0}]
    result = validate_partitions(parted, parts)
    assert result[0]["disk_label"] == "msdos"

def test_disk_label_fallback_to_default():
    parted = {
        "disk": {"size": 4096.0, "dev": "/dev/sda", "table": ""},
        "partitions": []
    }
    parts = [{"num": 1, "size": 1024.0}]
    result = validate_partitions(parted, parts)
    assert result[0]["disk_label"] == "gpt"

def test_disk_label_explicit_default():
    parted = {
        "disk": {"size": 4096.0, "dev": "/dev/sda"},
        "partitions": []
    }
    parts = [{"num": 1, "size": 1024.0}]
    result = validate_partitions(parted, parts, default_label='msdos')
    assert result[0]["disk_label"] == "msdos"

def test_partition_must_exist_with_require_existing():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 4096.0)

    requested = [{"num": 2, "size": 1024.0}]
    with pytest.raises(AnsibleFilterError, match=r"/dev/sda2 not found — expected to exist"):
        validate_partitions(parted, requested, require_existing=True)

def test_partition_must_exist_with_require_existing_nvme():
    parted = parted_info([
        {"num": 1, "begin": 0.0, "end": 1024.0, "size": 1024.0}
    ], 4096.0)
    parted["disk"]["dev"] = "/dev/nvme0n1"

    requested = [{"num": 2, "size": 1024.0}]
    with pytest.raises(AnsibleFilterError, match=r"/dev/nvme0n1p2 not found — expected to exist"):
        validate_partitions(parted, requested, require_existing=True)
