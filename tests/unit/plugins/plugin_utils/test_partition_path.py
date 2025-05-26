import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Partition


class TestPartitionPath(unittest.TestCase):
    """Unit tests for Partition.path() method with different disk types and edge cases."""

    def setUp(self):
        self.parts = [
            {"part": Partition({"num": 1}, idx=0, disk="/dev/sda"), "path": "/dev/sda1"},
            {"part": Partition({"num": 5}, idx=1, disk="/dev/sdb"), "path": "/dev/sdb5"},
            {"part": Partition({"num": 6}), "path": None},
            {"part": Partition({"num": 1}, idx=2, disk="/dev/nvme0n1"), "path": "/dev/nvme0n1p1"},
            {"part": Partition({"num": 10}, idx=3, disk="/dev/nvme1n1"), "path": "/dev/nvme1n1p10"},
            {"part": Partition({"num": 2}), "path": "/dev/nvme1n1p2", "param": ["/dev/nvme1n1"]},
        ]

    def test_path(self):
        for test in self.parts:
            with self.subTest(disk=(test["part"]._disk or "not specified"), num=test["part"].num):
                param = test.get("param", [])
                if test["path"] is None:
                    self.assertIsNone(test["part"].path(*param))
                else:
                    self.assertEqual(test["part"].path(*param), test["path"])

if __name__ == '__main__':
    unittest.main()
