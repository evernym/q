TYPES = [
    'ping',
    'pong'
]

def handle(mwc, typ, agent):
    if typ == 'ping':
        agent.trans.send('{"@type": "pong"}', mwc.sender)
    return False