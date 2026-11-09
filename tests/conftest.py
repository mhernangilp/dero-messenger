from pathlib import Path

import pytest

from dero_messenger.conversations import Messenger, initial_state
from dero_messenger.storage import Store
from dero_messenger.transport import Simulated

PASSWORD = "test passphrase is long enough"


def participant(root: Path, name: str) -> Messenger:
    store = Store(root / name / "state.db", PASSWORD, initial_state(f"sim:{name}"))
    return Messenger(store, Simulated(root / "chain" / "ledger.db", f"sim:{name}"))


@pytest.fixture
def pair(tmp_path):
    alice, bob = participant(tmp_path, "alice"), participant(tmp_path, "bob")
    alice.add_contact("sim:bob", "Bob", bob.identity()["public_key"])
    bob.add_contact("sim:alice", "Alice", alice.identity()["public_key"])
    yield alice, bob
    alice.store.close()
    bob.store.close()
    alice.transport.db.close()
    bob.transport.db.close()


def establish(alice, bob):
    sid = alice.request("Bob")
    bob.sync()
    bob.accept(sid)
    alice.sync()
    return sid


@pytest.fixture(autouse=True)
def forbid_real_http_in_tests(monkeypatch):
    import httpx

    def forbidden(*args, **kwargs):
        raise AssertionError("Real HTTP is forbidden in tests; use a mocked transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", forbidden)
