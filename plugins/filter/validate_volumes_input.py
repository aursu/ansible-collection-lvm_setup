# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin to validate the structure of logical volume definitions
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeInput

DOCUMENTATION = r'''
---
name: validate_volumes_input
author: Alexander Ursu
version_added: "1.0"
short_description: Validate the structure of logical volume input definitions
description:
  - This filter validates that a list of logical volume definitions is structurally correct.
    Each volume must define C(name), C(vg), and C(size). Optionally, it may include C(filesystem) and C(mountpoint).
    All volumes must belong to the same volume group.
options:
  volumes:
    description:
      - List of volume definitions. Each item must be a dictionary with required and optional keys.
    type: list
    elements: dict
    required: true
seealso:
  - name: validate_volume
    description: Performs full validation and planning of a logical volume
    plugin: aursu.lvm_setup.validate_volume
'''

EXAMPLES = r'''
- name: Validate volume structure
  assert:
    that:
      - validate_volumes_input([
          { 'name': 'data1', 'vg': 'data', 'size': '100g' },
          { 'name': 'data2', 'vg': 'data', 'size': '200g', 'mountpoint': '/mnt/data2' }
        ])
'''

RETURN = r'''
_value:
  description: True if the structure is valid; otherwise, raises an error
  type: bool
  returned: always
'''

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
