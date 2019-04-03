#!/usr/bin/env python

# '''An SSI agent that interacts through the file system.'''

import os
import sys
import json
import datetime
import asyncio
import configargparse
import logging

from . import log_helpers
from . import baseagent
from . import file_transport
from . import handlers
from . import handler_common

from indy import crypto, did, wallet


class Agent(baseagent.Agent):

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

    def handle_msg(self, wc):
        # Record when we received this message.
        wc.in_time = datetime.datetime.utcnow()
        handled = False
        # decrypt wc.msg
        loop = asyncio.get_event_loop()
        wc.msg = loop.run_until_complete(self.securemsg.decryptMsg(wc.msg))
        wc.obj = json.loads(wc.msg[1].decode("utf-8"))
        # wc.obj = json.loads(wc.msg)
        typ = wc.obj.get('@type')
        if typ:
            candidates = handlers.HANDLERS_BY_MSG_TYPE.get(typ)
            if candidates:
                for handler in candidates:
                    if handler.handle(wc, self):
                        resp = handler.handle(wc, self)
                        msg_to_encrypt = handler_common.finish_msg(resp)
                        encrypted = loop.run_until_complete(self.securemsg.encryptMsg(msg_to_encrypt))
                        self.trans.send(encrypted, wc.sender, wc.in_reply_to, wc.subject)
                        handled = True
                        break
            if not handled:
                etxt = 'Unhandled message -- unsupported @type %s with %s.' % (typ, wc)
                logging.warning(etxt)
                self.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
            else:
                logging.debug('Handled message of @type %s.' % typ)
        else:
            etxt = 'Unhandled message -- missing @type with %s.' % wc
            logging.warning(etxt)
            self.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
        return handled

    async def run(self):
        logging.info('Agent started.')
        try:
            while True:
                try:
                    wc = await self.trans.receive()
                    if wc:
                        self.handle_msg(wc)
                    else:
                        await asyncio.sleep(2.0)
                except KeyboardInterrupt:
                    return
                except json.decoder.JSONDecodeError as e:
                    self.trans.send(handler_common.problem_report(wc, str(e)), wc.sender, wc.in_reply_to, wc.subject)
                except:
                    log_helpers.log_exception()
        finally:
            logging.info('Agent stopped.')

async def main():
    agent = Agent()
    agent.configure()
    await agent.open_wallet()
    await agent.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('')
