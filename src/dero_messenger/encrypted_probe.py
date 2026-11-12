"""One-transfer PSK demo with a passphrase-encrypted, restartable key store.

Preparation is local only. Sending still requires approval of the exact proposal.
Resuming an already reserved experiment performs read-only reconciliation only.
"""

import argparse
import getpass
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .mainnet_probe import ALICE, BOB, Probe, emit, wallet_for
from .rpc import RPCError
from .storage import Store

MAGIC = b"CP\x01"
AAD = b"ChainChat PSK probe v1\x00" + ALICE.encode() + b"\x00" + BOB.encode()
GREETING = b"Hello Bob!"


def encrypt_greeting(key: bytes) -> bytes:
    nonce = os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, GREETING, AAD + MAGIC)


def decrypt_greeting(key: bytes, packet: bytes) -> str:
    if not packet.startswith(MAGIC) or len(packet) != 41:
        raise ValueError("Invalid PSK probe packet")
    plaintext = AESGCM(key).decrypt(packet[3:15], packet[15:], AAD + MAGIC)
    if plaintext != GREETING:
        raise ValueError("Unexpected probe plaintext")
    return plaintext.decode("utf-8")


def replace_unspent_proposal(probe: Probe) -> None:
    """Supersede only a never-submitted proposal; preserve the single experiment budget."""
    probe.db.execute("BEGIN IMMEDIATE")
    try:
        record = probe.record()
        if record["status"] != "prepared" or record["transfer_calls_reserved"] != 0:
            raise ValueError("Cannot replace a submitted or uncertain experiment")
        history = record.get("superseded_proposals", [])
        if record["proposal_sha256"] != probe.digest:
            history.append(record["proposal_sha256"])
        record.update(
            proposal=probe.proposal, proposal_sha256=probe.digest, superseded_proposals=history
        )
        probe.save(record)
        probe.db.execute("COMMIT")
    except BaseException:
        probe.db.execute("ROLLBACK")
        raise


def load_key(directory: Path, passphrase: str, *, create: bool = False) -> tuple[bytes, bytes]:
    path = directory / "encrypted-key.db"
    initial = None
    if not create and not path.exists():
        raise ValueError("Probe key store is missing; do not regenerate a submitted probe")
    if create:
        # Store uses initial only when no encrypted row exists. This also recovers
        # an empty file left by an interrupted or previously failed initialization.
        key = AESGCM.generate_key(bit_length=256)
        initial = {
            "purpose": "chainchat-psk-probe-v1",
            "key": key.hex(),
            "packet": encrypt_greeting(key).hex(),
        }
    store = Store(path, passphrase, initial)
    try:
        state = store.snapshot()
        if state.get("purpose") != "chainchat-psk-probe-v1":
            raise ValueError("Wrong encrypted key store")
        key, packet = bytes.fromhex(state["key"]), bytes.fromhex(state["packet"])
        decrypt_greeting(key, packet)
        return key, packet
    finally:
        store.close()


def prepare_persistent(directory: Path, passphrase: str) -> dict:
    previous = Probe(directory / "probe.db")
    try:
        record = previous.record()
        if record["status"] != "prepared" or record["transfer_calls_reserved"] != 0:
            raise ValueError("Cannot prepare a replacement after any submission attempt")
    finally:
        previous.close()
    _, packet = load_key(directory, passphrase, create=True)
    probe = Probe(directory / "probe.db", packet)
    try:
        replace_unspent_proposal(probe)
        return probe.record()
    finally:
        probe.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    args = parser.parse_args()
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    passphrase = os.getenv("DERO_CHAT_PASSPHRASE")
    if not passphrase:
        if not sys.stdin.isatty():
            raise ValueError("Run in a private terminal to enter the application passphrase")
        passphrase = getpass.getpass("Application encryption passphrase (not wallet password): ")
        if args.action == "prepare":
            if passphrase != getpass.getpass("Confirm application passphrase: "):
                raise ValueError("Passphrases do not match")
    directory = Path(".mainnet")
    if args.action == "prepare":
        emit(prepare_persistent(directory, passphrase))
        print("Prepared locally. Key encrypted on disk; no network calls or spending.")
        return
    key, packet = load_key(directory, passphrase)
    probe = Probe(directory / "probe.db", packet)
    try:
        record = probe.record()
        if record["proposal"] != probe.proposal:
            raise ValueError("Stored key/packet does not match the prepared proposal")
        emit(record)
        reserved = record["transfer_calls_reserved"] == 1
        if not reserved:
            print(
                "Enter the exact proposal SHA-256 ONLY after approval; other input cancels:",
                flush=True,
            )
            if input().strip() != probe.digest:
                print("No authorization supplied; nothing submitted.")
                return
        else:
            print("Prior attempt already reserved: read-only reconciliation, no resend.")
        alice, bob = wallet_for("alice"), wallet_for("bob")
        if not reserved:
            try:
                txid = probe.broadcast(probe.digest, alice, bob)
                print(f"Submitted txid: {txid}", flush=True)
            except (RPCError, ValueError) as exc:
                print(f"Submission stopped: {exc}. No retry will occur.", flush=True)
                if probe.record()["transfer_calls_reserved"] != 1:
                    return
        # Only read-only calls follow the one permitted submission attempt.
        while True:
            try:
                result = probe.reconcile(alice, bob)
                if result.get("bytes_equal"):
                    greeting = decrypt_greeting(key, bytes.fromhex(result["received_hex"]))
                    print(f"Bob decrypted and authenticated: {greeting}", flush=True)
                    result["psk_decryption_verified"] = True
                    result["plaintext_sha256"] = hashlib.sha256(GREETING).hexdigest()
                    # Do not persist message plaintext or key in the evidence database.
                    probe.save(result)
                    emit(result)
                    if result.get("status") in ("delivered", "budget_violation"):
                        return
                else:
                    print("Waiting for wallet indexing; read-only reconciliation.", flush=True)
            except (RPCError, ValueError, InvalidTag) as exc:
                print(f"Read-only verification: {type(exc).__name__}. No resend.", flush=True)
            time.sleep(10)
    finally:
        probe.close()


if __name__ == "__main__":
    try:
        main()
    except InvalidTag:
        print("Incorrect application passphrase or damaged encrypted key store.")
        raise SystemExit(1) from None
    except (ValueError, RPCError, EOFError) as exc:
        # No raw upstream responses, cryptographic keys, or local variables are printed.
        print(json.dumps({"error": str(exc)}))
        raise SystemExit(1) from None
