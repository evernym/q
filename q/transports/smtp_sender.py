import re
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

EXAMPLES = 'mailto:alice@example.com?via=user:pass@mail.my.org:2345'
_PAT = re.compile(r'mailto:([^@]+@[^@?]+)[?](.*?)via=([^:]+):([^@]*)@([^:]+)(?::([1-9][0-9]{3,4}))(.*)')
_VIA_PAT = re.compile(r'[?&]via=([^:]+):([^@]*)@([^:]+)(?::([1-9][0-9]{3,4}))')


def match(uri):
    return bool(_PAT.match(uri))


def purify_target(url):
    """
    Convert a url for this sender into just the portion needed to identify the target
    (removing info about the username, password, and smtp server).
    """
    m = _VIA_PAT.search(url)
    if m:
        return url[:m.span()[0]] + url[m.span()[1]:]


class Sender:

    def __init__(self, uri):
        m = _PAT.match(uri)
        if not m:
            raise ValueError('Expected an SMTP endpoint that matches regex: %s' % _PAT.pattern)
        self.user = m.group(3)
        self.password = m.group(4)
        self.server = m.group(5)
        self.port = m.group(6)
        self.port = int(self.port) if self.port else 587
        headers = (m.group(2) + m.group(7)).split('&')
        headers = [x.split('=') for x in headers]
        self.headers = headers

    async def send(self, payload, email_addr):
        def do_send():
            m = MIMEMultipart()
            # Put default values in email headers.
            m['From'] = 'smtp_sender@q'
            m['Subject'] = 'DIDComm message'
            # Now override headers with anything from the mailto URL.
            for header in self.headers:
                if len(header) == 2:
                    m[header[0]] = header[1]
            m['To'] = email_addr
            m.attach(MIMEText('See attached file.', 'plain'))
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(payload)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', "attachment; filename=msg.dp")
            m.attach(p)
            s = smtplib.SMTP(self.server, self.port)
            s.starttls()
            s.login(self.user, self.password)
            s.sendmail(m['From'], email_addr, m.as_string())
            s.quit()

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, do_send)
        return await future
