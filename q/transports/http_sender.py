import aiohttp
import re

EXAMPLE = 'https://x.com/abc'
_PAT = re.compile('https?://.+$')


def match(uri):
    return bool(_PAT.match(uri))


class Sender:
    def __init__(self):
        pass

    async def send(self, payload, endpoint, *args):
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data=payload, headers={
                    'content-type': 'application/ssi-agent-wire'}) as resp:
                await resp.text()
                if resp.status >= 400:
                    raise RuntimeError('HTTP request returned status code %d.' % resp.status)
                return resp.headers.get('location') if resp.status >= 300 else None
