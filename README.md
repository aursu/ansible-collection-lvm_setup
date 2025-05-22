# Ansible Collection - aursu.lvm_setup


A modular Ansible collection for declarative LVM-based storage provisioning on Linux hosts.

This collection provides reusable roles and filter plugins for validating and creating disk partitions,
physical volumes (PVs), volume groups (VGs), and logical volumes (LVs). It is designed to support
structured and idempotent automation for real-world environments.

## Included Roles

| Role                         | Purpose                                                  |
|------------------------------|----------------------------------------------------------|
| `process_disks`              | Validates and creates partitions using `parted`          |
| `process_lvm`                | Validates and sets up PVs and volume groups              |
| `process_volumes`            | Creates logical volumes, formats them, and mounts        |

## Filter Plugins

This collection includes filter plugins for validating input and planning storage operations:

- `validate_partitions`, `partition_path`, `partition_paths`
- `validate_lvm_partition`, `validate_pvs`, `validate_vg`, `validate_volume`, `validate_mount`
- Utility filters: `to_mib`, `mib`

## Example Playbook

Located in [`playbooks/setup_storage.yml`](playbooks/setup_storage.yml)

```yaml
- name: Create LVM setup on host
  hosts: all
  become: true

  vars:
    debug_mode: false

  roles:
    - aursu.lvm_setup.process_disks
    - aursu.lvm_setup.process_lvm
    - aursu.lvm_setup.process_volumes
````

## Example Variable File

```yaml
partitions:
  /dev/sda:
    - num: 6
  /dev/sdb:
    - num: 6

vg_name: data

volumes:
  - name: data1
    vg: data
    size: 200g
    filesystem: xfs
    mountpoint: /mnt/disks/data1
  - name: data2
    vg: data
    size: 200g
    filesystem: xfs
    mountpoint: /mnt/disks/data2
```

## Requirements

* Python 3.8+
* Ansible 2.14+
* `community.general` collection (for `parted` module)

Install dependency manually (if needed):

```bash
ansible-galaxy collection install community.general
```

## Testing Filters

Unit tests are located in:

```
tests/unit/plugins/filter/
```

Run tests with:

```bash
PYTHONPATH=. pytest tests/unit/plugins/filter/
```
