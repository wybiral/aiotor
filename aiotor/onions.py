import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib

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

