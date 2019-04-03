#!/usr/bin/env python

# '''A SSI agent that interacts by email.'''

import logging
import os
import sys
import time
import json
import datetime
import asyncio

import log_helpers
import mail_transport
import handlers
import handler_common
from indy import crypto, did, wallet

class Agent():

    def __init__(self, cfg=None, transport=None, securemsg=None):
        self.cfg = cfg
        self.securemsg = securemsg
        if not transport:
            transport = mail_transport.MailTransport(cfg)
        self.trans = transport

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
            print("handlers.HANDLERS_BY_MSG_TYPE is:  ")
            print(candidates)
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

    def fetch_msg(self):
        return self.trans.receive()

    async def run(self):
        logging.info('Agent started.')
        try:
            while True:
                try:
                    wc = self.fetch_msg()
                    if wc == "test":
                        await wallet.close_wallet(securemsg.wallet_handle)
                        client = "test"
                        securemsg.wallet_config = '{"id": "%s-wallet"}' % client
                        securemsg.wallet_credentials = '{"key": "%s-wallet-key"}' % client
                        securemsg.wallet_handle = await wallet.open_wallet(securemsg.wallet_config, securemsg.wallet_credentials)

                        print('wallet = %s' % securemsg.wallet_handle)

                        meta = await did.list_my_dids_with_meta(securemsg.wallet_handle)
                        res = json.loads(meta)

                        securemsg.my_did = res[0]["did"]
                        securemsg.my_vk = res[0]["verkey"]

                    elif wc:
                        self.handle_msg(wc)
                    else:
                        time.sleep(2.0)
                except KeyboardInterrupt:
                    sys.exit(0)
                except json.decoder.JSONDecodeError as e:
                    agent.trans.send(handler_common.problem_report(wc, str(e)), wc.sender, wc.in_reply_to, wc.subject)
                except:
                    log_helpers.log_exception()
        finally:
            logging.info('Agent stopped.')

class SecureMsg():
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
#
    def build_json(self):
        did_vk = {}
        did_vk["did"] = self.my_did
        did_vk["my_vk"] = self.my_vk
        return json.dumps(did_vk)

    async def init(self):
        me = 'TestAgent'.strip()
        self.wallet_config = '{"id": "%s-wallet"}' % me
        self.wallet_credentials = '{"key": "%s-wallet-key"}' % me

        try:
            await wallet.create_wallet(self.wallet_config, self.wallet_credentials)
        except:
            pass
        self.wallet_handle = await wallet.open_wallet(self.wallet_config, self.wallet_credentials)
        print('wallet = %s' % self.wallet_handle)

        (self.my_did, self.my_vk) = await did.create_and_store_my_did(self.wallet_handle, "{}")
        print('my_did and verkey = %s %s' % (self.my_did, self.my_vk))

        self.their = input("Other party's DID and verkey? ").strip().split(' ')
        self.their_vk = self.their[1]
        return self.wallet_handle, self.my_did, self.my_vk, self.their[0], self.their[1]

    def __init__(self):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.init())
            time.sleep(1)  # waiting for libindy thread complete
        except KeyboardInterrupt:
            print('')

def _get_config_from_cmdline():
    import argparse
    parser = argparse.ArgumentParser(description="Run a Hyperledger Indy agent that communicates by email.")
    parser.add_argument("--sf", metavar='FOLDER', default="~/.mailagent", help="folder where state is stored (default=~/.mailagent)")
    parser.add_argument("--ll", metavar='LVL', default="DEBUG", help="log level (default=INFO)")
    args = parser.parse_args()
    args.sf = os.path.expanduser(args.sf)
    return args

def _get_config_from_file():
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = 'config.ini'
    if os.path.isfile(cfg_path):
        cfg.read('config.ini')
    return cfg

def _use_statefolder(args):
    if not os.path.exists(args.sf):
        os.makedirs(args.sf)
    os.chdir(args.sf)

def _get_loglevel(args):
    ll = ('DIWEC'.index(args.ll[0].upper()) + 1) * 10
    if ll <= 0:
        try:
            ll = int(args.loglevel)
        except:
            sys.exit('Unrecognized loglevel %s.' % args.loglevel)
    return ll

def _start_logging(ll):
    logging.basicConfig(
        filename='mailagent.log',
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=ll)

def _configure():
    args = _get_config_from_cmdline()
    _use_statefolder(args)
    cfg = _get_config_from_file()
    ll = _get_loglevel(args)
    _start_logging(ll)
    return cfg

if __name__ == '__main__':
    cfg = _configure()
    securemsg = SecureMsg()
    agent = Agent(cfg, securemsg=securemsg)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.run())
    # agent.run()
