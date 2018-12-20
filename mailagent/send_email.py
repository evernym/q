# Python code to illustrate Sending mail with attachments
# from your Gmail account

# libraries to be imported
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import handler_common

_subject_redundant_prefix_pat = re.compile('(i?)(re|fwd):.*')

def send(senderEmail, senderPwd, dest, fileName):
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
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication (If you use your personal email, use your personal password instread of 'I only talk via email!')
    s.login(senderEmail, senderPwd)

    # sending the mail
    s.sendmail(senderEmail, dest, m.as_string())

    # terminating the session
    s.quit()


#First and Second parameters are the sender email/password.  You can use your personal email/password here if you would like
#If you decide to use your personal email, make sure your two factor authentication is disabled
send('indyagent1@gmail.com', 'I 0nly talk via email!', 'indyagent1@gmail.com', 'testFileToSend.json')