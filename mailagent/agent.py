#!/usr/bin/env python

# '''A SSI agent that interacts by email.'''

import logging
import os
import sys
import time
import json

import agent_common
import mail_transport
import plugins

class Agent():

    def __init__(self, cfg=None, transport=None):
        self.cfg = cfg
        if not transport:
            transport = mail_transport.MailTransport(cfg)
        self.trans = transport

    def handle_msg(self, wc):
        handled = False
        wc.obj = json.loads(wc.msg)
        typ = wc.obj['@type']
        if typ:
            handlers = plugins.BY_TYPE.get(typ)
            if handlers:
                for handler in handlers:
                    if handler.handle(wc, self):
                        handled = True
                        break
            if not handled:
                logging.warning('Unhandled message -- unsupported @type %s with %s.' % (typ, wc))
        else:
            logging.warning('Unhandled message -- missing @type with %s.' % wc)
        return handled

    def fetch_msg(self):
        return self.trans.receive()

    def run(self):
        logging.info('Agent started.')
        try:
            while True:
                try:
                    wc = self.fetch_msg()
                    if wc:
                        self.handle_msg(wc)
                    else:
                        time.sleep(30.0)
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    agent_common.log_exception()
        finally:
            logging.info('Agent stopped.')

def _get_config_from_cmdline():
    import argparse
    parser = argparse.ArgumentParser(description="Run a Hyperledger Indy agent that communicates by email.")
    parser.add_argument("--sf", metavar='FOLDER', default="~/.mailagent", help="folder where state is stored (default=~/.mailagent)")
    parser.add_argument("--ll", metavar='LVL', default="INFO", help="log level (default=INFO)")
    args = parser.parse_args()
    args.sf = os.path.expanduser(args.sf)
    return args

def _get_config_from_file():
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = 'mailagent.cfg'
    if os.path.isfile(cfg_path):
        cfg.read(cfg_path)
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

def _load_plugins():
    plugins.load()

def _configure():
    args = _get_config_from_cmdline()
    _use_statefolder(args)
    cfg = _get_config_from_file()
    ll = _get_loglevel(args)
    _start_logging(ll)
    plugins.load()
    return cfg

if __name__ == '__main__':
    cfg = _configure()
    agent = Agent(cfg)
    agent.run()
