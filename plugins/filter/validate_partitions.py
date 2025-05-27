from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

def validate_partitions(parted_info, parts, default_label="gpt", require_existing=False):
    state = Disk.from_parted(parted_info)

    req = Disk(state.disk, parts)
    req.set_state_disk(state)

    req.set_table(default_label)

    return req.plan(required=require_existing)

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions": validate_partitions,
        }
