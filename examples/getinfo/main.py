from aiotor.controller import Controller
import asyncio
import sys

async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # get tor version
    info = await c.getinfo('version')
    print('Tor version:', info['version'])
    # get current circuits
    info = await c.getinfo('circuit-status')
    print('\nCircuits:')
    print(info['circuit-status'])

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())