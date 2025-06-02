import os
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.module_utils.size_utils import to_mib
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeInput

def validate_lv(lv, idx=0):
    if not isinstance(lv, dict):
        raise AnsibleFilterError(f"Volume entry #{idx + 1} must be a dictionary.")
    
    name = lv.get("name")
    vg = lv.get("vg")
    size = lv.get("size")

    if not name or not isinstance(name, str):
        raise AnsibleFilterError(f"Volume #{idx + 1} is missing a valid 'name' field.")

    if not vg or not isinstance(vg, str):
        raise AnsibleFilterError(f"Volume #{idx + 1} is missing a valid 'vg' field.")

    if not size:
        raise AnsibleFilterError(f"Volume '{name}' is missing a required 'size' field.")

    fs = lv.get("filesystem")
    if fs:
        if not isinstance(fs, str):
            raise AnsibleFilterError(f"Volume '{name}': 'filesystem' must be a string.")
        if fs not in {"ext4", "xfs", "btrfs"}:
            raise AnsibleFilterError(
                f"Unsupported filesystem '{fs}' in volume '{name}'. Supported: ext4, xfs, btrfs."
            )

    mountpoint = lv.get("mountpoint")
    if mountpoint:
        if not isinstance(mountpoint, str):
            raise AnsibleFilterError(f"Volume '{name}': 'mountpoint' must be a string.")
        if not os.path.isabs(mountpoint):
            raise AnsibleFilterError(f"Volume '{name}': 'mountpoint' must be an absolute path.")

    return True

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
    validate_lv(lv)

    if not isinstance(lvm_info, dict):
        raise AnsibleFilterError("Expected 'lvm_info' to be a dictionary.")
    if not isinstance(dev_info, dict):
        raise AnsibleFilterError("Expected 'dev_info' to be a dictionary.")

    vg = lv.get("vg")
    vg_list = {vg['vg_name']: vg for vg in lvm_info.get("vg", [])}

    if vg not in vg_list:
        raise AnsibleFilterError(f"Volume group '{vg}' not found in system")

    name = lv.get("name")
    size = lv.get("size")
    mountpoint = lv.get("mountpoint")
    fs = lv.get("filesystem")
    path = f"/dev/{vg}/{name}"

    entry = {
        "name": name,
        "path": path,
        "action": ""
    }

    # if device /dev/<vg_name>/<lv_name> exists
    if dev_info.get("is_exists"):
        entry["action"] = "skip"
        # check file system if defined
        if fs:
            # The 'blkid' field is present only after the LVM volume has been formatted with a filesystem.
            blkid_type = dev_info.get("blkid", {}).get("type")
            # optionally check filesystem match
            if blkid_type:
                if blkid_type != fs:
                    raise AnsibleFilterError(f"Filesystem mismatch: actual={blkid_type}, expected={fs}")
            else:
                entry["action"] = "format"
    else:
        # now check if there's enough VG free space only if the device doesn't exist
        vg_free = to_mib(vg_list[vg].get("vg_free", 0))
        lv_size = to_mib(size)

        if lv_size > vg_free:
            raise AnsibleFilterError(f"Not enough free space ({vg_free}) in VG '{vg}' to create LV '{name}' with size {lv_size}")

        entry["action"] = "create"

    return entry

class FilterModule(object):
    def filters(self):
        return {
            'validate_volume': validate_volume,
        }
