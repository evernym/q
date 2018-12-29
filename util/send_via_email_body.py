# Python code to illustrate Sending json-format mail via email body
# from your Gmail account

# libraries to be imported
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(senderEmail, senderPwd, dest):
    # instance of MIMEMultipart
    m = MIMEMultipart()

    # storing the senders email address.
    m['From'] = senderEmail  # TODO: get from config

    # storing the receivers email address
    m['To'] = dest

    # storing the subject
    m['Subject'] = 'temp'

    # attach the body with the msg instance
    body = '{"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/tictactoe/1.0/move", "@id": "518be002-de8e-456e-b3d5-8fe472477a86", "ill_be": "X", "moves": ["X:B2"],"comment_ltxt": "Let\'s play tic-tac-to. I\'ll be X. I pick cell B2."}'
    m.attach(MIMEText(body, 'plain'))

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication (If you use your personal email, use your personal password instread of 'I only talk via email!')
    s.login(senderEmail, senderPwd)

    # sending the mail
    s.sendmail(senderEmail, dest, m.as_string())

    # terminating the session
    s.quit()


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

def _apply_cfg(cfg, section, defaults):
    x = defaults
    if cfg and (cfg[section]):
        src = cfg[section]
        for key in src:
            x[key] = src[key]
    return x

_default_smtp_cfg = {
    'server': 'smtp.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'find the password from the config file',
    'port': '587'
}

args = _get_config_from_cmdline()
_use_statefolder(args)
cfg = _get_config_from_file()
smtp_cfg = _apply_cfg(cfg, 'smtp', _default_smtp_cfg)

# This is to send email to the agent.  Hence,
# You can use your personal email
send(smtp_cfg['username'], smtp_cfg['password'], smtp_cfg['server'], smtp_cfg['port'], 'indyagent1@gmail.com', 'testFileToSend.json')