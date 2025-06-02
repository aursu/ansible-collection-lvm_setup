from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeInput

def validate_volumes_input(volumes):
    """
    Validates the structure of the `volumes` variable.
    Each volume must be a dictionary with required keys: name, vg, and size.
    Optional: filesystem, mountpoint.
    """
    return VolumeInput(volumes).validate()

class FilterModule(object):
    def filters(self):
        return {
            'validate_volumes_input': validate_volumes_input,
        }
