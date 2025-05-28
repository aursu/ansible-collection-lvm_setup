import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

class TestDiskSetTable(unittest.TestCase):
    def setUp(self):
        parted_info = {
            "disk": {"size": 4096.0, "dev": "/dev/sda"},
            "partitions": []
        }
        parts = [{"num": 1, "size": 1024.0}]

        self.state = Disk.from_parted(parted_info)
        self.req = Disk(self.state.disk, parts)
    
    def setUpLinked(self):
        self.req.set_state_disk(self.state)
    
    def test_state_table(self):
        self.assertIsNone(self.state._table)
        self.assertEqual(self.state.table, "gpt")

    def test_req_table(self):
        self.assertIsNone(self.req._table)
        self.assertEqual(self.req.table, "gpt")

    def test_linked_req_table(self):
        self.setUpLinked()
        self.assertIsNone(self.req._table)
        self.assertEqual(self.req.table, "gpt")

if __name__ == '__main__':
    unittest.main()
