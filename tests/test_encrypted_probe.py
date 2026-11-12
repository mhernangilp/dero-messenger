import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from dero_messenger.encrypted_probe import (
    decrypt_greeting,
    encrypt_greeting,
    replace_unspent_proposal,
)
from dero_messenger.mainnet_probe import Probe, proposal_digest
from dero_messenger.protocol import from_rpc, payload_rpc


def test_psk_greeting_roundtrip_and_authentication():
    key = AESGCM.generate_key(bit_length=256)
    packet = encrypt_greeting(key)
    assert len(packet) == 41
    assert b"Hello Bob!" not in packet
    assert decrypt_greeting(key, from_rpc(payload_rpc(packet))) == "Hello Bob!"
    assert encrypt_greeting(key) != packet
    with pytest.raises(InvalidTag):
        decrypt_greeting(AESGCM.generate_key(bit_length=256), packet)
    with pytest.raises(InvalidTag):
        decrypt_greeting(key, packet[:-1] + bytes([packet[-1] ^ 1]))


def test_replacement_does_not_reuse_old_approval_or_reset_spending(tmp_path):
    path = tmp_path / "probe.db"
    original = Probe(path)
    original.close()
    key = AESGCM.generate_key(bit_length=256)
    replacement = Probe(path, encrypt_greeting(key))
    replace_unspent_proposal(replacement)
    assert proposal_digest() in replacement.record()["superseded_proposals"]
    with pytest.raises(ValueError, match="approval"):
        replacement.broadcast(proposal_digest(), None, None)
    record = replacement.record()
    record.update(status="submission_uncertain", transfer_calls_reserved=1, reserved_atomic=182)
    replacement.save(record)
    with pytest.raises(ValueError, match="Cannot replace"):
        replace_unspent_proposal(replacement)
    replacement.close()
    assert key not in path.read_bytes()


def test_persistent_key_preserves_exact_packet_and_approval_across_restart(tmp_path):
    from dero_messenger.encrypted_probe import load_key, prepare_persistent

    password = "an independent application passphrase"
    first = prepare_persistent(tmp_path, password)
    key, packet = load_key(tmp_path, password)
    second = prepare_persistent(tmp_path, password)
    key_again, packet_again = load_key(tmp_path, password)
    assert key == key_again and packet == packet_again
    assert first["proposal_sha256"] == second["proposal_sha256"]
    assert decrypt_greeting(key_again, packet_again) == "Hello Bob!"
    disk = (tmp_path / "encrypted-key.db").read_bytes()
    assert key not in disk and key.hex().encode() not in disk
    with pytest.raises(InvalidTag):
        load_key(tmp_path, "incorrect application passphrase")
    assert (tmp_path / "encrypted-key.db").stat().st_mode & 0o777 == 0o600


def test_persistent_prepare_cannot_reset_reserved_budget(tmp_path):
    from dero_messenger.encrypted_probe import load_key, prepare_persistent

    password = "an independent application passphrase"
    prepare_persistent(tmp_path, password)
    _, packet = load_key(tmp_path, password)
    probe = Probe(tmp_path / "probe.db", packet)
    record = probe.record()
    record.update(status="submission_uncertain", transfer_calls_reserved=1, reserved_atomic=182)
    probe.save(record)
    probe.close()
    with pytest.raises(ValueError, match="submission attempt"):
        prepare_persistent(tmp_path, password)
    with pytest.raises(ValueError, match="missing"):
        load_key(tmp_path / "missing", password)


def test_short_passphrase_then_empty_file_initialization_recovers(tmp_path):
    from dero_messenger.encrypted_probe import load_key, prepare_persistent

    with pytest.raises(ValueError, match="12 characters"):
        prepare_persistent(tmp_path, "short")
    path = tmp_path / "encrypted-key.db"
    assert not path.exists()
    # Reproduce the empty file left by the old initialization bug.
    path.touch(mode=0o600)
    password = "a valid application passphrase"
    prepared = prepare_persistent(tmp_path, password)
    key, packet = load_key(tmp_path, password)
    assert packet.hex() == prepared["proposal"]["payload_hex"]
    assert decrypt_greeting(key, packet) == "Hello Bob!"
