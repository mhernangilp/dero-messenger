# DERO Private Messenger: verified PoC results and report source

This document is a concise source for a final academic/engineering report. Use the
linked records for detailed evidence. All Mainnet observations below relate to
DERO Stargate on 2026-11-10/11. Distinguish source-code measurements, simulated
results, wallet RPC observations, and user-reported application output.

This DERO experiment is part of **ChainChat**, a broader research / Proof of Value
project evaluating blockchains as cover channels for communication with privacy
and anonymity. DERO is one of the transports studied. Anonymity remains a research
objective; this experiment does not establish resistance to traffic analysis.

## Aim and system

The PoC investigates whether DERO transactions can carry asynchronous,
application-authenticated and encrypted messages without a centralized messaging
server. It extends earlier research using Ethereum transactions as encrypted
communication carriers. Three independent participants are represented by wallet
addresses and separate application profiles. Official DERO wallets own spending
keys and sign transactions; the Python app does not read wallet keys or wallet DBs.

The implementation uses Python 3.11+, `cryptography`, `httpx`, Typer, Rich and
SQLite. Scrypt-derived AES-GCM protects the local application state. Simulation is
the default. Mainnet Wallet RPC is restricted to localhost, with explicit paid
transaction enablement, destination/quantity limits, a durable single-use budget
ledger and per-transaction user confirmation in the normal CLI. The explicitly
approved fixed batches used proposal hashes and the same shared ledger.

## What is established

