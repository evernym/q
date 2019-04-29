import re
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

EXAMPLES = 'mailto:alice@example.com?via=user:pass@mail.my.org:587'
_PAT = re.compile(r'mailto:([^@]+@[^?]+)[?](.*?)via=([^:]+):([^@]*)@([^:]+)(?::([1-9][0-9]{0,4}))?(.*)')


def match(uri):
    return bool(_PAT.match(uri))


def split_uri(uri):
    m = _PAT.match(uri)
    if not m:
        raise ValueError('Expected an SMTP endpoint that matches regex: %s' % _PAT.pattern)
    user = m.group(3)
    password = m.group(4)
    server = m.group(5)
    port = m.group(6)
    port = int(port) if port else 587
    headers = (m.group(2) + m.group(7)).split('&')
    headers = [x.split('=') for x in headers]
    uri = m.group(1)
    return uri, user, password, server, port, headers

class Sender:

    async def send(self, payload, mailto_uri):
        email_addr, user, password, server, port, headers = split_uri(mailto_uri)
        def do_send():
            m = MIMEMultipart()
            # Put default values in email headers.
            m['From'] = 'smtp_sender@q'
            m['Subject'] = 'DIDComm message'
            # Now override headers with anything from the mailto URL.
            for header in headers:
                if len(header) == 2:
                    m[header[0]] = header[1]
            m['To'] = email_addr
            m.attach(MIMEText('See attached file.', 'plain'))
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(payload)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', "attachment; filename=msg.dp")
            m.attach(p)
            s = smtplib.SMTP(server, port)
            s.starttls()
            s.login(user, password)
            s.sendmail(m['From'], email_addr, m.as_string())
            s.quit()

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, do_send)
        return await future
