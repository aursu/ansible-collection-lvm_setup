from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import PartitionInput

def validate_partitions_input(partitions, allow_gaps=False):
    PartitionInput(partitions).validate(allow_gaps)
    return True

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions_input": validate_partitions_input,
        }
