# Ansible Role: process_volumes

This role creates logical volumes inside a volume group (VG) using validated input definitions.

It supports:

- Creating LVs based on a list of volume definitions
- Formatting filesystems (xfs, ext4, btrfs)
- Validating existing mountpoints
- Skipping existing volumes if already present and correct

## Example Usage

```yaml
- name: Create logical volumes
  hosts: all
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

## Author

Alexander Ursu ([alexander.ursu@gmail.com](mailto:alexander.ursu@gmail.com))

## License

MIT
