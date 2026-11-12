# ChainChat — DERO Proof of Value

## Project Overview
English-only research PoC evaluating DERO Stargate as one blockchain cover channel
for the broader ChainChat project. Demonstrates consent-based asynchronous encrypted
messaging. Privacy and anonymity are research objectives, not established guarantees.
No execution of received content, centralized messaging server or automatic mining.

## Architecture
`src/dero_messenger/` separates cryptography, binary protocol, transport, official
wallet RPC, conversation orchestration, encrypted SQLite storage, monitoring and CLI.
`tests/` exercises offline behavior; `scripts/` contains demos and experiment tools;
`docs/` contains design, source findings and preserved public experiment evidence.
Ed25519 identities authenticate ephemeral X25519 exchanges; transcript-bound
HKDF-SHA256 derives directional AES-256-GCM keys. Fingerprints require independent
verification. Signatures do not prove ownership of a claimed DERO wallet address.
Outgoing envelopes become fragments/transfers; incoming transfers are deduplicated,
reassembled, authenticated and persisted. Local state is passphrase encrypted.

## Technology Stack
Python 3.11+ declared, including 3.13; local recorded validation used Python 3.14.9.
cryptography, httpx, Typer, Rich, SQLite, pytest and Ruff. Target: Linux;
local development used Arch Linux. README installation is distribution-neutral.
Use the project virtual environment. Never install into system Python.

## Coding Conventions
All code, comments, logs, documentation and tests are English. Use type hints,
small modules, explicit errors, bounded input parsing and security-sensitive tests.
Inspect existing code before changing it; preserve compatibility unless justified.
Never treat unauthenticated transport metadata as identity evidence.

## Security Requirements
Never access wallet seeds, private keys or wallet databases. Never start, stop,
restart or reconfigure the user's wallets. Connect only to already-running localhost
Wallet RPCs; credentials stay in local environment variables. Never log secrets or
request application passphrases in chat. The app passphrase is not a wallet password.
Use AEAD, validate incoming envelopes, prevent replay and durably reserve nonces.
Never send from cloned/restored old profiles: rollback can repeat nonces.
Simulation is the default. Every paid Mainnet transfer requires explicit enablement,
human approval and a shared SpendingGate policy/ledger with strict limits.
Reserve cost before RPC; uncertain submissions block spending. Never automatically
retry, release a reservation or reset/clone the ledger. Reconcile existing TXIDs.
The gate cannot constrain other RPC clients or the official wallet's internal retry.
Never assume blockchain privacy implies application anonymity.

## Current Implementation Status
Implemented: CLI profiles, contacts, request/accept/reject, send/read/listen/sync,
outbox/proposal/reconcile; authenticated handshake, durable counters, bounded
fragmentation, out-of-order handling, encrypted persistence, simulation and Wallet RPC.
Latest verified local run: 81 pytest tests; Ruff lint/format passed. Paid paths are
mocked and real HTTP is forbidden in tests. Both CLI demos pass; the three-profile
demo uses 33 simulated transfers, two sessions and a ten-fragment message.
Release153 source: 0e8a90770b2817e6857af03f1c5642cb7913815f. Native144 bytes minus
33 reserved bytes leaves111 serialized argument bytes. Official Go tests accept78
raw bytes as110 CBOR bytes and reject79. New chunks58 + header20; legacy82-byte
chunks remain readable. Never silently rewrite old outboxes. Crypto is unchanged.
GetAddress/GetHeight omit params; GetBalance uses{}. Standard-address validation
uses MakeIntegratedAddress with empty payload_rpc. GetTransfers.sender is diagnostic
only: Release153 labels the recipient ring index as sender. Fingerprint pinning is
required; no Wallet RPC ownership-signature method was found.
Wallets user-reported Release153; remote daemon reported Release152. See findings.

## Completed Mainnet Evidence
Earlier one-transfer PSK probe decrypted "Hello Bob!": TXID
 a930ce565116983f5cd4b05bcaf1ebebab3be72294b71b517b74f6dad74c8684.
Height7884098; amount1 + fee181 =182 atomic; observed latency42.245s. Temporary
key was not saved. Its authorization and budget are consumed; never replay it.
Alice/Bob authenticated SID7449a7ca589687e87c4307cf0fc562f3 completed six request
and three acceptance transfers, then a two-fragment encrypted greeting. User reported
Bob sync at height7888203 and read "Hello Bob, this is an encrypted message over DERO."
This is user-provided local decryption evidence combined with independently retrieved
recipient RPC ciphertext receipts. All11 transfers had >=10 estimated confirmations.
Gross debit2002 atomic (0.02002 DERO), fees1991; PSK probe excluded. Last observed
balances Alice2909/Bob3963 atomic are historical, never a current spending check.
The fifth request RPC timed out but its exact packet was found in both histories:
5f9d3c29646f3d90b28c48526d141152b7542df400f0985c9484ece07a5cbfbd.
It was reconciled without retry; temporary history disappearance/blockhash change
was observed. Root cause not fully proven. Preserve original and later evidence.
All prior paid approvals are consumed. Never rerun historical batch runners.
Charlie uses replacement charlie-app-v2; public key in three-wallet-identities.json.
Charlie's Mainnet session, a long encrypted Mainnet message and stopped-wallet
recovery remain untested. Simulation success is not Mainnet offline validation.

## Limits and Repository Conventions
No Double Ratchet, secure deletion, receipts, identity-rotation UI, deep-reorg rollback
or backup-rollback protection. Receive keys remain for offline delivery; send sessions
expire after30 days/10,000 messages. Profiles have finite quotas; see protocol.md.
Public ring candidates include Alice/Bob; visibility does not identify actual roles.
README stays short; detailed commands live in docs/running.md and docs/README.md
indexes evidence. Historical snapshots retain capture-time pending states.
Superseded working logs live in docs/archive/; current summaries and RPC findings
reflect the completed Alice/Bob result. Preserve raw evidence paths for tools.
Keep .mainnet/, .demo/, wallet/profile databases, credentials, wallets.txt, caches,
build outputs and generated report ZIP out of Git. Preserve private files locally.
Build a public report packet with scripts/build_report_packet.py; do not commit it.
See docs/final-report-source.md for current claims and docs/report-handoff.md for export.

## Development Instructions for Future Agents
1. Read AGENTS.md and relevant existing code before making changes.
2. Follow the documented architecture and English-only conventions.
3. Preserve backwards compatibility unless a change is justified.
4. Run relevant tests and Ruff after modifications; never run paid tests.
5. Update this file for significant decisions, milestones or limitations.
6. Keep this file under200 lines; consolidate obsolete context.
7. Link detailed docs instead of duplicating them.
8. Never claim functionality or tests without verification.
9. Document unresolved issues instead of assuming they are solved.
10. Do not interpret RPC connectivity or old approvals as new spending authorization.
