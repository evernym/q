import unittest
import helpers
import protocols

class ProtocolsTest(unittest.TestCase):
    def test_every_protocol_loads(self):
        self.assertTrue(protocols.BY_TYPE)
        self.assertTrue(protocols.BY_NAME)
        self.assertFalse(protocols.BAD)

if __name__ == '__main__':
    unittest.main()
