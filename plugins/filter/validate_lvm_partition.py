from ansible.errors import AnsibleFilterError

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
    if not isinstance(info, dict):
        raise AnsibleFilterError(f"Expected partition 'info' to be a dictionary for {path}.")

    if not info.get('is_exists', False):
        raise AnsibleFilterError(f"Partition {path} does not exist.")

    if info.get('stat', {}).get('error') is not None:
        raise AnsibleFilterError(f"Partition {path} file status error: {info['stat']['error']}")

    filetype = info.get('filetype')
    if filetype != 'b':
        raise AnsibleFilterError(f"{path} is not a block device (actual filetype is {filetype}).")

    blkid_type = info.get('blkid', {}).get('type')
    if blkid_type is not None and blkid_type != "LVM2_member":
        raise AnsibleFilterError(f"Partition {path} contains unexpected filesystem: {blkid_type}")

    return True

class FilterModule(object):
    def filters(self):
        return {
            'validate_lvm_partition': validate_lvm_partition
        }
