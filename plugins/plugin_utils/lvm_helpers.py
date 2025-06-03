import os.path
from abc import ABC
from typing import Any, Optional
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.module_utils.size_utils import to_mib

class Device:
    def __init__(self, path):
        """
        Represents a device with a given absolute path.

        Args:
            path (str): The absolute path to the device (e.g., /dev/sda).

        Raises:
            AnsibleFilterError: If the path is not a string or not an absolute path.
        """
        if isinstance(path, str) and os.path.isabs(path):
            self._path = path
        else:
            raise AnsibleFilterError(f"Invalid device path: {path!r}. Must be an absolute path string.")

        # Initially assume the device does not exist
        self._is_exists: bool = False
        self._stat_error: Optional[str] = None
        self._filetype: Optional[str] = None
        self._fs_type: Optional[str] = None
        self._mount: list[dict[str, str]] = []

        # No device info available at instantiation
        self.raw_info: dict[str, Any] = {}

    @classmethod
    def from_dev_info(cls, path: str, dev_info: dict[str, Any]) -> "Device":
        """
        Create a Device instance from a given path and device information.

        Args:
            path (str): The absolute path to the device (e.g., "/dev/sda1").
            dev_info (dict[str, Any]): Dictionary containing device metadata.

        Returns:
            Device: An initialized Device object.

        Raises:
            AnsibleFilterError: If dev_info is not a dictionary.
        """
        if not isinstance(dev_info, dict):
            raise AnsibleFilterError(f"Expected device information 'dev_info' to be a dictionary for {path}, got {type(dev_info).__name__}")

        obj = cls(path)
        obj.from_metadata(dev_info)

        return obj
    
    def _set_existence_flag(self, dev_info: dict[str, Any]) -> None:
        """Set the internal existence flag based on dev_info."""
        self._is_exists = bool(dev_info.get("is_exists", False))

    def _set_stat_error(self, dev_info: dict[str, Any]) -> None:
        """Set the internal existence flag based on dev_info."""
        self._stat_error = dev_info.get('stat', {}).get('error')
    
    def _set_filetype(self, dev_info: dict[str, Any]) -> None:
        self._filetype = dev_info.get('filetype')
    
    def _set_filesystem_type(self, dev_info: dict[str, Any]) -> None:
        self._fs_type = dev_info.get('blkid', {}).get('type')

    def _set_mount_points(self, dev_info: dict[str, Any]) -> None:
        self._mount = dev_info.get('mount', [])

    def from_metadata(self, dev_info: dict[str, Any]) -> None:
        self._set_existence_flag(dev_info)
        self._set_stat_error(dev_info)
        self._set_filetype(dev_info)
        self._set_filesystem_type(dev_info)
        self._set_mount_points(dev_info)

        self.raw_info = dev_info

    @property
    def is_exists(self) -> bool:
        return self._is_exists
    
    @property
    def path(self) -> str:
        return self._path
    
    @property
    def fs_type(self) -> str:
        return self._fs_type
    
    def is_stat_error(self) -> bool:
        return bool(self._stat_error)
    
    def is_block_device(self) -> bool:
        return self._filetype == "b"
    
    def has_filesystem(self) -> bool:
        return bool(self.fs_type)

    def is_lvm2_member(self) -> bool:
        return self.fs_type == "LVM2_member"
    
    def validate_lvm(self) -> bool:
        """
        Validate the device for use as an LVM physical volume.

        Raises:
            AnsibleFilterError: If the device is invalid for LVM use.
        """
        if not self.is_exists:
            raise AnsibleFilterError(f"Partition {self.path} does not exist.")
        
        if self.is_stat_error():
            raise AnsibleFilterError(f"Partition file {self.path} stat error: {self._stat_error}")
        
        if not self.is_block_device():
            raise AnsibleFilterError(f"Partition {self.path} is not a block device (actual filetype is {self._filetype}).")
        
        if self.has_filesystem() and not self.is_lvm2_member():
            raise AnsibleFilterError(f"Partition {self.path} contains unexpected filesystem: {self.fs_type}")

        return True

    def validate_mount(self, mountpoint: str):
        if self.is_exists and mountpoint:
            for mount in self._mount:
                target = mount.get("target")
                if target and target == mountpoint:
                    return True
        return False

