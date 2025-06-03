# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for generating partition paths for all partitions on a given set of disks
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import PartitionInput

DOCUMENTATION = r'''
---
name: partition_paths_system
author: Alexander Ursu
version_added: "1.0"
short_description: Return partition paths for all partitions on a set of disks
description:
  - This filter returns a comma-separated string of partition device paths from a dictionary of disks and their partitions.
    Each key in the dictionary must be a disk path (e.g. C(/dev/sda)), and each value must be a list of partitions with a C(num) field.
options:
  partitions:
    description:
      - Dictionary mapping disk paths to lists of partition metadata, each with at least a C(num) field.
    type: dict
    required: true
seealso:
  - name: partition_paths_disk
    description: Returns a list of partition paths for a single disk
    plugin: aursu.lvm_setup.partition_paths_disk
'''

EXAMPLES = r'''
- name: Get all partition paths across system
  debug:
    msg: >-
      {{
        {
          '/dev/sda': [ { 'num': 1 }, { 'num': 2 } ],
          '/dev/sdb': [ { 'num': 1 } ]
        } | aursu.lvm_setup.partition_paths_system
      }}
  # Returns: "/dev/sda1,/dev/sda2,/dev/sdb1"
'''

RETURN = r'''
_value:
  description: Comma-separated string of all partition paths on the system
  type: str
  returned: always
'''

def partition_paths_system(partitions):
    return ",".join(PartitionInput(partitions).paths())

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths_system": partition_paths_system,
        }
