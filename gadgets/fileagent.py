#!/usr/bin/env python

# '''An SSI agent that interacts through the file system.'''

import os
import sys
import time
import json
import datetime
import asyncio
import configargparse
import logging

import baseagent
import file_transport
import handlers
import handler_common

from indy import crypto, did, wallet

class Agent(baseagent.Agent):

    def __init__(self):
        super().__init__()
        self.queue_dir = None

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
                agent.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
            else:
                logging.debug('Handled message of @type %s.' % typ)
        else:
            etxt = 'Unhandled message -- missing @type with %s.' % wc
            logging.warning(etxt)
            agent.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
        return handled

    async def fetch_msg(self):
        return await self.trans.receive()

    async def run(self):
        logging.info('Agent started.')
        try:
            while True:
                try:
                    wc = await self.fetch_msg()
                    if wc == "test":
                        await wallet.close_wallet(self.wallet_handle)
                        client = "test"
                        self.wallet_config = '{"id": "%s-wallet"}' % client
                        self.wallet_credentials = '{"key": "%s-wallet-key"}' % client
                        self.wallet_handle = await wallet.open_wallet(securemsg.wallet_config, securemsg.wallet_credentials)

                        print('wallet = %s' % self.wallet_handle)

                        meta = await did.list_my_dids_with_meta(self.wallet_handle)
                        res = json.loads(meta)

                        self.my_did = res[0]["did"]
                        self.my_vk = res[0]["verkey"]

                    elif wc:
                        self.handle_msg(wc)
                    else:
                        await asyncio.sleep(2.0)
                except KeyboardInterrupt:
                    sys.exit(0)
                except json.decoder.JSONDecodeError as e:
                    agent.trans.send(handler_common.problem_report(wc, str(e)), wc.sender, wc.in_reply_to, wc.subject)
                except:
                    agent_common.log_exception()
        finally:
            await logging.info('Agent stopped.')

    async def encryptMsg(self, msg):
        with open('plaintext.txt', 'w') as f:
            f.write(msg)
        with open('plaintext.txt', 'rb') as f:
            msg = f.read()
        encrypted = await crypto.auth_crypt(self.wallet_handle, self.my_vk, self.their_vk, msg)
        return encrypted

    async def decryptMsg(self, encrypted):
        decrypted = await crypto.auth_decrypt(self.wallet_handle, self.my_vk, encrypted)
        return (decrypted)

    def build_json(self):
        did_vk = {}
        did_vk["did"] = self.my_did
        did_vk["my_vk"] = self.my_vk
        return json.dumps(did_vk)

def _use_statefolder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    os.chdir(folder)

def _get_loglevel(args):
    ll = ('DIWEC'.index(args.loglevel[0].upper()) + 1) * 10
    if ll <= 0:
        try:
            ll = int(args.loglevel)
        except:
            sys.exit('Unrecognized loglevel %s.' % args.loglevel)
    return ll

def _start_logging(ll):
    logging.basicConfig(
        filename=MY_MODULE_NAME + '.log',
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=ll)

async def main():
    agent = Agent()
    args = agent.configure()
    await agent.open_wallet()
    await agent.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('')
