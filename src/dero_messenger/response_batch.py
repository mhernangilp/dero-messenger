"""Submit only the exact approved Bob acceptance; reuse the shared spending ledger.

No application or wallet secrets are read. Restarting never repeats a reserved call.
"""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from . import protocol as p
from .experiment import SpendingGate, pending_proposal
from .mainnet_probe import ALICE, BOB, wallet_for
from .rpc import RPCError

APPROVED_HASH = "5bc06e0f4b6843113344c5013418840b1f56749fd8edc93cbcc7686857ab6147"
PROPOSAL = Path("docs/bob-response-proposal.json")
POLICY = Path(".mainnet/three-wallet-policy.json")
REPORT = Path("docs/bob-response-result.json")


def validated_proposal(value: dict) -> list[dict]:
    rows = value["transactions"]
    if len(rows) != 3:
        raise ValueError("Only the three approved fragments are permitted")
    state = dict(
        address=BOB,
        outbox=[
            dict(
                status="pending",
                payload=r["payload_hex"],
                destination=r["destination"],
                envelope_id=r["envelope_id"],
            )
            for r in rows
        ],
    )
    expected = pending_proposal(state, 181)
    if value != expected or expected["proposal_sha256"] != APPROVED_HASH:
        raise ValueError("Proposal differs from the exact human-approved transaction batch")
    pending = {}
    for row in rows:
        if row["destination"] != ALICE:
            raise ValueError("Wrong recipient")
        envelope = p.reconstruct(pending, bytes.fromhex(row["payload_hex"]))
    request_packets = json.loads(Path("docs/alice-request-proposal.json").read_text())[
        "transactions"
    ]
    parts = {}
    for packet in request_packets:
        request = p.reconstruct(parts, bytes.fromhex(packet["payload_hex"]))
    p.parse_accept(envelope, request)
    return rows


def digest(row: dict) -> str:
    return hashlib.sha256(
        json.dumps([BOB, ALICE, row["payload_hex"], 1, 181, 16], separators=(",", ":")).encode()
    ).hexdigest()


def entry_for(wallet, txid: str) -> dict | None:
    try:
        entry = wallet.rpc.call("GetTransferbyTXID", {"txid": txid})["entry"]
        return entry if entry.get("txid") == txid and int(entry.get("height", 0)) > 0 else None
    except RPCError as exc:
        if exc.not_found:
            return None
        raise


def check_entry(entry: dict, packet: bytes) -> None:
    if entry.get("payloaderror") or p.from_rpc(entry.get("payload_rpc", [])) != packet:
        raise ValueError("Indexed payload mismatch; stop spending")
    if int(entry["amount"]) != 1 or int(entry["fees"]) != 181:
        raise ValueError("Actual amount/fee differs from approved values; stop spending")


def metadata(entry: dict) -> dict:
    return {
        k: entry[k]
        for k in (
            "txid",
            "pos",
            "height",
            "topoheight",
            "blockhash",
            "time",
            "sender",
            "destination",
            "amount",
            "fees",
            "incoming",
        )
        if k in entry
    }


def save(report: dict) -> None:
    temporary = REPORT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(REPORT)


