"""An SSI agent that interacts through the file system."""

if __name__ == '__main__':
    import sys
    print("You can't run a script from inside a python package without -m switch.\n" +
        "See https://www.python.org/dev/peps/pep-0366/. Run bin/<this script name> instead.")
    sys.exit(1)

import os
import json
import asyncio
import configargparse
import logging
import time

from .. import log_helpers
from . import base
from .. import protocols
from ..transports import folder_channel

from indy import crypto, did, wallet


class Agent(base.Agent):

    def __init__(self):
        super().__init__()
        # Object isn't fully inited; must call .configure() next.
        # Until then, these next properties don't have meaningful values.
        self.queue_dir = None
        self.trans = None

    def configure(self, argv=None):
        parser = configargparse.ArgumentParser(
            description="Run an agent that communicates via the file system.",
            default_config_files=[self.conf_file_path])
        parser.add_argument('--endpoint', metavar='URI', help='Endpoint to use with remote parties.')
        super().configure_reset(parser)
        args = super().configure(parser, argv)
        self.queue_dir = os.path.join(self.folder, 'queue')
        os.makedirs(self.queue_dir, exist_ok=True)
        self.trans = folder_channel.Channel(self.queue_dir, is_destward=False)
        self.endpoint = args.endpoint if args.endpoint else self.queue_dir

    async def handle_msg(self, wc):
        handled = False
        # We might have received a plaintext message, in which case unpack is unnecessary.
        # If not, do the unpack now.
        if not wc.obj:
            await self.unpack(wc)
        if wc.obj:
            if wc.type:
                parsed_type = protocols.parse_msg_type(wc.type)
                handler_info = protocols.find_handler(parsed_type)
                if handler_info:
                    try:
                        if await handler_info.module.handle(wc, parsed_type, self):
                            handled = True
                    finally:
                        if wc.interaction:
                            self.interdb.set_interaction(wc.interaction)
                if not handled:
                    etxt = 'Unhandled message -- unsupported @type %s with %s.' % (wc.type, wc)
                    logging.warning(etxt)
                else:
                    logging.debug('Handled message of @type %s.' % wc.type)
            else:
                etxt = 'Unhandled message -- missing @type with %s.' % wc
                logging.warning(etxt)
        else:
            etxt = 'Unhandled message -- not able to turn into native object representation with %s' % wc
            logging.warning(etxt)
        return handled

    async def run(self):
        my_id = self.folder.replace(os.path.expanduser('~'), '~')
        logging.info('Agent at %s started.' % my_id)
        wait_interval = 0.25
        try:
            while True:
                try:
                    wc = await self.trans.receive()
                    if wc:
                        wait_interval = 0.25
                        await self.handle_msg(wc)
                    elif wait_interval < 3:
                        wait_interval *= 2
                    if self.interrupt_requested:
                        break
                    if not wc:
                        await asyncio.sleep(wait_interval)
                except KeyboardInterrupt:
                    return
                except json.decoder.JSONDecodeError as e:
                    logging.warning(str(e))
                except:
                    log_helpers.log_exception()
        finally:
            logging.info('Agent at %s stopped.' % my_id)

async def main():
    agent = Agent()
    agent.configure()
    await agent.open_wallet()
    await agent.run()
