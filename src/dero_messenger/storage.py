"""Encrypted SQLite snapshot with transactional serialization of all state changes."""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import crypto

AAD = b"dero-chat/database/schema-1"


def private_directory(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("Profile directory must not be a symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)


class Store:
    def __init__(self, path: Path, passphrase: str, initial: dict | None = None):
        private_directory(path.parent)
        if path.is_symlink():
            raise ValueError("Database must not be a symlink")
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        path.chmod(0o600)
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported database schema")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, "
                "salt BLOB NOT NULL, ciphertext BLOB NOT NULL)"
            )
            row = self.db.execute("SELECT salt, ciphertext FROM state WHERE id=1").fetchone()
            if row is None:
                if initial is None:
                    raise ValueError("Profile is not initialized; run setup")
                salt = os.urandom(16)
                self.key = crypto.password_key(passphrase, salt)
                blob = crypto.seal(self.key, json.dumps(initial).encode(), AAD)
                self.db.execute("INSERT INTO state VALUES (1, ?, ?)", (salt, blob))
                self.db.execute("PRAGMA user_version=1")
            else:
                self.key = crypto.password_key(passphrase, row[0])
                crypto.unseal(self.key, row[1], AAD)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            self.db.close()
            raise

    @contextmanager
    def transaction(self) -> Iterator[dict]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            blob = self.db.execute("SELECT ciphertext FROM state WHERE id=1").fetchone()[0]
            state = json.loads(crypto.unseal(self.key, blob, AAD))
            yield state
            blob = crypto.seal(self.key, json.dumps(state).encode(), AAD)
            self.db.execute("UPDATE state SET ciphertext=? WHERE id=1", (blob,))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def snapshot(self) -> dict:
        with self.transaction() as state:
            return state

    def close(self) -> None:
        self.db.close()
