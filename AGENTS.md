# DERO Private Messenger

## Project Overview
An English-only Python proof of concept for consent-based asynchronous encrypted
messaging using DERO Stargate transactions. Extends research on blockchain-carried
encrypted communication. No execution of received content or centralized server.

## Architecture
`src/dero_messenger/` separates cryptography, binary protocol, transport, wallet RPC,
conversation orchestration, encrypted SQLite persistence, monitoring, and CLI.
`tests/` exercises offline behavior; `docs/` holds detailed findings and design.
Independent Ed25519 identities authenticate ephemeral X25519 handshakes. HKDF-SHA256
derives directional AES-256-GCM keys. Identity fingerprints require external verification.
Outgoing envelopes are fragmented into transfers; incoming transfers are deduplicated,
reassembled, authenticated, and persisted. Local state is passphrase encrypted.

## Technology Stack
Python 3.11+ (including 3.13), cryptography, httpx, Typer, Rich, SQLite, pytest, ruff.
Target platform: Arch Linux. Use a project virtual environment.

## Coding Conventions
All project content is English. Use type hints, small modules, explicit errors,
bounded input parsing, and tests for security-sensitive behavior. Never treat
unauthenticated transport metadata as cryptographic identity evidence.

## Security Requirements
Never expose wallet seeds, private keys, or secrets in logs. Wallet RPC stays on
loopback. Keep wallet operations separate from application encryption. Use AEAD,
validate incoming envelopes, prevent replay, and reserve nonces durably before send.
Blockchain privacy is not a guarantee of application anonymity. Simulation is the
default; real paid transfers require explicit enablement and confirmation.

## Current Implementation Status
Implemented: CLI profiles/contacts/request/accept/reject/send/read/listen/sync/outbox,
Ed25519-authenticated X25519, HKDF directional AES-GCM, durable counters, bounded
fragmentation, deferred out-of-order envelopes, encrypted SQLite state, simulation,
and loopback-only official Wallet RPC adapter with per-transfer confirmation.
Latest validation: 46 pytest tests pass; paid paths are mocked and real HTTP is
forbidden in tests. Ruff lint/format and the separate-process simulation pass after the Release153 fixes.
Release153 inspected: 0e8a90770b2817e6857af03f1c5642cb7913815f. V2 reserves 33 native
payload bytes: CBOR limit is 111. Measured 78 raw bytes -> 110 CBOR bytes; 79 fails.
New fragment chunks are 58 bytes plus a 20-byte header. Legacy 82-byte chunks are
readable; both peers must upgrade for new sending. Do not silently rewrite old outboxes.
Cryptographic envelopes/key derivation are unchanged. Do not authenticate sender metadata.
Fixed live RPC bug: omit params for GetAddress/GetHeight; GetBalance takes {}.
Standard-address validation uses MakeIntegratedAddress with empty payload_rpc.
Read-only Mainnet checks now pass: both user-provided addresses match, balances
4544/4500 atomic unlocked, prior payment indexed with fee 181. Wallets are user-reported
Release153; daemon GetInfo reports Release152, Mainnet, within one block of wallets.
Never access the user's wallet files or start/restart/stop/reconfigure wallet processes.
Use only already-running localhost RPC; credentials stay in local environment variables.
Added mainnet_probe module with fixed Alice/Bob allowlist, exact proposal hash,
single-use durable call/budget reservation, no automatic retry, and read-only reconciliation.
The binary probe was superseded at the user's request by AES-GCM encrypted "Hello Bob!".
An encrypted_probe process holds the temporary PSK only in memory and waits for exact
replacement approval. No broadcast; same one-call budget ledger (182 atomic: 1+181).
Proposal hash: 92022135cffed5bb12f6f4b49449c26de48dba1a59329e7de22807833ef08054.
Do not start duplicate runners or discard the in-memory key while awaiting approval.
This locally simulates a pre-shared key; it is not the authenticated-handshake test.
If the process dies after sending, reconcile without resending; lost key is unrecoverable.
See docs/mainnet-validation.md and mainnet-encrypted-proposal.json for exact bytes.
Gate protects against accidental app retries; it cannot constrain other RPC clients
or the official wallet's internal retry loop. Never reset/clone the experiment ledger.
Normal transport confirms every fragment; chat flush resumes after prior txid indexing.
Authentication/connectivity errors now propagate instead of appearing as indexing delays.
Known limits: no Double Ratchet, secure deletion, receipts, archive UI, identity
rotation UI, deep-reorg rollback, or backup-rollback protection. Never send from an
old restored/cloned profile. Profiles have finite lifetime quotas; see protocol.md.
Old receive keys remain for offline delivery; send rotation is 30 days/10,000 messages.
Mainnet application payload delivery remains unverified pending explicit approval.
The earlier report of absent RPC listeners is historical and has been superseded.
Detailed findings, limitations, and validation records are in docs/.

## Development Instructions for Future Agents
1. Read this file before making changes.
2. Inspect relevant existing code before implementing modifications.
3. Follow the documented architecture and conventions.
4. Preserve backwards compatibility unless a change is justified.
5. Run relevant tests after modifications.
6. Update this file for significant decisions, milestones, or limitations.
7. Keep this file within 200 lines; consolidate obsolete material.
8. Avoid duplicating detailed documentation under `docs/`.
9. Never claim implementation or test success without verification.
10. Document unresolved issues instead of assuming them solved.
