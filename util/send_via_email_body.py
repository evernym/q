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


#First and Second parameters are the sender email/password.  You can use your personal email/password here if you would like
#If you decide to use your personal email, make sure your two factor authentication is disabled
send('indyagent1@gmail.com', 'I 0nly talk via email!', 'indyagent1@gmail.com')