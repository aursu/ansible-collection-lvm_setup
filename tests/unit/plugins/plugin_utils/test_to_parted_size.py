import unittest
from ansible_collections.aursu.lvm_setup.plugins.plugin_utils.filter_helpers import SizeInterface

class Device(SizeInterface):
    def __init__(self):
        pass

class TestSizeInterface(unittest.TestCase):
    def setUp(self):
        self.dev = Device()
    
    def test_numeric_input(self):
        self.assertEqual(self.dev._to_parted_size(1024), "1024MiB")
        self.assertEqual(self.dev._to_parted_size(1000.0), "1000MiB")
        self.assertEqual(self.dev._to_parted_size(1000.0, align=24), "1024MiB")
        self.assertEqual(self.dev._to_parted_size(99.7), "99MiB")  # truncated by int()

    def test_percentage_string(self):
        self.assertEqual(self.dev._to_parted_size("100%"), "100%")
        self.assertEqual(self.dev._to_parted_size("  75% "), "75%")
    
    def test_string_number(self):
        self.assertEqual(self.dev._to_parted_size("1000"), "1000MiB")
        self.assertEqual(self.dev._to_parted_size("1000", align=48), "1048MiB")
        self.assertEqual(self.dev._to_parted_size(" 300 "), "300MiB")

if __name__ == '__main__':
    unittest.main()
