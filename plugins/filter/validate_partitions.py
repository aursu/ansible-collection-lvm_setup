# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for validating and planning partition layout on a disk
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Disk

DOCUMENTATION = r'''
---
name: validate_partitions
author: Alexander Ursu
version_added: "1.0"
short_description: Validate and generate plan to align partition layout on disk
description:
  - This filter compares the current partition table (from parted) with the desired layout and returns an action plan.
    It ensures all partitions are valid, optionally requiring that they already exist.
    It also supports setting the partition table label (e.g. C(gpt), C(msdos)) if not yet defined.
options:
  parted_info:
    description:
      - Dictionary with disk and partitions metadata from parted, typically collected via C(community.general.parted).
    type: dict
    required: true
  parts:
    description:
      - List of requested partition definitions with at least a C(num) and C(size) or C(end) field.
    type: list
    elements: dict
    required: true
  default_label:
    description:
      - Partition table label to use if none is set. Common values: C(gpt), C(msdos).
    type: str
    required: false
    default: gpt
  require_existing:
    description:
      - If true, all partitions must already exist on the disk; otherwise, a plan will be generated to create missing ones.
    type: bool
    required: false
    default: false
seealso:
  - name: validate_partitions_exist
    description: Asserts that all specified partitions already exist
    plugin: aursu.lvm_setup.validate_partitions_exist
'''

EXAMPLES = r'''
- name: Generate partitioning plan for disk
  set_fact:
    validated_parts: >-
      {{ parted_info | aursu.lvm_setup.validate_partitions(parts, default_label='gpt') }}

- name: Ensure required partitions already exist
  set_fact:
    validated: >-
      {{ parted_info | aursu.lvm_setup.validate_partitions(parts, require_existing=True) }}
'''

RETURN = r'''
_value:
  description: List of partition plans with calculated start/end positions and actions ("create", "skip")
  type: list
  elements: dict
  returned: always
'''

def validate_partitions(parted_info, parts, default_label="gpt", require_existing=False):
    state = Disk.from_parted(parted_info)

    req = Disk(state.disk, parts)
    req.set_state_disk(state)

    req.set_table(default_label)

    return req.plan(required=require_existing)

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions": validate_partitions,
        }
