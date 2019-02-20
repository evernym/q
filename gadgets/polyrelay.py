'''
A pluggable relay lets you translate any agent transport into
any different transport, for arbitrary testing scenarios.
'''
import sys
import argparse
import re

EMAIL_PAT = re.compile('^[A-Za-z0-9][^@]*@[^.@]+[.][^@]*$')
HTTP_PAT = re.compile('https?://.+$')


def relay(src, dests):
    msg = src.receive()
    for dest in dests:
        dest.send(msg)

def load_transport(t):
    pass

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=
            'Relay agent messages from a source to one or more dest transports.')
        parser.add_argument('src', metavar='SRC', type=str, nargs=1,
                            help='A source like http://localhost:8080 or me@example.com' + \
                                 ' or ~/myfolder. The transport will be detected based on' + \
                                 ' argument type.')
        parser.add_argument('dest', metavar='DEST', type=str, nargs='+',
                            help='A destination in the same format as SRC.')

        args = parser.parse_args()
        src = load_transport(args.src)
        dests = [load_transport(x) for x in args.dest]
        while True:
            relay(src, dests)
    except KeyboardInterrupt:
        print('')
