# Ansible Role: process_volumes

This role creates logical volumes inside a volume group (VG) using validated input definitions.

It supports:

- Creating LVs based on a list of volume definitions
- Formatting filesystems (xfs, ext4, btrfs)
- Mounting them, and recording them in `/etc/fstab` with `nofail` by default
- Detecting an existing mount that is recorded **wrongly** - a source that no longer resolves, or
  options that are missing - and correcting the file without disturbing the running mount
- Skipping volumes that are already present and correct

## Example Usage

```yaml
- name: Create logical volumes
  hosts: storage
  roles:
    - role: aursu.lvm_setup.process_volumes
```

## Required Variables

```yaml
volumes:
  - name: data1
    vg: data
    size: 200g
    filesystem: xfs
    mountpoint: /mnt/data1
```

| Key | Required | Description |
|---|---|---|
| `name` | yes | Logical volume name. |
| `vg` | yes | Volume group it belongs to. |
| `size` | yes | Size, e.g. `200g`. |
| `filesystem` | no | One of `ext4`, `xfs`, `btrfs`. Omit to create the LV without formatting it. |
| `mountpoint` | no | Absolute path. Omit to create the volume and leave mounting to something else. |
| `opts` | no | Mount options written to `/etc/fstab`, e.g. `defaults,nofail,noatime`. Aliased as `options`. Defaults to `lvm_mount_opts_default`. |

## Role Defaults

```yaml
lvm_mount_opts_default: defaults,nofail
```

### Why the default contains `nofail`

A non-root mount that fails without `nofail` fails `local-fs.target`. The host then never reaches
`multi-user.target`, never starts sshd, and answers ICMP while refusing every TCP port. On a guest
with no console there is no way back in.

Until 1.3.0 this role passed no options at all, and `ansible.posix.mount` defaults to `defaults`,
which does not include `nofail`. Every entry the role had ever written was therefore exposed to
this.

### `_netdev` is not inferred

Network filesystems need `_netdev` as well. It is **not** derived from `filesystem`, because this
role only ever creates local filesystems (`ext4`, `xfs`, `btrfs`). A caller mounting something else
sets it explicitly through `opts`.

## Correcting an existing mount

The mount task is planned by `aursu.lvm_setup.mount_plan`, which compares the declared volume
against **both** the live mount table (`aursu.general.dev_info`) and the static one
(`aursu.general.fstab_info`), and yields one of:

| action | meaning | `ansible.posix.mount` state |
|---|---|---|
| `skip` | mounted in the right place, recorded correctly | task not run |
| `mount` | not mounted | `mounted` |
| `update` | mounted correctly, but `/etc/fstab` is missing, names another device, or has the wrong options | `present` |

`update` uses `present` deliberately: it rewrites the file and **leaves the running mount alone**.
A remount is unnecessary there and can be harmful - on a Kubernetes node the volume is bind-mounted
into live pod paths and is busy, so remounting would fail and turn a latent boot fault into an
immediate outage.

The static table is required because `nofail` and `_netdev` are directives to the systemd fstab
generator rather than kernel mount options: they never appear in live mount output, so a check for
them against it can never succeed.

## Author

Alexander Ursu ([alexander.ursu@gmail.com](mailto:alexander.ursu@gmail.com))

## License

MIT
