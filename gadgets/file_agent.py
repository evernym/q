#!/usr/bin/env python

# '''An SSI agent that interacts through the file system.'''

import aiologger
import os
import sys
import time
import json
import datetime
import asyncio
import configargparse

import agent_common
import file_transport
import handlers
import handler_common

from indy import crypto, did, wallet

logger = aiologger.Logger.with_default_handlers()

MY_MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
DEFAULT_FOLDER = '~/.' + MY_MODULE_NAME
DEFAULT_CONF_FILE = os.path.join(DEFAULT_FOLDER, 'conf')
DEFAULT_LOG_LEVEL = 'DEBUG' #good for development; switch to INFO for production

class Agent:

    def __init__(self, cfg):
        self.cfg = cfg
        os.makedirs('queue', exist_ok=True)
        self.trans = file_transport.FileTransport('queue', folder_is_destward=False)
        self.wallet_config = '{"id": "%s", "storage_config": {"path": "%s"}}' % (cfg.wallet, cfg.folder)
        self.wallet_credentials = '{"key": "%s"}' % cfg.p

    @property
    def wallet_folder(self):
        return os.path.join(self.cfg.folder, self.cfg.wallet)

    @property
    def wallet_file(self):
        return os.path.join(self.wallet_folder, 'sqlite.db')

    async def open_wallet(self):
        exists = os.path.isfile(self.wallet_file)
        if exists:
            if self.cfg.reset:
                os.path.unlink(self.wallet_file)
                exists = False
        if not exists:
            await wallet.create_wallet(self.wallet_config, self.wallet_credentials)
        self.wallet_handle = await wallet.open_wallet(self.wallet_config, self.wallet_credentials)

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
                await logger.warning(etxt)
                agent.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
            else:
                await logger.debug('Handled message of @type %s.' % typ)
        else:
            etxt = 'Unhandled message -- missing @type with %s.' % wc
            await logger.warning(etxt)
            agent.trans.send(handler_common.problem_report(wc, etxt), wc.sender, wc.in_reply_to, wc.subject)
        return handled

    async def fetch_msg(self):
        return self.trans.receive()

    async def run(self):
        await logger.info('Agent started.')
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
            await logger.info('Agent stopped.')

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
    logger.basicConfig(
        filename=MY_MODULE_NAME + '.log',
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=ll)

def _configure():
    # This config object allows overrides of config;
    # cmdline > env variable > config file > hard-coded.
    parser = configargparse.ArgumentParser(
        description="Run an agent that communicates via the file system.",
        default_config_files=[DEFAULT_CONF_FILE])
    parser.add_argument('-p', metavar='PHRASE', required=True, help="passphrase used to unlock wallet")
    parser.add_argument('-w', '--wallet', metavar='NAME', default='wallet', help='name of wallet to use')
    parser.add_argument('-r', '--reset', action='store_true', default=False, help='reset the wallet instead of keeping accumulated state')
    parser.add_argument('-l', '--loglevel', metavar='LVL', default=DEFAULT_LOG_LEVEL, help="log level (default=%s)" % DEFAULT_LOG_LEVEL)
    parser.add_argument('-f', '--folder', metavar='FOLDER', default=DEFAULT_FOLDER, help="folder where state is stored (default=%s)" % DEFAULT_FOLDER)
    args = parser.parse_args()
    args.folder = os.path.expanduser(args.folder)
    # Make current working directory the folder where agent persists state.
    _use_statefolder(args.folder)
    _start_logging(_get_loglevel(args))
    return args

async def main():
    cfg = _configure()
    agent = Agent(cfg)
    await agent.open_wallet()
    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())
