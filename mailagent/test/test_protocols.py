import unittest
import helpers
import protoplugins

class ProtocolsTest(unittest.TestCase):
    def test_every_protocol_loads(self):
        self.assertTrue(protoplugins.BY_TYPE)
        self.assertTrue(protoplugins.BY_NAME)
        self.assertFalse(protoplugins.BAD)

if __name__ == '__main__':
    unittest.main()
