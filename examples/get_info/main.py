'''
Example of querying the Tor controller using get_info()
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
    # get tor version
    version = await c.get_info('version')
    print('Tor version:', version)
    # get current circuits
    circuits = await c.get_info('circuit-status')
    print('\nCircuits:')
    print(circuits)

# ugh, windows
if sys.platform == 'win32':
    elp = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(elp)

asyncio.run(main())