# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Shim wrapper for community.general parted conversion utilities.

Provides `convert_to_mib(size, unit)` to convert human-friendly sizes to MiB using
community.general's `parted` module functions.

Used in module_utils and filters for compatibility and to avoid hard dependency during runtime.
"""

DOCUMENTATION = r'''
---
module_utils: community_general_shim
author: Alexander Ursu
short_description: Convert disk size + unit to MiB using community.general.parted functions
description:
  - This module_utils shim provides access to community.general's parted size conversion logic.
    It safely attempts to import and use C(parted.convert_to_bytes) and C(format_disk_size),
    and falls back gracefully if the collection is not present.
  - Useful in filters and custom logic where users may provide C(size: 100, unit: GB) format.
requirements:
  - community.general
'''

EXAMPLES = r'''
# Convert "100" GB to MiB
>>> convert_to_mib("100", "GB")
97656.25

# Normalize known unit
>>> _normalize_unit("gb")
"GB"

# Safe fallback if community.general not available
>>> convert_to_mib("100", "FOOBYTES")
None
'''

RETURN = r'''
_normalize_unit:
  description: >
    Normalize a unit string (e.g. 'gb', 'MiB') to match parted's supported units.
    Returns the canonical string from parted's unit list, or None if unavailable or invalid.
  type: str
  returned: when called

convert_to_mib:
  description: >
    Convert a given size + unit (e.g. "100", "GB") into a float representing MiB.
    Returns None if the unit is invalid or community.general.parted is not available.
  type: float
  returned: when called
'''

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
