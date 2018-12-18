import os
import time
import sys
import email
import getpass, imaplib
import json
import re
sys.path.append('../')
from mailagent.mail_transport import MailTransport

'''An agent that interacts by SMTP.'''

class Agent():

    def __init__(self, cfg=None, transport=None):
        self.cfg = cfg
        if not transport:
            transport = MailTransport(cfg)
        self.trans = transport
        self.imapSession = imaplib.IMAP4_SSL(self.trans.imap_cfg['server'])
        self.imapUsr = self.trans.imap_cfg['username']
        self.imapPwd = self.trans.imap_cfg['password']


    def process_message(self, msg):
        # sender_key, plaintext = self.decrypt(msg)
        # if plaintext:
        if msg:
            typ = msg.get_type()
            if typ == 'ping':
                self.handle_ping()
            else:
                raise Exception('Unkonwn message type %s' % typ)

    def find_between(self, s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.rindex(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def fetch_message(self):
        msg = []
        try:
            typ, accountDetails = self.imapSession.login(self.imapUsr, self.imapPwd)
            time.sleep(5)
            if typ != 'OK':
                print
                'Not able to sign in!'
                raise

            # imapSession.select('[Gmail]/All Mail')
            self.imapSession.select('Inbox')
            # type, data = self.imapSession.select('Inbox')
            typ, data = self.imapSession.search(None, '(UNSEEN)')
            if typ != 'OK':
                print
                'Error searching Inbox.'
                raise

            for msgId in data[0].split():
                typ, messageParts = self.imapSession.fetch(msgId, '(RFC822)')
                if typ != 'OK':
                    print
                    'Error fetching mail.'
                    raise

                emailBody = messageParts[0][1]
                # try:
                print("email body Type is: ", type(emailBody))
                emailBody = emailBody.decode("utf-8")
                print("new email body Type is: ", type(emailBody))
                mail = email.message_from_string(emailBody)
                msgPayload = mail._payload[0]._payload
                mainMsg = msgPayload[msgPayload.find("{"):msgPayload.find("}")+1]
                jsonMsgPayload = json.loads(mainMsg)
                msg.append(jsonMsgPayload)
                print(jsonMsgPayload)
                # except Exception as e:
                #     print(e)
            print(msg)
            return msg
        except Exception as e:
            print(e)
            'Not able to download all attachments.'

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

def get_cfg_from_cmdline():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--statefolder" ,default="~/.mailagent", help="folder where state is stored")
    parser.add_argument("-l", "--loglevel", default="WARN", help="min level of messages written to log")
    args = parser.parse_args()
    args.statefolder = os.path.expanduser(args.statefolder)
    return args

def get_config_from_file():
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = 'mailagent.cfg'
    if os.path.isfile(cfg_path):
        cfg.read(cfg_path)
    return cfg

def configure():
    args = get_cfg_from_cmdline()

    sf = args.statefolder
    if not os.path.exists(sf):
        os.makedirs(sf)
    os.chdir(sf)

    cfg = get_config_from_file()
    return cfg

if __name__ == '__main__':
    cfg = configure()
    agent = Agent(cfg)
    agent.run()
