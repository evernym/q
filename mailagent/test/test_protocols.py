import unittest
import helpers
import protocol_loader

class ProtocolTest(unittest.TestCase):
    def test_all_load(self):
        bad = protocol_loader.load_all()
        self.assertFalse(bad)

if __name__ == '__main__':
    unittest.main()
