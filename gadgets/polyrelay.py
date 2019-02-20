'''
A pluggable relay lets you translate any agent transport into
any different transport, for arbitrary testing scenarios.
'''
import sys
import argparse
import re
import os
import time

import file_transport

IMAP_PAT = re.compile('^([A-Za-z0-9][^@:]*):([^@]*)@(.+):([0-9]{1,5})$')
SMTP_PAT = re.compile('^[A-Za-z0-9][^@]*@[^.@]+[.][^@]*$')
HTTP_PAT = re.compile('https?://.+$')

def relay(src, dests):
    mwc = src.receive()
    if mwc is not None:
        for dest in dests:
            dest.send(mwc.msg)
        return mwc

def load_transport(t, is_dest):
    if IMAP_PAT.match(t):
        raise ValueError('IMAP transport not yet supported.')
    if SMTP_PAT.match(t):
        raise ValueError('SMTP transport not yet supported.')
    elif HTTP_PAT.match(t):
        raise ValueError('Mail transport not yet supported.')
    else:
        if not os.path.isdir(t):
            raise ValueError('Folder "%s" does not exist.' % t)
        return file_transport.FileTransport(t, is_dest)
    pass

def main(argv, interrupter=None):
    try:
        parser = argparse.ArgumentParser(description=
            'Relay agent messages from a source to one or more destinations, possibly changing' + \
            ' transports in the process. Transports will be detected based on argument formats.')
        parser.add_argument('src', metavar='SRC', type=str,
                            help='A source like http://localhost:8080 or user:pass@imapserver:port' + \
                                 ' or ~/myfolder.')
        parser.add_argument('dest', metavar='DEST', type=str, nargs='+',
                            help='A destination like http://localhost:8080 or me@example.com' + \
                                 ' or ~/myfolder.')

        args = parser.parse_args(argv)
        src = load_transport(args.src, False)
        dests = [load_transport(x, True) for x in args.dest]
        while True:
            msg = relay(src, dests)
            if interrupter is not None:
                if interrupter(msg):
                    break
            if not msg:
                time.sleep(1)
    except KeyboardInterrupt:
        print('')

if __name__ == '__main__':
    main(sys.argv[1:])
