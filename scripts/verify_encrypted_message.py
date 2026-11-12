"""Read-only verification of Bob's two received encrypted message fragments."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from dero_messenger import protocol as p
from dero_messenger.mainnet_probe import wallet_for
from dero_messenger.request_batch import check_entry, entry_for, metadata

proposal = json.loads(Path("docs/alice-message-proposal.json").read_text())
result = json.loads(Path("docs/alice-message-result.json").read_text())
if len(proposal["transactions"]) != 2 or len(result["transactions"]) != 2:
    raise ValueError("Expected exactly two message transactions")
bob = wallet_for("bob")
height = bob.height()
pending = {}
receipts = []
for row, record in zip(proposal["transactions"], result["transactions"], strict=True):
    entry = entry_for(bob, record["txid"])
    if entry is None or not entry.get("incoming"):
        raise ValueError("Bob has not indexed a message fragment")
    packet = p.from_rpc(entry["payload_rpc"])
    check_entry(entry, bytes.fromhex(row["payload_hex"]))
    envelope = p.reconstruct(pending, packet)
    receipts.append(
        dict(
            **metadata(entry),
            payload_sha256=hashlib.sha256(packet).hexdigest(),
            confirmations=max(0, height - entry["height"] + 1),
        )
    )
kind, sid = p.parse_header(envelope)
if (
    kind != p.MESSAGE
    or sid.hex() != "7449a7ca589687e87c4307cf0fc562f3"
    or int.from_bytes(envelope[18:26], "big") != 0
):
    raise ValueError("Wrong encrypted session metadata")
report = dict(
    observed_at_utc=datetime.now(UTC).isoformat(),
    wallet_height=height,
    receipts=receipts,
    envelope_sha256=hashlib.sha256(envelope).hexdigest(),
    envelope_bytes=len(envelope),
    session=sid.hex(),
    counter=0,
    both_fragments_match=True,
    all_ten_confirmations=all(x["confirmations"] >= 10 for x in receipts),
    bob_aes_gcm_decryption="Pending local app sync/read with passphrase",
)
Path("docs/alice-message-delivery.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        dict(
            minimum_confirmations=min(x["confirmations"] for x in receipts),
            envelope_sha256=report["envelope_sha256"],
            both_fragments_match=True,
        ),
        indent=2,
    )
)
