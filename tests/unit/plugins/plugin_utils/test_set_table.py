import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.disks_helpers import Disk

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
    
    def setUpTable(self, default_label="gpt"):
        self.setUpLinked()
        self.req.set_table(default_label)
    
    def test_state_table(self):
        self.assertIsNone(self.state._table)
        self.assertIsNone(self.state.table)

    def test_req_table(self):
        self.assertIsNone(self.req._table)
        self.assertEqual(self.req.table, "gpt")

    def test_linked_req_table(self):
        self.setUpLinked()
        self.assertIsNone(self.req._table)
        self.assertEqual(self.req.table, "gpt")

    def test_set_table(self):
        self.setUpTable()
        self.assertIsNone(self.state._table)
        self.assertIsNone(self.state.table)
        self.assertEqual(self.req._table, "gpt")
        self.assertEqual(self.req.table, "gpt")

    def test_set_table_value(self):
        self.setUpTable("msdos")
        self.assertIsNone(self.state._table)
        self.assertIsNone(self.state.table)
        self.assertEqual(self.req._table, "msdos")
        self.assertEqual(self.req.table, "msdos")

if __name__ == '__main__':
    unittest.main()
