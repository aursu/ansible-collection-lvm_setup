from typing import Any, List
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup

def validate_pvs(lvm_info: dict[str, Any], paths: list[str], vg_name: str) -> List[dict[str, str]]:
    """
    Determine the required LVM action for each partition path.

    Args:
        lvm_info: Parsed LVM information with "pv" data.
        paths: List of full device paths (e.g., "/dev/sda6").
        vg_name: Target volume group name.

    Returns:
        List of dictionaries with:
            - path: the device path
            - action: one of "create", "add", or "skip"
    """
    return VolumeGroup.from_lvm_info(vg_name, lvm_info).plan_pvs(paths)

class FilterModule(object):
    def filters(self):
        return {
            'validate_pvs': validate_pvs
        }
