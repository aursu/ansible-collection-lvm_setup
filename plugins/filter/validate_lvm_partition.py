from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import Device

def validate_lvm_partition(path, info):
    """
    Validate if a partition is suitable for use as a physical volume.

    It must:
    - Exist
    - Be a block device
    - Have no stat error
    - Have blkid section
    - blkid.type must be absent or 'LVM2_member'
    """
    dev = Device.from_dev_info(path, info)
    return dev.validate_lvm()

class FilterModule(object):
    def filters(self):
        return {
            'validate_lvm_partition': validate_lvm_partition
        }
