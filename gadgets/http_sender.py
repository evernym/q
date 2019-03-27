import aiohttp
import re

PAT = re.compile('https?://.+$')

class HttpSender:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    async def send(self, payload, *args):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, data=payload, headers={
                    'content-type': 'application/ssi-agent-wire'}) as resp:
                await resp.text()
                if resp.status >= 400:
                    raise RuntimeError('HTTP request returned status code %d.' % resp.status)
                return resp.headers.get('location') if resp.status >= 300 else None
