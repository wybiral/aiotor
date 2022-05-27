import aiotor
import asyncio
import sys

# event handler to display bandwidth usage
async def bw_event(e):
    print('Bandwidth: read={}, written={}'.format(e.read, e.written))

# event handler to display circuit changes
async def circ_event(e):
    print('Circuit: id={}, status={}, path={}'.format(e.id, e.status, e.path))

async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = aiotor.Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # listen for bandwidth update event
    await c.events.on('BW', bw_event)
    # listen for circuit update event
    await c.events.on('CIRC', circ_event)
    # run until terminated
    while True:
        await asyncio.sleep(1)

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())