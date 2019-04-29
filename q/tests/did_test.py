import pytest

from ..did import DID

d = DID("did:fake:abc")

def test_simple_did_parses_correctly():
    assert d.method == 'fake'
    assert d.nsi == 'abc'
    assert str(d) == d.value

def check_compare(a, b, a_is_lt, a_is_gt):
    equal = (not a_is_lt) and (not a_is_gt)
    assert (a == b) == equal
    assert (a != b) != equal
    assert (a > b) == a_is_gt
    assert (a < b) == a_is_lt
    assert (a >= b) == (not a_is_lt)
    assert (a <= b) == (not a_is_gt)

def test_did_compares_to_string():
    b = d.value
    check_compare(d, b, False, False)
    b += 'X'
    check_compare(d, b, True, False)

def test_did_compares_to_did():
    s = DID(d.value)
    check_compare(d, s, False, False)
    s.value = s.value[:-3] + "aaa"
    check_compare(d, s, False, True)

def test_did_is_hashable():
    assert {d: 1}

def test_did_is_case_sensitive():
    assert d != DID(d.value.upper())

def test_did_without_prefix():
    x = DID(d.nsi)
    assert x.value.startswith('did:')
    assert bool(x.method)
    assert x.nsi == d.nsi