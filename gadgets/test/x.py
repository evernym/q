import asyncio
import aiohttp
from aiohttp import web
from multidict import MultiDict
import logging
import random

post_body_signal = asyncio.Event()
post_body = None

async def accept_post(request):
    global post_body
    global post_body_signal
    logging.info('about to await POST')
    post_body = await request.content.read()
    logging.info('responding to POST')
    resp = web.Response(text="202 OK", headers=MultiDict({"Content-Type": "text/plain"}))
    resp.set_status(202)
    logging.info('about to raise post_body_signal')
    post_body_signal.set()
    return resp

async def web_server_port():
    post_body = None
    post_body_signal.clear()
    app = web.Application()
    app.add_routes([web.post('/', accept_post)])
    runner = web.AppRunner(app)
    logging.info('about to await setup of web server')
    await runner.setup()
    port = random.randint(10000, 65000)
    site = web.TCPSite(runner, 'localhost', port)
    logging.info('about to await start of web server on port %d' % port)
    await site.start()
    logging.info('yielding web server on port %d' % port)
    return (port, runner)

async def post_main(port):
    async with aiohttp.ClientSession() as session:
        headers = {
            'content-type': 'application/ssi-agent-wire'
        }
        async with session.post("http://localhost:%d" % port, data="hello", headers=headers) as resp:
            if resp.status != 202:
                print(resp.status)
                print(await resp.text())

async def main():
    try:
        port, runner = await web_server_port()
        main = asyncio.create_task(post_main(port))
        global post_body_signal
        await post_body_signal.wait()
    finally:
        logging.info('about to clean up web server')
        await runner.cleanup()

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=0)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except:
        pass
    loop.close()