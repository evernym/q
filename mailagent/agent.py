#!/usr/bin/env python

# '''An agent that interacts by SMTP.'''

import os
import sys
import time
import mail_transport

class Agent():

    def __init__(self, cfg=None, transport=None):
        self.cfg = cfg
        if not transport:
            transport = mail_transport.MailTransport(cfg)
        self.trans = transport

    def process_message(self, msg):
        sender_key, plaintext = self.decrypt(msg)
        if plaintext:
            typ = plaintext.get_type()
            if typ == 'ping':
                self.handle_ping()
            else:
                raise Exception('Unkonwn message type %s' % typ)

    def fetch_message(self):
        return self.trans.receive()

    def run(self):
        while True:
            try:
                msg = self.fetch_message()
                if msg:
                    self.process_message(msg)
                else:
                    time.sleep(1000)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                traceback.print_exc()

def _get_cfg_from_cmdline():
    import argparse
    parser = argparse.ArgumentParser(description="Run a Hyperledger Indy agent that communicates by email.")
    parser.add_argument("-s", "--statefolder", default="~/.mailagent", help="folder where state is stored")
    parser.add_argument("-l", "--loglevel", default="WARN", help="min level of messages written to log")
    args = parser.parse_args()
    args.statefolder = os.path.expanduser(args.statefolder)
    return args

def _get_config_from_file():
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = 'mailagent.cfg'
    if os.path.isfile(cfg_path):
        cfg.read(cfg_path)
    return cfg

def _configure():
    args = _get_cfg_from_cmdline()

    sf = args.statefolder
    if not os.path.exists(sf):
        os.makedirs(sf)
    os.chdir(sf)

    cfg = _get_config_from_file()

    ll = ('DIWEC'.index(args.loglevel[0].upper()) + 1) * 10
    if ll <= 0:
        try:
            ll = int(args.loglevel)
        except:
            sys.exit('Unrecognized loglevel %s.' % args.loglevel)

    import logging
    logging.basicConfig(
        filename=os.path.join('mailagent.log'),
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=ll)

    return cfg

if __name__ == '__main__':
    cfg = _configure()
    agent = Agent(cfg)
    agent.run()
