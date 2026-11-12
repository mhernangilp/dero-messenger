> Historical working record, archived on 2026-11-12. Pending states and
> commands describe earlier stages; use the [current documentation](../README.md)
> for results and operation. Relative Markdown links have been adjusted.

# Validation record

## Repository preparation (2026-11-12)

README simplified around ChainChat's DERO Proof of Value; detailed commands moved
to `running.md`. Public evidence preserved, generated ZIP/build outputs and local
state excluded from Git, and stale AGENTS.md operational notes consolidated.
No cryptographic or transport behavior changed in this preparation.

Executed successfully: `pytest -q` (81 passed), Ruff lint and format checks,
`scripts/demo.py` and `scripts/demo_three.py`. The latter completed exactly
33 simulated transfers. Both demos used temporary profiles and no live RPC.

## Final Alice-to-Bob Mainnet milestone (2026-11-11)

Six signed request fragments, three signed response fragments and two encrypted
message fragments were retrieved from the official recipient Wallet RPC instances.
The user then reported Bob's local `sync` and `chat read Alice` output recovering
`Hello Bob, this is an encrypted message over DERO.` This confirms one authenticated
session message in one direction when combined with the on-chain receipt evidence.
See [final report source](../final-report-source.md) and
[verbatim Bob output](../bob-plaintext-confirmation.md). The 33-transfer three-wallet
workflow, long message and offline application restart passed only in simulation;
Charlie's Mainnet session and stopped-wallet recovery have not been performed.
Historical test counts and pending states below describe their respective dates.
After the final documentation update, `.venv/bin/pytest -q` passed **81 tests**;
`.venv/bin/ruff check src tests scripts` and
`.venv/bin/ruff format --check src tests scripts` passed. Tests do not submit paid
transactions or use live HTTP.

## Latest result: Mainnet encrypted greeting delivered

2026-11-10: one explicitly authorized real Mainnet transfer carried an encrypted
`Hello Bob!`. Bob-side application verification retrieved identical bytes and
successfully authenticated/decrypted them. Actual total: 182 atomic units; observed
latency: 42.245 seconds. See [Mainnet evidence](mainnet-validation.md) for txid,
height, fee, hashes, confirmation estimate, and the limits of this test.

After fixing short-passphrase/empty-file recovery, **49 tests passed** (1.82 seconds),
and Ruff lint/format passed. Paid automated-test paths remained mocked. The live
experiment was a separate explicitly approved operation, not part of pytest.
The rest of this document is the historical validation record.

2026-11-10: **48 tests passed** after adding passphrase-encrypted persistent probe
keys. Original exact authorization was received, but the memory-only runner/key
was gone before any broadcast; ledger confirms zero attempts and no txid. No new
Mainnet proposal has been generated. See mainnet-validation.md for recovery steps.

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

## Three-wallet preparation validation, 2026-11-10/11

Executed `.venv/bin/pytest -q`: **68 passed**. Executed Ruff check and format check
for `src tests scripts`: pass. The tests forbid real HTTP; all paid paths are mocked.
Executed `scripts/demo_three.py` in separate CLI processes: pass, exactly33 simulated
transfers, two authenticated sessions, separate peer conversations, 512-byte plaintext
reassembled from10 transfers and Bob application restart recovery. See recorded
`demo-three-output.txt`. This is not a stopped-wallet Mainnet test.

Executed the official Release153 serializer and Go asserting boundary test against
commit `0e8a90770b2817e6857af03f1c5642cb7913815f`: pass; output in
`release153-capacity.txt`. New attack tests cover signed-field substitutions,
impersonation with a different key, cross-session ciphertext, bounded incomplete
legacy groups, exact message-cost boundaries, durable spending caps, duplicate
submissions and uncertain status. Existing replay, tamper, restart/nonce and
out-of-order tests remain passing. No cryptographic protocol changes were made.

Source/live evidence is distinguished in `three-wallet-plan.md`; pending Mainnet
steps require Charlie configuration and explicit paid-transfer approval.

## Unpaid request preparation

After user-created three-wallet profiles: **69 tests passed**; Ruff lint/format
passed. New test verifies request preparation never calls send, persists pending
state, exports stable public proposals without private identity/ephemeral keys,
and refuses proposals while a submission is uncertain. All three supplied public
identity fingerprints were recomputed and match. No new Mainnet call was submitted.

## Approved request runner and reconciliation

74 automated tests passed; Ruff check/format passed for src/tests/scripts. Tests
mock every paid path. New coverage: immutable six-fragment proposal, rejection of
changed bytes/addresses, single-use ledger across restarts, uncertainty blocking,
read-only outbox reconciliation with payload verification and acceptance preparation
without sending. Live observations are recorded separately in mainnet-validation.md
and alice-request-result.json; automated test success is not live delivery evidence.
