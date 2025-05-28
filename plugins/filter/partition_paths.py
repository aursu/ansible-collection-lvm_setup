from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Disk

def partition_paths(disk, parts):
    return Disk(disk, parts).paths()

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths": partition_paths
        }
