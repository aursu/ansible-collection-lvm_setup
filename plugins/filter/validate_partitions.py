import sys
import os
from ansible.errors import AnsibleFilterError

from utils import to_mib, mib

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

def validate_partitions_input(partitions, allow_gaps=False):
    if not isinstance(partitions, dict):
        raise AnsibleFilterError("Expected 'partitions' to be a dictionary.")

    for disk, parts in partitions.items():
        if not isinstance(parts, list):
            raise AnsibleFilterError(f"Expected a list of partitions for device '{disk}', got {type(parts).__name__}.")

        tracked_nums = set()

        for idx, part in enumerate(parts):
            is_last = idx == len(parts) - 1

            if not isinstance(part, dict):
                raise AnsibleFilterError(f"Each partition entry for '{disk}' must be a dictionary. Found: {part}")

            num = part.get("num")

            if num is None:
                raise AnsibleFilterError(f"Missing 'num' field in partition #{idx+1} for disk '{disk}'.")

            if not isinstance(num, int):
                raise AnsibleFilterError(f"'num' must be an integer in partition #{idx+1} for disk '{disk}'. Got: {num}")

            if num in tracked_nums:
                raise AnsibleFilterError(f"Duplicate partition number {num} on disk '{disk}'.")

            tracked_nums.add(num)

            size = part.get("size")
            if size is None:
                if not is_last:
                    raise AnsibleFilterError(f"Missing 'size' field for partition #{num} for disk '{disk}'.")
            else: 
                if to_mib(size) < 0:
                    raise AnsibleFilterError(
                        f"Expected positive 'size' field for partition #{num} for disk '{disk}'. Got: {size}"
                    )

        if not allow_gaps:
            num_min = min(tracked_nums)
            num_max = max(tracked_nums)
            if len(tracked_nums) <= (num_max - num_min):
                raise AnsibleFilterError(
                    f"Partition numbers on disk '{disk}' have gaps: {sorted(tracked_nums)}."
                )
    return True

def partition_paths_all(partitions):
    """
    Extract all partition paths from validated `partitions` dictionary.

    For example:
      partitions = {
          "/dev/sda": [{"num": 1}, {"num": 2}],
          "/dev/nvme0n1": [{"num": 1}]
      }

      → "/dev/sda1,/dev/sda2,/dev/nvme0n1p1"
    """
    validate_partitions_input(partitions)

    result = []
    for disk, parts in partitions.items():
        result.extend(partition_paths(disk, parts))
    return ",".join(result)

def validate_partitions(parted_info, parts, default_label="gpt", require_existing=False):
    results = []

    # Extract disk size
    disk_dev = parted_info.get("disk", {}).get("dev")
    disk_size = parted_info.get("disk", {}).get("size")  # Already in MiB
    disk_label = parted_info.get("disk", {}).get("table") or default_label

    if disk_size is None:
        raise AnsibleFilterError("Disk size information is missing in parted_info.")
    
    # Extract existing partitions
    disk_parts = parted_info.get("partitions", [])
    parts_by_num = {p["num"]: p for p in disk_parts if "num" in p}

    # Sort existing partitions by number
    sorted_parts = sorted(disk_parts, key=lambda p: p["num"])

    for req_part in parts:
        req_num = req_part.get("num")
        req_size = req_part.get("size")

        if req_num is None:
            raise AnsibleFilterError("Requested partition is missing 'num' field.")

        disk_part = parts_by_num.get(req_num)
        part_path = partition_path(disk_dev, req_num)
        if disk_part:
            part_start = float(disk_part.get("begin", 0))
            part_end = float(disk_part.get("end", 0))
            if req_size is None:
                # Check if disk_part is the last partition on disk
                following_parts = [p for p in sorted_parts if p["num"] > req_num]
                if following_parts:
                    next_num = following_parts[0]["num"]
                    raise AnsibleFilterError(
                        f"While partition {req_num} already exists: no size specified before another existing partition (next: {next_num})"
                    )
                results.append({
                    "num": req_num,
                    "status": "ok",
                    "warning": "",
                    "error": "",
                    "action": "skip",
                    "disk_label": disk_label,
                    "part_start": part_start,
                    "part_end": part_end
                })
            else:
                actual_size = float(disk_part.get("size", 0))
                expected_size = to_mib(req_size)
                if round(actual_size) == round(expected_size):
                    warning = ""
                else:
                    warning = "size mismatch"
                results.append({
                    "num": req_num,
                    "status": "ok",
                    "warning": warning,
                    "error": "",
                    "action": "skip",
                    "disk_label": disk_label,
                    "part_start": part_start,
                    "part_end": part_end
                })
            continue

        if require_existing:
            raise AnsibleFilterError(
                f"Partition {part_path} not found — expected to exist at this point (require_existing is set)"
            )

        # Partition does not exist — need to create
        prev_end = 0.0
        next_begin = disk_size
        next_num = None

        # Determine available space by checking the nearest existing partitions before and after
        # the requested partition number. This ensures we allocate partitions without overlapping
        # and accurately simulate real disk layout constraints.
        for part in sorted_parts:
            if part["num"] < req_num:
                prev_end = max(prev_end, float(part["end"]))
            elif part["num"] > req_num:
                if next_num is None or part["num"] < next_num:
                    next_begin = float(part["begin"])
                    next_num = part["num"]

        available_space = next_begin - prev_end

        if req_size is None:
            if next_num is not None:
                raise AnsibleFilterError(
                    f"Partition {req_num}: no size specified and another partition {next_num} follows"
                )

            results.append({
                "num": req_num,
                "status": "ok",
                "warning": "",
                "error": "",
                "action": "create",
                "disk_label": disk_label,
                "part_start": mib(prev_end, 1),
                "part_end": "100%"
            })
            new_part = {"begin": prev_end + 1, "end": disk_size, "num": req_num}
        else:
            expected_size = to_mib(req_size)

            if available_space < expected_size:
                raise AnsibleFilterError(
                    f"Partition {req_num}: requested size {expected_size:.2f} MiB exceeds available space ({available_space:.2f} MiB)"
                )

            if next_num == req_num + 1:
                part_end = next_begin - 1 # align to 1 MiB before next partition (parted default alignment: 1 MiB / 2048 sectors)
            else:
                part_end = prev_end + expected_size

            results.append({
                "num": req_num,
                "status": "ok",
                "warning": "",
                "error": "",
                "action": "create",
                "disk_label": disk_label,
                "part_start": mib(prev_end, 1),
                "part_end": mib(part_end)
            })
            new_part = {"begin": prev_end + 1, "end": part_end, "num": req_num}

        # add newly created partition to tracking structures
        disk_parts.append(new_part)
        parts_by_num[req_num] = new_part
        sorted_parts = sorted(disk_parts, key=lambda p: p["num"])

    return results

def validate_partitions_exist(parted_info, parts, default_label="gpt"):
    validate_partitions(parted_info, parts, default_label=default_label, require_existing=True)
    return True

class FilterModule(object):
    def filters(self):
        return {
            "partition_path": partition_path,
            "partition_paths": partition_paths,
            "partition_paths_all": partition_paths_all,
            "validate_partitions": validate_partitions,
            "validate_partitions_input": validate_partitions_input,
            "validate_partitions_exist": validate_partitions_exist
        }
