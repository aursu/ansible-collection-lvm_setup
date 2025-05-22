from ansible_collections.aursu.lvm_setup.plugins.module_utils.partition_utils import partition_path

def _filter_partition_paths(disk, parts):
    """
    Generate full partition paths for a given disk and list of partition entries.

    Each entry in `parts` must be a dictionary containing the key 'num' (partition number).
    The resulting path is generated using standard naming conventions:
    - For SATA/SCSI disks: /dev/sda + 1 → /dev/sda1
    - For NVMe disks: /dev/nvme0n1 + 1 → /dev/nvme0n1p1

    Args:
        disk (str): Base disk path (e.g. /dev/sda or /dev/nvme0n1).
        parts (list): List of partition dictionaries, each with a 'num' key.

    Returns:
        list[str]: List of full partition paths.
    """
    return [partition_path(disk, p["num"]) for p in parts]
