from abc import ABC
from typing import Optional
from ansible.errors import AnsibleFilterError
from ansible_collections.aursu.lvm_setup.plugins.module_utils.size_utils import to_mib
from ansible_collections.aursu.lvm_setup.plugins.module_utils.community_general_shim import convert_to_mib

class SizeInterface(ABC):
    def __init__(self):
        self._unit = None
        # context message used in validation error reporting
        self._unit_msg = ""
        # raw 'size' field from input (may be missing or malformed)
        self._size = None
        self.size = None

    # 1. The argument 'part_start' doesn't respect required format.The size unit is case sensitive.
    # 2. Error: You requested a partition from 60208MiB to 915715MiB (sectors 123305984..1875385007).
    #    The closest location we can manage is 60208MiB to 915715MiB (sectors 123305992..1875384974).
    # 3. Warning: The resulting partition is not properly aligned for best performance: 123305992s % 2048s != 0s
    def _to_parted_size(self, value, align=0, unit="MiB"):
        if isinstance(value, str):
            value = value.strip()
            if value.endswith("%"):
                return value
            value = float(value)
        return f"{int(value + align)}{unit}"

    def _convert_to_mib(self, size, unit):
        if size:
            if unit is None or unit == "mib":
                return to_mib(size)
            else:
                return convert_to_mib(size, unit)
        return None
        
    def _convert_size(self, data, name):
        """
        Extract a raw size field and convert it to MiB.

        Args:
            data (dict): Input data dictionary.
            name (str): Field name to extract from data (e.g., "size", "size_limit").

        Returns:
            tuple: (raw_value, size_in_mib)
        """
        size_raw = data.get(name)
        size_in_mib = self._convert_to_mib(size_raw, self._unit)

        return size_raw, size_in_mib
    
    def _assert_size(self, name, raw_value, converted, required=True, context=""):
        """
        Assert that a size field is present (if required), convertible, and positive.

        Args:
            name (str): Name of the field (used in error messages).
            raw_value: Raw size value as received from input.
            converted: Size value converted to MiB.
            required (bool): Whether the field must be present.
            context (str): Optional context for error messages.
        """
        if raw_value is None:
            if required:
                raise AnsibleFilterError(f"Missing '{name}' field{context}.")
            return  # Optional size, and not provided — acceptable

        if converted is None:
            raise AnsibleFilterError(
                f"Unable to convert '{name}' field to MiB{context}. Got: {raw_value}{self._unit_msg}"
            )

        if converted <= 0:
            raise AnsibleFilterError(
                f"Expected positive '{name}' field in 'MiB'{context}. Got: {raw_value}{self._unit_msg}"
            )

    def _set_unit_meta(self, data):
        self._unit = data.get("unit")
        if self._unit:
            self._unit_msg = f" in '{self._unit}'"

    def _set_size_meta(self, data):
        self._size, self.size = self._convert_size(data, "size")

    def validate_size(self, required=True, context=""):
        self._assert_size("size", self._size, self.size, required, context)

