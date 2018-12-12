import unittest

import helpers
import plugins

class ProtocolsTest(unittest.TestCase):
    def test_every_protocol_loads(self):
        self.assertTrue(plugins.BY_TYPE)
        self.assertTrue(plugins.BY_NAME)
        self.assertFalse(plugins.BAD)

if __name__ == '__main__':
    unittest.main()
