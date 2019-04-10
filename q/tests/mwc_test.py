from .. import mtc, mwc

PARTIAL_TRUST = mtc.MessageTrustContext(confidentiality=True, authenticated_origin=True)


def test_NULL_MWC():
    assert not bool(mwc.NULL_MWC)


def test_nonempty_msg():
    assert bool(mwc.MessageWithContext('hi'))


def test_empty_msg_nonempty_trust():
    assert not bool(mwc.MessageWithContext(tc=PARTIAL_TRUST))


def test_str_with_id():
    wc = mwc.MessageWithContext(b'{"x" :\t25 \r\n\t"@id":\r\n"abc")', PARTIAL_TRUST)
    wc.unpacked = {'sender_verkey': 'Fred'}
    assert '{..."@id":"abc"...} from Fred with confidentiality, authenticated_origin' == str(wc)


def test_str_with_type():
    wc = mwc.MessageWithContext(b'{"x" :\t25 \r\n\t"@type":\r\n"abcwxyz;x/1.0/foo")')
    assert '{..."@type":"...x/1.0/foo"...} from nobody with zero trust' == str(wc)


def test_str_with_type_and_id():
    wc = mwc.MessageWithContext(b'{"x":25,"@id":"abc", "@type":\r\n"abcwxyz;x/1.0/foo")', PARTIAL_TRUST)
    assert '{..."@type":"...x/1.0/foo","@id":"abc"...} from nobody with confidentiality, authenticated_origin' == str(wc)


def test_str_with_no_id():
    wc = mwc.MessageWithContext('{"test":\n"abc"}', mtc.ZERO_TRUST)
    assert '{"test": "abc"} from nobody with zero trust' == str(wc)


def test_long_str_with_no_id():
    wc = mwc.MessageWithContext(b'{"attr_name":\n"abcdeklmnopq",\t\r\n  "x": 3.14159   }', mtc.ZERO_TRUST)
    assert '{"attr_name": "abcdeklmnopq", "x": 3.... from nobody with zero trust' == str(wc)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])