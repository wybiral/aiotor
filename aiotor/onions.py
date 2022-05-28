import asyncio
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib
from .textprotocol import parse

class Onions:

    def __init__(self, controller):
        self.controller = controller
        self.__onions = {}

    async def add(self, onion, wait=False):
        ''' add an Onion to the controller as an ephemeral onion service '''
        if onion.id in self.__onions:
            return
        controller = self.controller
        key_str = '{}:{}'.format(onion.key_type, onion.key)
        ports = onion.ports
        ports_str = ' '.join('Port={},{}'.format(k, ports[k]) for k in ports)
        cmd_str = 'ADD_ONION ' + key_str + ' ' + ports_str
        resp = await controller.io.cmd(cmd_str)
        if resp['status'] != 250:
            raise Exception('Request failed')
        args, kwargs = parse(' '.join(resp['lines']))
        onion.id = kwargs['ServiceID']
        if 'PrivateKey' in kwargs:
            key_type, key = kwargs['PrivateKey'].split(':', maxsplit=1)
            onion.key_type = key_type
            onion.key = key
        self.__onions[onion.id] = onion
        if wait:
            event = asyncio.Event()
            async def hs_desc(e):
                if e.address != onion.id:
                    return
                if e.action == 'UPLOADED':
                    event.set()
            await controller.events.add('HS_DESC', hs_desc)
            await event.wait()
            await controller.events.remove('HS_DESC', hs_desc)
        return onion

    async def remove(self, onion):
        ''' remove an Onion service from the controller '''
        controller = self.controller
        resp = await controller.io.cmd('DEL_ONION ' + onion.id)
        if resp['status'] != 250:
            raise Exception('Request failed')
        if onion.id in self.__onions:
            del self.__onions[onion.id]


class Onion:

    def __init__(self):
        self.key_type = 'NEW'
        self.key = 'BEST'
        self.id = None
        self.ports = {}

    @classmethod
    def random(cls):
        ''' generate new random Onion object '''
        private_key = ed25519.Ed25519PrivateKey.generate()
        return cls.from_key(private_key)

    @classmethod
    def from_key(cls, private_key):
        ''' create Onion object from existing ed25519 key '''
        onion = cls()
        onion.key_type = 'ED25519-V3'
        onion.key = format_key(private_key)
        onion.id = calculate_id(private_key.public_key())
        return onion


def format_key(private_key):
    ''' convert ed25519 key to Tor format '''
    b = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    h = hashlib.sha512()
    h.update(b[:32])
    p = list(h.digest())
    p[0] &= 248
    p[31] &= 127
    p[31] |= 64
    return base64.b64encode(bytes(p)).decode('utf8')

def calculate_id(public_key):
    ''' calculate onion service ID from ed25519 public key '''
    b = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    h = hashlib.sha3_256()
    h.update(b'.onion checksum')
    h.update(b)
    h.update(b'\x03')
    d = h.digest()
    c = d[:2]
    combined = b + c + b'\x03'
    service_id = base64.b32encode(combined)
    return service_id.decode('utf8').replace('=', '').lower()
