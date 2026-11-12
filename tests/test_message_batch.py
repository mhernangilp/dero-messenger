import copy
import json
from pathlib import Path

import pytest

from dero_messenger import message_batch as batch


def proposal():
    return json.loads(Path("docs/alice-message-proposal.json").read_text())


def test_exact_approved_batch_validation():
    value = proposal()
    assert len(batch.validated_proposal(value)) == 2
    for field in ("sender", "payload_hex", "destination"):
        changed = copy.deepcopy(value)
        changed["transactions"][0][field] += "0"
        with pytest.raises((ValueError, KeyError)):
            batch.validated_proposal(changed)


def test_batch_is_single_use_and_resumable_without_resending(tmp_path, monkeypatch):
    exercise(tmp_path, monkeypatch, fail=False)


def test_uncertain_call_blocks_entire_batch(tmp_path, monkeypatch):
    exercise(tmp_path, monkeypatch, fail=True)


def exercise(tmp_path, monkeypatch, fail):
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal()))
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            dict(
                participants={batch.ALICE: 17, batch.BOB: 8, "dero1" + "q" * 61: 8},
                max_transactions=33,
                max_debit_atomic=6006,
                fee_atomic=181,
            )
        )
    )
    monkeypatch.setattr(batch, "PROPOSAL", proposal_path)
    monkeypatch.setattr(batch, "POLICY", policy_path)
    monkeypatch.setattr(batch, "REPORT", tmp_path / "result.json")
    ledger = {}

    class Wallet:
        def __init__(self, incoming):
            self.incoming = incoming
            self.rpc = self

        def status(self):
            return dict(
                address=batch.BOB if self.incoming else batch.ALICE,
                height=100,
                balance=5000,
                unlocked_balance=5000,
            )

        def validate(self, address):
            assert address in (batch.ALICE, batch.BOB)

        def call(self, method, params):
            if method == "GetTransfers":
                return {"entries": []}
            if method == "Transfer":
                assert not self.incoming
                assert params["fees"] == 181 and params["ringsize"] == 16
                txid = f"{len(ledger) + 1:064x}"
                ledger[txid] = params
                if fail:
                    raise TimeoutError("uncertain")
                return dict(txid=txid)
            assert method == "GetTransferbyTXID"
            txid = params["txid"]
            params = ledger[txid]
            return dict(
                entry=dict(
                    txid=txid,
                    height=99,
                    incoming=self.incoming,
                    amount=1,
                    fees=181,
                    payload_rpc=params["transfers"][0]["payload_rpc"],
                )
            )

    wallets = dict(alice=Wallet(False), bob=Wallet(True))
    monkeypatch.setattr(batch, "wallet_for", wallets.__getitem__)
    with pytest.raises(ValueError, match="approval"):
        batch.run("wrong")
    assert not ledger
    batch.run("", read_only=True)
    assert not ledger
    if fail:
        with pytest.raises(TimeoutError):
            batch.run(batch.APPROVED_HASH)
        with pytest.raises(ValueError, match="Uncertain"):
            batch.run(batch.APPROVED_HASH)
        assert len(ledger) == 1
    else:
        batch.run(batch.APPROVED_HASH)
        batch.run(batch.APPROVED_HASH)
        assert len(ledger) == 2
        report = json.loads(batch.REPORT.read_text())
        assert report["status"] == "all_two_indexed"
        assert report["actual_gross_debit_atomic"] == 364
