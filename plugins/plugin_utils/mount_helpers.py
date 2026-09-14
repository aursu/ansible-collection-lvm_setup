# -*- coding: utf-8 -*-
# Copyright (c) 2026, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""Planning helpers for logical-volume mounts.

The problem this solves
-----------------------

``Device.validate_mount`` in :mod:`lvm_helpers` answers one question - "is
something mounted at this path?" - by comparing the target and nothing else.
That is enough to decide whether to *create* a mount, and it is not enough for
anything else, because a mount can be present and still wrong in two ways that
both matter at boot:

* the ``/etc/fstab`` source can name a device that no longer exists, for example
  after a volume group is renamed. The live mount survives until the next reboot,
  at which point the entry fails to resolve;
* the ``/etc/fstab`` options can lack ``nofail``. A non-root mount that fails
  without ``nofail`` blocks ``local-fs.target``, so the host never reaches
  ``multi-user.target`` and never starts sshd.

Together those produce a host that answers ICMP with every TCP port refused, and
on a guest with no console there is no way back in.

Both faults are invisible to a target-only comparison, and both are invisible in
the *live* mount table as well: the kernel reports the device it actually
mounted and its own effective options, and ``nofail`` is a directive to the
systemd fstab generator rather than a kernel mount option, so it never appears
there. Checking for it against live options fails on every run and never
converges.

So planning a mount needs the static table too, which is what
``aursu.general.fstab_info`` provides.

The safety property
-------------------

