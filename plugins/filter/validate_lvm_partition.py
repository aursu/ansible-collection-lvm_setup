# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for validating whether a partition is suitable for use as an LVM physical volume (PV)
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import Device

DOCUMENTATION = r'''
---
name: validate_lvm_partition
author: Alexander Ursu
version_added: "1.0"
short_description: Validate if a partition is suitable for use as an LVM physical volume
description:
  - This filter checks whether a given partition can be safely used as an LVM physical volume.
    It validates existence, file type, stat errors, and the presence/compatibility of filesystem type.
options:
  path:
    description:
      - Full device path to the partition (e.g. /dev/sda6).
    type: str
    required: true
  info:
    description:
      - Dictionary with device metadata, typically collected via a custom Ansible module like C(aursu.general.dev_info).
    type: dict
    required: true
seealso:
  - name: validate_pvs
    description: Plans actions for physical volumes based on LVM info
    plugin: aursu.lvm_setup.validate_pvs
'''

EXAMPLES = r'''
- name: Assert that a partition is valid for LVM
  assert:
    that:
      - "/dev/sda6" | aursu.lvm_setup.validate_lvm_partition(dev_info)
'''

RETURN = r'''
_value:
  description: True if partition is valid for LVM PV usage; raises an error otherwise
  type: bool
  returned: always
'''

def validate_lvm_partition(path, info):
    """
    Validate if a partition is suitable for use as a physical volume.

    It must:
    - Exist
    - Be a block device
    - Have no stat error
    - Have blkid section
    - blkid.type must be absent or 'LVM2_member'
    """
    return Device.from_dev_info(path, info).validate_lvm()

class FilterModule(object):
    def filters(self):
        return {
            'validate_lvm_partition': validate_lvm_partition
        }
