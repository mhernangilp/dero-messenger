"""Application cryptography, independent of wallet keys and transport."""

import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


def identity() -> bytes:
    return ed25519.Ed25519PrivateKey.generate().private_bytes_raw()


def public(secret: bytes) -> bytes:
    return ed25519.Ed25519PrivateKey.from_private_bytes(secret).public_key().public_bytes_raw()


def fingerprint(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()


def sign(secret: bytes, data: bytes) -> bytes:
    return ed25519.Ed25519PrivateKey.from_private_bytes(secret).sign(data)


def verify(key: bytes, signature: bytes, data: bytes) -> None:
    ed25519.Ed25519PublicKey.from_public_bytes(key).verify(signature, data)


def ephemeral() -> tuple[bytes, bytes]:
    key = x25519.X25519PrivateKey.generate()
    return key.private_bytes_raw(), key.public_key().public_bytes_raw()


def derive(secret: bytes, peer: bytes, transcript: bytes) -> tuple[bytes, bytes]:
    shared = x25519.X25519PrivateKey.from_private_bytes(secret).exchange(
        x25519.X25519PublicKey.from_public_bytes(peer)
    )
    material = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=hashlib.sha256(transcript).digest(),
        info=b"dero-chat/v1/A-to-B|B-to-A",
    ).derive(shared)
    return material[:32], material[32:]


def password_key(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < 12:
        raise ValueError("Use a passphrase of at least 12 characters")
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(passphrase.encode())


def seal(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def unseal(key: bytes, blob: bytes, aad: bytes) -> bytes:
    return AESGCM(key).decrypt(blob[:12], blob[12:], aad)


def encrypt(key: bytes, counter: int, plaintext: bytes, aad: bytes) -> bytes:
    return AESGCM(key).encrypt(counter.to_bytes(12, "big"), plaintext, aad)


def decrypt(key: bytes, counter: int, ciphertext: bytes, aad: bytes) -> bytes:
    return AESGCM(key).decrypt(counter.to_bytes(12, "big"), ciphertext, aad)
