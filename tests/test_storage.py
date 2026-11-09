import pytest
from conftest import PASSWORD
from cryptography.exceptions import InvalidTag

from dero_messenger.conversations import initial_state
from dero_messenger.storage import Store


def test_persistence_encryption_permissions_and_wrong_password(tmp_path):
    path = tmp_path / "profile" / "state.db"
    state = initial_state("sim:alice")
    state["messages"] = [{"text": "sensitive plaintext marker"}]
    store = Store(path, PASSWORD, state)
    store.close()
    assert b"sensitive plaintext marker" not in path.read_bytes()
    assert state["identity"].encode() not in path.read_bytes()
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    with pytest.raises(InvalidTag):
        Store(path, "a wrong password long enough")
    store = Store(path, PASSWORD)
    assert store.snapshot() == state
    with pytest.raises(RuntimeError), store.transaction() as mutable:
        mutable["height"] = 123
        raise RuntimeError("crash before commit")
    assert store.snapshot()["height"] == 0
    store.close()
