import json
import uuid
import datetime
import re

PROBLEM_REPORT_MSG_TYPE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report"

_id_pat = re.compile(r'"@id"\s*:\s*"([^"]*)"')
_thid_pat = re.compile(r'"~thread"\s*:\s*{[^{}]*"thid"\s*:\s*"([^"]*)"')


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
    m = _thid_pat.search(txt)
    if not m:
        m = _id_pat.search(txt)
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