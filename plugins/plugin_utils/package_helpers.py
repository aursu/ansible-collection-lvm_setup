# -*- coding: utf-8 -*-
# Copyright (c) 2026, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""Resolution of the OS packages a set of logical volumes needs.

The roles call external tools - ``pvs``/``lvcreate`` from lvm2, ``mkfs.*``
from each filesystem's package - and install them first. Which mkfs packages
are needed depends on the filesystems the volumes declare, so the list is
computed here rather than in a Jinja chain: it is validated, unit-tested and
gives a clear error for a filesystem nobody mapped.
"""

from typing import Any

from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.general.plugins.plugin_utils.packages import PackageNames
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.lvm_helpers import LogicalVolume


class RequiredPackages:
    """The packages a list of volumes needs.

    The base packages come first, then the package(s) of each filesystem in the
    order the volumes declare them. Duplicates are dropped and the order is kept,
    so the result is the same on every run. Everything is validated in the
    constructor; ``resolve()`` cannot be called on a half-checked object.
    """

    def __init__(self, volumes: Any, base_packages: Any, filesystem_packages: Any):
        if not isinstance(volumes, list):
            raise AnsibleFilterError(f"Expected 'volumes' to be a list, got {type(volumes).__name__}.")
        if not isinstance(filesystem_packages, dict):
            raise AnsibleFilterError(
                f"Expected 'filesystem_packages' to be a dict, got {type(filesystem_packages).__name__}."
            )

        self._base = PackageNames(base_packages, "base_packages").names
        self._by_filesystem = {
            fs: PackageNames(packages, f"filesystem_packages[{fs!r}]").names
            for fs, packages in filesystem_packages.items()
        }

        # LogicalVolume rejects a non-dict entry and an unsupported filesystem
        # with the same messages the rest of the collection uses.
        self._volumes = [LogicalVolume(volume, idx) for idx, volume in enumerate(volumes)]
        for volume in self._volumes:
            volume.validate_filesystem()

    @property
    def filesystems(self) -> list:
        """Filesystems the volumes declare, each once, in declaration order."""
        return list(dict.fromkeys(volume.fs for volume in self._volumes if volume.fs))

    def resolve(self) -> list:
        packages = list(self._base)
        for fs in self.filesystems:
            if fs not in self._by_filesystem:
                raise AnsibleFilterError(
                    f"No package is mapped for filesystem '{fs}' in 'filesystem_packages'."
                )
            packages.extend(self._by_filesystem[fs])
        return list(dict.fromkeys(packages))
