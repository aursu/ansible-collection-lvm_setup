def partition_path(disk, number):
    """
    Return full partition device path for a given disk and partition number.
    Examples:
      - /dev/sda, 1        → /dev/sda1
      - /dev/nvme0n1, 1    → /dev/nvme0n1p1
    """
    return f"{disk}p{number}" if "nvme" in disk else f"{disk}{number}"

def partition_paths(disk, parts):
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
