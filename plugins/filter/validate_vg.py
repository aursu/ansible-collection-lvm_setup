from ansible.errors import AnsibleFilterError

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
    if not isinstance(vg_name, str):
        raise AnsibleFilterError("Expected 'vg_name' to be a string.")

    if not isinstance(lvm_info, dict):
        raise AnsibleFilterError("Expected 'lvm_info' to be a dictionary.")

    vg_list = [vg.get("vg_name") for vg in lvm_info.get("vg", [])]
    if vg_name not in vg_list:
        raise AnsibleFilterError(f"Volume group '{vg_name}' not found in system.")

    return True

class FilterModule(object):
    def filters(self):
        return {
            'validate_vg': validate_vg
        }
