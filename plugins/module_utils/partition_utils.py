def partition_path(disk, number):
    """
    Return full partition device path for a given disk and partition number.
    Examples:
      - /dev/sda, 1        → /dev/sda1
      - /dev/nvme0n1, 1    → /dev/nvme0n1p1
    """
    return f"{disk}p{number}" if "nvme" in disk else f"{disk}{number}"
