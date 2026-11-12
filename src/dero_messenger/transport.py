"""Simulated ledger and explicitly enabled official DERO Wallet RPC transport."""

import hashlib
import json
import os
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .experiment import SpendingGate
from .protocol import CAPACITY, from_rpc, payload_rpc
from .rpc import RPCError
from .storage import private_directory
from .wallet import Wallet


@dataclass
class Transfer:
    txid: str
    position: int
    height: int
    confirmations: int
    payload: bytes
    reported_sender: str = ""
    fee_atomic: int | None = None
    topoheight: int | None = None
    blockhash: str = ""
    timestamp: str = ""

    @property
    def key(self) -> str:
        return f"{self.txid}:{self.position}"


class Transport(Protocol):
    def validate(self, address: str) -> None: ...
    def ready(self, txid: str) -> bool: ...
    def send(self, destination: str, payload: bytes) -> str: ...
    def incoming(self) -> tuple[int, list[Transfer]]: ...


class Simulated:
    def __init__(self, path: Path, address: str):
        private_directory(path.parent)
        self.address = address
        self.db = sqlite3.connect(path, timeout=30)
        path.chmod(0o600)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS ledger "
            "(height INTEGER PRIMARY KEY AUTOINCREMENT, txid TEXT UNIQUE, "
            "destination TEXT, payload BLOB)"
        )
        self.db.commit()

    def ready(self, txid: str) -> bool:
        return True

    def validate(self, address: str) -> None:
        if not address.isascii() or not 1 <= len(address) <= 128:
            raise ValueError("Invalid simulated address")
        if any(ord(c) < 33 or ord(c) > 126 for c in address):
            raise ValueError("Invalid simulated address")

    def send(self, destination: str, payload: bytes) -> str:
        self.validate(destination)
        payload_rpc(payload)
        txid = hashlib.sha256(self.address.encode() + destination.encode() + payload).hexdigest()
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO ledger (txid,destination,payload) VALUES (?,?,?)",
                (txid, destination, payload),
            )
        return txid

    def incoming(self) -> tuple[int, list[Transfer]]:
        height = self.db.execute("SELECT COALESCE(MAX(height),0) FROM ledger").fetchone()[0]
        rows = self.db.execute(
            "SELECT txid,height,payload FROM ledger WHERE destination=? ORDER BY height",
            (self.address,),
        )
        return height, [Transfer(t, 0, h, height - h + 1, p) for t, h, p in rows]


class Dero:
    def __init__(
        self,
        wallet: Wallet,
        address: str,
        enabled: bool = False,
        fee_atomic: int = 121,
        confirm: Callable[[str], bool] | None = None,
        spending_gate: SpendingGate | None = None,
    ):
        self.wallet, self.address, self.enabled = wallet, address, enabled
        self.fee_atomic, self.confirm = fee_atomic, confirm
        self.spending_gate = spending_gate

    def ready(self, txid: str) -> bool:
        try:
            entry = self.wallet.rpc.call("GetTransferbyTXID", {"txid": txid})["entry"]
            return entry.get("txid") == txid and int(entry.get("height", 0)) > 0
        except RPCError as exc:
            if exc.not_found:
                return False
            raise

    def validate(self, address: str) -> None:
        self.wallet.validate(address)

    def send(self, destination: str, payload: bytes) -> str:
        if not self.enabled:
            raise ValueError("Mainnet sends are disabled")
        if self.wallet.address() != self.address:
            raise ValueError("Wallet does not match profile")
        self.validate(destination)
        args = payload_rpc(payload)
        if not 1 <= self.fee_atomic <= 100000:
            raise ValueError("Fee must be between 1 and 100000 atomic units")
        parameters = {
            "transfers": [{"destination": destination, "amount": 1, "payload_rpc": args}],
            "ringsize": 16,
            "fees": self.fee_atomic,
        }
        prompt = (
            f"Sender {self.address}; destination {destination}; amount 1 atomic (0.00001 DERO); "
            f"configured fee {self.fee_atomic} atomic; maximum intended debit "
            f"{1 + self.fee_atomic} atomic; payload {len(payload)}/{CAPACITY} bytes. "
            f"Payload hex: {payload.hex()}; SHA-256: {hashlib.sha256(payload).hexdigest()}. "
            f"RPC Transfer parameters: {json.dumps(parameters, sort_keys=True)}. "
            "Configured fee is not a live quote. Submit this transaction only?"
        )
        if self.confirm is None or not self.confirm(prompt):
            raise ValueError("Transfer not confirmed")
        if self.spending_gate is None:
            raise ValueError("A shared experiment spending policy is required for paid sends")
        balance = self.wallet.rpc.call("GetBalance", {})["unlocked_balance"]
        return self.spending_gate.submit(
            self.address,
            destination,
            payload,
            self.fee_atomic,
            balance,
            True,
            lambda: self.wallet.rpc.call(
                "Transfer",
                parameters,
            )["txid"],
        )

    def reconcile(self, destination: str, payload: bytes) -> str | None:
        """Match a submitted reservation against official history without broadcasting."""
        if self.wallet.address() != self.address or self.spending_gate is None:
            raise ValueError("Matching wallet and shared spending ledger required")
        known = self.spending_gate.lookup(self.address, destination, payload, self.fee_atomic)
        if known is None:
            return None
        if known[0] != "submitted" or not known[1]:
            raise ValueError("Uncertain reservation needs manual history reconciliation")
        try:
            entry = self.wallet.rpc.call("GetTransferbyTXID", {"txid": known[1]})["entry"]
        except RPCError as exc:
            if exc.not_found:
                return None
            raise
        if int(entry.get("height", 0)) <= 0:
            return None
        if (
            entry.get("txid") != known[1]
            or entry.get("incoming") is not False
            or entry.get("destination") != destination
            or entry.get("payloaderror")
            or int(entry.get("amount", -1)) != 1
            or int(entry.get("fees", -1)) != self.fee_atomic
            or from_rpc(entry.get("payload_rpc", [])) != payload
        ):
            raise ValueError("Reserved transaction does not match official history")
        return known[1]

    def incoming(self) -> tuple[int, list[Transfer]]:
        if self.wallet.address() != self.address:
            raise ValueError("Wallet does not match profile")
        height = self.wallet.height()
        entries = self.wallet.incoming()
        transfers = []
        for entry in entries:
            if not entry.get("incoming") or entry.get("coinbase") or entry.get("payloaderror"):
                continue
            try:
                packet = from_rpc(entry.get("payload_rpc", []))
                h = int(entry["height"])
                transfers.append(
                    Transfer(
                        entry["txid"],
                        int(entry.get("pos", 0)),
                        h,
                        max(0, height - h + 1),
                        packet,
                        str(entry.get("sender", ""))[:128],
                        int(entry["fees"]) if "fees" in entry else None,
                        int(entry["topoheight"]) if "topoheight" in entry else None,
                        str(entry.get("blockhash", ""))[:64],
                        str(entry.get("time", ""))[:80],
                    )
                )
            except (ValueError, KeyError, TypeError):
                continue
        return height, sorted(transfers, key=lambda t: (t.height, t.txid, t.position))


def wallet_auth() -> tuple[str, str] | None:
    user, password = os.getenv("DERO_WALLET_USER"), os.getenv("DERO_WALLET_PASSWORD")
    if bool(user) != bool(password):
        raise ValueError("Set both wallet RPC credential variables")
    return (user, password) if user and password else None
