import pytest
from ansible.errors import AnsibleFilterError

from ansible_collections.aursu.lvm_setup.plugins.filter.mount_plan import mount_plan

LV = {
    "name": "data1",
    "vg": "data",
    "size": "200g",
    "filesystem": "xfs",
    "mountpoint": "/mnt/disks/data1",
}

# The live mount table, as aursu.general.dev_info returns it. Note the source is
# the device-mapper name and the options are the kernel's effective ones - this
# is why neither `nofail` nor a stale fstab source can be seen from here.
MOUNTED = {
    "is_exists": True,
    "mount": [
        {
            "target": "/mnt/disks/data1",
            "source": "/dev/mapper/data-data1",
            "fstype": "xfs",
            "options": "rw,relatime,attr2,inode64,logbufs=8,logbsize=32k,noquota",
        }
    ],
}

NOT_MOUNTED = {"is_exists": True, "mount": []}
ABSENT = {"is_exists": False}


def fstab(source="/dev/data/data1", options="defaults,nofail",
          target="/mnt/disks/data1", fstype="xfs"):
    return {"target": target, "source": source, "fstype": fstype, "options": options}


class TestNothingToDo:
    def test_mounted_and_recorded_correctly_is_skipped(self):
        plan = mount_plan(LV, MOUNTED, fstab())
        assert plan["action"] == "skip"
        assert plan["mount_state"] is None
        assert plan["reasons"] == []

    def test_option_order_does_not_matter(self):
        plan = mount_plan(LV, MOUNTED, fstab(options="nofail,defaults"))
        assert plan["action"] == "skip"

    def test_device_mapper_source_is_accepted(self):
        plan = mount_plan(LV, MOUNTED, fstab(source="/dev/mapper/data-data1"))
        assert plan["action"] == "skip"

    def test_uuid_source_is_left_alone(self):
        # The collection did not write a UUID= source and cannot resolve one
        # here, so it does not churn the entry.
        plan = mount_plan(LV, MOUNTED, fstab(source="UUID=66310f17-f78d-421e-ae23-154fd646d32f"))
        assert plan["action"] == "skip"


class TestNotMounted:
    def test_absent_volume_is_mounted(self):
        plan = mount_plan(LV, NOT_MOUNTED, None)
        assert plan["action"] == "mount"
        assert plan["mount_state"] == "mounted"
        assert plan["opts"] == "defaults,nofail"

    def test_nonexistent_device_is_mounted(self):
        plan = mount_plan(LV, ABSENT, None)
        assert plan["action"] == "mount"

    def test_mounted_somewhere_else_counts_as_not_mounted(self):
        elsewhere = {"is_exists": True, "mount": [{"target": "/wrong"}]}
        plan = mount_plan(LV, elsewhere, None)
        assert plan["action"] == "mount"


class TestAlreadyMountedButWrong:
    """The cases validate_mount cannot see.

    validate_mount compares only the mount target, so for every test in this
    class it returns True and the caller skips the task. Each one leaves a host
    that looks healthy and fails to boot.
    """

    def test_missing_nofail_is_corrected_without_remounting(self):
        plan = mount_plan(LV, MOUNTED, fstab(options="defaults"))
        assert plan["action"] == "update"
        # `present`, not `mounted`: rewrite the file, leave the running mount be.
        assert plan["mount_state"] == "present"
        assert plan["opts"] == "defaults,nofail"
        assert any("missing nofail" in r for r in plan["reasons"])

    def test_stale_fstab_source_is_corrected(self):
        # Measured on k8s2..k8s10 2026-09-14: the volume group was renamed from
        # `data-ssd` to `data`, and fstab was never updated. The volumes stayed
        # mounted for 16 months, so nothing surfaced the fault.
        plan = mount_plan(LV, MOUNTED, fstab(source="/dev/data-ssd/data1", options="defaults,nofail"))
        assert plan["action"] == "update"
        assert plan["mount_state"] == "present"
        assert any("would not resolve at boot" in r for r in plan["reasons"])

    def test_both_faults_are_reported_together(self):
        plan = mount_plan(LV, MOUNTED, fstab(source="/dev/data-ssd/data1", options="defaults"))
        assert plan["action"] == "update"
        assert len(plan["reasons"]) == 2

    def test_mounted_but_absent_from_fstab_is_recorded(self):
        plan = mount_plan(LV, MOUNTED, None)
        assert plan["action"] == "update"
        assert plan["fstab_present"] is False
        assert any("no /etc/fstab entry" in r for r in plan["reasons"])

    def test_the_fix_converges(self):
        # Applying the plan must make the next run a no-op, or the play is never
        # idempotent. This is the check that catches comparing fstab options
        # against live kernel options.
        first = mount_plan(LV, MOUNTED, fstab(source="/dev/data-ssd/data1", options="defaults"))
        assert first["action"] == "update"

        after = mount_plan(LV, MOUNTED, fstab(source=first["path"], options=first["opts"]))
        assert after["action"] == "skip"


class TestOptsDeclaration:
    def test_explicit_opts_win_over_the_default(self):
        lv = dict(LV, opts="defaults,nofail,noatime")
        plan = mount_plan(lv, MOUNTED, fstab(options="defaults,nofail"))
        assert plan["action"] == "update"
        assert plan["opts"] == "defaults,nofail,noatime"

    def test_options_is_accepted_as_an_alias(self):
        lv = dict(LV, options="defaults,nofail")
        assert mount_plan(lv, MOUNTED, fstab())["action"] == "skip"

    def test_caller_may_override_the_default_opts(self):
        plan = mount_plan(LV, MOUNTED, fstab(options="defaults"), default_opts="defaults")
        assert plan["action"] == "skip"

    def test_netdev_is_expressible_even_though_it_is_not_inferred(self):
        lv = dict(LV, opts="defaults,nofail,_netdev")
        plan = mount_plan(lv, NOT_MOUNTED, None)
        assert "_netdev" in plan["opts"]

    @pytest.mark.parametrize("bad", ["", ",", " , "])
    def test_empty_opts_is_rejected(self, bad):
        # An empty options field is an fstab syntax error, so it must not be
        # quietly treated as "defaults".
        with pytest.raises(AnsibleFilterError):
            mount_plan(dict(LV, opts=bad), MOUNTED, fstab())

    def test_whitespace_in_an_option_is_rejected(self):
        with pytest.raises(AnsibleFilterError):
            mount_plan(dict(LV, opts="defaults, nofail"), MOUNTED, fstab())


class TestInputValidation:
    def test_dev_info_must_be_a_dict(self):
        with pytest.raises(AnsibleFilterError):
            mount_plan(LV, "not-a-dict", fstab())

    def test_fstab_entry_must_be_a_dict_or_none(self):
        with pytest.raises(AnsibleFilterError):
            mount_plan(LV, MOUNTED, "not-a-dict")

    def test_relative_mountpoint_is_rejected(self):
        with pytest.raises(AnsibleFilterError):
            mount_plan(dict(LV, mountpoint="mnt/disks/data1"), MOUNTED, fstab())

    def test_unsupported_filesystem_is_rejected(self):
        with pytest.raises(AnsibleFilterError):
            mount_plan(dict(LV, filesystem="ntfs"), MOUNTED, fstab())

    def test_volume_without_a_mountpoint_is_never_mounted(self):
        lv = {"name": "vault", "vg": "data", "size": "10g", "filesystem": "xfs"}
        plan = mount_plan(lv, NOT_MOUNTED, None)
        assert plan["action"] == "skip"
        assert plan["mount_state"] is None
        assert plan["mounted"] is False
        assert plan["mountpoint"] is None