| Claim | Evidence | Scope |
| --- | --- | --- |
| Release153 binary `payload_rpc` boundary | [Official Go serializer test](release153-capacity.txt) | Source measurement, not paid maximal-boundary broadcast |
| One AES-GCM PSK payload transfer | [Probe result](mainnet-probe-result.json) | Real Mainnet, pre-shared key, outside authenticated session |
| Six-fragment signed request Alice→Bob | [Request stage report](alice-request-validation.md) | Real Mainnet, signature and both recipient histories verified |
| Three-fragment signed acceptance Bob→Alice | [Handshake report](handshake-validation.md), [transcript evidence](handshake-delivery.json) | Real Mainnet; both signatures and transcript binding verified |
| Session-key encrypted message Alice→Bob | [Two-fragment delivery](alice-message-delivery.json), [Bob's plaintext output](bob-plaintext-confirmation.md) | Real Mainnet; local output is user-provided evidence of AES-GCM decryption |
| Two contacts plus long message plus offline restart | [Three-process demo](demo-three-output.txt) | Deterministic simulation only |
| Charlie Mainnet session, long encrypted Mainnet message, wallet stopped/restarted recovery | No TXIDs | **Not yet validated on Mainnet** |

All three official wallet RPC endpoints were read-only checked at
[height 7886624](three-wallet-health-2026-11-11.json). The user showed wallet
Release153 (`3.6.0-153.DEROHE.STARGATE+21082026`) startup logs; the configured
daemon reported Release152 (`3.6.0-152.DEROHE.STARGATE+14082026`). An RPC check
cannot attest the exact executable binary. Charlie's first application passphrase
was forgotten; a fresh `charlie-app-v2` identity was created and pinned by Bob.
Neither Charlie identity has yet participated in a paid Mainnet handshake.

## Protocol and payload size

A request contains version/type/session ID, Alice and Bob application Ed25519
public identities, Alice's ephemeral X25519 public key, both claimed DERO addresses
and Alice's signature. Bob's acceptance adds his ephemeral X25519 key, the request
hash and Bob's signature. HKDF-SHA256 over the complete transcript derives separate
32-byte directional AES-256-GCM keys. The message header and counter are additional
authenticated data. A durable, per-direction counter prevents nonce reuse across
normal restarts; receive counters prevent replay. Identities are pinned only after
fingerprint comparison outside the chain. These signatures prove application-key
possession and transcript agreement, **not cryptographic ownership of a DERO wallet
address**. See [protocol](protocol.md) and [threat model](threat-model.md).

Release153 source defines a 144-byte user-data space and reserves 33 bytes for a
native ephemeral key, leaving **111 serialized argument bytes**. The chosen single
`m/S` base64 field carries **78 arbitrary binary bytes**: its CBOR encoding uses 110
bytes. A 79-byte packet needs 114 bytes and is rejected locally. The 20-byte app
fragment header leaves **58 envelope bytes** per new transaction. The historical
102-byte raw/82-byte fragment assumption applied to a different 144-byte argument
limit and fails for Release153 sending. A 105-character ASCII `m/S` value fits the
111-byte serializer boundary, but that is not 105 arbitrary binary bytes under the
current encoding. These are source/tests findings; only shorter and maximal-78-byte
packets inside the live batches have actually been broadcast, not a paid 79-byte
rejection probe. See [findings](dero-findings.md).

The signed request was 312 bytes/6 fragments; acceptance 146 bytes/3 fragments.
The first session message was 92 bytes/2 fragments, counter 0 and session
`7449a7ca589687e87c4307cf0fc562f3`. Bob's local output recovered:
`Hello Bob, this is an encrypted message over DERO.` The application currently
limits plaintext to 4096 UTF-8 bytes; the simulated 512-byte long message used
10 fragments. Mainnet long-message delivery is not claimed.

## Mainnet transactions and measured costs

One DERO equals 100,000 atomic units. Each of the eleven authenticated-session
transactions used amount 1 atomic, configured/observed fee 181 atomic, and ring
size 16. Public TXIDs and per-fragment heights are in the three stage reports:
[request](alice-request-validation.md), [acceptance](handshake-validation.md),
[message](alice-message-validation.md).

| Stage | Transfers | Fees | Amounts transferred | Gross sender debit |
| --- | ---: | ---: | ---: | ---: |
| Alice signed request | 6 | 0.01086 DERO | 0.00006 DERO | 0.01092 DERO |
| Bob signed acceptance | 3 | 0.00543 DERO | 0.00003 DERO | 0.00546 DERO |
| Alice encrypted session message | 2 | 0.00362 DERO | 0.00002 DERO | 0.00364 DERO |
| **Total** | **11** | **0.01991 DERO** | **0.00011 DERO** | **0.02002 DERO** |

The earlier independent PSK probe cost 0.00182 DERO and is **not included** in
this eleven-transfer session total. Its observed first receipt was about 42.245
seconds. Session message fragments were first observed after about 22.028 and
11.937 seconds, including construction, polling and indexing. These are individual
observations, not transport latency distributions. Final read-only verification of
the session message found at least ten confirmations for both fragments. Alice's
balance after the eleven transfers was 0.02909 DERO; Bob's was 0.03963 DERO.
The shared ledger recorded eleven submitted reservations and 0.02002 DERO of a
0.06006 DERO proposed three-wallet budget; the unused remainder is not authorization.

The historical input of 0.09225 DERO mining reward in roughly one hour at roughly
2.78 kH/s is a single local observation. On simple arithmetic, the eleven-transfer
gross debit equals about 21.7% of that gross hourly reward. It is not a mining
forecast or a net-profit calculation and excludes electricity/hardware costs.
No mining was started by the application.

## Privacy and operational findings

DERO's explorer exposed the probe TX hash, height, timestamp, fee, size and sixteen
candidate ring-member addresses, **including Alice and Bob**. Candidate visibility
does not identify which member actually sent or received the payment. Normal
amount and destination are not plainly labeled in the public transaction as they
are in an ordinary Ethereum transaction; wallet endpoints know them. Our confirmed
probe explorer showed 3.146 kB as a rounded displayed transaction size. The remote
daemon can observe connection origin, queries and timing. Application traffic
patterns, repeated fragment transactions and disclosures of public TXIDs can aid
correlation. DERO PoW does not grant application-level anonymity. See
[privacy analysis](privacy-analysis.md).

Release153's `GetTransfers.sender` is unsuitable for identity attribution: Bob's
incoming Alice→Bob entries name Bob; Alice's incoming Bob→Alice entries name Alice.
Source writes the recipient ring index then reads it as a sender index. The PoC
ignores this field for cryptographic authentication and uses signed, pinned
application identities. The official wallet has CLI file-signing features, but a
corresponding Wallet RPC method was not found; wallet-address ownership is not
cryptographically proven in this experiment. See [source findings](dero-findings.md).

During the request batch, the fifth Transfer RPC timed out after the wallet had
submitted it. The application stopped. Read-only checks matched the exact packet
in both wallets and recorded its existing TXID without retrying. Later wallet
history temporarily omitted recent entries, then restored them; one observed block
hash changed at the same height. Release153 history sync source can truncate and
rebuild entries after a block-hash mismatch, which is consistent with the event.
The full cause was not independently established. This incident shows why balance
changes and transient missing history must not trigger automatic resubmission.
Original and later evidence is preserved in the [request stage report](alice-request-validation.md).

## Reproducibility and remaining work

The simulated three-profile CLI workflow produced 33 ledger transfers, distinct
Alice/Bob and Charlie/Bob sessions, separate conversations at Bob, replies, a
10-fragment message and recovery after a simulated offline period. `pytest` passed
81 tests; paid paths were mocked and real HTTP was forbidden during tests. Ruff
lint/format checks and Release153 Go boundary tests passed. See
[validation](validation.md) and [demo output](demo-three-output.txt).

A full **three-wallet Mainnet** claim still needs Charlie's independent handshake,
messages from both senders, a long encrypted multi-transaction message and a
manual Bob wallet stop/restart offline-recovery trial. The PoC does not implement a
Double Ratchet, secure deletion, receipts, deep-reorg rollback or robust backup
rollback protection. Wallet and application profile loss prevents old ciphertext
recovery. Do not describe the simulated offline test as Mainnet offline validation.
