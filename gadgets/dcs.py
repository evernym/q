import os
import configargparse
import aiofiles
import asyncio

import baseagent
import transports
import fake_identities


class Agent(baseagent.Agent):
    def __init__(self):
        super().__init__()
        # Object isn't fully inited; must call .configure() next.
        # Until then, these next properties don't have meaningful values.
        self.dest = None

    def configure(self):
        parser = configargparse.ArgumentParser(
            description="Send DIDComm messages via cmdline.",
            default_config_files=[self.conf_file_path])
        parser.add_argument('msg', metavar='MSG', type=str,
                            help='Path to a plaintext DIDComm message file.')
        parser.add_argument('dest', metavar='DEST', type=str,
                            help='An endpoint like https://x.com/abc or ~/myfolder or' + \
                                 ' smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com.')
        parser.add_argument('--anon', action='store_true', help="use anoncrypt mode")
        parser.add_argument('key', metavar='KEY', nargs="+", help=
            "Verkeys to encrypt for, or %s. If --anon is missing and dest is Bob, then Alice is the sender--and vice versa." % ' | '.join(fake_identities.ALL.keys()))
        args = super().configure(parser)
        self.dest = transports.load(args.dest, True)
        return args

    async def send(self, fname, *keys):
        if not os.path.isfile(fname):
            raise ValueError('Message file %s does not exist or is not readable.' % fname)
        async with aiofiles.open(fname, 'rb') as f:
            data = await f.read()
        if self.wallet_handle is None:
            await self.open_wallet()


async def main():
    agent = Agent()
    args = agent.configure()
    await agent.send(args.msg, *args.key)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('')
