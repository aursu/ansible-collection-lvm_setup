# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for generating partition paths for all partitions on a given disk
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Disk

DOCUMENTATION = r'''
---
name: partition_paths_disk
author: Alexander Ursu
version_added: "1.0"
short_description: Return all partition paths for a given disk
description:
  - This filter returns a list of full device paths for all partitions on a specified disk.
    Each partition dictionary must include a 'num' key representing the partition number.
options:
  disk:
    description:
      - Base disk device path (e.g. /dev/sda or /dev/nvme0n1).
    type: str
    required: true
  parts:
    description:
      - List of partition metadata dictionaries, each with at least a 'num' key.
    type: list
    elements: dict
    required: true
seealso:
  - name: partition_path
    description: Returns the full path for a single partition
    plugin: aursu.lvm_setup.partition_path
'''

EXAMPLES = r'''
# Example: return ['/dev/sda6', '/dev/sda7']
- debug:
    msg: "{{ '/dev/sda' | aursu.lvm_setup.partition_paths_disk([{ 'num': 6 }, { 'num': 7 }]) }}"
'''

RETURN = r'''
_value:
  description: List of partition device paths for the disk
  type: list
  elements: str
  returned: always
'''

def partition_paths_disk(disk, parts):
    return Disk(disk, parts).paths()

class FilterModule(object):
    def filters(self):
        return {
            "partition_paths_disk": partition_paths_disk
        }
