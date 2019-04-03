import aiofiles
import asyncio
import configargparse
import os
import re

import indy

from .. import transports
from . import base
from .. import fake_identities

NAMED_KEYS_PAT = re.compile('|'.join(fake_identities.ALL_NAMES), re.I)


class Agent(base.Agent):
    def __init__(self):
        super().__init__()
        # Object isn't fully inited; must call .configure() next.
        # Until then, these next properties don't have meaningful values.
        self.dest = None

    def configure(self):
        keynames = ' | '.join(fake_identities.ALL_NAMES)
        parser = configargparse.ArgumentParser(
            description="Send DIDComm messages via cmdline.",
            default_config_files=[self.conf_file_path])
        parser.add_argument('msg', metavar='MSG', type=str, help=
                'Path to a plaintext DIDComm message file.')
        parser.add_argument('dest', metavar='DEST', type=str, help=
                'An endpoint like https://x.com/abc or ~/myfolder or ' +
                'smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com.')
        parser.add_argument('sender', metavar='FROM', type=str, help=
                'A DID, key, or keyname like %s, to use as sender. For ' % keynames +
                'anoncrypt mode, use "anon". DIDs must be in wallet.')
        parser.add_argument('to', metavar='TO', nargs="+", help=
                'A DID, key, keyname, or keyname set to encrypt for. See keynames above. ' +
                'DIDs must be in wallet. Keyname sets are values delimited by +, as in ' +
                'ALICE+ALICE_EXTRA_EDGE. Multiple TO args become a route, from srcward to ' +
                'destward (so first arg would be mediator).')
        args = super().configure(parser)
        self.dest = transports.load(args.dest, True)
        return args

    async def norm_sender_key(self, key_name):
        if key_name.upper() == 'anon':
            return None
        key = key_name
        m = NAMED_KEYS_PAT.match(key_name)
        if m:
            item = fake_identities.ALL[key_name.upper()]
            this_did = item['did']
            if this_did:
                try:
                    ver_key = await indy.did.key_for_local_did(self.wallet_handle, this_did)
                except indy.error.IndyError:
                    this_did, ver_key = await indy.did.create_and_store_my_did(self.wallet_handle,
                            '{"seed": "%s"}' % item['seed'])
                assert ver_key == item['ver_key']
            return item['ver_key']
        return key

    def norm_recipient_keys(self, keys, make_list=True):
        if '+' in keys:
            return [self.norm_recipient_keys(x, False) for x in keys.split('+') if x]
        m = NAMED_KEYS_PAT.match(keys)
        if m:
            item = fake_identities.ALL[keys.upper()]
            keys = item['ver_key']
        return [keys] if make_list else keys

    async def send(self, fname, to):
        if not os.path.isfile(fname):
            raise ValueError('Message file %s does not exist or is not readable.' % fname)
        async with aiofiles.open(fname, 'rb') as f:
            msg = await f.read()
        msg = msg.decode('utf-8')
        if self.wallet_handle is None:
            await self.open_wallet()
        sender_key = await self.norm_sender_key(self.args.sender)
        i = len(to) - 1
        while i >= 0:
            # Always anon-crypt to mediator
            if i == 0 and len(to) > 1:
                sender = None
            else:
                sender = sender_key
            recipients = self.norm_recipient_keys(to[i])
            msg = await indy.crypto.pack_message(self.wallet_handle, msg, recipients, sender)
            msg = msg.decode('utf-8')
            i -= 1
        await self.dest.send(msg)


async def main():
    agent = Agent()
    args = agent.configure()
    await agent.send(args.msg, args.to)