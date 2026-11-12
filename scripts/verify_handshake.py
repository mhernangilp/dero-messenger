"""Read-only Mainnet transcript verification. Does not unlock app profiles or send."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from dero_messenger import protocol as p
from dero_messenger.mainnet_probe import wallet_for
from dero_messenger.request_batch import check_entry, entry_for, metadata

result = dict(observed_at_utc=datetime.now(UTC).isoformat(), receipts=[], envelopes={})
for label, recipient, proposal_path, report_path in [
    ("request", "bob", "docs/alice-request-proposal.json", "docs/alice-request-result.json"),
    ("acceptance", "alice", "docs/bob-response-proposal.json", "docs/bob-response-result.json"),
]:
    wallet = wallet_for(recipient)
    height = wallet.height()
    proposal = json.loads(Path(proposal_path).read_text())
    report = json.loads(Path(report_path).read_text())
    if len(report["transactions"]) != proposal["count"]:
        raise ValueError("Not all packets have submission evidence")
    pending = {}
    for row, record in zip(proposal["transactions"], report["transactions"], strict=True):
        entry = entry_for(wallet, record["txid"])
        if entry is None or not entry.get("incoming"):
            raise ValueError("Recipient has not indexed a transaction")
        packet = p.from_rpc(entry["payload_rpc"])
        check_entry(entry, bytes.fromhex(row["payload_hex"]))
        envelope = p.reconstruct(pending, packet)
        result["receipts"].append(
            dict(
                stage=label,
                packet_sha256=hashlib.sha256(packet).hexdigest(),
                confirmations=max(0, height - entry["height"] + 1),
                **metadata(entry),
            )
        )
    result["envelopes"][label] = envelope.hex()
request = bytes.fromhex(result["envelopes"]["request"])
acceptance = bytes.fromhex(result["envelopes"]["acceptance"])
parsed = p.parse_request(request)
p.parse_accept(acceptance, request)
identities = json.loads(Path("docs/three-wallet-identities.json").read_text())
if (
    parsed["identity"].hex() != identities["alice"]["public_identity"]
    or parsed["target"].hex() != identities["bob"]["public_identity"]
    or parsed["source"] != identities["alice"]["address"]
    or parsed["destination"] != identities["bob"]["address"]
):
    raise ValueError("Transcript identity/address mismatch")
result.update(
    session_id=parsed["sid"].hex(),
    both_signatures_verified=True,
    transcript_sha256=hashlib.sha256(request + acceptance).hexdigest(),
    all_ten_confirmations=all(r["confirmations"] >= 10 for r in result["receipts"]),
    on_chain_transcript_complete=True,
    alice_local_key_derivation="Pending user unlock and app sync",
    shared_key_confirmation="Not yet tested with encrypted session message",
)
Path("docs/handshake-delivery.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in ("envelopes", "receipts")}, indent=2))
