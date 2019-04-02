import re

PAT = re.compile('^([A-Za-z0-9][^@:]*):([^@]*)@(.+):([0-9]{1,5})$')
EXAMPLE = 'imap://user:pass@imapserver:port'

class Receiver:
    def __init__(self, mailbox):
        raise ValueError('IMAP transport not yet supported.')