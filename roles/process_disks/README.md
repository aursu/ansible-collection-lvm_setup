# Ansible Role: process_disks

This role manages disk partitioning on Linux systems using a declarative `partitions` variable.

It supports:

- Validating requested partitions against current layout (via parted)
- Creating new partitions with proper alignment
- Skipping existing ones
- Generating device paths for further LVM use

## Example Usage

```yaml
- name: Prepare disks
  hosts: all
  roles:
    - role: aursu.lvm_setup.process_disks
```

## Required Variables

```yaml
partitions:
  /dev/sda:
    - num: 6
      size: 400g
    - num: 7
      size: 100g
```

## Author

Alexander Ursu ([alexander.ursu@gmail.com](mailto:alexander.ursu@gmail.com))

## License

MIT
