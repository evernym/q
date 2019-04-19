import copy
import pytest

from ..did_doc import *

SIMPLE_DID = "did:fake:abc"
SIMPLE_VERKEY = "FaKeVeRkEy"
SIMPLE_ENDPOINT = "https://example.com/myagent"

@pytest.fixture
def scratch():
    yield DIDDoc.from_scratch(SIMPLE_DID, SIMPLE_VERKEY, SIMPLE_ENDPOINT)

def check_did_doc(dd):
    g = lambda x: dd.obj.get(x)
    assert g('id') == SIMPLE_DID
    assert g('@context') == MAIN_CONTEXT

    def assert_array(which, how_many=1):
        array = g(which)
        assert isinstance(array, list)
        assert len(array) == how_many
        return array[0]

    key1 = SIMPLE_DID + '#1'
    keydef = assert_array('publicKey')
    assert keydef.get('id') == key1
    assert keydef.get('type') == "Ed25519VerificationKey2018"
    assert keydef.get('controller') == SIMPLE_DID
    assert keydef.get('publicKeyBase58') == SIMPLE_VERKEY

    authn = assert_array('authentication')
    assert authn.get("type") == "Ed25519SignatureAuthentication2018"
    assert authn.get("publicKey") == keydef.get('id')

    svc = assert_array('service')
    svc_id = svc.get("id")
    assert svc_id.startswith(SIMPLE_DID)
    assert ';' in svc_id
    assert svc.get("type") == "IndyAgent"
    assert svc.get("recipientKeys")[0] == key1
    assert svc.get("serviceEndpoint") == SIMPLE_ENDPOINT


def test_scratch_is_well_formed(scratch):
    check_did_doc(scratch)

def test_from_did_doc_text(scratch):
    check_did_doc(DIDDoc(str(scratch)))

def test_from_obj(scratch):
    check_did_doc(DIDDoc(copy.deepcopy(scratch.obj)))
