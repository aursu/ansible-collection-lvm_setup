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
