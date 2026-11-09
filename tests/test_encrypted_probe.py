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
