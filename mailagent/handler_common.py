import json
import uuid
import datetime

PROBLEM_REPORT_MSG_TYPE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report"

def start_msg(typ:str, thid:str=None, in_time:datetime.datetime=None):
    msg = {}
    msg['@type'] = typ
    msg['@id'] = str(uuid.uuid4())
    if thid:
        x = {}
        msg['@thread'] = x
        x['thid'] = thid
        x['seqnum'] = 0
    if in_time:
        x = {}
        msg['@timing'] = x
        x['in_time'] = in_time.isoformat()
    return msg

def finish_msg(json_dict):
    if json_dict.get('@timing'):
        json_dict['@timing']['out_time'] = datetime.datetime.utcnow().isoformat()
    return json.dumps(json_dict)

def get_thread_id(wc):
    thid = wc.obj.get('@thread')
    if not thid:
        thid = wc.obj.get('@id')
    return thid

def problem_report(wc, explain_ltxt, code:str=None, catalog:str=None):
    if wc:
        thid = get_thread_id(wc)
    msg = start_msg(PROBLEM_REPORT_MSG_TYPE, thid, wc.in_time)
    msg['explain_ltxt'] = explain_ltxt
    if code and catalog:
        x = {}
        msg['explain_l10n'] = x
        x['code'] = code
        x['catalog'] = catalog
    return finish_msg(msg)