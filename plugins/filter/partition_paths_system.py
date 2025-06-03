from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import PartitionInput

def partition_paths_system(partitions):
    return ",".join(PartitionInput(partitions).paths())

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths_system": partition_paths_system,
        }
