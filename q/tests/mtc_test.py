from ..mtc import *

ZERO = MessageTrustContext()
PARTIAL = MessageTrustContext(INTEGRITY | CONFIDENTIALITY)


def test_zero_trust():
    assert '0' == ZERO.initials
    assert '0' == str(ZERO)
    assert '0' == ZERO.labels


def test_partial_trust():
    assert 'ci' == PARTIAL.initials
    assert 'ci' == str(PARTIAL)
    assert 'confidentiality, integrity' == PARTIAL.labels


def test_flag_changes():
    x = MessageTrustContext()
    assert (SIZE_OK & x.flags) == 0
    assert '0' == x.initials
    x.flags |= (SIZE_OK | VALUES_OK)
    assert 'sv' == x.initials
    assert 'size, values' == x.labels
    x.flags &= ~SIZE_OK
    assert 'v' == x.initials
    assert 'values' == x.labels

def test_from_initials():
    x = MessageTrustContext.from_initials("sA.n ")
    assert x.flags == SIZE_OK | AUTHENTICATED_ORIGIN | NONREPUDIATION

def test_from_labelsinitials():
    x = MessageTrustContext.from_labels("Integrity, ,,Confidentiality")
    assert x.flags == INTEGRITY | CONFIDENTIALITY
