import unittest
import helpers
import mtc

PARTIAL_TRUST = mtc.MessageTrustContext(True, False, True)

class MtcTest(unittest.TestCase):
    def test_ZERO_TRUST(self):
        self.assertFalse(mtc.ZERO_TRUST)
    def test_PARTIAL_TRUST(self):
        self.assertTrue(PARTIAL_TRUST)
    def test_str_ZERO_TRUST(self):
        self.assertEqual('zero trust', str(mtc.ZERO_TRUST))
    def test_str_ZERO_TRUST(self):
        self.assertEqual('confidentiality, authenticated_origin', str(PARTIAL_TRUST))
    def test_as_json(self):
        self.assertEqual('{"confidentiality": true, "integrity": false, "authenticated_origin": true, "non_repudiation": false}', PARTIAL_TRUST.as_json())

if __name__ == '__main__':
    unittest.main()
