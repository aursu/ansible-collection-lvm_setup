# -*- coding: utf-8 -*-
# Copyright (c) 2025, Alexander Ursu <alexander.ursu@gmail.com>
# SPDX-License-Identifier: MIT

"""
Helper utility for converting size strings to MiB using binary units.

Provides to_mib() function that supports 'm', 'g', 't' suffixes for MiB, GiB, and TiB respectively.
"""

from ansible.errors import AnsibleFilterError

DOCUMENTATION = r'''
---
module_utils: size_utils
author: Alexander Ursu
short_description: Convert disk size strings into MiB using binary units (m, g, t)
description:
  - This utility provides a simple converter for sizes like '400g', '512m', '1t'
    into MiB values. It supports only binary units, not decimal (e.g., GB vs GiB).
  - Used internally by filters and validation logic for partitioning and LVM.
requirements: []
'''

EXAMPLES = r'''
# Convert '400g' to MiB
>>> to_mib("400g")
409600.0

# Convert '1t' to MiB
>>> to_mib("1t")
1048576.0

# Convert int directly
>>> to_mib(512)
512.0

# Raise error on invalid string
>>> to_mib("500x")
AnsibleFilterError
'''

RETURN = r'''
to_mib:
  description: >
    Converts a string or number representing a size into MiB. Accepts units:
    'm' (MiB), 'g' (GiB), 't' (TiB). Only binary suffixes are supported.
  type: float
  returned: when called
  raises:
    - AnsibleFilterError on invalid format or unsupported unit
'''

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
