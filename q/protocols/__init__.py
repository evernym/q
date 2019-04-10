import collections
import re

from .semver import Semver

HandlerInfo = collections.namedtuple('HandlerInfo', ['module', 'doc_uri', 'protocol_name', 'semver', 'messages', 'roles'])
SplitMsgTypeUri = collections.namedtuple('SplitMsgTypeUri', ['doc_uri', 'protocol_name', 'semver', 'msg_type_name'])
SplitProtocolIdentifierUri = collections.namedtuple('SplitProtocolIdentifierUri', ['doc_uri', 'protocol_name', 'semver'])
HandlerCandidate = collections.namedtuple('HandlerCandidate', ['handler', 'compatible'])

HANDLERS = []

MSG_TYPE_URI_PAT = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/([a-z0-9._-]+)$')
PROTOCOL_IDENTIFIER_URI_PAT = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/?$')


def parse_msg_type(mturi) -> SplitMsgTypeUri:
    """
    Split a message type identifier URI into a 4-tuple of
    (doc_uri, protocol_name, semver, message_type_name).
    See https://github.com/hyperledger/indy-hipe/blob/76303dc/text/protocols/uris.md.
    """
    m = MSG_TYPE_URI_PAT.match(mturi)
    if m:
        return SplitMsgTypeUri(m.group(1), m.group(2), Semver(m.group(3)), m.group(4))


def parse_protocol_identifier(piuri) -> SplitProtocolIdentifierUri:
    """
    Split a protocol identifier URI into a 3-tuple of
    (doc_uri, protocol_name, semver).
    See https://github.com/hyperledger/indy-hipe/blob/76303dc/text/protocols/uris.md.
    """
    m = PROTOCOL_IDENTIFIER_URI_PAT.match(piuri)
    if m:
        return SplitProtocolIdentifierUri(m.group(1), m.group(2), Semver(m.group(3)))


def compare_identifiers(a, b):
    '''
    Compare two identifiers in the way that many DIDComm HIPEs require -- case-insensitive,
    and ignoring punctuation and whitespace.
    '''
    if a is None:
        return 0 if b is None else -1
    elif b is None:
        return 1

    def next(i, txt, end):
        i += 1
        while i < end:
            c = txt[i]
            if c.isalnum():
                return i, c
            i += 1
        return None, None

    ai = -1
    bi = -1
    alen = len(a)
    blen = len(b)
    while True:
        ai, ac = next(ai, a, alen)
        bi, bc = next(bi, b, blen)
        if ai is None:
            return 0 if bi is None else -1
        elif bi is None:
            return 1
        ac = ord(ac.lower())
        bc = ord(bc.lower())
        n = ac - bc
        if n:
            return n


def find_handler(mturi: SplitMsgTypeUri):
    """
    Return the best handler to process this protocol+version+message type.
    """
    if isinstance(mturi, str):
        mturi = parse_msg_type(mturi)
    best_candidate = None
    for handler in HANDLERS:
        # Found a handler that knows about this protocol's namespace.
        if mturi.doc_uri == handler.doc_uri:
            # Handler knows about the protocol of which this message is a part.
            if compare_identifiers(mturi.protocol_name, handler.protocol_name) == 0:
                # Does it know about this specific message type?
                for mtn in handler.messages:
                    # If yes...
                    if compare_identifiers(mturi.msg_type_name, mtn) == 0:
                        # This handler knows about the protocol and the message type. Now check
                        # semver compatibility. First look for exact matches. These are our preferred
                        # answer.
                        if mturi.semver == handler.semver:
                            best_candidate = HandlerCandidate(handler, 5)
                            break
                        # Okay, semver matching is going to be fuzzy instead. See how fuzzy this
                        # combination is.
                        compatible = handler.semver.compatible_with(mturi.semver)
                        if compatible:
                            replace = False
                            # If first fuzzy match, just make it the best candidate for now.
                            if best_candidate is None:
                                replace = True
                            else:
                                # Another handler claims the protocol as well. We prefer handlers that
                                # are newer than a message type, so no features are lost. However, among
                                # newer handlers, we prefer a handler that's closer to the message type's
                                # version, since it is likely to require less adjustment of behavior to
                                # avoid new features. Thus, for a message version of 1.2, we prefer a
                                # handler that's capable of 1.3 over one that's capable of 1.1. For a
                                # message version of 1.2.1, we prefer a handler that's capable of 1.2.6
                                # over a handler that's capable of 1.2.9. (I'm not sure if that's a
                                # perfect algorithm; it's just what we're going with for now.)
                                if compatible > 0:
                                    if best_candidate.compatible > 0:  # Previous candidate is also later; which is better?
                                        # Pick the one that's closer to the message type's version.
                                        if handler.semver < best_candidate.handler.semver:
                                            replace = True
                                    else:  # Previous best was earlier than this message's version
                                        replace = True
                                else:
                                    if best_candidate.compatible > 0:
                                        replace = True
                                    else:
                                        if handler.semver > best_candidate.handler.semver:
                                            replace = True
                            if replace:
                                best_candidate = HandlerCandidate(handler, compatible)
    return best_candidate.handler if best_candidate else None


def _load_plugins():
    import importlib
    import os
    my_folder = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(my_folder):
        if item == 'tests' or item.startswith('_') or ('.' in item) or (
                not os.path.isdir(os.path.join(my_folder, item))):
            continue
        handler = importlib.import_module(f'.{item}', __name__)
        global HANDLERS
        for protocol_info in handler.SUPPORTED:
            doc_uri, protocol_name, semver = parse_protocol_identifier(protocol_info[0])
            HANDLERS.append(HandlerInfo(handler, doc_uri, protocol_name, semver, protocol_info[1], protocol_info[2]))

_load_plugins()
del _load_plugins
