from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

def validate_partitions_exist(parted_info, parts, default_label="gpt"):
    disk = Disk.from_parted(parted_info)

    req = Disk(disk.disk, parts)
    req.set_state(disk)
    req.set_table(default_label)
    
    req.plan(required=True)

    return True

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions_exist": validate_partitions_exist
        }
