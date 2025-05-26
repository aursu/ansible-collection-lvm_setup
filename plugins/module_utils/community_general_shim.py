def _normalize_unit(unit):
    """
    Attempts to normalize a parted unit using community.general's parted_units list.
    Returns the canonical unit string if found, otherwise None.
    Falls back silently if community.general is not installed.
    """
    try:
        from ansible_collections.community.general.plugins.modules.parted import parted_units
    except Exception:
        return None

    if not isinstance(unit, str):
        return None

    unit_lower = unit.lower()
    return next((u for u in parted_units if u.lower() == unit_lower), None)

def convert_to_mib(size, unit):
    """
    Convert a disk size with unit (e.g., '100', 'GB') to a float value in MiB.
    Returns float (e.g., 512.0) or None if conversion is not available or invalid.
    """
    try:
        from ansible_collections.community.general.plugins.modules.parted import (
            format_disk_size,
            convert_to_bytes,
        )
    except Exception:
        return None

    normalized_unit = _normalize_unit(unit)
    if not normalized_unit:
        return None

    size_bytes = convert_to_bytes(size, normalized_unit)
    value, _ = format_disk_size(size_bytes, "MiB")

    return value
