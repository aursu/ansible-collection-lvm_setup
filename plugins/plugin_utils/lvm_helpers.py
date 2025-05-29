import os.path
from abc import ABC
from typing import Any, Optional
from ansible.errors import AnsibleFilterError

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
        self._fs_type= dev_info.get('blkid', {}).get('type')

    def from_metadata(self, dev_info: dict[str, Any]) -> None:
        self._set_existence_flag(dev_info)
        self._set_stat_error(dev_info)
        self._set_filetype(dev_info)
        self._set_filesystem_type(dev_info)

        self.raw_info = dev_info

    def is_exists(self) -> bool:
        return self._is_exists
    
    def is_stat_error(self) -> bool:
        return bool(self._stat_error)
    
    def is_block_device(self) -> bool:
        return self._filetype == "b"
    
    def has_filesystem(self) -> bool:
        return bool(self._fs_type)

    def is_lvm2_member(self) -> bool:
        return self._fs_type == "LVM2_member"
    
    def validate_lvm(self) -> bool:
        """
        Validate the device for use as an LVM physical volume.

        Raises:
            AnsibleFilterError: If the device is invalid for LVM use.
        """
        if not self.is_exists():
            raise AnsibleFilterError(f"Partition {self._path} does not exist.")
        
        if self.is_stat_error():
            raise AnsibleFilterError(f"Partition file {self._path} stat error: {self._stat_error}")
        
        if not self.is_block_device():
            raise AnsibleFilterError(f"Partition {self._path} is not a block device (actual filetype is {self._filetype}).")
        
        if self.has_filesystem() and not self.is_lvm2_member():
            raise AnsibleFilterError(f"Partition {self._path} contains unexpected filesystem: {self._fs_type}")

        return True

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

    @classmethod
    def from_lvm_info(cls, path: str, lvm_info: dict[str, Any]) -> "PhysicalVolume":
        if not isinstance(lvm_info, dict):
            raise AnsibleFilterError(f"Expected LVM information 'lvm_info' to be a dictionary for {path}, got {type(lvm_info).__name__}")

        obj = cls(path)
        obj.from_metadata(lvm_info)

        return obj

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
