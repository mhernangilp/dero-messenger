"""Run the complete simulation in isolated CLI processes; no wallet or network needed."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="dero-chat-demo-"))
    executable = str(Path(sys.executable).parent / "dero-chat")
    env = dict(
        os.environ,
        DERO_CHAT_PASSPHRASE="simulation-only demonstration passphrase",
        NO_COLOR="1",
        TERM="dumb",
        COLUMNS="240",
    )

    def run(name: str, *args: str) -> str:
        result = subprocess.run(
            [executable, "--profile", str(root / name), *args],
            env=env,
            check=True,
            text=True,
            capture_output=True,
        )
        print(f"[{name}] {' '.join(args[:2])}\n{result.stdout.strip()}")
        return result.stdout

    names = ("alice", "bob", "charlie")
    addresses = {n: "dero1" + c * 61 for n, c in zip(names, "qpr", strict=True)}
    # Synthetic 66-character addresses are used only by the simulated backend.
    keys = {}
    for name in names:
        run(name, "setup", "--address", addresses[name], "--chain", str(root / "chain.db"))
        keys[name] = json.loads(run(name, "identity"))["public_key"]
    for sender, receiver in (
        ("alice", "bob"),
        ("bob", "alice"),
        ("charlie", "bob"),
        ("bob", "charlie"),
    ):
        run(
            sender,
            "contacts",
            "add",
            addresses[receiver],
            "--alias",
            receiver,
            "--identity",
            keys[receiver],
            "--verified",
        )
    for sender in ("alice", "charlie"):
        request = run(sender, "chat", "request", "bob")
        sid = re.search(r"\b[0-9a-f]{32}\b", request).group()
        run("bob", "sync")
        run("bob", "chat", "accept", sid)
        run(sender, "sync")
        run(sender, "chat", "send", "bob", "Hello Bob!")
        run("bob", "sync")
        assert "Hello Bob!" in run("bob", "chat", "read", sender)
        run("bob", "chat", "send", sender, f"Hello {sender.capitalize()}!")
        run(sender, "sync")
    run("alice", "chat", "send", "bob", "L" * 512)
    run("bob", "sync")
    assert "L" * 32 in run("bob", "chat", "read", "alice")
    # No Bob process is running while Charlie sends. This is application offline recovery,
    # not evidence that a real DERO wallet can be stopped and resumed successfully.
    run("charlie", "chat", "send", "bob", "Offline message")
    run("bob", "sync")
    assert "Offline message" in run("bob", "chat", "read", "charlie")
    import sqlite3

    with sqlite3.connect(root / "chain.db") as db:
        assert db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 33
    print(
        "PASS: three independent CLI profiles; two authenticated sessions; "
        "separate conversations; ten-fragment message; offline recovery; 33 simulated transfers."
    )
    print(root)


if __name__ == "__main__":
    main()
