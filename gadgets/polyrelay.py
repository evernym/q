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

import transports
import http_receiver


async def relay(src, dests):
    mwc = await src.receive()
    if mwc is not None:
        for dest in dests:
            await dest.send(mwc.msg)
        return mwc


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
        src = transports.load(args.src, False)
        try:
            dests = [transports.load(x, True) for x in args.dest]
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