class PhysicalVolume:
    def __init__(self, path: str):
        if isinstance(path, str) and os.path.isabs(path):
            self._path = path
        else:
            raise AnsibleFilterError(f"Invalid PV path: {path!r}. Must be an absolute path string.")

        self._is_exists: bool = False
        self._vg_name: Optional[str] = None
        self._pv_attr: Optional[str] = None
        self._pv_fmt: Optional[str] = None
        self._pv_size: Optional[str] = None
        self._pv_free: Optional[str] = None

        # No device info available at instantiation
        self.raw_info: dict[str, str] = {}
        self._lvm_info: Optional[dict[str, Any]] = None

    def from_metadata(self, lvm_info: dict[str, list[dict[str, str]]]) -> None:
        """
        Populate PV information from lvm_info, if available.

        Args:
            lvm_info (dict): LVM info structure containing "pv" entries.
        """
        for pv in lvm_info.get("pv", []):
            if pv.get("pv_name") == self._path:
                self._is_exists = True
                self._vg_name = pv.get("vg_name")
                self._pv_attr = pv.get("pv_attr")
                self._pv_fmt =  pv.get("pv_fmt")
                self._pv_size = pv.get("pv_size")
                self._pv_free = pv.get("pv_free")
                self.raw_info = pv
                break
        self._lvm_info = lvm_info

    @classmethod
    def from_lvm_info(cls, path: str, lvm_info: dict[str, Any]) -> "PhysicalVolume":
        if not isinstance(lvm_info, dict):
            raise AnsibleFilterError(
                f"Expected LVM information 'lvm_info' to be a dictionary for {path}, "
                f"got {type(lvm_info).__name__}"
            )

        obj = cls(path)
        obj.from_metadata(lvm_info)

        return obj

    @property
    def path(self) -> str:
        return self._path

    def validate_group(self, vg_name: str) -> bool:
        """
        Validate whether the PV is suitable for use in the given VG.

        Returns:
            True if PV exists and is already in the correct VG.
            False if PV does not exist or is not yet in any VG.

        Raises:
            AnsibleFilterError: If PV is already in a different VG.
        """
        if self._is_exists:
            if self._vg_name:
                if self._vg_name == vg_name:
                    return True
                raise AnsibleFilterError(
                    f"Persistent volume {self._path} is already part of another volume group: {self._vg_name}"
                )
        return False

    def plan(self, vg_name: str) -> dict[str, str]:
        """
        Determine the required action for this PV with respect to the target volume group.

        Args:
            vg_name (str): Name of the target volume group.

        Returns:
            dict: Plan with keys "path", "action".

        Raises:
            AnsibleFilterError: If vg_name is not provided or PV is already in another VG.
        """
        if not vg_name:
            raise AnsibleFilterError(
                f"Volume group name ('vg_name') must be specified to determine action for physical volume {self._path}."
            )

        if self.validate_group(vg_name):
            action = "skip"
        elif self._is_exists:
            action = "add"
        else:
            action = "create"
        return {
            "path": self._path,
            "action": action
        }

