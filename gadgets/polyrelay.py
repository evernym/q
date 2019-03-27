'''
A pluggable relay that lets you translate any agent transport into
any different transport, for arbitrary testing scenarios.
'''

import sys
import argparse
import re
import os
import logging
import asyncio

import file_transport
import http_sender
import http_receiver
import smtp_sender

IMAP_PAT = re.compile('^([A-Za-z0-9][^@:]*):([^@]*)@(.+):([0-9]{1,5})$')

async def relay(src, dests):
    mwc = await src.receive()
    if mwc is not None:
        for dest in dests:
            await dest.send(mwc.msg)
        return mwc

def load_transport(t, is_dest):
    http_matched = False
    if IMAP_PAT.match(t):
        raise ValueError('IMAP transport not yet supported.')
    elif smtp_sender.PAT.match(t):
        if is_dest:
            return smtp_sender.SmtpSender(t)
        else:
            raise ValueError("SMTP transport can only be a dest, not a source. Use IMAP instead.")
    if http_receiver.PAT.match(t):
        if not is_dest:
            return http_receiver.HttpReceiver(t)
        else:
            http_matched = True
    if http_sender.PAT.match(t):
        if is_dest:
            return http_sender.HttpSender(t)
        else:
            http_matched = True
    if http_matched:
        raise ValueError("HTTP arg reverses src and dest syntax.")
    else:
        t = os.path.expanduser(t)
        if not os.path.isdir(t):
            raise ValueError('Folder "%s" does not exist.' % t)
        return file_transport.FileTransport(t, is_dest)

async def main(argv, interrupter=None):
    try:
        parser = argparse.ArgumentParser(description=
            'Relay agent messages from a source to one or more destinations, possibly changing' + \
            ' transports in the process. Transports will be detected based on argument formats.')
        parser.add_argument('src', metavar='SRC', type=str,
                            help='A source like http://localhost:8080 or ~/myfolder' + \
                                 ' or imap://user:pass@imapserver:port.')
        parser.add_argument('dest', metavar='DEST', type=str, nargs='+',
                            help='A destination like https://x.com/abc or ~/myfolder or' + \
                                 'smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com.')

        args = parser.parse_args(argv)
        src = load_transport(args.src, False)
        try:
            dests = [load_transport(x, True) for x in args.dest]
            logging.debug('Relaying from %s to %s' % (args.src, args.dest))
            while True:
                msg = await relay(src, dests)
                if interrupter is not None:
                    if interrupter(msg):
                        break
                if not msg:
                    await asyncio.sleep(1)
        finally:
            if isinstance(src, http_receiver.HttpReceiver):
                await src.stop_serving()
    except KeyboardInterrupt:
        print('')


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
