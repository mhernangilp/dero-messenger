"""One explicitly authorized Mainnet transport probe; never opens wallet files.

Run with `python -m dero_messenger.mainnet_probe --help`. The durable gate limits
this probe to one Transfer invocation. It is not an OS sandbox for unlocked RPC.
"""

import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

import typer

from .protocol import from_rpc, payload_rpc
from .rpc import RPC, RPCError
from .storage import private_directory
from .wallet import Wallet

ALICE = "dero1qynrm8qn82vesxjcecuwr0dt7lg5gy4e0jdrhddup5ms6k70562zqqgq9e8tk"
BOB = "dero1qy9uv73wh4s3ew3s68q5ws6y3nn6sutwr6xs6g7mhzuefe09uyvdcqglpgwya"
KNOWN_TX = "27ba10c4f20ae1f8db549465b4cf3e589011319fdbdb8e2ebca020e8bc0098bf"
PAYLOAD = bytes(range(24))
AMOUNT, FEE, BUDGET = 1, 181, 182
ENDPOINTS = {"alice": "http://127.0.0.1:20209/json_rpc", "bob": "http://127.0.0.1:20210/json_rpc"}
app = typer.Typer(pretty_exceptions_enable=False, no_args_is_help=True)


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def proposal(payload: bytes = PAYLOAD) -> dict:
    return {
        "probe": "chainchat-release153-binary-001" if payload == PAYLOAD else "chainchat-psk-001",
        "sender": ALICE,
        "destination": BOB,
        "endpoint": ENDPOINTS["alice"],
        "payload_hex": payload.hex(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "max_transactions": 1,
        "maximum_total_atomic": BUDGET,
        "rpc": {
            "method": "Transfer",
            "params": {
                "transfers": [
                    {"destination": BOB, "amount": AMOUNT, "payload_rpc": payload_rpc(payload)}
                ],
                "ringsize": 16,
                "fees": FEE,
            },
        },
    }


def proposal_digest() -> str:
    return hashlib.sha256(canonical(proposal())).hexdigest()


def wallet_for(name: str) -> Wallet:
    prefix = f"DERO_{name.upper()}_RPC_"
    user = os.getenv(prefix + "USER", os.getenv("DERO_WALLET_USER"))
    password = os.getenv(prefix + "PASSWORD", os.getenv("DERO_WALLET_PASSWORD"))
    if bool(user) != bool(password):
        raise ValueError(f"Set both {prefix}USER and {prefix}PASSWORD")
    return Wallet(RPC(ENDPOINTS[name], (user, password) if user and password else None))


def metadata(entry: dict) -> dict:
    allowed = ("txid", "height", "topoheight", "blockhash", "pos", "incoming", "amount", "fees")
    return {k: entry[k] for k in allowed if k in entry}


def health(wallets: dict[str, Wallet]) -> dict:
    report = {"observed_at_utc": datetime.now(UTC).isoformat(), "wallets": {}}
    for name, address in (("alice", ALICE), ("bob", BOB)):
        record = {}
        report["wallets"][name] = record
        official = wallets[name]
        try:
            record.update(official.status())
            record["address_matches"] = record["address"] == address
            if not record["address_matches"]:
                raise ValueError("Wallet address mismatch")
            official.validate(address)
            record["address_parser"] = "passed"
            known = official.rpc.call("GetTransferbyTXID", {"txid": KNOWN_TX})["entry"]
            record["known_transaction"] = metadata(known)
            entries = (
                official.rpc.call(
                    "GetTransfers",
                    {
                        "in": True,
                        "out": True,
                        "coinbase": False,
                        "min_height": 7879672,
                    },
                ).get("entries")
                or []
            )
            record["history_contains_known_transaction"] = any(
                e.get("txid") == KNOWN_TX for e in entries
            )
        except (RPCError, ValueError, KeyError) as exc:
            record["error"] = str(exc)
    return report


class Probe:
    """Single-use budget reservation, committed BEFORE the only paid RPC call."""

    def __init__(self, path: Path, payload: bytes = PAYLOAD):
        self.payload = payload
        self.proposal = proposal(payload)
        self.digest = hashlib.sha256(canonical(self.proposal)).hexdigest()
        private_directory(path.parent)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        path.chmod(0o600)
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS probe "
            "(id INTEGER PRIMARY KEY CHECK(id=1), record TEXT NOT NULL)"
        )
        self.db.execute(
            "INSERT OR IGNORE INTO probe VALUES(1,?)",
            (
                json.dumps(
                    {
                        "proposal": self.proposal,
                        "proposal_sha256": self.digest,
                        "status": "prepared",
                        "transfer_calls_reserved": 0,
                        "reserved_atomic": 0,
                    }
                ),
            ),
        )

    def record(self) -> dict:
        return json.loads(self.db.execute("SELECT record FROM probe WHERE id=1").fetchone()[0])

    def save(self, record: dict) -> None:
        self.db.execute("UPDATE probe SET record=? WHERE id=1", (json.dumps(record),))

    def broadcast(self, approval_sha256: str, alice: Wallet, bob: Wallet) -> str:
        if approval_sha256 != self.digest:
            raise ValueError("Explicit approval must match the exact proposal SHA-256")
        # No paid calls occur during preflight. Check both identities and parsing.
        if alice.address() != ALICE or bob.address() != BOB:
            raise ValueError("Wallet address mismatch; refusing broadcast")
        alice.validate(BOB)
        alice_status = alice.status()
        if alice_status["unlocked_balance"] < BUDGET:
            raise ValueError("Insufficient unlocked balance for the maximum cost")
        if abs(alice.height() - bob.height()) > 10:
            raise ValueError("Wallet heights differ by more than 10 blocks")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            record = self.record()
            if (
                record["status"] != "prepared"
                or record["transfer_calls_reserved"] != 0
                or record["proposal"] != self.proposal
                or record["proposal_sha256"] != approval_sha256
            ):
                raise ValueError("Proposal changed or single-use authorization already consumed")
            record.update(
                status="submission_uncertain",
                transfer_calls_reserved=1,
                reserved_atomic=BUDGET,
                approval_sha256=approval_sha256,
                submitted_at=time.time(),
                approved_at_utc=datetime.now(UTC).isoformat(),
            )
            self.save(record)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        # A crash/error leaves a durable consumed authorization. There is no retry path.
        try:
            result = alice.rpc.call("Transfer", self.proposal["rpc"]["params"])
            txid = result.get("txid", "")
            if not isinstance(txid, str) or not re.fullmatch(r"[0-9a-f]{64}", txid):
                raise ValueError("Wallet returned an invalid transaction ID; reconcile history")
            record.update(status="submitted", txid=txid)
            self.save(record)
            return txid
        except (RPCError, ValueError) as exc:
            record["submission_error"] = str(exc)
            self.save(record)
            raise

    def reconcile(self, alice: Wallet, bob: Wallet) -> dict:
        record = self.record()
        if record["transfer_calls_reserved"] != 1:
            raise ValueError("No authorized submission to reconcile")
        if alice.address() != ALICE or bob.address() != BOB:
            raise ValueError("Wallet identity mismatch")
        expected_payload = bytes.fromhex(record["proposal"]["payload_hex"])
        # Only structured public probe bytes are matched. Never print proofs/raw history.
        entries = (
            alice.rpc.call(
                "GetTransfers",
                {
                    "in": False,
                    "out": True,
                    "coinbase": False,
                    "min_height": 0,
                },
            ).get("entries")
            or []
        )
        matches = []
        for entry in entries:
            if (
                entry.get("incoming")
                or entry.get("destination") != BOB
                or entry.get("amount") != AMOUNT
                or entry.get("payloaderror")
            ):
                continue
            try:
                if from_rpc(entry.get("payload_rpc", [])) == expected_payload:
                    matches.append(entry)
            except (ValueError, TypeError, KeyError):
                continue
        txid = record.get("txid")
        if not txid:
            ids = {entry["txid"] for entry in matches}
            if len(ids) != 1:
                record["reconciliation"] = "No unique outgoing payload match; never retry"
                self.save(record)
                return record
            txid = ids.pop()
            record.update(txid=txid, status="submitted")
        sent = [entry for entry in matches if entry.get("txid") == txid]
        if sent:
            record["sender_evidence"] = metadata(sent[0])
        incoming = bob.incoming()
        for entry in incoming:
            if (
                entry.get("txid") != txid
                or entry.get("incoming") is not True
                or entry.get("amount") != AMOUNT
                or entry.get("payloaderror")
            ):
                continue
            decoded = from_rpc(entry.get("payload_rpc", []))
            record["receiver_evidence"] = metadata(entry)
            record["received_hex"] = decoded.hex()
            record["received_sha256"] = hashlib.sha256(decoded).hexdigest()
            record["bytes_equal"] = decoded == expected_payload
            if decoded != expected_payload:
                record["status"] = "payload_mismatch"
                break
            record.setdefault("first_observed_at", time.time())
            record["delivery_latency_upper_bound_seconds"] = (
                record["first_observed_at"] - record["submitted_at"]
            )
            record["confirmation_estimate"] = max(0, bob.height() - entry["height"] + 1)
            # Fees must come from the sender history; do not treat missing as zero.
            if sent and isinstance(sent[0].get("fees"), int):
                record["actual_total_atomic"] = AMOUNT + sent[0]["fees"]
                record["within_budget"] = record["actual_total_atomic"] <= BUDGET
                record["status"] = "delivered" if record["within_budget"] else "budget_violation"
            else:
                record["status"] = "delivered_fee_unverified"
            break
        self.save(record)
        return record

    def close(self) -> None:
        self.db.close()