When a volume is already mounted and only the fstab entry is wrong, the plan is
``update`` - rewrite the file and leave the running mount alone. Remounting to
"fix" it would be both unnecessary and dangerous: on a Kubernetes node the
volume is bind-mounted into live pod paths and is busy, and a remount that fails
there turns a latent boot problem into an immediate outage. The fstab entry is
what the *next* boot reads, and correcting it is the entire fix.
"""

from typing import Any, Optional

from ansible.errors import AnsibleFilterError

# Source specs that name a device by identity rather than by path. The collection
# does not write these, so it does not second-guess them either: an entry using
# one is left as it stands.
OPAQUE_SOURCE_PREFIXES = ("UUID=", "LABEL=", "PARTUUID=", "PARTLABEL=", "ID=")

# Applied when a volume declares no opts of its own. nofail is the load-bearing
# half: see the module docstring.
DEFAULT_MOUNT_OPTS = "defaults,nofail"


def split_opts(opts: Optional[str]) -> set:
    """Split an fstab options field into comparable tokens.

    Comparison is by token set rather than by string so that ordering does not
    cause spurious changes.

    >>> sorted(split_opts("defaults,nofail"))
    ['defaults', 'nofail']
    >>> sorted(split_opts("nofail,defaults"))
    ['defaults', 'nofail']
    >>> split_opts(None)
    set()
    >>> sorted(split_opts("defaults,,nofail "))
    ['defaults', 'nofail']
    """
    if not opts:
        return set()
    return {token.strip() for token in opts.split(",") if token.strip()}


def is_opaque_source(source: Optional[str]) -> bool:
    """Whether a source names a device by identity rather than by path.

    >>> is_opaque_source("UUID=29112d36-c757-4706-bde1-35ce90136486")
    True
    >>> is_opaque_source("/dev/data/data1")
    False
    >>> is_opaque_source(None)
    False
    """
    if not source:
        return False
    return source.startswith(OPAQUE_SOURCE_PREFIXES)


class FstabEntry:
    """One line of the static mount table, as returned by fstab_info."""

    def __init__(self, entry: Optional[dict]):
        if entry is not None and not isinstance(entry, dict):
            raise AnsibleFilterError(
                f"Expected an fstab entry to be a dictionary or None, "
                f"got {type(entry).__name__}"
            )
        self._entry = entry or {}

    @property
    def is_present(self) -> bool:
        return bool(self._entry)

    @property
    def target(self) -> Optional[str]:
        return self._entry.get("target")

    @property
    def source(self) -> Optional[str]:
        return self._entry.get("source")

    @property
    def options(self) -> Optional[str]:
        return self._entry.get("options")

    def source_matches(self, paths: set) -> bool:
        """Whether the recorded source still names the intended device.

        An opaque source such as UUID= is accepted as it stands: the collection
        did not write it and cannot resolve it here, so rewriting it would be
        churn.
        """
        if not self.is_present:
            return False
        if is_opaque_source(self.source):
            return True
        return self.source in paths

    def options_match(self, wanted: str) -> bool:
        if not self.is_present:
            return False
        return split_opts(self.options) == split_opts(wanted)


class MountPlan:
    """Decide what, if anything, to do about one volume's mount.

    The action is one of:

    skip
        Mounted where it should be, and the fstab entry names the right device
        with the right options. Nothing to do.
    mount
        Not mounted. Mount it and write the fstab entry.
    update
        Mounted correctly, but the fstab entry is missing, names a device that
        is not this volume, or carries the wrong options. Rewrite the entry
        without touching the running mount.
    """

    def __init__(self, volume, dev_info: dict, fstab_entry=None,
                 default_opts: str = DEFAULT_MOUNT_OPTS):
        self._volume = volume
        self._fstab = FstabEntry(fstab_entry)
        self._default_opts = default_opts

        if not isinstance(dev_info, dict):
            raise AnsibleFilterError(
                f"Expected device information 'dev_info' to be a dictionary for "
                f"{volume.path}, got {type(dev_info).__name__}"
            )
        self._mounts = dev_info.get("mount") or []
        self._is_exists = bool(dev_info.get("is_exists", False))

    @property
    def opts(self) -> str:
        """The options this volume should carry, declared or defaulted."""
        return self._volume.opts or self._default_opts

    def is_mounted(self) -> bool:
        """Whether the device is live-mounted at the declared mount point."""
        mountpoint = self._volume.mount
        if not (self._is_exists and mountpoint):
            return False
        for mount in self._mounts:
            if mount.get("target") == mountpoint:
                return True
        return False

    def reasons(self) -> list:
        """Why the plan is not skip. Empty when there is nothing to do."""
        reasons = []
        if not self._volume.mount:
            # Nothing is asked for, so nothing is wrong. A volume may legitimately
            # be created and left unmounted - dev-web-013 declares exactly that,
            # so that Puppet owns its mounts and can guarantee nofail.
            return reasons
        if not self.is_mounted():
            reasons.append(f"not mounted at {self._volume.mount}")
            return reasons

        if not self._fstab.is_present:
            reasons.append(f"no /etc/fstab entry for {self._volume.mount}")
            return reasons

        if not self._fstab.source_matches(self._volume.paths):
            known = " or ".join(sorted(self._volume.paths))
            reasons.append(
                f"/etc/fstab names {self._fstab.source!r}, which is not this "
                f"volume ({known}); it would not resolve at boot"
            )

        if not self._fstab.options_match(self.opts):
            missing = sorted(split_opts(self.opts) - split_opts(self._fstab.options))
            detail = ""
            if missing:
                detail = "; missing " + ", ".join(missing)
            reasons.append(
                f"/etc/fstab options are {self._fstab.options!r}, expected "
                f"{self.opts!r}{detail}"
            )

        return reasons

    def action(self) -> str:
        if not self._volume.mount:
            return "skip"
        if not self.is_mounted():
            return "mount"
        if self.reasons():
            return "update"
        return "skip"

    def to_dict(self) -> dict[str, Any]:
        action = self.action()
        return {
            "name": self._volume.name,
            "path": self._volume.path,
            "mountpoint": self._volume.mount,
            "fstype": self._volume.fs,
            "opts": self.opts,
            "action": action,
            "mounted": self.is_mounted(),
            "fstab_present": self._fstab.is_present,
            "fstab_source": self._fstab.source,
            "fstab_options": self._fstab.options,
            "reasons": self.reasons(),
            # The state to hand to ansible.posix.mount. "present" is the safe
            # one: it rewrites fstab and leaves a busy, running mount untouched.
            "mount_state": {"mount": "mounted", "update": "present"}.get(action),
        }
