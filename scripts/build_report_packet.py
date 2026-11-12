"""Build a public-only evidence packet for an external report writer."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/report-evidence.zip"
FILES = (
    "README.md",
    "pyproject.toml",
    "docs/report-handoff.md",
    "docs/README.md",
    "docs/running.md",
    "docs/final-report-source.md",
    "docs/bob-plaintext-confirmation.md",
    "docs/alice-request-validation.md",
    "docs/handshake-validation.md",
    "docs/alice-message-validation.md",
    "docs/mainnet-probe-result.json",
    "docs/alice-request-proposal.json",
    "docs/alice-request-result.json",
    "docs/bob-response-proposal.json",
    "docs/bob-response-result.json",
    "docs/handshake-delivery.json",
    "docs/alice-message-proposal.json",
    "docs/alice-message-result.json",
    "docs/alice-message-delivery.json",
    "docs/dero-findings.md",
    "docs/release153-capacity.txt",
    "docs/protocol.md",
    "docs/architecture.md",
    "docs/threat-model.md",
    "docs/privacy-analysis.md",
    "docs/validation.md",
    "docs/mainnet-validation.md",
    "docs/three-wallet-plan.md",
    "docs/three-wallet-budget.json",
    "docs/demo-three-output.txt",
    "docs/three-wallet-health-2026-11-11.json",
    "docs/three-wallet-identities.json",
    "docs/probe-public-observations.json",
    "src/dero_messenger/crypto.py",
    "src/dero_messenger/protocol.py",
    "src/dero_messenger/transport.py",
    "src/dero_messenger/conversations.py",
    "src/dero_messenger/storage.py",
    "src/dero_messenger/wallet.py",
    "src/dero_messenger/rpc.py",
    "src/dero_messenger/experiment.py",
    "scripts/demo_three.py",
    "scripts/payload_capacity_test.go",
)


def build() -> None:
    """Copy only explicitly reviewed public files and hash their contents."""
    manifest: dict[str, object] = {
        "description": "Public DERO Private Messenger PoC report evidence",
        "scope": "Alice/Bob Mainnet session; three-wallet simulation",
        "files": {},
    }
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            path = ROOT / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Missing or symlinked evidence file: {name}")
            contents = path.read_bytes()
            archive.writestr(name, contents)
            manifest["files"][name] = {
                "sha256": hashlib.sha256(contents).hexdigest(),
                "bytes": len(contents),
            }
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {*FILES, "MANIFEST.json"}
    print(f"Created {OUTPUT} with {len(FILES)} public files")


if __name__ == "__main__":
    build()
