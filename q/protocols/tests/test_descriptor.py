from ..descriptor import Descriptor as D

FQNAME_1 = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification'

def test_normal():
    d = D(FQNAME_1, '1.0')
    assert str(d) == 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0'
    assert d.fqname == FQNAME_1
    assert d.version == '1.0'
    assert d.name == 'notification'
