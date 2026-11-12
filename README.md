# ChainChat — DERO Proof of Value

A research proof of concept for **ChainChat**, a broader project exploring
blockchains as cover channels for communication with privacy and anonymity.
DERO Stargate is one of the blockchain transports being evaluated.

This Python CLI demonstrates asynchronous, authenticated, end-to-end encrypted
messaging over ordinary DERO transfers, without a centralized messaging server.
Anonymity is a research objective; this PoC does not establish anonymity against
traffic analysis or a global observer.

## What works

- Independent profiles, local contacts and fingerprint verification.
- Ed25519-authenticated X25519 exchange, HKDF-SHA256 and directional AES-256-GCM keys.
- Fragmentation, replay protection, encrypted local persistence and offline retrieval.
- A simulated backend for testing without wallets, funds or a daemon.

**Mainnet result:** Alice and Bob completed an authenticated handshake and Bob
read `Hello Bob, this is an encrypted message over DERO.` Eleven transactions
cost **0.02002 DERO** gross. The earlier pre-shared-key probe cost 0.00182 DERO
separately. Three participants, a longer message and offline recovery passed in
simulation; Charlie's Mainnet session and stopped-wallet recovery remain untested.
See the [experiment report](docs/final-report-source.md) for TXIDs and evidence limits.

## Install on Arch Linux

Python 3.11+ is declared; the recorded local validation used Python 3.14.9.
Use a virtual environment:

```bash
sudo pacman -S --needed python python-pip git
git clone https://github.com/mhernangilp/dero-messenger.git
cd dero-messenger
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
```

The lock file records the validated dependency versions. To resolve compatible
dependencies instead, use `python -m pip install -e '.[dev]'` inside the venv.

## Run the demonstrations

```bash
# Alice/Bob: handshake, encrypted greeting, reply and offline application recovery.
python scripts/demo.py

# Alice/Bob/Charlie: separate sessions, a ten-fragment message and offline recovery.
python scripts/demo_three.py
```

Each demo creates disposable profiles in a temporary directory and runs CLI
commands in separate processes. Success ends with `PASS` and the artifact path.
These demos use only the simulated transport and spend no funds.

For manual CLI commands and the reviewed Mainnet sequence, see
[Running the PoC](docs/running.md). Inspect commands with `dero-chat --help`.
Mainnet requires already-running official wallets on localhost, verified contact
fingerprints, explicit enablement, a shared spending policy and approval for each
transfer. Application passphrases are separate from wallet passwords.

## Test

```bash
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
```

The latest local run passed **81 tests**. Paid paths are mocked and tests block
real HTTP. Tests cover cryptography, tampering, replay, payload boundaries,
fragmentation, persistence, nonce safety across restarts and offline synchronization.

## Research notes

Release153 accepts **78 binary packet bytes** with this app's encoding, leaving
**58 bytes** after the fragment header. Each fragment needs its own transfer.
Application identities require external fingerprint verification and do not prove
ownership of a DERO address. Public ring members and network metadata can aid
correlation; DERO privacy does not automatically provide application anonymity.

This is an unaudited research prototype. It has no Double Ratchet or deep-reorg
rollback. Preserve application profiles; never send from cloned or rolled-back
state. Keep wallet files, credentials and local profiles out of Git.

- [Documentation index](docs/README.md)
- [Protocol and wire format](docs/protocol.md)
- [DERO RPC and payload findings](docs/dero-findings.md)
- [Threat model](docs/threat-model.md) and [privacy analysis](docs/privacy-analysis.md)
- [Validation record](docs/validation.md)

Source code is under `src/dero_messenger/`, tests under `tests/`, and reproducible
demos and evidence tools under `scripts/`.
