import json
import uuid
import datetime
import re

from ..protocols import HANDLERS

PROBLEM_REPORT_MSG_TYPE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report"

_ID_PAT = re.compile(r'"@id"\s*:\s*"([^"]*)"')
_THID_PAT = re.compile(r'"~thread"\s*:\s*{[^{}]*"thid"\s*:\s*"([^"]*)"')


def start_msg(typ: str, thid: str = None, in_time: datetime.datetime = None):
    msg = {'@type': typ, '@id': str(uuid.uuid4())}
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
    if wc.thid: return wc.thid
    if wc.id: return wc.id
    return get_thread_id_from_text(wc.plaintext) if wc.plaintext else None


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


class attribute_dict(dict):
    """Dict with attribute based access to keys."""
    marker = object()

    def __init__(self, **kwargs):
        super().__init__()
        for key in kwargs:
            self.__setitem__(key, kwargs[key])

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, attribute_dict):
            value = attribute_dict(**value)
        super(attribute_dict, self).__setitem__(key, value)

    def __getitem__(self, key):
        found = self.get(key, attribute_dict.marker)
        if found is attribute_dict.marker:
            found = attribute_dict()
            super(attribute_dict, self).__setitem__(key, found)
        return found

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return attribute_dict(**self)

    __setattr__ = __setitem__
    __getattr__ = __getitem__
