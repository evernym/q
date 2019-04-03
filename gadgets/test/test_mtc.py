import helpers
import mtc

PARTIAL_TRUST = mtc.MessageTrustContext(True, False, True)


def test_ZERO_TRUST():
    assert not bool(mtc.ZERO_TRUST)


def test_PARTIAL_TRUST():
    assert PARTIAL_TRUST


def test_str_ZERO_TRUST():
    assert 'zero trust' == str(mtc.ZERO_TRUST)


def test_str_ZERO_TRUST():
    assert 'confidentiality, authenticated_origin' == str(PARTIAL_TRUST)


def test_as_json():
    assert '{"confidentiality": true, "integrity": false, "authenticated_origin": true, "non_repudiation": false}' == PARTIAL_TRUST.as_json()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])