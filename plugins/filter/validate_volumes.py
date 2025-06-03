from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup,LogicalVolume, Device

# +---------------------------------------+--------------------------------------------------------+
# | Empty dev_info & lvm_info             | Formatted dev_info & lvm_info                          |
# +---------------------------------------+--------------------------------------------------------+
# | "dev_info": {                         | "dev_info": {                                          |
# |     "changed": false,                 |     "blkid": {                                         |
# |     "failed": false,                  |         "block_size": "4096",                          |
# |     "filetype": "b",                  |         "dev_name": "/dev/data/data1",                 |
# |     "is_exists": true,                |         "type": "xfs",                                 |
# |     "stat": {                         |         "uuid": "66310f17-f78d-421e-ae23-154fd646d32f" |
# |         "atime": 1747406171.799727,   |     },                                                 |
# |         "ctime": 1747406109.8289678,  |     "changed": false,                                  |
# |         "dev": 5,                     |     "failed": false,                                   |
# |         "gid": 6,                     |     "filetype": "b",                                   |
# |         "ino": 2283,                  |     "is_exists": true,                                 |
# |         "mode": 25008,                |     "stat": {                                          |
# |         "mtime": 1747406109.8289678,  |         "atime": 1747406302.2787282,                   |
# |         "nlink": 1,                   |         "ctime": 1747406302.275689,                    |
# |         "rdev": 64513,                |         "dev": 5,                                      |
# |         "size": 0,                    |         "gid": 6,                                      |
# |         "uid": 0                      |         "ino": 2270,                                   |
# |     }                                 |         "mode": 25008,                                 |
# | }                                     |         "mtime": 1747406302.275689,                    |
# |                                       |         "nlink": 1,                                    |
# |                                       |         "rdev": 64512,                                 |
# |                                       |         "size": 0,                                     |
# |                                       |         "uid": 0                                       |
# |                                       |     }                                                  |
# |                                       | }                                                      |
# +---------------------------------------+--------------------------------------------------------+
# | "lvm_info": {                         | "lvm_info": {                                          |
# |     "changed": false,                 |     "changed": false,                                  |
# |     "failed": false,                  |     "failed": false,                                   |
# |     "lv": [],                         |     "lv": [                                            |
# |     "pv": [],                         |         {                                              |
# |     "vg": [                           |             "convert_lv": "",                          |
# |         {                             |             "copy_percent": "",                        |
# |             "lv_count": "0",          |             "data_percent": "",                        |
# |             "pv_count": "2",          |             "lv_attr": "-wi-a-----",                   |
# |             "snap_count": "0",        |             "lv_name": "data1",                        |
# |             "vg_attr": "wz--n-",      |             "lv_size": "204800.00m",                   |
# |             "vg_free": "1710944.00m", |             "metadata_percent": "",                    |
# |             "vg_name": "data",        |             "mirror_log": "",                          |
# |             "vg_size": "1710944.00m"  |             "move_pv": "",                             |
# |         }                             |             "origin": "",                              |
# |     ]                                 |             "pool_lv": "",                             |
# | }                                     |             "vg_name": "data"                          |
# |                                       |         },                                             |
# |                                       |         {                                              |
# |                                       |             "convert_lv": "",                          |
# |                                       |             "copy_percent": "",                        |
# |                                       |             "data_percent": "",                        |
# |                                       |             "lv_attr": "-wi-a-----",                   |
# |                                       |             "lv_name": "data2",                        |
# |                                       |             "lv_size": "204800.00m",                   |
# |                                       |             "metadata_percent": "",                    |
# |                                       |             "mirror_log": "",                          |
# |                                       |             "move_pv": "",                             |
# |                                       |             "origin": "",                              |
# |                                       |             "pool_lv": "",                             |
# |                                       |             "vg_name": "data"                          |
# |                                       |         }                                              |
# |                                       |     ],                                                 |
# |                                       |     "pv": [],                                          |
# |                                       |     "vg": [                                            |
# |                                       |         {                                              |
# |                                       |             "lv_count": "2",                           |
# |                                       |             "pv_count": "2",                           |
# |                                       |             "snap_count": "0",                         |
# |                                       |             "vg_attr": "wz--n-",                       |
# |                                       |             "vg_free": "1301344.00m",                  |
# |                                       |             "vg_name": "data",                         |
# |                                       |             "vg_size": "1710944.00m"                   |
# |                                       |         }                                              |
# |                                       |     ]                                                  |
# |                                       | }                                                      |
# +---------------------------------------+--------------------------------------------------------+
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
