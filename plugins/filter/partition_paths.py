from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import _filter_partition_paths as partition_paths

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths": partition_paths
        }
