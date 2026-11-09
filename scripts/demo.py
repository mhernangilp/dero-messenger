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

    for name in ("alice", "bob"):
        run(name, "setup", "--address", f"sim:{name}", "--chain", str(root / "chain.db"))
    a = json.loads(run("alice", "identity"))["public_key"]
    b = json.loads(run("bob", "identity"))["public_key"]
    # The demo directly obtains the correct public keys from both local profiles.
    run("alice", "contacts", "add", "sim:bob", "--alias", "Bob", "--identity", b, "--verified")
    run("bob", "contacts", "add", "sim:alice", "--alias", "Alice", "--identity", a, "--verified")
    request = run("alice", "chat", "request", "Bob")
    sid = re.search(r"\b[0-9a-f]{32}\b", request).group()
    run("bob", "sync")
    run("bob", "chat", "requests")
    run("bob", "chat", "accept", sid)
    run("alice", "sync")
    run("alice", "chat", "send", "Bob", "Hello Bob, this is an encrypted message over DERO.")
    run("bob", "sync")
    assert "Hello Bob" in run("bob", "chat", "read", "Alice")
    run("bob", "chat", "send", "Alice", "Hello Alice, your message decrypted successfully.")
    run("alice", "sync")
    # Every invocation is a fresh process, including after Alice goes offline.
    run("bob", "chat", "send", "Alice", "This message waited while you were offline.")
    run("alice", "sync")
    assert "waited while you were offline" in run("alice", "chat", "read", "Bob")
    print("PASS: independent profiles, authenticated session, replies, and offline recovery.")
    print(root)


if __name__ == "__main__":
    main()
