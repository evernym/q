import re
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

PAT = re.compile('^smtp://([A-Za-z0-9][^@:]*):([^@]*)@([^:/]+)(?::([0-9]{1,5}))?[?](.{14,})$')
FROM_PAT = re.compile('from=((?:[A-Za-z0-9][^=&@]*)@(?:[^.=&]+)[.](?:[^.=&]+[^=&]*))')
TO_PAT = re.compile('to=((?:[A-Za-z0-9][^=&@]*)@(?:[^.=&]+)[.](?:[^.=&]+[^=&]*))')

EXAMPLE = 'smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com'


class Sender:

    def __init__(self, endpoint):
        m = PAT.match(endpoint)
        if not m:
            raise ValueError('Expected an SMTP endpoint that matches regex: %s' % PAT.pattern)
        self.user = m.group(1)
        self.password = m.group(2)
        self.server = m.group(3)
        self.port = m.group(4)
        self.port = int(self.port) if self.port else 587
        query = m.group(5)
        m = FROM_PAT.search(query)
        if m:
            self.sender = m.group(1)
        else:
            raise ValueError('Expected "from=<addr>" in query string.')
        m = TO_PAT.search(query)
        if m:
            self.to = m.group(1)
        else:
            raise ValueError('Expected "to=<addr>" in query string.')

    async def send(self, payload):
        def do_send():
            m = MIMEMultipart()
            m['From'] = 'smtp_sender'
            m['To'] = self.to
            subj = 'DIDComm message'
            m['Subject'] = subj
            m.attach(MIMEText('See attached file.', 'plain'))
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(payload)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', "attachment; filename=msg.dp")
            m.attach(p)
            s = smtplib.SMTP(self.server, self.port)
            s.starttls()
            s.login(self.user, self.password)
            s.sendmail(self.sender, self.to, m.as_string())
            s.quit()

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, do_send)
        return await future
