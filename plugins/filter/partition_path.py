from typing import Any
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Partition

def partition_path(disk: str, part: dict[str, Any]) -> str:
    return Partition(part).path(disk)

class FilterModule(object):
    def filters(self):
        return {
            "partition_path": partition_path
        }