class LogicalVolume:
    SUPPORTED_FS = {"ext4", "xfs", "btrfs"}

    def __init__(self, lv_data, idx=None):
        self._index: Optional[int] = None
        self._msg_in: Optional[str] = ""
        self._msg_for: Optional[str] = ""
        self.set_index(idx)

        self._name: Optional[str] = None
        self._vg: Optional[str] = None
        self._size: Optional[str] = None
        self._fs: Optional[str] = None
        self._mount: Optional[str] = None

        self._path: Optional[str] = None
        # device mapper path
        self._dm_path: Optional[str] = None

        self.raw_data: dict[str, str] = {}
        self._lvm_info: Optional[dict[str, Any]] = None

        self.state: Optional["LogicalVolume"] = None

        self._device: Optional[Device] = None
        self._is_exists: bool = False

        self.from_metadata(lv_data)

    def set_index(self, idx=None):
        if not isinstance(idx, int):
            return
        self._index = idx
        self._msg_in = f" in logical volume #{idx+1}"
        self._msg_for = f" for logical volume #{idx+1}"

    @property
    def index(self) -> Optional[int]:
        return self._index

    def _get_field_meta(self, lv_data, name, alt_name=None):
        raw_field = None
        if name in lv_data:
            raw_field = lv_data.get(name)
        elif alt_name and alt_name in lv_data:
            raw_field = lv_data.get(alt_name)
        return raw_field
    
    def _get_property(self, raw_field):
        if isinstance(raw_field, str) and raw_field:
            return raw_field
        return None
    
    def _validate_field(self, raw_field, field, name, alt_name=None):
        alt_msg_and = f" (and '{alt_name}')" if alt_name else ""
        alt_msg_or = f" (or '{alt_name}')" if alt_name else ""
        if raw_field is None:
            raise AnsibleFilterError(f"Missing '{name}'{alt_msg_and} field{self._msg_in}.")
        if field is None:
            raise AnsibleFilterError(f"'{name}'{alt_msg_or} must be non empty string{self._msg_in}. Got: {raw_field}")
        return True

    def _set_name_meta(self, lv_data):
        self._name = self._get_field_meta(lv_data, "name", "lv_name")

    @property
    def name(self) -> Optional[str]:
        return self._get_property(self._name)

    def validate_name(self):
        return self._validate_field(self._name, self.name, "name", "lv_name")
    
    def _set_group_meta(self, lv_data):
        self._vg = self._get_field_meta(lv_data, "vg", "vg_name")

    @property
    def vg(self) -> Optional[str]:
        return self._get_property(self._vg)

    def validate_group(self):
        return self._validate_field(self._vg, self.vg, "vg", "vg_name")

    def _set_size_meta(self, lv_data):
        self._size = self._get_field_meta(lv_data, "size", "lv_size")

    @property
    def size(self) -> Optional[str]:
        return self._get_property(self._size)

    def validate_size(self):
        return self._validate_field(self._size, self.size, "size", "lv_size")

    @property
    def lv_size(self) -> float:
        return to_mib(self.size) if self.size else 0

    def _set_filesystem_meta(self, lv_data):
        self._fs = self._get_field_meta(lv_data, "filesystem")

    @property
    def fs(self) -> Optional[str]:
        return self._get_property(self._fs)

    def validate_filesystem(self):
        fs = self.fs
        if fs and self._validate_field(self._fs, fs, "filesystem") and fs not in self.SUPPORTED_FS:
            raise AnsibleFilterError(
                f"Unsupported filesystem '{fs}' in volume '{self.name}'. Supported: {', '.join(sorted(self.SUPPORTED_FS))}."
            )
        return True

    @property
    def is_exists(self) -> bool:
        return self._is_exists
    
    def has_filesystem(self) -> bool:
        return self.is_device_attached() and self.is_exists and self._device.has_filesystem()

    def has_same_filesystem(self):
        if self.has_filesystem():
            fs = self.fs
            if fs:
                return fs == self._device.fs_type
        return False

    def _set_mountpoint_meta(self, lv_data):
        self._mount = self._get_field_meta(lv_data, "mountpoint")

    def validate_mountpoint(self):
        mount = self.mount
        if mount and self._validate_field(self._mount, mount, "mountpoint") and not os.path.isabs(mount):
            raise AnsibleFilterError(f"Volume '{self.name}': 'mountpoint' must be an absolute path.")
        return True

    def from_metadata(self, lv_data: dict[str, str]) -> None:
        if not isinstance(lv_data, dict):
            raise AnsibleFilterError(f"Volume entry must be a dictionary{self._msg_for}. Found: {lv_data}")

        self._set_name_meta(lv_data)
        self._set_group_meta(lv_data)
        self._set_size_meta(lv_data)
        self._set_filesystem_meta(lv_data)
        self._set_mountpoint_meta(lv_data)

        self.validate_name()
        self.validate_group()
        self.validate_size()

        self.raw_data = lv_data

    def validate(self):
        self.validate_name()
        self.validate_group()
        self.validate_size()
        self.validate_filesystem()
        self.validate_mountpoint()

        return True

    @property
    def mount(self) -> Optional[str]:
        return self._get_property(self._mount)

    @property
    def path(self) -> str:
        return f"/dev/{self.vg}/{self.name}"
    
    @property
    def dm_path(self) -> str:
        return f"/dev/mapper/{self.vg}-{self.name}"
    
    @property
    def paths(self) -> set[str]:
        return {self.path, self.dm_path}

    @classmethod
    def from_lvm_info(cls, name: str, lvm_info: dict[str, Any]) -> Optional["LogicalVolume"]:
        for idx, lv_data in enumerate(lvm_info.get("lv", [])):
            if lv_data.get("lv_name") == name:
                lv = cls(lv_data, idx)
                lv._lvm_info = lvm_info
                return lv
        return None

    @classmethod
    def from_volume(cls, volume: "LogicalVolume", include_state: bool = False) -> "LogicalVolume":
        lv = cls(volume.raw_data, volume.index)
        lv._lvm_info = volume._lvm_info

        if include_state and volume.has_state():
            lv.set_state(volume.state)

        if volume.is_device_attached():
            lv.attach_device(volume._device)

        return lv
    
    def set_state(self, volume: Optional["LogicalVolume"] = None):
        if volume is None:
            return
        if self.name == volume.name and self.vg == volume.vg:
            self.state = LogicalVolume.from_volume(volume)

    def is_device_attached(self) -> bool:
        return self._device is not None

    def has_state(self) -> bool:
        return self.state is not None

    def attach_device(self, device: Device, pass_through=False):
        if pass_through:
            if device.path in self.paths:
                self._device = device
                self._is_exists = device.is_exists
        else:
            dev = Device.from_dev_info(self.path, device.raw_info)
            self.attach_device(dev, pass_through=True)

    def plan_template(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "action": "",
        }

    def plan(self):
        plan = self.plan_template()
        if self.is_exists:
            plan["action"] = "skip"
            if self.fs:
                if self.has_filesystem():
                    if not self.has_same_filesystem():
                        raise AnsibleFilterError(f"Filesystem mismatch: actual={self._device.fs_type}, expected={self.fs}")
                else:
                    plan["action"] = "format"
        else:
            plan["action"] = "create" 
        return plan

