'''An agent that interacts only by SMTP.'''

import time, traceback, sys

class Agent():
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
                    time.sleep(250)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                traceback.print_exc()

if __name__ == '__main__':
    # Create an agent and run it forever.
    agent = Agent()
    agent.run()
