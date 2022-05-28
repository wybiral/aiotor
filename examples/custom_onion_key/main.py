import aiotor
from aiotor.onions import Onion
import asyncio
from cryptography.hazmat.primitives.asymmetric import ed25519
import sys

async def main():
    # connect to tor controller and authenticate
    # 9151 is Tor Browser control port
    c = aiotor.Controller(host='127.0.0.1', port=9151)
    await c.connect()
    await c.authenticate()
    # generate new ed25519 private key
    key = ed25519.Ed25519PrivateKey.generate()
    # create onion from user-supplied private key
    onion = Onion.from_key(key)
    # print calculated onion id
    print('calculated id: ' + onion.id)
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