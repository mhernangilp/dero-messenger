import pytest
from conftest import PASSWORD, establish

from dero_messenger import protocol as p
from dero_messenger.storage import Store
from dero_messenger.transport import Transfer


def test_end_to_end_offline_restart_and_duplicate_transactions(pair, tmp_path):
    alice, bob = pair
    sid = establish(alice, bob)
    a = alice.store.snapshot()["sessions"][sid]
    b = bob.store.snapshot()["sessions"][sid]
    assert a["tx"] == b["rx"] and a["rx"] == b["tx"]
    assert "ephemeral" not in a and "ephemeral" not in b
    alice.send("Bob", "Hello Bob, this is an encrypted message over DERO.")
    bob.sync()
    assert bob.store.snapshot()["messages"][-1]["text"].startswith("Hello Bob")
    bob.send("Alice", "Hello Alice")
    alice.sync()
    alice.store.close()
    bob.send("Alice", "Sent while Alice was offline")
    alice.store = Store(tmp_path / "alice" / "state.db", PASSWORD)
    alice.sync()
    assert alice.store.snapshot()["messages"][-1]["text"] == "Sent while Alice was offline"
    before = alice.store.snapshot()["messages"]
    alice.sync()
    assert alice.store.snapshot()["messages"] == before
    alice.send("Bob", "Counter survives restart")
    assert alice.store.snapshot()["sessions"][sid]["counter"] == 2
    bob.sync()
    assert bob.store.snapshot()["sessions"][sid]["received"] == [0, 1]


def test_replayed_envelope_and_tamper(pair):
    alice, bob = pair
    sid = establish(alice, bob)
    alice.send("Bob", "one")
    packets = alice.store.snapshot()["outbox"]
    pending = {}
    envelope = None
    for item in packets:
        result = p.reconstruct(pending, bytes.fromhex(item["payload"]))
        if result and p.parse_header(result)[0] == p.MESSAGE:
            envelope = result
    bob.sync()
    with pytest.raises(ValueError, match="Replayed"), bob.store.transaction() as state:
        bob.receive(state, envelope)
    assert bob.store.snapshot()["sessions"][sid]["received"] == [0]


def test_wrong_contact_key_reject_and_replay_request(pair):
    alice, bob = pair
    sid = alice.request("Bob")
    bob.sync()
    with bob.store.transaction() as state:
        state["contacts"].clear()
    with pytest.raises(ValueError, match="fingerprint"):
        bob.accept(sid)
    bob.reject(sid)
    req = bytes.fromhex(alice.store.snapshot()["sessions"][sid]["request"])
    with bob.store.transaction() as state:
        assert bob.receive(state, req) is None
    assert bob.store.snapshot()["sessions"][sid]["status"] == "rejected"


def test_uncertain_send_reserves_nonce_and_recovers(pair, monkeypatch):
    alice, bob = pair
    sid = establish(alice, bob)
    original = alice.transport.send

    def fail_after_submission(address, payload):
        original(address, payload)
        raise RuntimeError("connection dropped after submission")

    monkeypatch.setattr(alice.transport, "send", fail_after_submission)
    with pytest.raises(RuntimeError):
        alice.send("Bob", "recover me")
    assert alice.store.snapshot()["sessions"][sid]["counter"] == 1
    assert alice.store.snapshot()["outbox"][-1]["status"] == "sending"
    monkeypatch.setattr(alice.transport, "send", original)
    alice.flush(retry_uncertain=True)
    bob.sync()
    assert [m["text"] for m in bob.store.snapshot()["messages"]] == ["recover me"]


def test_response_and_data_reordering(pair, monkeypatch):
    alice, bob = pair
    sid = alice.request("Bob")
    bob.sync()
    bob.accept(sid)
    bob.send("Alice", "before response is processed")
    height, incoming = alice.transport.incoming()
    monkeypatch.setattr(alice.transport, "incoming", lambda: (height, list(reversed(incoming))))
    alice.sync()
    assert alice.store.snapshot()["messages"][-1]["text"] == "before response is processed"


def test_confirmation_gate(pair, monkeypatch):
    alice, bob = pair
    alice.request("Bob")
    height, records = bob.transport.incoming()
    bob.confirmations = 10
    monkeypatch.setattr(
        bob.transport,
        "incoming",
        lambda: (height, [Transfer(t.txid, t.position, t.height, 1, t.payload) for t in records]),
    )
    assert bob.sync() == []
    assert not bob.store.snapshot()["sessions"]
    monkeypatch.setattr(
        bob.transport,
        "incoming",
        lambda: (
            height + 10,
            [Transfer(t.txid, t.position, t.height, 11, t.payload) for t in records],
        ),
    )
    assert bob.sync()


def test_message_size_and_rotation(pair):
    alice, bob = pair
    sid = establish(alice, bob)
    with pytest.raises(ValueError):
        alice.send("Bob", "x" * 4097)
    alice.send("Bob", "x" * 4096)
    bob.sync()
    assert len(bob.store.snapshot()["messages"][-1]["text"]) == 4096
    with alice.store.transaction() as state:
        state["sessions"][sid]["counter"] = 10000
    with pytest.raises(ValueError, match="limit"):
        alice.send("Bob", "rotate")


def test_partial_fragments_persist_across_restart(pair, tmp_path, monkeypatch):
    alice, bob = pair
    sid = alice.request("Bob")
    height, records = bob.transport.incoming()
    monkeypatch.setattr(bob.transport, "incoming", lambda: (height, records[:1]))
    bob.sync()
    assert not bob.store.snapshot()["sessions"]
    assert bob.store.snapshot()["fragments"]
    bob.store.close()
    bob.store = Store(tmp_path / "bob" / "state.db", PASSWORD)
    monkeypatch.setattr(bob.transport, "incoming", lambda: (height, records))
    bob.sync()
    assert bob.store.snapshot()["sessions"][sid]["status"] == "incoming"


def test_paid_transport_pacing_preserves_pending_fragments(pair, monkeypatch):
    alice, bob = pair
    monkeypatch.setattr(alice.transport, "ready", lambda txid: False)
    sid = alice.request("Bob")
    outbox = alice.store.snapshot()["outbox"]
    assert outbox[0]["status"] == "submitted"
    assert all(x["status"] == "pending" for x in outbox[1:])
    bob.sync()
    assert not bob.store.snapshot()["sessions"]
    monkeypatch.setattr(alice.transport, "ready", lambda txid: True)
    alice.flush()
    bob.sync()
    assert bob.store.snapshot()["sessions"][sid]["status"] == "incoming"


def test_tampered_message_does_not_consume_receive_counter(pair):
    from cryptography.exceptions import InvalidTag

    from dero_messenger import crypto

    alice, bob = pair
    sid = establish(alice, bob)
    key = bytes.fromhex(alice.store.snapshot()["sessions"][sid]["tx"])
    aad = p.header(p.MESSAGE, bytes.fromhex(sid)) + bytes(8)
    valid = aad + crypto.encrypt(key, 0, b"authentic", aad)
    tampered = valid[:-1] + bytes([valid[-1] ^ 1])
    with bob.store.transaction() as state:
        with pytest.raises(InvalidTag):
            bob.receive(state, tampered)
        assert state["sessions"][sid]["received"] == []
        assert bob.receive(state, valid)
    assert bob.store.snapshot()["messages"][-1]["text"] == "authentic"


def test_outgoing_message_submission_status(pair):
    alice, bob = pair
    establish(alice, bob)
    alice.send("Bob", "status")
    assert alice.store.snapshot()["messages"][-1]["status"] == "submitted"
