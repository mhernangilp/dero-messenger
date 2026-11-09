import os

import pytest
from cryptography.exceptions import InvalidSignature

from dero_messenger import crypto
from dero_messenger import protocol as p


def test_authenticated_transcript():
    a, b = crypto.identity(), crypto.identity()
    _, ap = crypto.ephemeral()
    _, bp = crypto.ephemeral()
    req = p.request(a, os.urandom(16), crypto.public(b), ap, "sim:alice", "sim:bob")
    assert p.parse_request(req)["identity"] == crypto.public(a)
    response = p.accept(b, req, bp)
    assert p.parse_accept(response, req) == bp
    with pytest.raises(InvalidSignature):
        p.parse_request(req[:-1] + bytes([req[-1] ^ 1]))
    with pytest.raises(ValueError):
        p.accept(a, req, bp)
    with pytest.raises(ValueError):
        p.parse_accept(response, p.request(a, os.urandom(16), crypto.public(b), ap, "a", "b"))
    with pytest.raises(InvalidSignature):
        p.parse_accept(response[:50] + bytes(32) + response[82:], req)


@pytest.mark.parametrize("size", [1, 82, 83, 4096, p.MAX_ENVELOPE])
def test_fragment_roundtrip_and_duplicates(size):
    envelope = os.urandom(size)
    packets = p.fragments(envelope)
    pending = {}
    result = None
    for packet in reversed(packets):
        assert len(packet) <= p.CAPACITY
        assert p.from_rpc(p.payload_rpc(packet)) == packet
        result = p.reconstruct(pending, packet)
        if result is None:
            assert p.reconstruct(pending, packet) is None
    assert result == envelope
    assert not pending


def test_fragment_limits_expiration_missing_and_integrity():
    with pytest.raises(ValueError):
        p.fragments(bytes(p.MAX_ENVELOPE + 1))
    with pytest.raises(ValueError):
        p.payload_rpc(bytes(103))
    packets = p.fragments(bytes(200))
    pending = {}
    assert p.reconstruct(pending, packets[0], now=0) is None
    assert p.reconstruct(pending, packets[1], now=p.TTL + 1) is None
    assert len(next(iter(pending.values()))["chunks"]) == 1
    pending = {}
    for packet in packets[:-1]:
        p.reconstruct(pending, packet)
    with pytest.raises(ValueError, match="digest"):
        p.reconstruct(pending, packets[-1][:-1] + b"x")
    pending = {}
    for i in range(64):
        p.reconstruct(pending, p.fragments(bytes([i]) * 200)[0])
    with pytest.raises(ValueError, match="quota"):
        p.reconstruct(pending, p.fragments(b"z" * 200)[0])


@pytest.mark.parametrize("data", [b"", bytes(19), b"DM" + bytes(18), b"x" * 103])
def test_malformed_fragments(data):
    with pytest.raises(ValueError):
        p.reconstruct({}, data)


def test_invalid_versions_reflection_and_truncated_handshake():
    secret = crypto.identity()
    _, eph = crypto.ephemeral()
    req = p.request(secret, bytes(16), crypto.public(secret), eph, "alice", "alice")
    with pytest.raises(ValueError, match="participants"):
        p.parse_request(req)
    with pytest.raises(ValueError):
        p.parse_request(bytes([2]) + req[1:])
    with pytest.raises(ValueError):
        p.parse_request(req[:100])
    for value in (
        [],
        [{"name": "m", "datatype": "S", "value": "!"}],
        [{"name": "m", "datatype": "S", "value": "A" * 140}],
    ):
        with pytest.raises(ValueError):
            p.from_rpc(value)


def test_release153_capacity_and_legacy_receive():
    import hashlib

    assert p.CAPACITY == 78 and p.CHUNK == 58
    assert p.from_rpc(p.payload_rpc(bytes(78))) == bytes(78)
    with pytest.raises(ValueError):
        p.payload_rpc(bytes(79))
    envelope = bytes(range(200))
    chunks = [envelope[i : i + 82] for i in range(0, len(envelope), 82)]
    packets = [
        p.FRAGMENT.pack(b"DM", hashlib.sha256(envelope).digest()[:16], i, len(chunks)) + chunk
        for i, chunk in enumerate(chunks)
    ]
    pending = {}
    for packet in packets:
        result = p.reconstruct(pending, packet)
    assert result == envelope
