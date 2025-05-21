from ansible.errors import AnsibleFilterError

def validate_pvs(lvm_info, paths, vg_name):
    """
    Validate PV status of each partition:
    - If PV exists and is in correct VG → skip
    - If PV exists but in different VG → raise error
    - If PV exists and not in any VG → add
    - If not PV → create

    Returns list of:
    - path: full partition path
    - action: 'create', 'add', or 'skip'
    - warning: optional warning (e.g. already PV but not in VG)
    - error: always empty (since real errors raise exception)
    """
    results = []

    if not isinstance(paths, list):
        raise AnsibleFilterError("Expected 'paths' to be a list.")

    if not isinstance(lvm_info, dict):
        raise AnsibleFilterError("Expected 'lvm_info' to be a dictionary.")
    
    if not vg_name:
        raise AnsibleFilterError("Volume group name ('vg_name') must be provided.")

    pvs = lvm_info.get("pvs", [])
    pv_map = {pv.get("pv_name"): pv for pv in pvs if "pv_name" in pv}

    for path in paths:
        result = {
            "path": path,
            "action": "",
            "warning": "",
            "error": ""
        }

        pv = pv_map.get(path)
        if pv:
            pv_vg = pv.get("vg_name")
            if pv_vg == vg_name:
                result["action"] = "skip"
            elif not pv_vg:
                result["action"] = "add"
            else:
                raise AnsibleFilterError(
                    f"Persistent volume {path} is already part of another volume group: {pv_vg}"
                )
        else:
            result["action"] = "create"

        results.append(result)

    return results

class FilterModule(object):
    def filters(self):
        return {
            'validate_pvs': validate_pvs
        }
