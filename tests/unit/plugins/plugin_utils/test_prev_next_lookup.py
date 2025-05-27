import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

class TestDiskSetSize(unittest.TestCase):
    def setUp(self):
        parted_info = {
            "disk": {"size": 4096.0, "dev": "/dev/sda"},
            "partitions": []
        }
        parts = [{"num": 1, "size": 1024.0}]
        self.state = Disk.from_parted(parted_info)
        self.dev = Disk(self.state.disk, parts)
    
    def test_prev_next_lookup(self):
        self.assertEqual(self.dev.prev_next_lookup(self.state, 1), [])

if __name__ == '__main__':
    unittest.main()
