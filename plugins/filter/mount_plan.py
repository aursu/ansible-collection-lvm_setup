# -*- coding: utf-8 -*-
# Copyright (c) 2026, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""Ansible filter plugin that plans a logical volume's mount."""

from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import LogicalVolume
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.mount_helpers import (
    DEFAULT_MOUNT_OPTS,
    MountPlan,
)

DOCUMENTATION = r'''
---
name: mount_plan
author: Alexander Ursu
version_added: "1.3.0"
short_description: Plan the mount of a logical volume, including its fstab entry
description:
  - Decides whether a logical volume needs mounting, needs its C(/etc/fstab) entry corrected,
    or needs nothing at all, and reports why.
  - This supersedes P(aursu.lvm_setup.validate_mount#filter), which compares only the mount
    target. A target-only comparison cannot see an fstab entry whose source no longer exists,
    nor one missing C(nofail) - both of which leave a host unable to boot while looking
    entirely healthy until it is restarted.
  - Requires the static mount table, which the live mount table cannot supply. C(nofail) and
    C(_netdev) are directives to the systemd fstab generator, not kernel mount options, so they
    never appear in live output. Use M(aursu.general.fstab_info) to obtain it.
options:
  lv:
    description:
      - Dictionary describing the logical volume. Requires C(name), C(vg) and C(size); honours
        the optional C(mountpoint), C(filesystem) and C(opts) keys.
    type: dict
    required: true
  dev_info:
    description:
      - Live device metadata for this volume, from M(aursu.general.dev_info).
    type: dict
    required: true
  fstab_entry:
    description:
      - The C(/etc/fstab) entry for this volume's mount point, from M(aursu.general.fstab_info).
      - Pass C(none) when the mount point is absent from the file.
    type: dict
    required: false
    default: null
  default_opts:
    description:
      - Mount options applied when the volume declares no C(opts) of its own.
      - The default deliberately includes C(nofail), so that a non-root mount which fails cannot
        block C(local-fs.target) and strand the host.
      - Network filesystems additionally need C(_netdev). This is not inferred, because the
        collection creates only local filesystems (ext4, xfs, btrfs); set it explicitly through
        C(opts) if a caller mounts something else.
    type: str
    required: false
    default: defaults,nofail
seealso:
  - module: aursu.general.fstab_info
  - module: aursu.general.dev_info
'''

EXAMPLES = r'''
- name: Read the live and static views of the volume
  aursu.general.dev_info:
    dev: "/dev/data/data1"
  register: dev_info

- name: Read the fstab entry for its mount point
  aursu.general.fstab_info:
    path: /mnt/disks/data1
  register: fstab

- name: Plan the mount
  ansible.builtin.set_fact:
    plan: "{{ lv | aursu.lvm_setup.mount_plan(dev_info, fstab.entry) }}"

# A volume mounted from a renamed volume group yields:
#   action: update
#   mount_state: present
#   reasons:
#     - "/etc/fstab names '/dev/data-ssd/data1', which is not this volume
#        (/dev/data/data1 or /dev/mapper/data-data1); it would not resolve at boot"
#     - "/etc/fstab options are 'defaults', expected 'defaults,nofail'; missing nofail"
'''

RETURN = r'''
_value:
  description: The mount plan.
  type: dict
  returned: always
  contains:
    action:
      description:
        - V(skip) when mounted correctly and recorded correctly.
        - V(mount) when not mounted.
        - V(update) when mounted correctly but the fstab entry is missing or wrong.
      type: str
    mount_state:
      description:
        - The C(state) to pass to M(ansible.posix.mount), or C(none) when the action is V(skip).
        - V(present) for an update, so that the file is corrected and a running - possibly
          busy - mount is left alone.
      type: str
    opts:
      description: The options the fstab entry should carry.
      type: str
    mounted:
      description: Whether the device is live-mounted at the declared mount point.
      type: bool
    fstab_present:
      description: Whether the mount point appears in C(/etc/fstab) at all.
      type: bool
    fstab_source:
      description: The source recorded in C(/etc/fstab), if any.
      type: str
    fstab_options:
      description: The options recorded in C(/etc/fstab), if any.
      type: str
    reasons:
      description: Human-readable reasons the action is not V(skip). Empty when it is.
      type: list
      elements: str
'''


def mount_plan(lv, dev_info, fstab_entry=None, default_opts=DEFAULT_MOUNT_OPTS):
    volume = LogicalVolume(lv)
    volume.validate()

    return MountPlan(volume, dev_info, fstab_entry, default_opts).to_dict()


class FilterModule(object):
    def filters(self):
        return {
            'mount_plan': mount_plan
        }