class Partition(SizeInterface):
    def __init__(self, part_data, idx=None, disk=None):
        if not isinstance(part_data, dict):
            raise AnsibleFilterError(f"Partition entry must be a dictionary. Found: {part_data}")

        super().__init__()

        self._disk = None

        # raw 'num' field from input (may be str or int, possibly invalid)
        self._num = None
        # validated and converted partition number (int or None)
        self.num = None

        # context messages used in validation error reporting
        self._disk_msg: str = ""
        self._msg_in: str = ""
        self._msg_for: str = ""
        self._num_msg: str = ""

        # raw values from parted input
        self._begin: Optional[float] = None
        self._end: Optional[float] = None

        # converted values in MiB
        self.begin: Optional[float] = None
        self.end: Optional[float] = None

        self._set_num_meta(part_data)
        self._set_unit_meta(part_data)
        self._set_size_meta(part_data)
        self._set_begin_meta(part_data)
        self._set_end_meta(part_data)

        self.set_index(idx)
        self.set_disk(disk)

        # previous and next partitions
        self.prev: Optional["Partition"] = None
        self.next_part: Optional["Partition"] = None

        self.state: Optional["Partition"] = None

        # num is mandatory set to int
        self.validate_num()

        # TODO: flags, fstype, name

    def set_state(self, part: Optional["Partition"] = None):
        if part is None:
            return
        part.validate_begin()
        part.validate_end()
        part.validate_size()
        self.state = part

    def _set_num_meta(self, part_data):
        self._num = part_data.get("num")
        try:
            self.num = int(self._num)
        except (ValueError, TypeError) as e:
            self.num = None
            self._num_msg = str(e)

    def _set_begin_meta(self, part_data):
        self._begin, self.begin = self._convert_size(part_data, "begin")

    def _set_end_meta(self, part_data):
        self._end, self.end = self._convert_size(part_data, "end")
    
    def set_index(self, idx=None):
        if not isinstance(idx, int):
            return
        self._msg_in = f" in partition #{idx+1}"
        self._msg_for = f" for partition #{idx+1}"

    def set_disk(self, disk=None):
        if disk is None or not disk.startswith('/dev/'):
            return
        self._disk = disk
        self._disk_msg = f" for disk '{disk}'"

    def is_last(self) -> bool:
        """
        Returns True if this partition is the last one in the list (i.e., has no next).
        """
        return self.next_part is None

    def validate_num(self):
        if self._num is None:
            raise AnsibleFilterError(f"Missing 'num' field{self._msg_in}{self._disk_msg}.")
        if self.num is None:
            raise AnsibleFilterError(f"'num' must be an integer{self._msg_in}{self._disk_msg}. Got: {self._num} ({self._num_msg})")
        return True
    
    def validate_begin(self):
        self._assert_size(
            "begin",
            self._begin,
            self.begin,
            required=False,
            context=f"{self._msg_for}{self._disk_msg}"
        )

    def validate_end(self):
        self._assert_size(
            "end",
            self._end,
            self.end,
            required=False,
            context=f"{self._msg_for}{self._disk_msg}"
        )

    def validate(self):
        self.validate_num()
        self.validate_size(required=(not self.is_last()), context=f"{self._msg_for}{self._disk_msg}")
    
    def path(self, disk: Optional[str] = None):
        """
        Return full partition device path for a given disk and partition number.
        Examples:
        - /dev/sda, 1        → /dev/sda1
        - /dev/nvme0n1, 1    → /dev/nvme0n1p1
        """
        disk = self._disk if disk is None or not disk.startswith('/dev/') else disk
        if disk is None or self.num is None:
            return None
        return f"{disk}p{self.num}" if disk.startswith('/dev/nvme') else f"{disk}{self.num}"

    def plan_template(self) -> dict:
        """
        Return a default plan dictionary for this partition,
        including current state if available.
        """
        return {
            "num": self.num,
            "status": "ok",
            "warning": "",
            "error": "",
            "action": "skip",
            "disk_label": "",  # to be filled by caller
            "part_start": self.state.begin if self.state else "",
            "part_end": self.state.end if self.state else "",
        }

    def plan(self, required=False):
        """
        Generate a partition plan for an existing partition based on its real disk state.

        If the partition exists, its size is validated (if specified). If no size is provided,
        the partition must be the last one on the disk. If the partition is required but not found,
        an error is raised.

        Args:
            required (bool): Whether this partition is expected to already exist.

        Returns:
            dict or None: A dictionary describing the plan, or None if not required and not present.

        Raises:
            AnsibleFilterError: If the partition is required but not present, or if size-related
                                constraints are violated.
        """
        if not self.state:
            if required:
                raise AnsibleFilterError(
                    f"Partition {self.path()} not found — expected to exist at this point (required is set)."
                )
            return None

        self.validate()

        warning = ""
        if self.size is None:
            if not self.state.is_last():
                raise AnsibleFilterError(
                    f"Partition {self.num} already exists, but no 'size' is specified "
                    f"and it is not the last partition."
                )
        elif round(self.size) != round(self.state.size):
            warning = "size mismatch"

        plan = self.plan_template()
        plan["warning"] = warning
        return plan

