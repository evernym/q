# Python code to illustrate Sending mail with json-format attachments
# from your Gmail account

# libraries to be imported
import smtplib
import os
from os.path import expanduser

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send(senderEmail, senderPwd, server, port, dest, fileName, userInput):
    userInput = int(userInput)
    filename = fileName
    attachment = open(filename, "rb")

    # instance of MIMEMultipart
    m = MIMEMultipart()

    if userInput == 1:
        # attach the body with the msg instance
        m.attach(MIMEText('See attached file.', 'plain'))

        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')

        # To change the payload into encoded form
        p.set_payload((attachment).read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header('Content-Disposition', "attachment; filename=msg.ap")

        # attach the instance 'p' to instance 'msg'
        m.attach(p)

    elif userInput == 2:
        # attach the body with the msg instance
        body = '{"@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/tictactoe/1.0/move", "@id": "518be002-de8e-456e-b3d5-8fe472477a86", "ill_be": "X", "moves": ["X:B2"],"comment_ltxt": "Let\'s play tic-tac-to. I\'ll be X. I pick cell B2."}'
        m.attach(MIMEText(body, 'plain'))

    else:
        raise Exception("Wrong Input")

    # storing the senders email address.
    m['From'] = senderEmail  # TODO: get from config

    # storing the receivers email address
    m['To'] = dest

    # storing the subject
    m['Subject'] = 'temp'

    # creates SMTP session
    s = smtplib.SMTP(server, port)

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
    parser.add_argument("--ll", metavar='LVL', default="DEBUG", help="log level (default=INFO)")
    args = parser.parse_args()
    return args

def _get_config_from_file():
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = home+'/.mailagent/config.ini'
    if os.path.isfile(cfg_path):
        cfg.read(home+'/.mailagent/config.ini')
    return cfg

def _apply_cfg(cfg, section, defaults):
    x = defaults
    if cfg and (cfg[section]):
        src = cfg[section]
        for key in src:
            x[key] = src[key]
    return x

_default_smtp_cfg = {
    'server': 'smtp.gmail.com',
    'username': 'your email',
    'password': 'find the password from the config file',
    'port': '587'
}

print(os.getcwd())
home = expanduser("~")
args = _get_config_from_cmdline()
cfg = _get_config_from_file()
smtp_cfg = _apply_cfg(cfg, 'smtp2', _default_smtp_cfg)

# This is to send email to the agent.  Hence,
# You can use your personal email
print(os.getcwd())
userInput = input("Enter 1 if you want to test sending msg via attached file.  Enter 2 if you want to send via email body: ")
send(smtp_cfg['username'], smtp_cfg['password'], smtp_cfg['server'], smtp_cfg['port'], 'indyagent1@gmail.com', '../mailagent/testFileToSend.json', userInput)