# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for validating if a logical volume is mounted at the expected mount point
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import LogicalVolume, Device

DOCUMENTATION = r'''
---
name: validate_mount
author: Alexander Ursu
version_added: "1.0"
short_description: Validate that a logical volume is mounted at its defined mount point
description:
  - This filter checks whether a logical volume is mounted at the path defined in its metadata (C(mountpoint) field).
    It validates the volume structure, retrieves device info, and inspects current mount state.
options:
  lv:
    description:
      - Dictionary representing a logical volume definition. Must include at least C(name), C(vg), and C(mountpoint).
    type: dict
    required: true
  dev_info:
    description:
      - Dictionary of device metadata for the given volume path. Should include mount information.
    type: dict
    required: true
seealso:
  - name: validate_volume
    description: Performs full validation and planning of a logical volume
    plugin: aursu.lvm_setup.validate_volume
'''

EXAMPLES = r'''
- name: Check whether LV is mounted at its declared mountpoint
  debug:
    msg: >-
      {{
        {
          'name': 'data1',
          'vg': 'data',
          'size': '200g',
          'mountpoint': '/mnt/data1'
        } | aursu.lvm_setup.validate_mount(dev_info)
      }}
'''

RETURN = r'''
_value:
  description: True if volume is mounted at its expected mountpoint, False otherwise
  type: bool
  returned: always
'''

def validate_mount(lv, dev_info):
    volume = LogicalVolume(lv)
    dev = Device.from_dev_info(volume.path, dev_info)

    if dev.is_exists and volume.validate():
        return dev.validate_mount(volume.mount)

    return False

class FilterModule(object):
    def filters(self):
        return {
            'validate_mount': validate_mount
        }
