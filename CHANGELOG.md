# Changelog

All notable changes to `aursu.lvm_setup` are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-09-15

### Fixed

- **1.3.0 shipped an unparseable task file and could not provision anything.**
  `roles/process_volumes/tasks/create_lv.yml` carried an orphaned fragment left by a botched
  line-based edit:

  ```yaml
  when:
    - debug_mode | default(false)
    - lv.mountpoint is defined
  | default(false)                 # orphan
    - lv.mountpoint is defined     # duplicate
  ```

  Any run reached `process_volumes` and died with *"While scanning a block scalar did not find
  expected comment or line break"*. On a from-scratch host that happens **after** the partition
  and the volume group have been created, so the disk is left half-provisioned: PV and VG
  present, no logical volume, no filesystem, no mount.

  Nothing in CI was in a position to catch it. The unit tests exercise the Python filters and
  never read a task file; `ansible-playbook --syntax-check` parses a play and what it
  *statically* includes, and `create_lv.yml` is reached through `include_tasks`, which is
  dynamic; and `ansible-galaxy collection build` copies files without parsing them. The first
  thing to object was a live run against real hardware.

  `.github/scripts/yaml_check.py` now parses every YAML file in the collection, in both the test
  and release workflows. Verified against the broken tree: exit 1, naming the file and line.

## [1.3.0] - 2026-09-14

### Changed - read this before upgrading

**Every fstab entry this collection writes now carries `nofail` by default, and existing
entries are corrected on the next run.** That is a deliberate behaviour change, not a side
effect, and it is why this is a minor release rather than a patch.

Until now `roles/process_volumes/tasks/create_lv.yml` called `ansible.posix.mount` with no
`opts` at all. The module's default is `defaults`, and `defaults` does not include `nofail`,
so every fstab line the collection has ever written omits it.

The consequence is not cosmetic. A non-root mount that fails without `nofail` fails
`local-fs.target`; the host then never reaches `multi-user.target`, never starts sshd, and
answers ICMP while refusing every TCP port. On a guest with no console there is no way back in.

### Added

- **`opts` on a volume definition.** Optional, aliased as `options`, and validated: an empty
  value or an option with surrounding whitespace is rejected rather than written into fstab,
  where it would be a syntax error.
- **`lvm_mount_opts_default` role default**, `defaults,nofail`, applied to any volume that does
  not declare its own `opts`.
- **`aursu.lvm_setup.mount_plan` filter**, which supersedes `validate_mount` for deciding
  whether to act. It returns a structure - `action`, `mount_state`, `opts`, `mounted`,
  `fstab_present`, `fstab_source`, `fstab_options`, `reasons` - so a caller can tell "not
  mounted" from "mounted, but recorded wrongly" and report the second as a change rather than
  a creation.
- **`plugins/plugin_utils/mount_helpers.py`**, holding that logic: `split_opts`,
  `is_opaque_source`, `FstabEntry` and `MountPlan`.
- Unit coverage in `tests/unit/plugins/filter/test_mount_plan.py`, including an explicit
  convergence test - applying a plan must make the next run a no-op.

### Fixed

- **The guard skipped every host that was already mounted, which made the change above useless
  on exactly the hosts that needed it.** The mount task was gated on
  `not (lv | aursu.lvm_setup.validate_mount(dev_info))`, and `validate_mount` compares only the
  mount target:

  ```python
  if target and target == mountpoint:
  ```

  Nothing in it models options or the source. So on a host where the volume was already mounted
  in the right place it returned true, the task was skipped, and a new `opts` default would
  never have reached a single existing host - only volumes created from scratch afterwards.

- **A stale fstab source was invisible for the same reason.** Measured across the estate on
  2026-09-14: seven of nine Kubernetes nodes had `/dev/data-ssd/data{1,2}` in fstab after the
  volume group was renamed to `data`. The device had not existed for months; the volumes stayed
  mounted because the nodes had not rebooted since. With no `nofail`, the next reboot of any of
  them would have failed `local-fs.target`. `mount_plan` reports this as
  `would not resolve at boot`.

### Safety

- When a volume is **already mounted** and only its fstab entry is wrong, the plan is `update`
  and the module is called with `state: present` - the file is corrected and the running mount
  is left alone. A remount is unnecessary there and actively dangerous: on a Kubernetes node
  the volume is bind-mounted into live pod paths and is busy, so remounting would turn a latent
  boot fault into an immediate outage.
- `_netdev` is **not** inferred from the filesystem type. The collection creates only local
  filesystems (`ext4`, `xfs`, `btrfs`), so there is nothing to infer it from; a caller mounting
  a network filesystem sets it explicitly through `opts`.
- An `UUID=`/`LABEL=`/`PARTUUID=` source is left as it stands. The collection did not write it
  and cannot resolve it, so rewriting it would be churn rather than a correction.

### Deprecated

- `aursu.lvm_setup.validate_mount` still exists and still returns a boolean, so nothing that
  uses it breaks. It answers only "is something mounted here?", which remains the right question
  when deciding whether to *create* a mount and is not sufficient for anything else. New callers
  should use `mount_plan`.

### Requires

- `aursu.general >= 1.6.0`, for the new `aursu.general.fstab_info` module.

  ⚠ It must be 1.6.0, not 1.5.0. Galaxy has served `aursu.general` 1.5.0 since
  2026-02-04, and that release does NOT contain `fstab_info` - it was published
  from a working tree whose version bump was never committed, so the repository
  read 1.4.0 while Galaxy read 1.5.0. A `>=1.5.0` requirement would resolve
  happily against the published 1.5.0 and then fail at run time with
  `couldn't resolve module/action aursu.general.fstab_info`.

  The static mount table is not obtainable from the live one. `dev_info` runs `findmnt -J`,
  which reports the device as actually mounted and the kernel's effective options; `nofail` and
  `_netdev` are directives to the systemd fstab generator rather than kernel mount options and
  never appear there. A check for them against live options fails on every run and never
  converges.

## [1.2.0]

Baseline for this changelog; earlier releases are recorded in the git history only.

[1.3.0]: https://github.com/aursu/ansible-collection-lvm_setup/releases/tag/v1.3.0
