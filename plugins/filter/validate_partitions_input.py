# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin for validating the structure of the input partition definitions per disk
"""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import PartitionInput

DOCUMENTATION = r'''
---
name: validate_partitions_input
author: Alexander Ursu
version_added: "1.0"
short_description: Validate the structure of input partition definitions per disk
description:
  - This filter checks the structural correctness of a partitions dictionary that maps disk names to lists of partitions.
    It validates types, uniqueness of partition numbers, and optionally allows or disallows numbering gaps.
options:
  partitions:
    description:
      - Dictionary mapping disk device paths (e.g. /dev/sda) to lists of partitions with at least a C(num) field.
    type: dict
    required: true
  allow_gaps:
    description:
      - Whether to allow non-sequential partition numbers (e.g. [1, 3] without 2).
    type: bool
    required: false
    default: false
seealso:
  - name: validate_partitions
    description: Validates and returns action plan for aligning partition layout
    plugin: aursu.lvm_setup.validate_partitions
'''

EXAMPLES = r'''
- name: Ensure partition structure is valid
  assert:
    that:
      - validate_partitions_input({
          '/dev/sda': [ { 'num': 1 }, { 'num': 2 } ],
          '/dev/sdb': [ { 'num': 1 } ]
        })

- name: Allow gaps in partition numbers
  assert:
    that:
      - validate_partitions_input({
          '/dev/sda': [ { 'num': 1 }, { 'num': 3 } ]
        }, allow_gaps=True)
'''

RETURN = r'''
_value:
  description: True if structure is valid; error is raised otherwise
  type: bool
  returned: always
'''

def validate_partitions_input(partitions, allow_gaps=False):
    PartitionInput(partitions, allow_gaps=allow_gaps)
    return True

class FilterModule(object):
    def filters(self):
        return {
            "validate_partitions_input": validate_partitions_input,
        }
