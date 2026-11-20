# 02 — Each role installs the packages whose tools it calls

| | |
|---|---|
| Release | 1.5.0 (2026-11-20) |
| PR | #1 `feature/role-packages`, merged as `a717944` |
| Commits | `f14ab0d` package tasks; `146e6ac` review: Python filter, install out of `validate.yml`; `2681bd0` `.DS_Store` untracked, `.gitignore` |

## What

Every role installs, as its first step, the OS packages that provide the tools
it calls: `parted`, `lvm2`, and the `mkfs` package of each filesystem the
volumes declare. The list for `process_volumes` comes from a new Python filter,
`required_packages`.

## Why — the goal

The roles called `parted`, `pvs`/`vgs`/`lvs`/`lvcreate` and `mkfs.*` and
installed none of them. On `media-gw`, whose root is not on LVM, `lvm2` was
absent: `process_disks` created a partition, then `process_lvm` failed with
`Failed to find required executable "pvs"`, leaving the disk half-provisioned.
A collection that configures LVM must resolve its own dependencies — not leave
every consumer to add a pre-task (which is what was first done, and rejected).

## How it works

- `process_disks`: first task installs `process_disks_packages` (`parted`).
- `process_lvm`: first task installs `process_lvm_packages` (`lvm2`, `parted` —
  this role also reads the partition table).
- `process_volumes`: first task installs
  `volumes | required_packages(process_volumes_packages, process_volumes_filesystem_packages)`.
- `required_packages` → `RequiredPackages(volumes, base, by_filesystem).resolve()`:
  1. validates the base list and each map value (a name or a list of names);
  2. builds a `LogicalVolume` for each volume and calls `validate_filesystem()`,
     so an unsupported filesystem fails with the collection's usual message
     before anything is installed;
  3. collects the declared filesystems once each, in declaration order;
  4. refuses a supported filesystem missing from the map, naming it;
  5. returns base + per-filesystem packages, deduplicated with order kept
     (`dict.fromkeys`), so the result is identical on every run.

## Where it is defined

| File | What |
|---|---|
| `roles/process_disks/defaults/main.yml`, `tasks/main.yml` | `process_disks_packages`; install as the first task |
| `roles/process_lvm/defaults/main.yml`, `tasks/main.yml` | `process_lvm_packages`; install as the first task |
| `roles/process_volumes/defaults/main.yml` | `process_volumes_packages`, `process_volumes_filesystem_packages` (xfs → xfsprogs, ext4 → e2fsprogs, btrfs → btrfs-progs; a name or a list) |
| `roles/process_volumes/tasks/main.yml` | install as the first task, through the filter |
| `roles/process_volumes/tasks/validate.yml` | read-only again (the install moved out) |
| `plugins/plugin_utils/package_helpers.py` | `RequiredPackages` |
| `plugins/filter/required_packages.py` | the filter and its documentation |
| `tests/unit/plugins/filter/test_required_packages.py` | 13 tests |
| `.gitignore` | `.DS_Store` |

## Rejected alternatives

- **A `lvm2` pre-task in the consumer playbook** (`home-manage`). Alexander:
  a role that configures LVM must not need its consumers to resolve its
  dependencies. Every consumer would repeat it.
- **The package list as a Jinja chain**
  (`selectattr | map | unique | map('extract') | list`). First version; rejected
  in review — unreadable, untestable, and an unmapped filesystem produced a
  template error. Replaced by the filter.
- **The install in `validate.yml`.** First version, placed after the input check
  so an unsupported filesystem was rejected before any install. Rejected in
  review: a file named `validate` must not change state. The filter checks the
  filesystem itself, which removed the reason for that placement.
- **A promise that `[]` disables package management.** Removed from the
  CHANGELOG before release: untested across package managers.

## Mistake on the way

`git add -A` in a repository without `.gitignore` committed three `.DS_Store`
files into the PR. Fixed by a follow-up commit (no force-push); files are now
staged by path.

## Verified by

107 unit tests (13 new); `ansible-lint roles/ playbooks/` exit 0; the filter by
FQCN returns `["lvm2","xfsprogs","e2fsprogs"]` for xfs, ext4, xfs and a volume
without a filesystem. Applied on `media-gw`: the three package tasks were `ok`
(already present), and the storage layout converged; a repeat run reported
`changed=0`.

## Side effect worth knowing

Installing a package runs its maintainer scripts: `lvm2` triggers an initramfs
rebuild on Ubuntu. On `media-gw` that exposed a full `/boot`, which is how the
kernel-retention work (`aursu.baseprofile.kernel_cleanup`) started.
