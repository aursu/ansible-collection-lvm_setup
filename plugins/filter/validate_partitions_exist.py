from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

def validate_partitions_exist(parted_info, parts):
    state = Disk.from_parted(parted_info)

    req = Disk(state.disk, parts)
    req.set_state_disk(state)

    req.plan(required=True)

    return True

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions_exist": validate_partitions_exist
        }
