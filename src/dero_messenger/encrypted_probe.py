"""Interactive, one-transfer pre-shared-key demo with key retained only in memory.

No network request occurs until the exact displayed proposal digest is entered.
The key is never printed or intentionally persisted. Process loss loses the key;
reconciliation can still verify ciphertext delivery, but cannot recover plaintext.
"""

import hashlib
import json
import os
import resource
import time
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .mainnet_probe import ALICE, BOB, Probe, emit, wallet_for
from .rpc import RPCError

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


def main() -> None:
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    key = AESGCM.generate_key(bit_length=256)
    packet = encrypt_greeting(key)
    assert decrypt_greeting(key, packet) == "Hello Bob!"
    probe = Probe(Path(".mainnet/probe.db"), packet)
    try:
        replace_unspent_proposal(probe)
        emit(probe.record())
        print("AES-256-GCM greeting: Hello Bob!; key held only in this process.", flush=True)
        print(
            "No transfer submitted. Enter the exact proposal SHA-256 ONLY after explicit "
            "user approval; any other input exits without sending:",
            flush=True,
        )
        approval = input().strip()
        if approval != probe.digest:
            print("No authorization supplied; nothing submitted.")
            return
        alice, bob = wallet_for("alice"), wallet_for("bob")
        try:
            txid = probe.broadcast(approval, alice, bob)
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
    except (ValueError, RPCError, EOFError) as exc:
        # No raw upstream responses, cryptographic keys, or local variables are printed.
        print(json.dumps({"error": str(exc)}))
        raise SystemExit(1) from None
