import configparser
from os.path import expanduser
home = expanduser("~")
cfg = configparser.ConfigParser()
cfg['imap'] = {
    'server': 'imap.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'Use password for indyagent',
    'ssl': '1',
    'port': '993'
}

cfg['smtp'] = {
    'server': 'smtp.gmail.com',
    'username': 'Your email',
    'password': 'Your password',
    'port': '587'
}
with open(home+'/.mailagent/config.ini', 'w') as f:
    cfg.write(f)