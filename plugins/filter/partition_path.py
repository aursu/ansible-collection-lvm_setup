# -*- coding: utf-8 -*-
# Copyright (c) 2024, Alex Ursu <your@email>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for generating full partition paths
"""

from typing import Any
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Partition

DOCUMENTATION = r'''
---
name: partition_path
author: Alexander Ursu
version_added: "1.0.0"
short_description: Generate partition device path from disk and partition metadata
description:
  - This filter returns the full partition device path (e.g. /dev/sda6 or /dev/nvme0n1p1)
    by combining the disk name and the partition metadata (with the required 'num' field).
options:
  part:
    description:
      - Partition metadata dictionary with at least the 'num' field (partition number).
    type: dict
    required: true
  disk:
    description:
      - Base disk device path (e.g. /dev/sda or /dev/nvme0n1).
    type: str
    required: true
seealso:
  - name: partition_paths_disk
    description: Returns list of partition paths on a given disk
    plugin: aursu.lvm_setup.partition_paths_disk
'''

EXAMPLES = r'''
# Example: return /dev/sda6
- debug:
    msg: "{{ '/dev/sda' | aursu.lvm_setup.partition_path({'num': 6}) }}"
'''

RETURN = r'''
_value:
  description: Full path to the partition device
  type: str
  returned: always
'''

def partition_path(disk: str, part: dict[str, Any]) -> str:
    return Partition(part).path(disk)

class FilterModule(object):
    def filters(self):
        return {
            "partition_path": partition_path
        }
