# Ansible Role: process_lvm

This role prepares physical volumes and creates or extends a volume group (VG) using validated partitions.

It supports:

- Validating partitions for LVM usage (block device, not formatted, etc.)
- Creating physical volumes if they don't exist
- Adding existing PVs to a volume group
- Creating the volume group if needed

## Example Usage

```yaml
- name: Process LVM physical volumes
  hosts: all
  roles:
    - role: aursu.lvm_setup.process_lvm
```

## Required Variables

```yaml
partitions:
  /dev/sda:
    - num: 6
    - num: 7

volume_group: data
```

## Author

Alexander Ursu ([alexander.ursu@gmail.com](mailto:alexander.ursu@gmail.com))

## License

MIT
