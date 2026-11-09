import hashlib

import pytest

from dero_messenger.mainnet_probe import (
    ALICE,
    AMOUNT,
    BOB,
    BUDGET,
    FEE,
    PAYLOAD,
    Probe,
    proposal,
    proposal_digest,
)
from dero_messenger.protocol import payload_rpc
from dero_messenger.rpc import RPCError

TXID = "ab" * 32


class FakeWallet:
    def __init__(self, address):
        self.own_address = address
        self.rpc = self
        self.paid_calls = []
        self.entries = []
        self.fail = False

    def address(self):
        return self.own_address

    def validate(self, destination):
        assert destination == BOB

    def status(self):
        return {"unlocked_balance": 4544}

    def height(self):
        return 100

    def incoming(self):
        return self.entries

    def call(self, method, params):
        if method == "Transfer":
            self.paid_calls.append(params)
            if self.fail:
                raise RPCError("uncertain")
            return {"txid": TXID}
        assert method == "GetTransfers"
        return {"entries": self.entries}


@pytest.fixture
def pair():
    return FakeWallet(ALICE), FakeWallet(BOB)


def test_probe_requires_exact_explicit_authorization(tmp_path, pair):
    alice, bob = pair
    probe = Probe(tmp_path / "probe.db")
    with pytest.raises(ValueError, match="approval"):
        probe.broadcast("wrong", alice, bob)
    assert not alice.paid_calls
    assert probe.record()["status"] == "prepared"
    probe.close()


def test_one_call_exact_parameters_and_durable_budget(tmp_path, pair):
    alice, bob = pair
    path = tmp_path / "probe.db"
    probe = Probe(path)
    assert probe.broadcast(proposal_digest(), alice, bob) == TXID
    assert alice.paid_calls == [proposal()["rpc"]["params"]]
    assert probe.record()["reserved_atomic"] == BUDGET == AMOUNT + FEE
    probe.close()
    probe = Probe(path)
    with pytest.raises(ValueError, match="consumed"):
        probe.broadcast(proposal_digest(), alice, bob)
    assert len(alice.paid_calls) == 1
    probe.close()


def test_uncertain_call_cannot_be_retried_after_restart(tmp_path, pair):
    alice, bob = pair
    alice.fail = True
    path = tmp_path / "probe.db"
    probe = Probe(path)
    with pytest.raises(RPCError):
        probe.broadcast(proposal_digest(), alice, bob)
    probe.close()
    probe = Probe(path)
    with pytest.raises(ValueError, match="consumed"):
        probe.broadcast(proposal_digest(), alice, bob)
    assert len(alice.paid_calls) == 1
    assert probe.record()["status"] == "submission_uncertain"
    probe.close()


def test_reject_wrong_wallet_and_changed_proposal(tmp_path, pair):
    alice, bob = pair
    probe = Probe(tmp_path / "probe.db")
    bob.own_address = ALICE
    with pytest.raises(ValueError, match="mismatch"):
        probe.broadcast(proposal_digest(), alice, bob)
    bob.own_address = BOB
    record = probe.record()
    record["proposal"]["rpc"]["params"]["fees"] += 1
    probe.save(record)
    with pytest.raises(ValueError, match="changed"):
        probe.broadcast(proposal_digest(), alice, bob)
    assert not alice.paid_calls
    probe.close()


def test_readonly_reconciliation_recovers_uncertain_tx_and_payload(tmp_path, pair):
    alice, bob = pair
    alice.fail = True
    probe = Probe(tmp_path / "probe.db")
    with pytest.raises(RPCError):
        probe.broadcast(proposal_digest(), alice, bob)
    entry = dict(
        txid=TXID,
        destination=BOB,
        amount=1,
        fees=FEE,
        height=90,
        blockhash="cd" * 32,
        pos=0,
        payload_rpc=payload_rpc(PAYLOAD),
    )
    alice.entries = [dict(entry, incoming=False)]
    bob.entries = [dict(entry, incoming=True)]
    result = probe.reconcile(alice, bob)
    assert result["status"] == "delivered"
    assert result["bytes_equal"]
    assert result["received_sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
    assert result["actual_total_atomic"] == BUDGET
    assert result["confirmation_estimate"] == 11
    assert len(alice.paid_calls) == 1
    probe.close()


def test_indexing_delay_never_retries(tmp_path, pair):
    alice, bob = pair
    probe = Probe(tmp_path / "probe.db")
    probe.broadcast(proposal_digest(), alice, bob)
    assert probe.reconcile(alice, bob)["status"] == "submitted"
    assert len(alice.paid_calls) == 1
    probe.close()
