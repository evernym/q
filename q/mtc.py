import re


class MessageTrustContext:
    """
    Describe the trust guarantees associated with a given message.
    See http://bit.ly/2UutabT for more information.

    MessageTrustContexts are castable to bool and interpeted as True if they have
    any trust at all, or False otherwise.

    MessageTrustContexts convert to strings as valid JSON.
    """
    def __init__(self, confidentiality:bool=False, integrity:bool=False,
                 authenticated_origin:bool=False, non_repudiation:bool=False):
        self.confidentiality = confidentiality
        self.integrity = integrity
        self.authenticated_origin = authenticated_origin
        self.non_repudiation = non_repudiation
        self.input_validations = []

    def __bool__(self):
        for item in self.__dict__.values():
            if item:
                return True
        return False

    def as_json(self):
        # Use normal python serialization, except quote strings with double quotes and make
        # boolean constants lowercase. This makes the string output JSON.
        return str(self.__dict__).replace("'", '"').replace('False', 'false').replace('True', 'true')

    def __str__(self):
        have_trust_names = []
        # Get all public attribute names.
        d = self.__dict__
        keys = [k for k in d.keys() if not k.startswith('_')]
        for key in keys:
            if d[key]:
                have_trust_names.append(key)
        if not have_trust_names:
            return 'zero trust'
        return ', '.join(have_trust_names)


"""A special global constant representing the degenerate, empty MessageTrustContext."""
ZERO_TRUST = MessageTrustContext()

_id_pat = re.compile(r'"@id"\s*:\s*"([^"]+)"', re.S)
_squeeze_pat = re.compile('\\s*\n[\t ]*')
