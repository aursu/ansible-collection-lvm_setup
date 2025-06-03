# Playbook: setup_storage.yml

This playbook configures disk storage on Linux systems using declarative inputs. It performs the following steps:

1. Validates and prepares disk partitions (`process_disks`)
2. Initializes physical volumes and creates or extends a volume group (`process_lvm`)
3. Creates logical volumes with filesystems and optionally mounts them (`process_volumes`)

## Usage

```bash
ansible-playbook playbooks/setup_storage.yml -l myhost
```

## Inventory Variables

The playbook expects the following variables to be defined per host (e.g., in host vars):

### `partitions`

Defines the partition layout per disk:

```yaml
partitions:
  /dev/sda:
    - num: 6
      size: 400g
    - num: 7
      size: 100g
```

### `volume_group`

Specifies the name of the volume group to create:

```yaml
volume_group: data
```

### `volumes`

List of logical volumes to create inside the volume group:

```yaml
volumes:
  - name: data1
    vg: data
    size: 200g
    filesystem: xfs
    mountpoint: /mnt/data1
  - name: data2
    vg: data
    size: 100g
    filesystem: ext4
    mountpoint: /mnt/data2
```

## Requirements

* Ansible 2.14+
* Root access to modify partitions and LVM
* Python 3.9+ recommended
* `community.general` collection (for parted info)

## Roles Used

* `aursu.lvm_setup.process_disks`
* `aursu.lvm_setup.process_lvm`
* `aursu.lvm_setup.process_volumes`

## Author

Alexander Ursu ([alexander.ursu@gmail.com](mailto:alexander.ursu@gmail.com))

## License

MIT
