"""Read-only verification of the six approved Alice request transactions at Bob."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from dero_messenger import protocol as p
from dero_messenger.mainnet_probe import wallet_for
from dero_messenger.request_batch import APPROVED_HASH, check_entry, entry_for, validated_proposal

proposal = json.loads(Path("docs/alice-request-proposal.json").read_text())
rows = validated_proposal(proposal)
result = json.loads(Path("docs/alice-request-result.json").read_text())
if result["status"] != "all_six_indexed" or result["proposal_sha256"] != APPROVED_HASH:
    raise ValueError("Batch is not fully indexed; reconcile before claiming delivery")
bob = wallet_for("bob")
height = bob.height()
pending = {}
receipts = []
for row, record in zip(rows, result["transactions"], strict=True):
    entry = entry_for(bob, record["txid"])
    if entry is None:
        raise ValueError("Previously indexed transaction is absent")
    packet = p.from_rpc(entry["payload_rpc"])
    check_entry(entry, bytes.fromhex(row["payload_hex"]))
    envelope = p.reconstruct(pending, packet)
    receipts.append(
        dict(
            txid=record["txid"],
            packet_sha256=hashlib.sha256(packet).hexdigest(),
            height=entry["height"],
            confirmations=max(0, height - entry["height"] + 1),
            reported_sender=entry.get("sender"),
        )
    )
request = p.parse_request(envelope)
identities = json.loads(Path("docs/three-wallet-identities.json").read_text())
if (
    request["identity"].hex() != identities["alice"]["public_identity"]
    or request["target"].hex() != identities["bob"]["public_identity"]
    or request["source"] != identities["alice"]["address"]
    or request["destination"] != identities["bob"]["address"]
):
    raise ValueError("Authenticated participants differ from pinned evidence")
report = dict(
    observed_at_utc=datetime.now(UTC).isoformat(),
    source="Bob official GetTransferbyTXID",
    wallet_height=height,
    receipts=receipts,
    reassembled_bytes=len(envelope),
    envelope_sha256=hashlib.sha256(envelope).hexdigest(),
    sid=request["sid"].hex(),
    signature_verified=True,
    identities_match=True,
    all_at_least_ten_confirmations=all(r["confirmations"] >= 10 for r in receipts),
    bob_application_sync="Pending user unlock of encrypted profile",
    handshake_complete=False,
)
Path("docs/alice-request-delivery.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
