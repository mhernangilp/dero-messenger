# Validation

## Latest local checks

Executed on 2026-11-12 in the project virtual environment:

```bash
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python scripts/demo.py
python scripts/demo_three.py
```

All **81 tests passed**; Ruff lint and formatting passed. Both CLI demos passed.
The tests mock paid paths and forbid real HTTP. Simulations use disposable
profiles, genuine application cryptography and a local ledger; they do not model
DERO consensus, fees, native privacy or network behavior.

| Check | Verified scope |
| --- | --- |
| Unit and integration tests | X25519/HKDF, signed transcripts, AES-GCM failures, replay, cross-session attacks, fragment bounds/reordering/duplicates, persistence, restart nonce safety, budget and uncertain-submission handling |
| Two-profile CLI demo | Signed handshake, encrypted greeting, reply and offline application recovery |
| Three-profile CLI demo | Two independent sessions, separate conversations, replies, 512-byte message in 10 fragments, offline application recovery; 33 simulated transfers |
| Official Go serializer test | Release153 accepts 78 raw packet bytes, rejects 79, and round-trips accepted bytes |
| Separate approved Mainnet experiment | Alice/Bob handshake plus one two-fragment message; 11 transfers, 0.02002 DERO gross |

Recorded simulation outputs are [two-profile Release153](demo-release153-output.txt)
and [three-profile](demo-three-output.txt). The [serializer output](release153-capacity.txt)
and [reproduction commands](dero-findings.md#payload-capacity) establish the local
boundary independently of live submission. Mainnet evidence is summarized in
[mainnet-validation.md](mainnet-validation.md).

## Limits

The recorded environment used Linux, Python 3.14.9 and Go 1.27.3-X:nodwarf5.
[requirements-dev.lock](../requirements-dev.lock) records Python package versions.
Python 3.11/3.12/3.13 and Arch package installation were not separately exercised.
Earlier source wallet compilation succeeded; no downloaded executable was run by
the project and no miner was started.

Charlie's Mainnet session, longer encrypted Mainnet messages and stopped-wallet
recovery have not been performed. Tests are not a security audit, anonymity proof
or guarantee of irreversible chain finality. See the
[final report source](final-report-source.md) for the distinction between official
source findings, RPC receipts and user-provided decryption output.

The [archived validation log](archive/validation.md) preserves intermediate test
counts and stage-specific observations. Those older pending states do not override
this summary.
