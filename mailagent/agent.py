'''An agent that interacts by SMTP.'''

class Agent():

    def __init__(self, cfg=None, transport=None):
        self.cfg = cfg
        if not transport:
            transport = MailTransport(cfg)
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
        # Put some code here that checks our inbox. If we have
        # something, return topmost (oldest) item. If not, return
        # None.
        return None

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
    parser.add_argument("-s", "--statefolder", default="~/.mailagent", help="folder where state is stored")
    parser.add_argument("-l", "--loglevel", default="WARN", help="min level of messages written to log")
    parser.parse_args()
    args.statefolder = os.path.expanduser(args.statefolder)

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
