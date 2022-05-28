'''
Example of running a basic HTTP server as an onion service and then mapping an
address to that onion. All requests made on this Tor instance should map
testing.com to the local "Hello world!" server.
'''

import aiotor
import asyncio
import sys

ADDRESS = 'testing.com'

# handle http requests
async def handler(r, w):
    # consume headers
    while True:
        line = await r.readline()
        if not line or line == b'\r\n':
            break
    w.write(b'HTTP/1.1 200 OK\r\n')
    w.write(b'Content-Type: text/html; charset=utf-8\r\n')
    w.write(b'\r\n')
    w.write(b'<html><h1>Hello world!</h1></html>')
    await w.drain()
    w.close()


async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = aiotor.Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # create an onion
    onion = aiotor.onions.Onion()
    # map port 80 on the onion to 127.0.0.1:8666
    onion.ports[80] = '127.0.0.1:8666'
    print('adding onion...')
    # start serving the onion and wait for publication
    await c.onions.add(onion, wait=True)
    print('added {}.onion'.format(onion.id))
    # map testing.com to the onion service address
    await c.map_address(ADDRESS, onion.id + '.onion')
    print('mapped {} to {}.onion'.format(ADDRESS, onion.id))
    # run until terminated
    s = await asyncio.start_server(handler, '127.0.0.1', 8666)
    await s.serve_forever()

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())