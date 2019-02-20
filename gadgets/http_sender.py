import requests
import re

PAT = re.compile('https?://.+$')

class HttpSender:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def send(self, payload, *args):
        r = requests.post(self.endpoint, headers={
            'content-type': 'application/ssi-agent-wire',
            'content-length': str(len(payload))}, data=payload)
        if r.status_code >= 400:
            raise RuntimeError('HTTP request returned status code %d.' % r.status_code)
        # If there's a location header, return the redirected URI as the ID of the sent message.
        return r.headers.get('location') if r.status_code >= 300 else None
