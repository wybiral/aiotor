'''
Example of sending signals to Tor controller.
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
    # send NEWNYM signal to make Tor use fresh circuits for future
    # connections instead of reusing existing ones.
    await c.signal('NEWNYM')

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())