# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin to validate and plan a logical volume based on LVM and device state
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup, LogicalVolume, Device

DOCUMENTATION = r'''
---
name: validate_volume
author: Alexander Ursu
version_added: "1.0"
short_description: Validate and plan a logical volume against system state
description:
  - This filter validates a logical volume definition and compares it with current system state,
    including LVM metadata and device information. It returns a plan of action such as create,
    skip, or format, depending on whether the volume already exists and matches expectations.
options:
  lv:
    description:
      - Dictionary defining a logical volume. Required fields: C(name), C(vg), C(size).
        Optional: C(filesystem), C(mountpoint).
    type: dict
    required: true
  lvm_info:
    description:
      - Dictionary of current LVM state, including C(vg), C(lv), and C(pv) sections.
        Typically obtained via C(aursu.general.lvm_info).
    type: dict
    required: true
  dev_info:
    description:
      - Device information for the target volume path, including filesystem type and mountpoints.
        Typically obtained from a module like C(aursu.general.dev_info).
    type: dict
    required: true
seealso:
  - name: validate_volumes_input
    description: Validates structure of input volume list
    plugin: aursu.lvm_setup.validate_volumes_input
  - name: validate_mount
    description: Validates that a volume is mounted correctly
    plugin: aursu.lvm_setup.validate_mount
'''

EXAMPLES = r'''
- name: Plan logical volume creation or formatting
  set_fact:
    lv_plan: >-
      {{
        validate_volume(
          {
            'name': 'data1',
            'vg': 'data',
            'size': '100g',
            'filesystem': 'xfs',
            'mountpoint': '/mnt/data1'
          },
          lvm_info,
          dev_info
        )
      }}
'''

RETURN = r'''
_value:
  description: Dictionary representing action plan for the volume (e.g. create, format, skip)
  type: dict
  returned: always
  sample:
    name: data1
    path: /dev/data/data1
    action: create
'''

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
