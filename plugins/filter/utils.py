from ansible.errors import AnsibleFilterError

def to_mib(value):
    """
    Converts a value like '400g', '512m', or '1t' into MiB (float).
    Supports binary units only: m (MiB), g (GiB), t (TiB)

    Examples:
      '400g' → 409600.0
      '1t'   → 1048576.0
      '512m' → 512.0
    """
    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        raise AnsibleFilterError(f"Invalid type for size: {type(value)}")

    value = value.strip().lower()

    try:
        if value.endswith("g"):
            return float(value[:-1]) * 1024
        elif value.endswith("m"):
            return float(value[:-1])
        elif value.endswith("t"):
            return float(value[:-1]) * 1024 * 1024
        else:
            raise ValueError(f"Unsupported unit in {value}")
    except ValueError:
        raise AnsibleFilterError(
            f"Unsupported or invalid size format: '{value}'. Only 'm', 'g', and 't' binary units are supported."
        )

# 1. The argument 'part_start' doesn't respect required format.The size unit is case sensitive.
# 2. Error: You requested a partition from 60208MiB to 915715MiB (sectors 123305984..1875385007).
#    The closest location we can manage is 60208MiB to 915715MiB (sectors 123305992..1875384974).
# 3. Warning: The resulting partition is not properly aligned for best performance: 123305992s % 2048s != 0s
def mib(value, align=0, unit="MiB"):
    if isinstance(value, str):
        value = value.strip()
        if value.endswith("%"):
            return value
        value = float(value)
    return f"{int(value + align)}{unit}"
