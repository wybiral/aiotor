import asyncio
import hashlib
import hmac
from os import urandom
from . import events
from .onions import Onion
from .textprotocol import parse, parse_keywords, TextProtocol

class Controller:

    def __init__(self, host='127.0.0.1', port=9051):
        self.host = host
        self.port = port
        self.events = events.Events(self)
        self.io = None
        self.auth = {
            'methods': [],
            'cookiefile': None
        }

    async def connect(self):
        ''' connect to tor controller '''
        r, w = await asyncio.open_connection(self.host, self.port)
        self.io = TextProtocol(r, w, event_queue=self.events.queue)
        self.__parse_protocolinfo(await self.io.cmd('PROTOCOLINFO 1'))

    def __parse_protocolinfo(self, resp):
        if resp['status'] != 250:
            raise Exception('Unable to connect')
        for line in resp['lines']:
            args, kwargs = parse(line)
            if args[0] == 'AUTH':
                self.auth['methods'] = kwargs['METHODS'].split(',')
                self.auth['cookiefile'] = kwargs.get('COOKIEFILE', None)

    async def authenticate(self, password=None):
        ''' authenticate using any available method '''
        methods = self.auth['methods']
        if 'NULL' in methods:
            resp = await self.__authenticate_none()
        elif 'HASHEDPASSWORD' and password is not None:
            resp = await self.__authenticate_password(password)
        elif 'SAFECOOKIE' in self.auth['methods'] and self.auth['cookiefile']:
            resp = await self.__authenticate_safecookie()
        elif 'COOKIE' in self.auth['methods'] and self.auth['cookiefile']:
            resp = await self.__authenticate_cookie()
        else:
            raise Exception('no authentication method available')
        if resp['status'] != 250:
            raise Exception('authentication failed')

    async def __authenticate_none(self):
        return await self.io.cmd('AUTHENTICATE')

    async def __authenticate_password(self, password):
        quoted = '"' + password + '"'
        return await self.io.cmd('AUTHENTICATE ' + quoted)

    async def __authenticate_safecookie(self):
        cookie = open(self.auth['cookiefile'], 'rb').read()
        # send client nonce
        client_nonce = urandom(32)
        challenge = 'AUTHCHALLENGE SAFECOOKIE ' + client_nonce.hex()
        resp = await self.io.cmd(challenge)
        args, kwargs = parse(resp['lines'][0])
        # authenticate server hash
        server_hash = bytes.fromhex(kwargs['SERVERHASH'])
        server_nonce = bytes.fromhex(kwargs['SERVERNONCE'])
        key = b'Tor safe cookie authentication server-to-controller hash'
        msg = cookie + client_nonce + server_nonce
        h = hmac.new(key, msg, hashlib.sha256).digest()
        if h != server_hash:
            raise Exception('invalid server hash')
        # construct client hash
        key = b'Tor safe cookie authentication controller-to-server hash'
        msg = cookie + client_nonce + server_nonce
        h = hmac.new(key, msg, hashlib.sha256).hexdigest()
        return await self.io.cmd('AUTHENTICATE ' + h)

    async def __authenticate_cookie(self):
        cookie = open(self.auth['cookiefile'], 'rb').read()
        return await self.io.cmd('AUTHENTICATE ' + cookie.hex())

    async def getinfo(self, key):
        resp = await self.io.cmd('GETINFO ' + key)
        if resp['status'] != 250:
            raise Exception('Request failed')
        text = ' '.join(resp['lines'])
        return parse_keywords(text)

    async def signal(self, signal):
        resp = await self.io.cmd('SIGNAL ' + signal)
        print(resp)
        if resp['status'] != 250:
            raise Exception('Request failed')

    async def add_onion(self, onion, wait=False):
        key_str = '{}:{}'.format(onion.key_type, onion.key)
        ports = onion.ports
        ports_str = ' '.join('Port={},{}'.format(k, ports[k]) for k in ports)
        resp = await self.io.cmd('ADD_ONION ' + key_str + ' ' + ports_str)
        if resp['status'] != 250:
            raise Exception('Request failed')
        args, kwargs = parse(' '.join(resp['lines']))
        onion.id = kwargs['ServiceID']
        if 'PrivateKey' in kwargs:
            key_type, key = kwargs['PrivateKey'].split(':', maxsplit=1)
            onion.key_type = key_type
            onion.key = key
        if wait:
            event = asyncio.Event()
            async def hs_desc(e):
                if e.address != onion.id:
                    return
                if e.action == 'UPLOADED':
                    event.set()
            await self.events.on('HS_DESC', hs_desc)
            await event.wait()
            await self.events.off('HS_DESC', hs_desc)
        return onion

    async def del_onion(self, onion):
        resp = await self.io.cmd('DEL_ONION ' + onion.id)
        if resp['status'] != 250:
            raise Exception('Request failed')