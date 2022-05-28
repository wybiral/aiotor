'''
Example of creating an onion service mapping to a local port. By default onions
are configured to randomly generate the id unless you specify your own key.
'''

import aiotor
import asyncio
import sys

async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = aiotor.Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # create an onion
    onion = aiotor.onions.Onion()
    # map port 80 on the onion to localhost:8000
    onion.ports[80] = 'localhost:8000'
    print('adding onion...')
    # start serving the onion and wait for publication
    await c.onions.add(onion, wait=True)
    print('serving {} at {}.onion'.format(onion.ports[80], onion.id))
    # run until terminated
    while True:
        await asyncio.sleep(1)

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())