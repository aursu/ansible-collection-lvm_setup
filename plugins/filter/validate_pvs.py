# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Ansible filter plugin to determine required actions for physical volumes in a volume group
"""

from typing import Any
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import VolumeGroup

DOCUMENTATION = r'''
---
name: validate_pvs
author: Alexander Ursu
version_added: "1.0"
short_description: Determine required actions for physical volumes in a volume group
description:
  - This filter compares device paths against current LVM metadata and determines whether
    each device needs to be created, added, or skipped when preparing physical volumes (PVs).
options:
  lvm_info:
    description:
      - Dictionary returned by a module like C(aursu.general.lvm_info), containing keys C(pv), C(vg), and C(lv).
    type: dict
    required: true
  paths:
    description:
      - List of full partition device paths to evaluate (e.g. C(/dev/sda6), C(/dev/nvme0n1p1)).
    type: list
    elements: str
    required: true
  vg_name:
    description:
      - Target volume group name which all given PVs should belong to.
    type: str
    required: true
seealso:
  - name: validate_lvm_partition
    description: Validates if a single partition can be used as a physical volume
    plugin: aursu.lvm_setup.validate_lvm_partition
'''

EXAMPLES = r'''
- name: Determine PV actions for /dev/sda6 and /dev/sdb7
  set_fact:
    pv_plan: >-
      {{ validate_pvs(lvm_info, ['/dev/sda6', '/dev/sdb7'], 'data') }}

- name: Create physical volumes
  ansible.builtin.command: "pvcreate {{ item.path }}"
  loop: "{{ pv_plan }}"
  when: item.action == 'create'
'''

RETURN = r'''
_value:
  description: List of dictionaries with required actions for each PV device
  type: list
  elements: dict
  returned: always
  sample:
    - path: /dev/sda6
      action: create
    - path: /dev/sdb7
      action: skip
'''

def validate_pvs(lvm_info: dict[str, Any], paths: list[str], vg_name: str) -> list[dict[str, str]]:
    """
    Determine the required LVM action for each partition path.

    Args:
        lvm_info: Parsed LVM information with "pv" data.
        paths: List of full device paths (e.g., "/dev/sda6").
        vg_name: Target volume group name.

    Returns:
        List of dictionaries with:
            - path: the device path
            - action: one of "create", "add", or "skip"
    """
    return VolumeGroup.from_lvm_info(vg_name, lvm_info).plan_pvs(paths)

class FilterModule(object):
    def filters(self):
        return {
            'validate_pvs': validate_pvs
        }
