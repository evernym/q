"""An SSI agent that interacts through the file system."""

if __name__ == '__main__':
    import sys
    print("You can't run a script from inside a python package without -m switch.\n" +
        "See https://www.python.org/dev/peps/pep-0366/. Run bin/<this script name> instead.")
    sys.exit(1)

import os
import json
import datetime
import asyncio
import configargparse
import logging

from .. import log_helpers
from . import base
from .. import protocols
from ..protocols import common
from ..transports import file_transport

from indy import crypto, did, wallet


class Agent(base.Agent):

    def __init__(self):
        super().__init__()
        # Object isn't fully inited; must call .configure() next.
        # Until then, these next properties don't have meaningful values.
        self.queue_dir = None
        self.trans = None

    def configure(self):
        parser = configargparse.ArgumentParser(
            description="Run an agent that communicates via the file system.",
            default_config_files=[self.conf_file_path])
        super().configure_reset(parser)
        args = super().configure(parser)
        self.queue_dir = os.path.join(self.folder, 'queue')
        os.makedirs(self.queue_dir, exist_ok=True)
        self.trans = file_transport.FileTransport(self.queue_dir, folder_is_destward=False)

    async def handle_msg(self, wc):
        handled = False
        await self.unpack(wc)
        typ = wc.obj.get('@type')
        if typ:
            parsed_type = protocols.parse_msg_type(typ)
            handler = protocols.find_handler(parsed_type)
            if handler:
                if await handler.handle(wc, parsed_type, self):
                    handled = True
            if not handled:
                etxt = 'Unhandled message -- unsupported @type %s with %s.' % (typ, wc)
                logging.warning(etxt)
            else:
                logging.debug('Handled message of @type %s.' % typ)
        else:
            etxt = 'Unhandled message -- missing @type with %s.' % wc
            logging.warning(etxt)
        return handled

    async def run(self):
        logging.info('Agent started.')
        try:
            while True:
                try:
                    wc = await self.trans.receive()
                    if wc:
                        await self.handle_msg(wc)
                    else:
                        await asyncio.sleep(2.0)
                except KeyboardInterrupt:
                    return
                except json.decoder.JSONDecodeError as e:
                    logging.warning(str(e))
                except:
                    log_helpers.log_exception()
        finally:
            logging.info('Agent stopped.')

async def main():
    agent = Agent()
    agent.configure()
    await agent.open_wallet()
    await agent.run()
