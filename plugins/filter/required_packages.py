# -*- coding: utf-8 -*-
# Copyright (c) 2026, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""Ansible filter plugin that lists the OS packages a set of volumes needs."""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.package_helpers import RequiredPackages

DOCUMENTATION = r'''
---
name: required_packages
author: Alexander Ursu
version_added: "1.5.0"
short_description: List the OS packages needed to create and format a set of logical volumes
description:
  - Returns the base packages followed by the package(s) providing C(mkfs) for each filesystem
    the volumes declare - only those filesystems, each once.
  - Duplicates are removed and the order is kept, so the result is stable across runs.
  - Every volume is checked as the rest of the collection checks it; an unsupported filesystem
    fails with the same message as M(aursu.lvm_setup.validate_volume#filter).
options:
  volumes:
    description:
      - List of volume definitions, as passed to the C(process_volumes) role. Only C(filesystem)
        affects the result; C(name), C(vg) and C(size) must be present as usual.
    type: list
    elements: dict
    required: true
  base_packages:
    description:
      - Packages needed whatever the filesystems, such as C(lvm2). A single name or a list.
    type: raw
    required: true
  filesystem_packages:
    description:
      - Map of filesystem type to the package name, or list of names, that provides its C(mkfs).
      - An empty list means the tools ship with the base system.
      - A filesystem used by a volume but missing from the map is an error.
    type: dict
    required: true
'''

EXAMPLES = r'''
- name: Ensure the LVM and filesystem tools are installed
  ansible.builtin.package:
    name: "{{ volumes | aursu.lvm_setup.required_packages(['lvm2'], {'xfs': 'xfsprogs', 'ext4': 'e2fsprogs'}) }}"
    state: present

# volumes declaring xfs, xfs, ext4 and one without a filesystem yield:
#   ['lvm2', 'xfsprogs', 'e2fsprogs']
'''

RETURN = r'''
_value:
  description: Package names, base packages first, without duplicates.
  type: list
  elements: str
  returned: always
'''


def required_packages(volumes, base_packages, filesystem_packages):
    return RequiredPackages(volumes, base_packages, filesystem_packages).resolve()


class FilterModule(object):
    def filters(self):
        return {
            'required_packages': required_packages,
        }
