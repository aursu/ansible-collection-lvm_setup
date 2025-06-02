from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import LogicalVolume, Device

def validate_mount(lv, dev_info):
    dev = Device.from_dev_info(dev_info)
    volume = LogicalVolume(lv)

    if dev.is_exists() and volume.validate():
        return dev.validate_mount(volume.mount)

    return False

class FilterModule(object):
    def filters(self):
        return {
            'validate_mount': validate_mount
        }
