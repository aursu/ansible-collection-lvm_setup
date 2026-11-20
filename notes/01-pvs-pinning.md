# 01 — `pvs:` pins a logical volume to named physical volumes

| | |
|---|---|
| Release | 1.4.0 (2026-11-20) |
| PR | none — pushed to `main` before the PR-only rule |
| Commits | `4f6b2f4` code and tests, `dbbc290` docs and release |

## What

A volume may carry `pvs: [/dev/...]`. The logical volume is created on those
physical volumes only, and the free-space check counts the free space on them
rather than on the whole volume group.

## Why — the goal

The home server `media-gw` uses **one volume group over two NVMe disks**
(Alexander's choice over one group per disk). Without pinning, LVM allocates a
new LV wherever it finds room, an LV can end up spread across both disks, and
losing either disk loses it. Each LV must stay on the disk chosen for it. The
collection had no way to say so: `lvol` was called without `pvs`.

## How it works

- `LogicalVolume` reads an optional `pvs` key. `validate_pvs()` accepts `None`
  (no pinning) or a non-empty list of absolute paths without duplicates.
- `VolumeGroup.plan_volume()`:
  - with `pvs`, free space = `free_on(pvs)` = sum of `pv_free` on those PVs;
    otherwise the group's `vg_free`;
  - `free_on()` refuses a PV that is not a member of the group — checked for an
    **existing** LV too, so a typo fails at once, not at the next create;
  - for a new LV, a size above that free space is refused with the PV names in
    the message.
- `create_lv.yml` reads `lvm_info` with `filter: all` (PV data was not fetched
  before) and passes `pvs: "{{ lv.pvs | default(omit) }}"` to
  `community.general.lvol`.

## Where it is defined

| File | What |
|---|---|
| `plugins/plugin_utils/lvm_helpers.py` | `PhysicalVolume.pv_free`; `LogicalVolume._pvs`, `pvs`, `validate_pvs()`; `VolumeGroup.plan_volume()` (free space on the named PVs), `VolumeGroup.free_on()` (membership + sum) |
| `roles/process_volumes/tasks/create_lv.yml` | `lvm_info` with `filter: all`; `pvs` passed to `lvol` |
| `tests/unit/plugins/filter/test_validate_volume.py` | 10 tests — the first tests of `validate_volume` |
| `roles/process_volumes/README.md`, `README.md`, `CHANGELOG.md` | the `pvs` key and its limits |

## Rejected alternatives

- **One volume group per disk.** Makes placement implicit and safe, but
  Alexander chose one group; pinning makes it explicit instead.
- **Checking free space against the whole group.** Correct without pinning,
  wrong with it: the group can have room while the named disk does not, and
  `lvcreate` would fail mid-run.
- **Validating membership only on create.** A typo in `pvs` of an existing LV
  would then wait silently until the next create.

## Verified by

94 unit tests; the 10 new ones run against the previous code as a control —
7 fail (everything that involves `pvs`), the 3 covering unchanged behaviour pass.
Applied on `media-gw` (with 1.5.0): `lvs -o +devices` shows both LVs on
`/dev/nvme0n1p4` only.

## Not covered

Whether an existing LV still lies only on its `pvs` is not verified —
`aursu.general.lvm_info` does not report `devices`. Volumes are not extended by
this collection.