def emit(value: dict) -> None:
    typer.echo(json.dumps(value, indent=2))


@app.command("health")
def health_command() -> None:
    """Only read-only wallet methods; never submits transfers."""
    emit(health({name: wallet_for(name) for name in ENDPOINTS}))


@app.command("prepare")
def prepare_command() -> None:
    """Display the exact fixed proposal without granting authorization."""
    probe = Probe(Path(".mainnet/probe.db"))
    try:
        emit(probe.record())
    finally:
        probe.close()


@app.command("broadcast")
def broadcast_command(approve_sha256: str = typer.Option(...)) -> None:
    """ONE paid call: run only after the user explicitly approves this exact digest."""
    probe = Probe(Path(".mainnet/probe.db"))
    try:
        emit({"txid": probe.broadcast(approve_sha256, wallet_for("alice"), wallet_for("bob"))})
    finally:
        probe.close()


@app.command("reconcile")
def reconcile_command() -> None:
    """Read-only history inspection, byte comparison, fee and latency evidence."""
    probe = Probe(Path(".mainnet/probe.db"))
    try:
        emit(probe.reconcile(wallet_for("alice"), wallet_for("bob")))
    finally:
        probe.close()


if __name__ == "__main__":
    os.umask(0o077)
    try:
        app()
    except (RPCError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from None
