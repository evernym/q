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

def send(senderEmail, senderPwd, server, port, dest, fileName):
    filename = fileName
    attachment = open(filename, "rb")

    # instance of MIMEMultipart
    m = MIMEMultipart()

    # storing the senders email address.
    m['From'] = senderEmail  # TODO: get from config

    # storing the receivers email address
    m['To'] = dest

    # storing the subject
    m['Subject'] = 'temp'

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

home = expanduser("~")
args = _get_config_from_cmdline()
cfg = _get_config_from_file()
smtp_cfg = _apply_cfg(cfg, 'smtp', _default_smtp_cfg)

# This is to send email to the agent.  Hence,
# You can use your personal email
send(smtp_cfg['username'], smtp_cfg['password'], smtp_cfg['server'], smtp_cfg['port'], 'indyagent1@gmail.com', '../mailagent/testFileToSend.json')