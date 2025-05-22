from ansible.errors import AnsibleFilterError

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.conv import (
    to_mib,
    mib
)
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.path import partition_path


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
            "validate_partitions": validate_partitions,
            "validate_partitions_exist": validate_partitions_exist
        }
