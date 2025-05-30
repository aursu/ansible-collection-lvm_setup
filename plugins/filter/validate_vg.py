from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup

def validate_vg(vg_name, lvm_info):
    """
    Validates that a given volume group name exists in lvm_info['vgs'].

    Args:
        vg_name (str): Name of the volume group to check.
        lvm_info (dict): Output from aursu.general.lvm_info with filter: vgs.

    Raises:
        AnsibleFilterError: if vg_name not found.

    Returns:
        True if VG exists.
    """
    return VolumeGroup.from_lvm_info(vg_name, lvm_info).validate()

class FilterModule(object):
    def filters(self):
        return {
            'validate_vg': validate_vg
        }
