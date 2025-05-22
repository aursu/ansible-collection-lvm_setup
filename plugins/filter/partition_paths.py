from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.path import partition_paths

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths": partition_paths
        }