class Disk(SizeInterface):
    def __init__(self, disk, parts, validation=True, allow_gaps=False, allow_empty=False):
        if not isinstance(parts, list):
            raise AnsibleFilterError(f"Expected a list of partitions for device '{disk}', got {type(parts).__name__}.")

        super().__init__()

        self._parts: list[Partition] = []
        self.disk: str = disk

        self._tracked_nums = set()
        self._duplicate: Optional[int] = None

        sorted_parts = sorted(parts, key=lambda p: (not isinstance(p.get("num"), int), p.get("num")))
        for idx, part_data in enumerate(sorted_parts):
            p = Partition(part_data, idx, disk)
            if self._parts:
                p.prev = self._parts[-1]
                self._parts[-1].next_part = p 
            self.add_part(p)

        # keep original input
        self.raw_parts = parts
        self.raw_disk = {}

        # Raw values from parted info (if available)
        self._table = None
        # Default partition table (used if disk is unformatted)
        self.table = "gpt"

        # Actual disk state
        self.state: Optional["Disk"] = None

        if validation:
            self.validate(allow_gaps, allow_empty)

    def from_metadata(self, disk_data):
        self._set_unit_meta(disk_data)
        self._set_size_meta(disk_data)
        self._set_table_meta(disk_data)

        self.raw_disk = disk_data

    @classmethod
    def from_parted(cls, parted_info):
        # extract disk and parts from parted_info
        disk_data = parted_info.get("disk", {})

        disk = disk_data.get("dev")
        parts = parted_info.get("partitions", [])

        disk_obj = cls(disk, parts, allow_gaps=True, allow_empty=True)
        disk_obj.from_metadata(disk_data)

        return disk_obj

    @classmethod
    def from_disk(cls, disk: "Disk"):
        # extract disk and parts from parted_info
        disk_obj = cls(disk.disk, disk.raw_parts, allow_gaps=True, allow_empty=True)

        raw_disk = disk.raw_disk if disk.raw_disk else {
            "unit": disk._unit,
            "size": disk._size,
            "table": disk._table
        }
        disk_obj.from_metadata(raw_disk)

        return disk_obj

    def set_state_disk(self, state: "Disk"):
        self.state = Disk.from_disk(state)

        for p in self._parts:
            p.set_state(self.state.parts_by_num(p.num))

    def parts_by_num(self, num=None):
        """
        Return a dictionary mapping partition numbers to Partition objects,
        or a single Partition if a number is specified.

        Only partitions with a valid (non-null) 'num' field are included.
        Useful for quick lookup by partition number.

        Args:
            num (int, optional): If specified, return only the matching Partition object.

        Returns:
            dict[int, Partition] or Partition or None: Partition dictionary or a single entry.
        """
        parts = {p.num: p for p in self._parts}
        if isinstance(num, int):
            return parts.get(num)
        return parts

    def sorted_parts(self) -> list[Partition]:
        """
        Return the list of Partition objects sorted by partition number.
        Partitions without a valid 'num' field (i.e. None) are placed at the end.

        Returns:
            list[Partition]: List of partitions sorted by number.
        """
        return sorted(self._parts, key=lambda p: p.num)

    def _set_table_meta(self, disk_data):
        table = disk_data.get("table")
        self._set_table(table)

    def _set_table(self, table):
        # Supported partition tables: aix, amiga, bsd, dvh, gpt, mac, msdos, pc98, sun, atari, loop
        if table in ["aix", "amiga", "bsd", "dvh", "gpt", "mac", "msdos", "pc98", "sun", "atari", "loop"]:
            self._table = table
            self.table = table

    def set_table(self, table="gpt"):
        if self._table:
            # Do not override the partition table if it was already set from parted info
            return
        self._set_table(table)

    def add_part(self, part: Partition):
        self._parts.append(part)

        part.validate_num()
        
        if part.num in self._tracked_nums:
            self._duplicate = part.num
        else:
            self._tracked_nums.add(part.num)

    def validate(self, allow_gaps=False, allow_empty=False):
        if not allow_empty:
            if not self._tracked_nums:
                raise AnsibleFilterError(f"Expected at least one partition to be provided for device '{self.disk}'.")

        for part in self._parts:
            part.validate()
        
        if self._duplicate:
            raise AnsibleFilterError(f"Duplicate partition number {self._duplicate} detected on disk '{self.disk}'.")

        if not allow_gaps:
            num_min = min(self._tracked_nums)
            num_max = max(self._tracked_nums)

            if len(self._tracked_nums) <= (num_max - num_min):
                raise AnsibleFilterError(
                    f"Partition numbers on disk '{self.disk}' contain gaps: {sorted(self._tracked_nums)}."
                )
        return True

    def paths(self):
        """
        Generate full partition paths for a given disk and list of partition entries.

        Each entry in `parts` must be a dictionary containing the key 'num' (partition number).
        The resulting path is generated using standard naming conventions:
        - For SATA/SCSI disks: /dev/sda + 1 → /dev/sda1
        - For NVMe disks: /dev/nvme0n1 + 1 → /dev/nvme0n1p1

        Args:
            disk (str): Base disk path (e.g. /dev/sda or /dev/nvme0n1).
            parts (list): List of partition dictionaries, each with a 'num' key.

        Returns:
            list[str]: List of full partition paths.
        """
        return [p.path() for p in self._parts if p.path()]

    def prev_next_lookup(self, state: "Disk", num: int) -> tuple[Optional[Partition], Optional[Partition]]:
        prev: Optional[Partition] = None
        next_part: Optional[Partition] = None

        for s in state.sorted_parts():
            if s.num < num:
                prev = s
            elif s.num > num:
                if next_part is None or s.num < next_part.num: 
                    next_part = s

        return prev, next_part

    def plan(self, required: bool = False) -> list[dict]:
        """
        Generate a full plan of actions required to align the requested partitions with the actual disk state.

        Args:
            required (bool): If True, raises errors for partitions that are missing in actual state.

        Returns:
            list[dict]: List of action plans per partition.
        """

        result = []

        # copy state into tmp object
        state = Disk.from_disk(self.state)
        state.validate_size()

        for p in self._parts:
            plan = p.plan(required)
            if plan:
                plan["disk_label"] = self.table
                result.append(plan)
                continue

            prev, next_part = self.prev_next_lookup(state, p.num)

            next_begin = next_part.begin if next_part else state.size
            prev_end = prev.end if prev else 0.0
            available_space = next_begin - prev_end

            plan = p.plan_template()

            if p.size is None:
                if next_part:
                    raise AnsibleFilterError(
                        f"Partition {p.num}: no 'size' specified and another partition {next_part.num} follows"
                    )

                part_end = "100%"
                part_data = {
                    "num": p.num,
                    "begin": prev_end + 1,
                    "end": next_begin,
                    "size": available_space,
                    "unit": "mib",
                }
            else:
                if available_space < p.size:
                    raise AnsibleFilterError(
                        f"Partition {p.num}: requested size {p.size:.2f} MiB exceeds available space ({available_space:.2f} MiB)"
                    )

                if next_part and (next_part.num == p.num + 1):
                    part_end = next_begin - 1 # align to 1 MiB before next partition (parted default alignment: 1 MiB / 2048 sectors)
                else:
                    part_end = prev_end + p.size

                part_data = {
                    "num": p.num,
                    "begin": prev_end + 1,
                    "end": part_end,
                    "size": p.size,
                    "unit": "mib",
                }

            plan.update({
                "action": "create",
                "disk_label": self.table,
                "part_start": self._to_parted_size(prev_end, 1),
                "part_end": self._to_parted_size(part_end),
            })                
            result.append(plan)

            # add newly created partition to tracking structures
            new_part = Partition(part_data, disk=self.disk)
            new_part.prev = prev
            new_part.next_part = next_part if next_part and next_part.num == p.num + 1 else None
            state.add_part(new_part)
        return result

class PartitionInput:
    def __init__(self, partitions, allow_gaps=False):
        if not isinstance(partitions, dict):
            raise AnsibleFilterError("Expected 'partitions' to be a dictionary.")
        self._disks = [Disk(disk, parts, allow_gaps=allow_gaps) for disk, parts in partitions.items()]
    
    def paths(self):
        result = []
        for d in self._disks:
            result.extend(d.paths())
        return result
