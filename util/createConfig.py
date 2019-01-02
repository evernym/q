import configparser
from os.path import expanduser
home = expanduser("~")
cfg = configparser.ConfigParser()
cfg['imap'] = {
    'server': 'imap.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'Use password for indyagent imap',
    'ssl': '1',
    'port': '993'
}

cfg['smtp'] = {
    'server': 'smtp.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'Use password for indyagent smtp',
    'port': '587'
}

cfg['smtp2'] = {
    'server': 'smtp.gmail.com',
    'username': 'User your own email for testing',
    'password': 'Use your email password for testing',
    'port': '587'
}
with open(home+'/.mailagent/config.ini', 'w') as f:
    cfg.write(f)