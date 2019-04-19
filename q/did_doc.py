import json

from . import did

MAIN_CONTEXT = "https://w3id.org/did/v1"

class DIDDoc:
    def __init__(self, obj):
        if isinstance(obj, str):
            obj = json.loads(obj)
        self.obj = obj

    @classmethod
    def from_scratch(cls, id, key, svc):
        # Guarantee prefix on DID
        id = str(did.DID(id))
        key1 = id + '#1'
        return DIDDoc({
            "@context": MAIN_CONTEXT,
            "id": str(id),
            "publicKey": [{
                "id": key1,
                "type": "Ed25519VerificationKey2018",
                "controller": id,
                "publicKeyBase58": key
            }],
            "authentication": [{
                "type": "Ed25519SignatureAuthentication2018",
                "publicKey": key1
            }],
            "service": [{
                "id": id + ";indy",
                "type": "IndyAgent",
                "recipientKeys": [key1],
                "serviceEndpoint": svc
            }]
        })

    @classmethod
    def from_json(cls, json_txt):
        return DIDDoc(json_txt)

    @classmethod
    def from_dict(cls, dict):
        return DIDDoc(dict)

    def __str__(self):
        return json.dumps(self.obj, indent=2)
