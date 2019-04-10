from ...protocols import *

MTYPE_1 = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec!notification/1.0/problem-report"
MTYPE_1_PARTS = ("did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/", "notification", "1.0", "problem-report")


def test_msg_type_split_normal():
    for c in ';:?=&|!$#@ ':
        mtype = MTYPE_1.replace('!', c)
    x = parse_msg_type(mtype)
    assert MTYPE_1_PARTS[0][:-1] == x[0][:-1]
    assert MTYPE_1_PARTS[1] == x[1]
    assert MTYPE_1_PARTS[2] == str(x[2])
    assert MTYPE_1_PARTS[3] == x[3]

def test_msg_type_split_no_prefix():
    assert parse_msg_type(MTYPE_1[MTYPE_1.index('!') + 1:]) == ('', "notification", semver.Semver("1.0"), "problem-report")

def test_msg_type_split_no_version():
    assert parse_msg_type(MTYPE_1.replace('1.0', '')) is None

def test_compare_identifiers_similar():
    assert compare_identifiers('this-is-a-test', 'This_is_a_Test') == 0
    assert compare_identifiers('this-is-a-test', 'thisIsATest') == 0
    assert compare_identifiers('this-is-a-test', 'This is a test!') == 0

def test_compare_identifiers_different():
    assert compare_identifiers('this-is-a-test', 'X') < 0
    assert compare_identifiers('X', 'this-is-a-test') > 0

def test_compare_identifiers_empty():
    assert compare_identifiers('x', '') > 0
    assert compare_identifiers('', 'x') < 0

def test_compare_identifiers_none():
    assert compare_identifiers('x', None) > 0
    assert compare_identifiers(None, 'x') < 0

def test_compare_identifiers_empty_none():
    assert compare_identifiers('', None) > 0
    assert compare_identifiers(None, '') < 0

def test_plugins_load():
    assert len(HANDLERS) >= 3

def test_find_handler():
    assert find_handler('did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping')
    assert find_handler('did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/protocol_discovery/1.0/query')
