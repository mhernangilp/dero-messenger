"""Unpaid three-wallet planning and durable per-transaction spending limits."""

import hashlib
import json
import os
import re
import sqlite3
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

from .protocol import CHUNK, MAX_TEXT, payload_rpc
from .storage import private_directory

FEE = 181
AMOUNT = 1
LONG_TEXT = "L" * 512


def fragment_count(envelope_bytes: int) -> int:
    if envelope_bytes < 1:
        raise ValueError("Empty envelope")
    return (envelope_bytes + CHUNK - 1) // CHUNK


def message_count(text: str) -> int:
    size = len(text.encode("utf-8"))
    if not 1 <= size <= MAX_TEXT:
        raise ValueError("Invalid message size")
    return fragment_count(42 + size)


def plan() -> dict:
    steps = [
        ("alice", "bob", "request", 312),
        ("bob", "alice", "accept", 146),
        ("charlie", "bob", "request", 312),
        ("bob", "charlie", "accept", 146),
        ("alice", "bob", "Hello Bob!", 52),
        ("charlie", "bob", "Hello Bob!", 52),
        ("bob", "alice", "Hello Alice!", 54),
        ("bob", "charlie", "Hello Charlie!", 56),
        ("alice", "bob", "512 ASCII L characters", 42 + len(LONG_TEXT)),
        ("charlie", "bob", "Offline message", 57),
    ]
    rows = [
        dict(
            sender=a,
            destination=b,
            operation=label,
            envelope_bytes=n,
            transactions=fragment_count(n),
            max_debit_atomic=fragment_count(n) * (FEE + AMOUNT),
        )
        for a, b, label, n in steps
    ]
    totals = {
        name: sum(row["transactions"] for row in rows if row["sender"] == name)
        for name in ("alice", "bob", "charlie")
    }
    count = sum(totals.values())
    return dict(
        status="proposal_only_no_spending_authorization",
        steps=rows,
        transactions=count,
        amount_per_tx=AMOUNT,
        fee_per_tx=FEE,
        max_debit_atomic=count * (FEE + AMOUNT),
        fees_atomic=count * FEE,
        per_wallet_transactions=totals,
        per_wallet_debit_atomic={n: t * (FEE + AMOUNT) for n, t in totals.items()},
        gross_mining_reward_dero="0.09225",
        observed_hashrate_kh_s="2.78",
        historical_probe_equivalents=str(Decimal("0.09225") / Decimal("0.00182")),
        historical_mining_minutes_for_plan=str(
            Decimal(count * (FEE + AMOUNT)) / Decimal(100000) / Decimal("0.09225") * 60
        ),
    )


