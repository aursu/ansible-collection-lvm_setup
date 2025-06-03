# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin to verify that a list of disk partitions exists on a given device
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Disk

DOCUMENTATION = r'''
---
name: validate_partitions_exist
author: Alexander Ursu
version_added: "1.0"
short_description: Assert that all specified partitions exist on a disk
description:
  - This filter checks that all requested partitions already exist on the specified disk.
    If any partition is missing or does not match expected structure, it raises an error.
options:
  parted_info:
    description:
      - Dictionary with parted output structure, usually collected via C(community.general.parted) or a compatible module.
    type: dict
    required: true
  parts:
    description:
      - List of requested partitions with C(num) and optional size fields to verify.
    type: list
    elements: dict
    required: true
seealso:
  - name: validate_partitions
    description: Validates and returns action plan for aligning partition layout
    plugin: aursu.lvm_setup.validate_partitions
'''

EXAMPLES = r'''
- name: Assert that partitions exist on /dev/sda
  assert:
    that:
      - validate_partitions_exist(parted_info, [{ 'num': 6 }, { 'num': 7 }])
'''

RETURN = r'''
_value:
  description: True if all requested partitions are found and valid; error is raised otherwise
  type: bool
  returned: always
'''

def validate_partitions_exist(parted_info, parts):
    state = Disk.from_parted(parted_info)

    req = Disk(state.disk, parts)
    req.set_state_disk(state)

    req.plan(required=True)

    return True

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions_exist": validate_partitions_exist
        }