def run(approval: str, *, read_only: bool = False) -> None:
    rows = validated_proposal(json.loads(PROPOSAL.read_text()))
    if not read_only and approval != APPROVED_HASH:
        raise ValueError("Exact batch approval required")
    sender, recipient = wallet_for("bob"), wallet_for("alice")
    health = dict(sender=sender.status(), recipient=recipient.status())
    if health["sender"]["address"] != BOB or health["recipient"]["address"] != ALICE:
        raise ValueError("Wallet mismatch")
    sender.validate(ALICE)
    recipient.validate(BOB)
    print(json.dumps(dict(read_only=read_only, health=health)), flush=True)
    if read_only:
        return
    gate = SpendingGate(POLICY.with_suffix(".db"), json.loads(POLICY.read_text()))
    report = (
        json.loads(REPORT.read_text())
        if REPORT.exists()
        else dict(
            proposal_sha256=APPROVED_HASH,
            authorization="User approved exact three-fragment batch",
            authorized_maximum_atomic=546,
            before=health,
            transactions=[],
            status="in_progress",
        )
    )
    try:
        if report["proposal_sha256"] != APPROVED_HASH:
            raise ValueError("Existing report mismatch")
        if gate.db.execute("SELECT 1 FROM attempts WHERE status='uncertain'").fetchone():
            raise ValueError("Uncertain submission: read-only reconciliation required; no retry")
        # History protects against a fragment submitted by another client outside this ledger.
        history = sender.rpc.call(
            "GetTransfers", {"in": False, "out": True, "coinbase": False, "min_height": 0}
        )
        for row in rows:
            known = gate.db.execute(
                "SELECT status,txid FROM attempts WHERE digest=?", (digest(row),)
            ).fetchone()
            if known:
                continue
            for entry in history.get("entries") or []:
                try:
                    matches = p.from_rpc(entry.get("payload_rpc", [])) == bytes.fromhex(
                        row["payload_hex"]
                    )
                except (ValueError, TypeError):
                    matches = False
                if matches:
                    raise ValueError(
                        "Existing matching wallet transaction without reservation; reconcile"
                    )
        save(report)
        for index, row in enumerate(rows):
            packet = bytes.fromhex(row["payload_hex"])
            known = gate.db.execute(
                "SELECT status,txid FROM attempts WHERE digest=?", (digest(row),)
            ).fetchone()
            if known:
                if known[0] != "submitted" or not known[1]:
                    raise ValueError("Reserved submission cannot be retried")
                txid = known[1]
                record = next((r for r in report["transactions"] if r.get("txid") == txid), None)
                if record is None:
                    record = dict(index=index, txid=txid, recovered_from_ledger=True)
                    report["transactions"].append(record)
            else:
                balance = sender.status()
                if balance["address"] != BOB:
                    raise ValueError("Sender changed")
                if int(balance["unlocked_balance"]) < (3 - index) * 182:
                    raise ValueError("Insufficient unlocked balance for remaining approved batch")
                record = dict(
                    index=index,
                    payload_sha256=row["payload_sha256"],
                    started_at_utc=datetime.now(UTC).isoformat(),
                    started_epoch=time.time(),
                    status="about_to_reserve",
                    balance_before=balance,
                )
                report["transactions"].append(record)
                save(report)
                txid = gate.submit(
                    BOB,
                    ALICE,
                    packet,
                    181,
                    balance["unlocked_balance"],
                    True,
                    lambda row=row: sender.rpc.call("Transfer", row["rpc"]["params"])["txid"],
                )
                record.update(txid=txid, status="submitted")
                save(report)
                print(json.dumps(dict(index=index, txid=txid, status="submitted")), flush=True)
            deadline = time.monotonic() + 900
            while True:
                sent, received = entry_for(sender, txid), entry_for(recipient, txid)
                if sent is not None and received is not None:
                    check_entry(sent, packet)
                    check_entry(received, packet)
                    if sent.get("incoming") or not received.get("incoming"):
                        raise ValueError("Unexpected history direction")
                    record.update(
                        sender_entry=metadata(sent),
                        receiver_entry=metadata(received),
                        payload_equal=True,
                        status="indexed",
                    )
                    record.setdefault("observed_at_utc", datetime.now(UTC).isoformat())
                    if "started_epoch" in record:
                        record.setdefault(
                            "observed_delivery_seconds", time.time() - record["started_epoch"]
                        )
                    report["after"] = dict(sender=sender.status(), recipient=recipient.status())
                    record["receiver_confirmation_estimate"] = max(
                        0, report["after"]["recipient"]["height"] - int(received["height"]) + 1
                    )
                    save(report)
                    print(
                        json.dumps(
                            dict(
                                index=index, txid=txid, status="indexed", height=received["height"]
                            )
                        ),
                        flush=True,
                    )
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Indexing deadline exceeded; existing txid must be reconciled"
                    )
                time.sleep(5)
        report.update(
            status="all_three_indexed",
            actual_fees_atomic=543,
            actual_amount_atomic=3,
            actual_gross_debit_atomic=546,
        )
        save(report)
    except BaseException as exc:
        report.update(
            status="stopped_reconcile_before_more_spending",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        save(report)
        raise
    finally:
        gate.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-sha256", default="")
    parser.add_argument("--read-only", action="store_true")
    args = parser.parse_args()
    run(args.approve_sha256, read_only=args.read_only)
