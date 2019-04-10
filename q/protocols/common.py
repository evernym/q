import json
import uuid
import datetime
import re

PROBLEM_REPORT_MSG_TYPE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report"

_ID_PAT = re.compile(r'"@id"\s*:\s*"([^"]*)"')
_THID_PAT = re.compile(r'"~thread"\s*:\s*{[^{}]*"thid"\s*:\s*"([^"]*)"')
MSG_TYPE_PAT = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/([a-z0-9._-]+)$')

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


def parse_msg_type(mtype):
    """
    Split a message type identifier into a 4-tuple of
    (doc-uri, protocol-name, semver, message-type-name).
    See https://github.com/hyperledger/indy-hipe/blob/76303dc/text/protocols/uris.md.
    """
    m = MSG_TYPE_PAT.match(mtype)
    if m:
        return m.group(1), m.group(2), m.group(3), m.group(4)


def start_msg(typ: str, thid: str = None, in_time: datetime.datetime = None):
    msg = {}
    msg['@type'] = typ
    msg['@id'] = str(uuid.uuid4())
    if thid:
        msg['~thread'] = {
            'thid': thid,
            'sender_order': 0
        }
    if in_time:
        msg['~timing'] = {
            'in_time': in_time.isoformat()
        }
    return msg


def finish_msg(json_dict):
    if json_dict.get('~timing'):
        json_dict['~timing']['out_time'] = datetime.datetime.utcnow().isoformat()
    return json.dumps(json_dict, indent=2)


def get_thread_id_from_text(txt):
    m = _THID_PAT.search(txt)
    if not m:
        m = _ID_PAT.search(txt)
    if m:
        return m.group(1)


def get_thread_id(wc):
    # Normally, we will have parsed JSON. However, if a message is malformed
    # but we still want its ID, fallback to regex parsing to get it.
    if wc.obj:
        thid = wc.obj.get('~thread',{}).get('thid')
        if not thid:
            thid = wc.obj.get('@id')
        return thid
    return get_thread_id_from_text(wc.raw)


def problem_report(wc, explain, code: str = None, catalog: str = None):
    if wc:
        thid = get_thread_id(wc)
    msg = start_msg(PROBLEM_REPORT_MSG_TYPE, thid, wc.in_time)
    msg['explain'] = explain
    if code and catalog:
        msg['explain~l10n'] = {
            'code': code,
            'catalog': catalog
        }
    return finish_msg(msg)