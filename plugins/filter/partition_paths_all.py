from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import _filter_partition_paths as partition_paths
from ansible_collections.aursu.lvm_setup.plugins.module_utils.size_utils import to_mib

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

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths_all": partition_paths_all,
            "validate_partitions_input": validate_partitions_input,
        }
