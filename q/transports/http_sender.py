import aiohttp
import re

EXAMPLE = 'https://user:pass@x.com/abc'
_PAT = re.compile('https?://.+$')
_BASIC_AUTH_PAT = re.compile('https?://(?:([^/:]+):([^/@]*)@)?.+$')


def match(uri):
    return bool(_PAT.match(uri))


def strip_basic_auth_from_uri(uri):
    # uri is passed to each Sender so it can extract authentication details or
    # similar.
    m = _BASIC_AUTH_PAT.match(uri)
    if m:
        return m.group(1), m.group(2), uri[:m.start(1)] + uri[m.end(2):]
    return None, None, uri


class Sender:
    async def send(self, payload, uri, *args):
        user, password, rest = strip_basic_auth_from_uri(uri)
        if user or password:
            auth = aiohttp.BasicAuth(login=user, password=password)
        else:
            auth = None
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(uri, data=payload, headers={
                    'content-type': 'application/ssi-agent-wire'}) as resp:
                await resp.text()
                if resp.status >= 400:
                    raise RuntimeError('HTTP request returned status code %d.' % resp.status)
                return resp.headers.get('location') if resp.status >= 300 else None
