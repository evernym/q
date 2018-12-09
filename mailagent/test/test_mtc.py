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

class MwetTest(unittest.TestCase):
    def test_NULL_MWET(self):
        self.assertFalse(mtc.NULL_MWET)
    def test_nonempty_msg(self):
        self.assertTrue(mtc.MessageWithExplicitTrust('hi'))
    def test_empty_msg_nonempty_trust(self):
        self.assertFalse(mtc.MessageWithExplicitTrust(tc=PARTIAL_TRUST))
    def test_str_with_id(self):
        mwet = mtc.MessageWithExplicitTrust('{"x" :\t25 \r\n\t""@id":\r\n"abc")', PARTIAL_TRUST)
        self.assertEqual('{..."@id":"abc"...} with confidentiality, authenticated_origin', str(mwet))
    def test_str_with_no_id(self):
        mwet = mtc.MessageWithExplicitTrust('{"test":\n"abc"}', mtc.ZERO_TRUST)
        self.assertEqual('{"test": "abc"} with zero trust', str(mwet))
    def test_long_str_with_no_id(self):
        mwet = mtc.MessageWithExplicitTrust('{"attr_name":\n"abcdeklmnopq",\t\r\n  "x": 3.14159   }', mtc.ZERO_TRUST)
        self.assertEqual('{"attr_name": "abcdeklmnopq", "x": 3.... with zero trust', str(mwet))

if __name__ == '__main__':
    unittest.main()
