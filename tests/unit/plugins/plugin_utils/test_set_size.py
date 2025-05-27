import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import Disk

class TestDiskSetSize(unittest.TestCase):
    def setUp(self):
        parted_info = {
            "disk": {"size": 4096.0, "dev": "/dev/sda"},
            "partitions": []
        }
        self.dev = Disk.from_parted(parted_info)
    
    def test_size(self):
        self.assertEqual(self.dev._size, 4096.0)
        self.assertEqual(self.dev.size, 4096.0)

if __name__ == '__main__':
    unittest.main()
