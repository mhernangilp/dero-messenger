# Validation record

Latest encrypted-greeting revision: **46 tests passed** (1.45 seconds). The prepared
41-byte AES-GCM probe has not been sent. PSK round-trip, tamper/wrong-key rejection,
and preservation of the one-call budget when superseding an unspent proposal pass.
See mainnet-validation.md for the replacement authorization state.

## Latest Release153 validation (2026-11-09)

- `pytest -q`: **44 passed** (1.49 seconds). Paid paths are mocked; real HTTP is
  forbidden by an autouse test fixture.
- Ruff lint and formatting: passed; 20 Python files formatted.
- Separate-process simulation: passed after the RPC and fragment-capacity fixes.
- Release153 native serializer round-trip: 24 and 78 bytes passed; 79 bytes exceeded
  the 111-byte serialized limit.
- Read-only live Mainnet Wallet RPC checks: both identities, balances, address
  parsing, and known-transaction history verified. Daemon reports Release152.
- Single 24-byte probe: prepared locally, not authorized, not broadcast.
- See [Mainnet validation](mainnet-validation.md) and its timestamped JSON snapshots.

The earlier validation record below is historical. Its no-listener result and
102-byte capacity do not describe the current Release153 setup.

## Initial validation record

Date: 2026-11-09. Local environment: Linux, Python 3.14.9, Go 1.27.3-X:nodwarf5.
Exact Python package versions are recorded in `requirements-dev.lock`.

## Executed successfully

- `.venv/bin/pytest -q`: **36 passed** (1.42 seconds in the final test run).
- `.venv/bin/ruff check src tests scripts`: passed.
- `.venv/bin/ruff format --check src tests scripts`: 18 files already formatted.
- `.venv/bin/dero-chat --help`: CLI entry point loads and exposes all command groups.
- `.venv/bin/python scripts/demo.py`: passed using separate CLI processes for every
  operation, independent encrypted profiles, a signed handshake, the exact requested
  greeting, a reply, and a second reply retrieved after Alice restarted.
- `go run -mod=vendor payload_probe.go` in pinned upstream source: 102 bytes accepted
  at 142 serialized bytes; 103, 104, and 105 rejected at 146 serialized bytes.
- `go build -mod=vendor -o /tmp/dero-official-wallet ./cmd/dero-wallet-cli` in the
  pinned upstream repository: passed. The executable was compiled, not used to
  create funded wallets or send transactions.

The full final simulation transcript is retained in `docs/demo-output.txt`.
Its identities are disposable public keys, and its temporary profile path is
specific to this execution. Re-running creates fresh random identities/session IDs.
No private key, passphrase, seed, or wallet credential is included in the transcript.
The demo source contains only a deliberately public simulation passphrase.

## Explicitly not validated

No local listeners were found at 127.0.0.1:10102, :10103, :20209, or :20210.
No live DERO node/wallet round trip, account registration, funding, Mainnet fee
acceptance, minimum-amount acceptance, or real-chain offline retrieval was performed.
No paid Mainnet operation was authorized or attempted. No miner was launched.
No claim of live deployment compatibility follows from mocked RPC tests.

The official wallet source build was tested; the README daemon build command and
Arch-specific package installation were not executed. Python 3.11/3.12/3.13 and
other OS distributions were not separately exercised. Cryptographic tests are not
a security audit. Reorganization behavior and traffic-analysis resistance are not
validated guarantees.