class VolumeGroup:
    def __init__(self, vg_name: str, volumes = []):
        """
        Initialize a VolumeGroup object with a given name.

        Args:
            vg_name (str): Name of the volume group.

        Raises:
            AnsibleFilterError: If vg_name is not a string or is empty.
        """
        if not isinstance(vg_name, str) or not vg_name.strip():
            raise AnsibleFilterError(f"Expected 'vg_name' to be a non-empty string, got: {vg_name!r}")

        self._name: str = vg_name
        self._is_exists: bool = False

        self._pvs: list[PhysicalVolume] = [] # Internal: ordered PVs attached to this VG
        self._volumes: list[LogicalVolume] = []

        self._tracked_names = set()
        self._duplicate: Optional[str] = None

        for idx, lv_data in enumerate(volumes):
            lv = LogicalVolume(lv_data, idx)
            self.add_volume(lv)

        self.raw_info: dict[str, str] = {}
        self._lvm_info: Optional[dict[str, Any]] = None

        self._vg_free: Optional[str] = None

        # Actual volume group state
        self.state: Optional["VolumeGroup"] = None

    def add_volume(self, volume: LogicalVolume):
        volume.validate_filesystem()
        volume.validate_mountpoint()

        self._volumes.append(volume)

        if volume.name in self._tracked_names:
            self._duplicate = volume.name
        else:
            self._tracked_names.add(volume.name)

    def from_metadata(self, lvm_info: dict[str, Any]):
        """
        Populate VG metadata from lvm_info if this VG is present.

        Args:
            lvm_info: Dictionary containing "vg" key with VG details.
        """
        if not isinstance(lvm_info, dict):
            raise AnsibleFilterError(
                f"Expected LVM information 'lvm_info' to be a dictionary for {self._name!r}, "
                f"got {type(lvm_info).__name__}"
            )

        # Find VG entry
        for vg in lvm_info.get("vg", []):
            if vg.get("vg_name") == self._name:
                self._is_exists = True
                self._vg_free = vg["vg_free"]
                self.raw_info = vg
                break

        # Collect PVs belonging to this VG
        self._pvs = []
        for pv in lvm_info.get("pv", []):
            if pv.get("vg_name") == self._name and "pv_name" in pv:
                self._pvs.append(PhysicalVolume.from_lvm_info(pv["pv_name"], lvm_info))

        self._volumes = []
        for lv in lvm_info.get("lv", []):
            if lv.get("vg_name") == self._name and "lv_name" in lv:
                self._volumes.append(LogicalVolume.from_lvm_info(lv["lv_name"], lvm_info))

        self._lvm_info = lvm_info

    @property
    def name(self) -> str:
        return self._name

    @property
    def duplicate(self) -> Optional[str]:
        return self._duplicate

    @property
    def pvs(self) -> dict[str, PhysicalVolume]:
        """
        Return a dictionary mapping PV paths to PhysicalVolume objects.

        Returns:
            dict[str, PhysicalVolume]: path → PV object
        """
        return {pv.path: pv for pv in self._pvs}

    @property
    def lvs(self) -> dict[str, LogicalVolume]:
        return {lv.name: lv for lv in self._volumes}

    @property
    def vg_free(self) -> float:
        if self.has_state():
            return self.state.vg_free
        return to_mib(self._vg_free) if self._vg_free else 0

    def set_state(self, lvm_info: dict[str, Any]):
        group = VolumeGroup.from_lvm_info(self.name, lvm_info)
        self.state = group
        for lv in self._volumes:
            if lv.name in self.state.lvs:
                lv.set_state(self.state.lvs[lv.name])

    def has_state(self) -> bool:
        return self.state is not None

    @property
    def is_exists(self) -> bool:
        if self.has_state():
            return self.state.is_exists
        return self._is_exists

    @classmethod
    def from_lvm_info(cls, vg_name: str, lvm_info: dict[str, Any]) -> "VolumeGroup":
        vg = cls(vg_name)
        vg.from_metadata(lvm_info)
        return vg

    def validate(self):
        if not self.is_exists:
            raise AnsibleFilterError(f"Volume group '{self.name}' not found in system.")
        return True

    def plan_pvs(self, paths: list[str]):
        if not isinstance(paths, list):
            raise AnsibleFilterError("Expected 'paths' to be a list.")

        lvm_info = self.state._lvm_info if self.has_state() else self._lvm_info

        return [
            PhysicalVolume.from_lvm_info(path, lvm_info).plan(self.name)
            for path in paths
        ]

    def plan_volume(self, volume: LogicalVolume) -> Optional[dict[str, str]]:
        plan = volume.plan() if volume.is_device_attached() else volume.plan_template()

        if self.has_state():
            if volume.name not in self.state.lvs:
                if volume.lv_size > self.state.vg_free:
                    raise AnsibleFilterError(
                        f"Not enough free space ({self.state._vg_free}) in VG '{self.name}' "
                        f"to create LV '{volume.name}' with size {volume.size}"
                    )
                plan["action"] = "create"
        return plan

class VolumeInput:
    def __init__(self, volumes: list[dict]):
        if not isinstance(volumes, list):
            raise AnsibleFilterError("Expected 'volumes' to be a list.")

        self._volumes = [LogicalVolume(volume, idx) for idx, volume in enumerate(volumes)]
        self._vg_names = {vol.vg for vol in self._volumes}

        if len(self._vg_names) > 1:
            raise AnsibleFilterError(
                f"Expected 'volumes' to be a set of volumes within single group. Got: {self._vg_names}."
            )
        self.vg_name = next(iter(self._vg_names))

    def validate(self):
        vg = VolumeGroup(self.vg_name)
        for lv in self._volumes:
            vg.add_volume(lv)
            if vg.duplicate:
                raise AnsibleFilterError(f"Duplicate LV name detected: '{vg.duplicate}'")
        return True