def pending_proposal(state: dict, fee: int) -> dict:
    """Public transaction proposal only; exclude identity secrets and session keys."""
    if not 1 <= fee <= 100000:
        raise ValueError("Invalid configured fee")
    if any(item["status"] == "sending" for item in state["outbox"]):
        raise ValueError("Uncertain submission; reconcile before proposing more transfers")
    rows = []
    for item in state["outbox"]:
        if item["status"] != "pending":
            continue
        packet = bytes.fromhex(item["payload"])
        rows.append(
            dict(
                sender=state["address"],
                destination=item["destination"],
                payload_hex=packet.hex(),
                payload_sha256=hashlib.sha256(packet).hexdigest(),
                envelope_id=item["envelope_id"],
                maximum_debit_atomic=fee + 1,
                rpc=dict(
                    method="Transfer",
                    params=dict(
                        transfers=[
                            dict(
                                destination=item["destination"],
                                amount=1,
                                payload_rpc=payload_rpc(packet),
                            )
                        ],
                        ringsize=16,
                        fees=fee,
                    ),
                ),
            )
        )
    body = dict(
        status="proposal_only_no_authorization",
        transactions=rows,
        count=len(rows),
        maximum_debit_atomic=len(rows) * (fee + 1),
    )
    body["proposal_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return body


class SpendingGate:
    """All clients must share this ledger; reservations never expire or auto-release.

    The policy is immutable once the ledger is created. Wallet/OS behavior remains
    trusted; this is not a sandbox against other programs with unlocked RPC access.
    """

    def __init__(self, path: Path, policy: dict):
        if set(policy) != {"participants", "max_transactions", "max_debit_atomic", "fee_atomic"}:
            raise ValueError("Invalid spending policy fields")
        if not isinstance(policy["participants"], dict) or len(policy["participants"]) != 3:
            raise ValueError("Policy requires three distinct wallet addresses")
        for address, limit in policy["participants"].items():
            if (
                not isinstance(address, str)
                or not address.startswith("dero1")
                or len(address) != 66
            ):
                raise ValueError("Policy requires standard DERO addresses")
            if type(limit) is not int or limit < 1:
                raise ValueError("Invalid per-wallet transaction limit")
        for field in ("max_transactions", "max_debit_atomic", "fee_atomic"):
            if type(policy[field]) is not int or policy[field] < 1:
                raise ValueError("Policy limits must be positive integers")
        self.policy = policy
        private_directory(path.parent)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        path.chmod(0o600)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=30)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY, body TEXT)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS attempts "
            "(digest TEXT PRIMARY KEY, sender TEXT, cost INTEGER, "
            "status TEXT, txid TEXT, balance_before INTEGER)"
        )
        encoded = json.dumps(policy, sort_keys=True)
        self.db.execute("INSERT OR IGNORE INTO policy VALUES (1, ?)", (encoded,))
        if self.db.execute("SELECT body FROM policy WHERE id=1").fetchone()[0] != encoded:
            self.db.close()
            raise ValueError("Spending policy changed; existing budget cannot be reset")

    def submit(
        self,
        sender: str,
        destination: str,
        packet: bytes,
        fee: int,
        unlocked_balance: int,
        approved: bool,
        broadcast: Callable[[], str],
    ) -> str:
        if approved is not True:
            raise ValueError("Every transaction requires explicit human approval")
        if (
            sender not in self.policy["participants"]
            or destination not in self.policy["participants"]
            or sender == destination
            or fee != self.policy["fee_atomic"]
        ):
            raise ValueError("Transfer is outside the approved spending policy")
        payload_rpc(packet)
        cost = 1 + fee
        if type(unlocked_balance) is not int or unlocked_balance < cost:
            raise ValueError("Insufficient unlocked funds")
        digest = hashlib.sha256(
            json.dumps(
                [sender, destination, packet.hex(), 1, fee, 16], separators=(",", ":")
            ).encode()
        ).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            count, spent = self.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(cost),0) FROM attempts"
            ).fetchone()
            own = self.db.execute(
                "SELECT COUNT(*) FROM attempts WHERE sender=?", (sender,)
            ).fetchone()[0]
            if self.db.execute("SELECT 1 FROM attempts WHERE status='uncertain'").fetchone():
                raise ValueError("Uncertain submission blocks spending; reconcile history first")
            if self.db.execute("SELECT 1 FROM attempts WHERE digest=?", (digest,)).fetchone():
                raise ValueError("This exact fragment already consumed its authorization")
            if (
                count >= self.policy["max_transactions"]
                or spent + cost > self.policy["max_debit_atomic"]
                or own >= self.policy["participants"][sender]
            ):
                raise ValueError("Experiment spending limit reached")
            self.db.execute(
                "INSERT INTO attempts VALUES (?,?,?,'uncertain',NULL,?)",
                (digest, sender, cost, unlocked_balance),
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        # Any exception leaves the reservation consumed and blocks further spending.
        txid = broadcast()
        if not isinstance(txid, str) or not re.fullmatch("[0-9a-f]{64}", txid):
            raise ValueError("Invalid txid; submission remains uncertain")
        self.db.execute(
            "UPDATE attempts SET status='submitted', txid=? WHERE digest=?", (txid, digest)
        )
        return txid

    def lookup(self, sender: str, destination: str, packet: bytes, fee: int) -> tuple | None:
        """Read an existing reservation; never create or release one."""
        digest = hashlib.sha256(
            json.dumps(
                [sender, destination, packet.hex(), 1, fee, 16], separators=(",", ":")
            ).encode()
        ).hexdigest()
        return self.db.execute(
            "SELECT status,txid FROM attempts WHERE digest=?", (digest,)
        ).fetchone()

    def close(self) -> None:
        self.db.close()


if __name__ == "__main__":
    print(json.dumps(plan(), indent=2))
