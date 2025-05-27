from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

def validate_partitions(parted_info, parts, default_label="gpt", require_existing=False):
    disk = Disk.from_parted(parted_info)

    req = Disk(disk.disk, parts)
    req.set_state(disk)
    req.set_table(default_label)
    
    return req.plan(required=require_existing)

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions": validate_partitions,
        }
