import unittest
import helpers
import mtc
import mwc

PARTIAL_TRUST = mtc.MessageTrustContext(confidentiality=True, authenticated_origin=True)

class MwcTest(unittest.TestCase):
    def test_NULL_MWC(self):
        self.assertFalse(mwc.NULL_MWC)
    def test_nonempty_msg(self):
        self.assertTrue(mwc.MessageWithContext('hi'))
    def test_empty_msg_nonempty_trust(self):
        self.assertFalse(mwc.MessageWithContext(tc=PARTIAL_TRUST))
    def test_str_with_id(self):
        wc = mwc.MessageWithContext('{"x" :\t25 \r\n\t""@id":\r\n"abc")', 'Fred', PARTIAL_TRUST)
        self.assertEqual('{..."@id":"abc"...} from Fred with confidentiality, authenticated_origin', str(wc))
    def test_str_with_no_id(self):
        wc = mwc.MessageWithContext('{"test":\n"abc"}', mtc.ZERO_TRUST)
        self.assertEqual('{"test": "abc"} from nobody with zero trust', str(wc))
    def test_long_str_with_no_id(self):
        wc = mwc.MessageWithContext('{"attr_name":\n"abcdeklmnopq",\t\r\n  "x": 3.14159   }', mtc.ZERO_TRUST)
        self.assertEqual('{"attr_name": "abcdeklmnopq", "x": 3.... from nobody with zero trust', str(wc))

if __name__ == '__main__':
    unittest.main()
