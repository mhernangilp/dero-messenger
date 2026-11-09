import pytest
from cryptography.exceptions import InvalidSignature, InvalidTag

from dero_messenger import crypto


def test_x25519_hkdf_direction_and_transcript():
    a, ap = crypto.ephemeral()
    b, bp = crypto.ephemeral()
    first, second = crypto.derive(a, bp, b"transcript")
    assert (first, second) == crypto.derive(b, ap, b"transcript")
    assert first != second
    assert len(first) == len(second) == 32
    assert crypto.derive(a, bp, b"different") != (first, second)
    with pytest.raises(ValueError):
        crypto.derive(a, bytes(32), b"null key")


def test_aead_tampering_nonce_aad_and_wrong_key():
    key = bytes(range(32))
    ciphertext = crypto.encrypt(key, 0, b"message", b"header")
    assert crypto.decrypt(key, 0, ciphertext, b"header") == b"message"
    assert ciphertext != crypto.encrypt(key, 1, b"message", b"header")
    for bad_key, counter, data, aad in [
        (bytes(32), 0, ciphertext, b"header"),
        (key, 1, ciphertext, b"header"),
        (key, 0, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]), b"header"),
        (key, 0, ciphertext, b"modified"),
    ]:
        with pytest.raises(InvalidTag):
            crypto.decrypt(bad_key, counter, data, aad)


def test_identity_signature():
    secret = crypto.identity()
    signature = crypto.sign(secret, b"transcript")
    crypto.verify(crypto.public(secret), signature, b"transcript")
    with pytest.raises(InvalidSignature):
        crypto.verify(crypto.public(secret), signature, b"substituted")
