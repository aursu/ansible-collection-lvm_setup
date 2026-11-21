# 04 — An existing mount point keeps its mode

| | |
|---|---|
| Release | 1.6.1 (2026-11-21) |
| PR | `fix/mountpoint-mode` |

## What

`process_volumes` creates a volume's mount point (mode `0755`) only when it
does not exist. An existing directory is no longer touched. "Ensure mount
point exists" became two tasks: `stat` of the path, then `file
state=directory mode=0755` when the path is not a directory.

## Why — the goal

The old task set `0755` on every run. After the first run the volume is
mounted there, so the path is the root of the volume's filesystem, and its
mode is the application's. dockerd keeps `/var/lib/docker` at `0710`; a dry
run on the home build host (2026-11-21) planned `/var/lib/docker 0710 →
0755` — Docker's data readable by every local user until the next dockerd
restart, and the same flip on every later run. Until this fix the consumer
had to pass only the volumes it changed in `--extra-vars`.

## How it works

1. `Read the mount point <path>` — `ansible.builtin.stat`, registers
   `lv_mountpoint`. Skipped without `mountpoint`.
2. `Create the mount point <path>` — runs when
   `not (lv_mountpoint.stat.isdir | default(false))`: the path is missing
   (`isdir` absent → `false`) or exists but is not a directory. In the second
   case the `file` module fails with "already exists as a file", as before —
   the change does not hide that error.

`stat` works in check mode, so a dry run reports exactly what an apply does.

## Where it is defined

| File | What |
|---|---|
| `roles/process_volumes/tasks/create_lv.yml` | the two tasks, with the reason in a comment |
| `roles/process_volumes/README.md` | `mountpoint` row: created when missing, existing left as it is |
| `galaxy.yml` | 1.6.1 |
| `CHANGELOG.md` | 1.6.1 |

## Rejected alternatives

- **A per-volume `mode` key.** It would let a consumer state `0710` for
  `/var/lib/docker` — duplicating a value dockerd owns, and wrong as soon as
  the application changes it. No consumer needs to *set* a mode; they need the
  role to stop setting one.
- **`file` without `mode`.** It still creates missing directories (with the
  umask), but `ansible-lint` flags `risky-file-permissions`, and the created
  mode would depend on the controller's settings.
- **Dropping the task** and relying on `ansible.posix.mount`, which creates a
  missing mount point itself. That directory's mode is then the module's
  choice, and check mode could not show the creation.

## Verified by

- The two tasks extracted from `create_lv.yml` and run in the
  `home-manage` control container against `localhost`: missing path →
  created `755`; existing directory `0710` → skipped, still `710`; no
  `mountpoint` → both skipped; a regular file at the path → fails "already
  exists as a file".
- Full `playbook_storage.yml` dry run against media-gw with this branch
  mounted over the installed collection (`ansible-galaxy` reports 1.6.1),
  **without** the `--extra-vars` workaround: `changed=0`; both
  "Create the mount point" tasks (`/var/lib/docker`,
  `/home/aursu/workspace`) skipped. With 1.6.0 the same run planned
  `/var/lib/docker 0710 → 0755`.
- `release_preflight.py --tag v1.6.1` (in the control container, which has
  PyYAML): tag matches `galaxy.yml`, Galaxy does not hold 1.6.1 yet.
