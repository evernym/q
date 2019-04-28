import aiohttp
import re

EXAMPLE = 'https://user:pass@x.com/abc'
_PAT = re.compile('https?://.+$')
_BASIC_AUTH_PAT = re.compile('https?://(?:([^/:]+):([^/@]*)@)?.+$')


def match(uri):
    return bool(_PAT.match(uri))


class Sender:
    def __init__(self, uri):
        # uri is passed to each Sender so it can extract authentication details or
        # similar.
        m = _BASIC_AUTH_PAT.match(uri)
        if m:
            self.user = m.group(1)
            self.password = m.group(2)
        pass

    async def send(self, payload, endpoint, *args):
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data=payload, headers={
                    'content-type': 'application/ssi-agent-wire'}) as resp:
                await resp.text()
                if resp.status >= 400:
                    raise RuntimeError('HTTP request returned status code %d.' % resp.status)
                return resp.headers.get('location') if resp.status >= 300 else None
