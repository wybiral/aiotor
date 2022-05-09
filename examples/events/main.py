from aiotor.controller import Controller
import asyncio
import sys

# event handler to display bandwidth usage
async def bw_event(event):
    print('Bandwidth: read={}, written={}'.format(event.read, event.written))

async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # listen for bandwidth events using bw_event handler
    await c.events.on('BW', bw_event)
    # run until terminated
    while True:
        await asyncio.sleep(1)

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())