# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin to validate that a volume group exists in the system
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup

DOCUMENTATION = r'''
---
name: validate_vg
author: Alexander Ursu
version_added: "1.0"
short_description: Validate that a volume group exists
description:
  - This filter checks if the specified volume group name exists in the provided LVM metadata (lvm_info).
    If the group is not found, an error is raised.
options:
  vg_name:
    description:
      - Name of the volume group to verify.
    type: str
    required: true
  lvm_info:
    description:
      - Dictionary containing output of LVM state, including the C(vg) key.
        Typically collected via C(aursu.general.lvm_info).
    type: dict
    required: true
seealso:
  - name: validate_pvs
    description: Validates and plans actions for physical volumes within a volume group
    plugin: aursu.lvm_setup.validate_pvs
'''

EXAMPLES = r'''
- name: Ensure volume group 'data' exists
  assert:
    that:
      - validate_vg('data', lvm_info)
'''

RETURN = r'''
_value:
  description: True if the volume group exists; otherwise, an error is raised
  type: bool
  returned: always
'''

def validate_vg(vg_name, lvm_info):
    """
    Validates that a given volume group name exists in lvm_info['vgs'].

    Args:
        vg_name (str): Name of the volume group to check.
        lvm_info (dict): Output from aursu.general.lvm_info with filter: vgs.

    Raises:
        AnsibleFilterError: if vg_name not found.

    Returns:
        True if VG exists.
    """
    return VolumeGroup.from_lvm_info(vg_name, lvm_info).validate()

class FilterModule(object):
    def filters(self):
        return {
            'validate_vg': validate_vg
        }
