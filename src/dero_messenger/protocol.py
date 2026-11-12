"""Versioned binary envelopes and bounded, persistent fragment reconstruction."""

import base64
import hashlib
import struct
import time

from . import crypto

VERSION = 1
REQUEST, ACCEPT, MESSAGE = 1, 2, 3
CAPACITY = 78  # Release153: base64 in CBOR {"mS": string}: 104 + 6 = 110 <= 111
LEGACY_CAPACITY = 102  # Read-only compatibility with historical packets
MAX_ENVELOPE = 8192
MAX_TEXT = 4096
HEADER = struct.Struct("!BB16s")
FRAGMENT = struct.Struct("!2s16sBB")
CHUNK = CAPACITY - FRAGMENT.size
MAX_FRAGMENTS = (MAX_ENVELOPE + CHUNK - 1) // CHUNK
TTL = 30 * 86400
DOMAIN = b"DERO Private Messenger handshake v1\x00"


def payload_rpc(packet: bytes) -> list[dict]:
    if not 1 <= len(packet) <= CAPACITY:
        raise ValueError("DERO packet capacity exceeded")
    return [{"name": "m", "datatype": "S", "value": base64.b64encode(packet).decode()}]


def from_rpc(arguments: list[dict]) -> bytes:
    if len(arguments) != 1 or arguments[0].get("name") != "m":
        raise ValueError("Not a messenger payload")
    arg = arguments[0]
    if arg.get("datatype") != "S" or not isinstance(arg.get("value"), str):
        raise ValueError("Invalid payload type")
    if len(arg["value"]) > 136:
        raise ValueError("Oversized payload")
    packet = base64.b64decode(arg["value"], validate=True)
    if not 1 <= len(packet) <= LEGACY_CAPACITY:
        raise ValueError("Invalid incoming payload length")
    return packet


def header(kind: int, sid: bytes) -> bytes:
    if len(sid) != 16 or kind not in (REQUEST, ACCEPT, MESSAGE):
        raise ValueError("Invalid envelope header")
    return HEADER.pack(VERSION, kind, sid)


def parse_header(data: bytes) -> tuple[int, bytes]:
    if not HEADER.size <= len(data) <= MAX_ENVELOPE:
        raise ValueError("Invalid envelope length")
    version, kind, sid = HEADER.unpack_from(data)
    if version != VERSION or kind not in (REQUEST, ACCEPT, MESSAGE):
        raise ValueError("Unsupported protocol")
    return kind, sid


def request(
    secret: bytes, sid: bytes, target_key: bytes, eph: bytes, source: str, destination: str
) -> bytes:
    a, b = source.encode("ascii"), destination.encode("ascii")
    if not 1 <= len(a) <= 128 or not 1 <= len(b) <= 128:
        raise ValueError("Invalid address length")
    body = header(REQUEST, sid) + crypto.public(secret) + target_key + eph
    body += bytes([len(a)]) + a + bytes([len(b)]) + b
    return body + crypto.sign(secret, DOMAIN + body)


def parse_request(data: bytes) -> dict:
    kind, sid = parse_header(data)
    if kind != REQUEST or len(data) < 182:
        raise ValueError("Invalid request")
    body, signature = data[:-64], data[-64:]
    key, target, eph = body[18:50], body[50:82], body[82:114]
    offset = 114
    addresses = []
    for _ in range(2):
        if offset >= len(body):
            raise ValueError("Truncated address")
        size = body[offset]
        offset += 1
        if not 1 <= size <= 128 or offset + size > len(body):
            raise ValueError("Invalid address")
        addresses.append(body[offset : offset + size].decode("ascii"))
        offset += size
    if offset != len(body) or key == target:
        raise ValueError("Invalid participants")
    crypto.verify(key, signature, DOMAIN + body)
    return dict(
        sid=sid,
        identity=key,
        target=target,
        ephemeral=eph,
        source=addresses[0],
        destination=addresses[1],
    )


def accept(secret: bytes, req: bytes, eph: bytes) -> bytes:
    parsed = parse_request(req)
    if parsed["target"] != crypto.public(secret):
        raise ValueError("Wrong responder identity")
    body = header(ACCEPT, parsed["sid"]) + hashlib.sha256(req).digest() + eph
    return body + crypto.sign(secret, DOMAIN + req + body)


def parse_accept(data: bytes, req: bytes) -> bytes:
    kind, sid = parse_header(data)
    parsed = parse_request(req)
    if (
        kind != ACCEPT
        or sid != parsed["sid"]
        or len(data) != 146
        or data[18:50] != hashlib.sha256(req).digest()
    ):
        raise ValueError("Response does not match request")
    crypto.verify(parsed["target"], data[-64:], DOMAIN + req + data[:-64])
    return data[50:82]


def fragments(envelope: bytes) -> list[bytes]:
    if not 1 <= len(envelope) <= MAX_ENVELOPE:
        raise ValueError("Envelope too large")
    mid = hashlib.sha256(envelope).digest()[:16]
    chunks = [envelope[i : i + CHUNK] for i in range(0, len(envelope), CHUNK)]
    return [FRAGMENT.pack(b"DM", mid, i, len(chunks)) + c for i, c in enumerate(chunks)]


def reconstruct(pending: dict, packet: bytes, now: float | None = None) -> bytes | None:
    now = time.time() if now is None else now
    for key in list(pending):
        if now - pending[key]["created"] > TTL:
            del pending[key]
    if not FRAGMENT.size < len(packet) <= LEGACY_CAPACITY:
        raise ValueError("Invalid fragment size")
    magic, mid, index, count = FRAGMENT.unpack_from(packet)
    chunk = packet[FRAGMENT.size :]
    if magic != b"DM" or not 1 <= count <= MAX_FRAGMENTS or index >= count:
        raise ValueError("Invalid fragment header")
    if index < count - 1 and len(chunk) not in (CHUNK, LEGACY_CAPACITY - FRAGMENT.size):
        raise ValueError("Noncanonical fragment")
    key = mid.hex()
    if key not in pending:
        if len(pending) >= 64:
            raise ValueError("Fragment quota reached")
        pending[key] = {"created": now, "count": count, "chunks": {}}
    group = pending[key]
    if group["count"] != count:
        raise ValueError("Conflicting fragment count")
    old = group["chunks"].get(str(index))
    if old is not None and old != chunk.hex():
        raise ValueError("Conflicting fragment")
    if (
        old is None
        and sum(len(c) // 2 for c in group["chunks"].values()) + len(chunk) > MAX_ENVELOPE
    ):
        raise ValueError("Fragment group exceeds envelope resource limit")
    group["chunks"][str(index)] = chunk.hex()
    if len(group["chunks"]) != count:
        return None
    chunks = [bytes.fromhex(group["chunks"][str(i)]) for i in range(count)]
    del pending[key]
    if count > 1 and (
        any(len(c) != len(chunks[0]) for c in chunks[:-1]) or len(chunks[-1]) > len(chunks[0])
    ):
        raise ValueError("Mixed fragment capacities")
    result = b"".join(chunks)
    if len(result) > MAX_ENVELOPE or hashlib.sha256(result).digest()[:16] != mid:
        raise ValueError("Fragment digest mismatch")
    return result
