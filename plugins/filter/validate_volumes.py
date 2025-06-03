from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup,LogicalVolume, Device

def validate_volume(lv, lvm_info, dev_info):

    volume = LogicalVolume(lv)
    volume.validate()

    dev = Device.from_dev_info(volume.path, dev_info)
    volume.attach_device(dev, pass_through=True)

    vg = VolumeGroup(volume.vg)
    vg.set_state(lvm_info)

    vg.validate()

    return vg.plan_volume(volume)

class FilterModule(object):
    def filters(self):
        return {
            'validate_volume': validate_volume,
        }
