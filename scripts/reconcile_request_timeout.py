"""Reconcile the observed fifth-fragment timeout, without making any Transfer call."""

import json
from datetime import UTC, datetime

from dero_messenger import protocol as p
from dero_messenger.mainnet_probe import ALICE, BOB, wallet_for
from dero_messenger.request_batch import (
    POLICY,
    PROPOSAL,
    REPORT,
    SpendingGate,
    check_entry,
    digest,
    metadata,
    save,
    validated_proposal,
)

rows = validated_proposal(json.loads(PROPOSAL.read_text()))
row = rows[4]
packet = bytes.fromhex(row["payload_hex"])
expected_txid = "5f9d3c29646f3d90b28c48526d141152b7542df400f0985c9484ece07a5cbfbd"
evidence = {}
for name, address, incoming in [("alice", ALICE, False), ("bob", BOB, True)]:
    wallet = wallet_for(name)
    if wallet.address() != address:
        raise ValueError("Wallet mismatch")
    entries = (
        wallet.rpc.call(
            "GetTransfers", {"in": True, "out": True, "coinbase": False, "min_height": 0}
        ).get("entries")
        or []
    )
    matches = []
    for entry in entries:
        try:
            identical = p.from_rpc(entry.get("payload_rpc", [])) == packet
        except (ValueError, TypeError):
            identical = False
        if identical:
            matches.append(entry)
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous history; reservation remains uncertain")
    entry = matches[0]
    check_entry(entry, packet)
    if (
        entry["txid"] != expected_txid
        or entry.get("incoming") is not incoming
        or int(entry.get("height", 0)) <= 0
    ):
        raise ValueError("Unexpected transaction evidence")
    if name == "alice" and entry.get("destination") != BOB:
        raise ValueError("Wrong destination")
    evidence[name] = metadata(entry)
gate = SpendingGate(POLICY.with_suffix(".db"), json.loads(POLICY.read_text()))
try:
    gate.db.execute("BEGIN IMMEDIATE")
    known = gate.db.execute(
        "SELECT status,txid FROM attempts WHERE digest=?", (digest(row),)
    ).fetchone()
    if known != ("uncertain", None):
        raise ValueError("Reservation is not the expected uncertain fifth submission")
    gate.db.execute(
        "UPDATE attempts SET status='submitted',txid=? WHERE digest=?", (expected_txid, digest(row))
    )
    gate.db.execute("COMMIT")
finally:
    gate.close()
report = json.loads(REPORT.read_text())
record = next(r for r in report["transactions"] if r["index"] == 4)
record.update(txid=expected_txid, status="submitted", recovered_after_timeout=True)
report["timeout_reconciliation"] = dict(
    observed_at_utc=datetime.now(UTC).isoformat(),
    evidence=evidence,
    action="Recorded existing TXID; no retry",
    reserved_cost_unchanged=True,
)
save(report)
print(json.dumps(report["timeout_reconciliation"], indent=2))
