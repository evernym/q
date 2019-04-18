from ..mwc import *

PARTIAL_TRUST = MessageTrustContext(CONFIDENTIALITY | AUTHENTICATED_ORIGIN)


def test_NULL_MWC():
    assert not bool(NULL_MWC)


def test_nonempty_msg():
    assert bool(MessageWithContext('hi'))


def test_empty_msg_nonempty_trust():
    assert not bool(MessageWithContext(tc=PARTIAL_TRUST))


def test_str_with_id():
    wc = MessageWithContext(b'{"x" :\t25 ,\r\n\t"@id":\r\n"abc", "sender_verkey": "Fred"}', PARTIAL_TRUST)
    assert '{..."@id":"abc"...} from Fred with mtc=+s+d-c-i-a' == str(wc)


def test_str_with_type():
    wc = MessageWithContext(b'{"x" :\t25, \r\n\t"@type":\r\n"abcwxyz;x/1.0/foo"}')
    assert '{..."@type":"...x/1.0/foo"...} from nobody with mtc=+s+d-c-i-a' == str(wc)


def test_str_with_type_and_id():
    wc = MessageWithContext(b'{"x":25,"@id":"abc", "@type":\r\n"abcwxyz;x/1.0/foo"}', PARTIAL_TRUST)
    assert '{..."@type":"...x/1.0/foo","@id":"abc"...} from nobody with mtc=+s+d-c-i-a' == str(wc)


def test_str_with_long_type():
    wc = MessageWithContext(b'{"x":25,"@id":"abc", "@type":\r\n"http://server.abcxyz.com/abcwxyz123456789abcwxyz123456789?foo=bar&p=x/1.0/foo"}')
    assert '{..."@type":"...x/1.0/foo","@id":"abc"...} from nobody with mtc=+s+d-c-i-a' == str(wc)


def test_str_with_no_id():
    wc = MessageWithContext('{"test":\n"abc"}')
    assert '{"test": "abc"} from nobody with mtc=+s+d-c-i-a' == str(wc)


def test_long_str_with_no_id():
    wc = MessageWithContext(b'{"attr_name":\n"abcdeklmnopq",\t\r\n  "x": 3.14159   }')
    assert '{"attr_name": "abcdeklmnopq", "x": 3.... from nobody with mtc=+s+d-c-i-a' == str(wc)


def test_in_time():
    wc = MessageWithContext('{}')
    assert wc.in_time

def test_sender():
    wc = MessageWithContext('{}')
    assert wc.sender is None
    wc = MessageWithContext('{"sender_verkey": "abc"}')
    assert wc.sender == "abc"
