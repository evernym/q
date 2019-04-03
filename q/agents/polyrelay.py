"""
A pluggable relay that lets you translate any agent transport into
any different transport, for arbitrary testing scenarios.
"""
if __name__ == '__main__':
    import sys
    print(f"You can't run a script from inside a python package.\n" +
        "See https://www.python.org/dev/peps/pep-0366/\n" +
        "Run bin/<this script name> instead.")
    sys.exit(1)


import argparse
import logging
import asyncio

from .. import transports


async def relay(src, dests):
    mwc = await src.receive()
    if mwc is not None:
        for dest in dests:
            await dest.send(mwc.msg)
        return mwc


async def main(argv, interrupter=None):
    try:
        parser = argparse.ArgumentParser(description=
                'Relay agent messages from a source to one or more destinations, ' +
                'possibly changing transports in the process. Transports will be ' +
                'detected based on argument formats.')
        parser.add_argument('src', metavar='SRC', type=str,
                            help=f'A source like {" | ".join(transports.RECEIVER_EX)}.')
        parser.add_argument('dest', metavar='DEST', type=str, nargs='+',
                            help=f'A destination like {" | ".join(transports.SENDER_EX)}.')

        args = parser.parse_args(argv)
        src = transports.load(args.src, transports.RECEIVERS)
        try:
            dests = [transports.load(x, transports.SENDERS) for x in args.dest]
            logging.debug('Relaying from %s to %s' % (args.src, args.dest))
            while True:
                msg = await relay(src, dests)
                if interrupter is not None:
                    if interrupter(msg):
                        break
                if not msg:
                    await asyncio.sleep(1)
        finally:
            # If I'm dealing with a receiver that's running a daemon, shut it down.
            stopper = getattr(src, 'stop', None)
            if stopper and callable(stopper):
                await stopper()
    except KeyboardInterrupt:
        print('')
