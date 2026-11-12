import os

import pytest
from conftest import PASSWORD
from cryptography.exceptions import InvalidSignature, InvalidTag

from dero_messenger import crypto
from dero_messenger import protocol as p
from dero_messenger.conversations import Messenger, initial_state
from dero_messenger.experiment import plan
from dero_messenger.storage import Store
from dero_messenger.transport import Simulated


def test_three_independent_profiles_and_exact_plan(tmp_path):
    names = ("alice", "bob", "charlie")
    addresses = {name: "dero1" + char * 61 for name, char in zip(names, "qpr", strict=True)}
    peers = {}
    for name in names:
        address = addresses[name]
        peers[name] = Messenger(
            Store(tmp_path / name / "state.db", PASSWORD, initial_state(address)),
            Simulated(tmp_path / "chain.db", address),
        )
    a, b, c = (peers[n] for n in names)
    for sender, receiver in [
        ("alice", "bob"),
        ("bob", "alice"),
        ("charlie", "bob"),
        ("bob", "charlie"),
    ]:
        peers[sender].add_contact(
            addresses[receiver], receiver, peers[receiver].identity()["public_key"]
        )
    sessions = []
    for sender in (a, c):
        sid = sender.request("bob")
        b.sync()
        b.accept(sid)
        sender.sync()
        sessions.append(sid)
    assert sessions[0] != sessions[1]
    state = b.store.snapshot()
    assert state["sessions"][sessions[0]]["rx"] != state["sessions"][sessions[1]]["rx"]
    a.send("bob", "Hello Bob!")
    c.send("bob", "Hello Bob!")
    b.sync()
    b.send("alice", "Hello Alice!")
    b.send("charlie", "Hello Charlie!")
    a.sync()
    c.sync()
    a.send("bob", "L" * 512)
    # Reverse the entire history, with duplicates: reconstruction must remain deterministic.
    original = b.transport.incoming
    height, entries = original()
    b.transport.incoming = lambda: (height, list(reversed(entries)) + entries)
    b.sync()
    b.store.close()
    b.transport.db.close()
    c.send("bob", "Offline message")
    b = Messenger(
        Store(tmp_path / "bob" / "state.db", PASSWORD),
        Simulated(tmp_path / "chain.db", addresses["bob"]),
    )
    peers["bob"] = b
    b.sync()
    before = b.store.snapshot()["messages"]
    b.sync()
    assert b.store.snapshot()["messages"] == before
    incoming = [m for m in before if m["direction"] == "in"]
    assert [(m["peer"], m["text"]) for m in incoming].count((addresses["alice"], "L" * 512)) == 1
    assert (
        incoming[-1]["peer"] == addresses["charlie"] and incoming[-1]["text"] == "Offline message"
    )
    assert (
        a.transport.db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        == plan()["transactions"]
    )
    for peer in peers.values():
        peer.store.close()
        peer.transport.db.close()


@pytest.mark.parametrize("offset", [0, 2, 18, 50, 82, 116, 125])
def test_signed_fields_cannot_be_substituted(offset):
    a, b = crypto.identity(), crypto.identity()
    _, ephemeral = crypto.ephemeral()
    req = p.request(a, os.urandom(16), crypto.public(b), ephemeral, "sim:alice", "sim:bob")
    changed = req[:offset] + bytes([req[offset] ^ 1]) + req[offset + 1 :]
    with pytest.raises((ValueError, InvalidSignature)):
        p.parse_request(changed)


def test_impersonation_and_cross_session_ciphertext(pair):
    from conftest import establish

    a, b = pair
    attacker = crypto.identity()
    _, eph = crypto.ephemeral()
    fake = p.request(
        attacker,
        os.urandom(16),
        bytes.fromhex(b.identity()["public_key"]),
        eph,
        "sim:alice",
        "sim:bob",
    )
    with b.store.transaction() as state:
        b.receive(state, fake)
    with pytest.raises(ValueError, match="fingerprint"):
        b.accept(p.parse_request(fake)["sid"].hex())
    first = establish(a, b)
    second = establish(a, b)
    key = bytes.fromhex(a.store.snapshot()["sessions"][first]["tx"])
    aad = p.header(p.MESSAGE, bytes.fromhex(first)) + bytes(8)
    ciphertext = crypto.encrypt(key, 0, b"original", aad)
    with b.store.transaction() as state:
        with pytest.raises(InvalidTag):
            b.receive(state, p.header(p.MESSAGE, bytes.fromhex(second)) + bytes(8) + ciphertext)
        assert state["sessions"][second]["received"] == []


def test_incomplete_legacy_group_is_bounded():
    pending = {}
    for i in range(99):
        p.reconstruct(pending, p.FRAGMENT.pack(b"DM", bytes(16), i, 142) + bytes(82))
    with pytest.raises(ValueError, match="resource limit"):
        p.reconstruct(pending, p.FRAGMENT.pack(b"DM", bytes(16), 99, 142) + bytes(82))
    assert sum(len(c) // 2 for c in pending[bytes(16).hex()]["chunks"].values()) <= 8192
