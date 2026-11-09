# Release153 Mainnet validation

## Status and authorization

**Latest revision:** the user requested an encrypted `Hello Bob!` instead of the
original deterministic binary packet. The original proposal is superseded and
cannot be submitted through its old approval hash. No funds have been spent.
The exact replacement is in [mainnet-encrypted-proposal.json](mainnet-encrypted-proposal.json).
The prior binary-probe details below are retained as history, not the current proposal.

The replacement uses a fresh random 256-bit AES-GCM key and 96-bit nonce. The
41-byte packet is `CP | version=1 | nonce:12 | ciphertext:10 | tag:16`; additional
authenticated data binds the probe domain, Alice/Bob addresses, and header. The key
is supplied locally to the sender encryption and Bob-side verification operations
within a single waiting process, simulating an already-shared symmetric key. This
does not validate key distribution, independent application profiles, or the
normal authenticated handshake. The established messaging protocol is unchanged.
The key is never printed, put in the transaction, or intentionally persisted. Core
dumps are disabled. OS memory/swap remains outside this application's guarantees.
If the process exits, its key is lost: do not recreate or resend a submitted probe.
Ciphertext reconciliation remains possible without the key, but decryption does not.

The user approved the prior probe while requesting a different message. A fresh
confirmation of the exact encrypted replacement is pending; the waiting process
has made no Wallet RPC calls. Its local single-use budget ledger is the same one,
not a second allowance. New plaintext is not saved in the SQLite evidence database;
the requested nonsecret greeting is documented here intentionally.

Replacement payload SHA-256:
`53980d4710b342e876c40fb3697d29097f134c2e99311e5cd7e1f24cfed0348b`.
Replacement proposal SHA-256:
`92022135cffed5bb12f6f4b49449c26de48dba1a59329e7de22807833ef08054`.
Amount 1 atomic, fee 181 atomic, configured total/local budget 182 atomic; one
application `Transfer` call. The official wallet's internal retry limitation below
still applies. After approval, the process will perform fresh wallet preflight,
submit once, and poll read-only history. It will display `Hello Bob!` only after
retrieving and authenticating the received ciphertext through Bob's Wallet RPC.

Encrypted-probe validation: **46 tests passed**, including wrong-key/tamper rejection
and refusal to reuse old approval or replace a spent/uncertain experiment. No live
payload has been broadcast. Do not start a second encrypted runner while the current
one holds the key and waits for approval.

**Read-only checks completed. The single binary probe is prepared, not authorized
or broadcast.** No handshake or paid application transaction has been initiated.
The user owns and manages the running wallets. Their wallet files have not been
opened, copied, decrypted, changed, or inspected by this project. No wallet process
has been started, stopped, restarted, or reconfigured.

The experiment permits only a specifically approved Alice-to-Bob payload test.
Wallet RPC connectivity is not spending consent. Approval is still pending; the
prepared proposal has zero reserved calls and zero reserved expenditure.

## Versions and topology

| Component | Version / observation | Evidence |
| --- | --- | --- |
| Alice official wallet | `3.6.0-153.DEROHE.STARGATE+21082026` | User-reported; this RPC API exposes no verified version method |
| Bob official wallet | `3.6.0-153.DEROHE.STARGATE+21082026` | User-reported; same limitation |
| Official source inspected | Release153, `0e8a90770b2817e6857af03f1c5642cb7913815f` | Official Git tag fetched and checked out locally |
| Remote daemon | `3.6.0-152.DEROHE.STARGATE+14082026` | Live `DERO.GetInfo` result |
| Daemon endpoint | `http://dero-node.mysrv.cloud:10102/json_rpc` | Read-only daemon query; no wallet credentials sent |
| Alice Wallet RPC | `http://127.0.0.1:20209/json_rpc` | Live read-only responses |
| Bob Wallet RPC | `http://127.0.0.1:20210/json_rpc` | Live read-only responses |

The daemon is Release152, not Release153. This is a recorded version difference;
it did not prevent the successful read-only checks. This report does not certify
all mixed-version behavior or remote-daemon archival retention. HTTP daemon
information is unauthenticated network evidence, not an independent chain proof.
The daemon's configured identity inside each wallet is user-reported: matching
heights and successful `GetBalance` synchronization support connectivity, but the
wallet RPC methods inspected do not reveal the configured daemon endpoint.

## Read-only health checks

The first requests reached both servers with HTTP 200. `GetAddress` and `GetHeight`
returned JSON-RPC `-32602` because the Python client supplied `params: {}` to handlers
with no argument parameter. `GetBalance` succeeded. The client now omits `params`
when no argument object is supplied and explicitly supplies `{}` to `GetBalance`.
A regression test verifies both wire forms. This was an application compatibility
bug, not evidence of an incorrect wallet address or a locked wallet.

The corrected calls observed:

| Check | Alice | Bob |
| --- | --- | --- |
| Address matches user configuration | yes | yes |
| Wallet block height | 7,879,723 | 7,879,723 |
| Balance, atomic units | 4,544 | 4,500 |
| Unlocked balance, atomic units | 4,544 | 4,500 |
| `MakeIntegratedAddress` with empty arguments | exact standard-address round trip | exact standard-address round trip |
| `GetTransferbyTXID` for known payment | outgoing record found | incoming record found |
| `GetTransfers` for known payment | record present | record present |

Addresses:

- Alice: `dero1qynrm8qn82vesxjcecuwr0dt7lg5gy4e0jdrhddup5ms6k70562zqqgq9e8tk`
- Bob: `dero1qy9uv73wh4s3ew3s68q5ws6y3nn6sutwr6xs6g7mhzuefe09uyvdcqglpgwya`

The immediately subsequent daemon query returned Mainnet (`testnet=false`),
`status=OK`, height/topoheight 7,879,724, stableheight 7,879,716, 44 incoming and 5
outgoing connections. Both wallets were within one block of the daemon snapshot.
These are point-in-time observations, not a guarantee of future synchronization.
A subsequent timestamped check at 2026-11-09 21:36 UTC again passed: both wallets
reported height 7,879,740 and unchanged balances; the daemon then reported
7,879,741. Full credential-free snapshots are in
[wallet health](mainnet-wallet-health.json) and [daemon health](mainnet-daemon-health.json).
The daemon omitted `prunedheight`, so archival completeness is not established.

Existing user-submitted payment (not a ChainChat probe):

- TXID: `27ba10c4f20ae1f8db549465b4cf3e589011319fdbdb8e2ebca020e8bc0098bf`
- Amount: 4,500 atomic = 0.04500 DERO.
- Fee reported by both wallet histories: 181 atomic = 0.00181 DERO.
- Height/topoheight: 7,879,672; payload position: 0.
- Block hash: `cb8d697c6531dcd1f13a57f62d0093254ade05a29d1119e3ccd7c3fb89bad9cb`.

No unrelated transaction payloads, transaction proofs, wallet seeds, private keys,
or RPC credential values were recorded. Read-only Wallet RPC calls may cause the
official wallet to update its own synchronized cache internally; the application
does not access wallet storage.

## Release153 source and serializer results

Source links are pinned to
[Release153 commit](https://github.com/deroproject/derohe/tree/0e8a90770b2817e6857af03f1c5642cb7913815f).

- [Transaction constants](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/transaction/transaction.go):
  `PAYLOAD0_LIMIT = 144 - 33`, or **111 serialized argument bytes**. The 145-byte
  native payload reserves 33 bytes for an ephemeral public key and one index byte.
- [Transaction builder](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/transaction_build.go):
  sends native CBOR payload type V2 with the ephemeral-key prefix. This changes the
  outer DERO encryption; the application's X25519/AES-GCM protocol is unchanged.
- [Wallet CLI comment handling](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/cmd/dero-wallet-cli/easymenu_post_open.go):
  the Comment prompt adds `{name: "C", datatype: "S", value: <text>}`; the ordinary
  interactive flow also adds a destination-port/payment-ID argument. Comment is not
  an independent data channel. Adding it or a port consumes the same CBOR budget.
- [RPC argument serialization](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/rpc.go):
  arguments become a CBOR map keyed by name plus datatype (`mS` for our field).
  `CheckPack` checks serialized length and fills the remaining space with random
  padding. No arbitrary Python bytes object is sent as a string: binary data uses
  canonical base64 in a standard string argument.
- [Transfer handler](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_transfer.go):
  validates against the 111-byte limit, builds/signs inside the official wallet,
  and submits. Parameters remain `transfers`, `ringsize`, and `fees`; each transfer
  includes `destination`, `amount`, and `payload_rpc`.
- [History decoding](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go)
  and [entry payload processing](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/wallet_rpc.go):
  decrypt V2 and populate `payload_rpc`, which `GetTransfers` returns. Do not
  authenticate a peer using the `sender` history field.

`scripts/payload_probe.go` now imports the actual `transaction.PAYLOAD0_LIMIT`;
it no longer hardcodes 144. It also decodes padded arguments and compares original
binary bytes. Executed inside the Release153 checkout:

```text
version=3.6.0-153.DEROHE.STARGATE+21082026 argument_limit=111
raw=24 CBOR=38 marshal=<nil> pack=<nil> roundtrip=true
raw=78 CBOR=110 marshal=<nil> pack=<nil> roundtrip=true
raw=79 CBOR=114 marshal=<nil> pack=Packed size 114 bytes, but limit is 111 roundtrip=false
raw=102 CBOR=142 marshal=<nil> pack=Packed size 142 bytes, but limit is 111 roundtrip=false
raw=103 CBOR=146 marshal=<nil> pack=Packed size 146 bytes, but limit is 111 roundtrip=false
```

**Correct send capacity: 78 raw packet bytes; 58 envelope bytes after the 20-byte
fragment header.** The earlier 102/82 result was valid for the old source but is
incompatible with Release153 sending. New outgoing fragments use 58-byte chunks.
The receiver still supports canonical historical 82-byte chunks; mixed chunk sizes
in one envelope are rejected. All peers must upgrade before receiving new smaller
fragments. Existing oversized pending outbox packets are not silently rewritten or
submitted; use fresh experimental profiles. Cryptographic transcript formats,
AEAD, counter allocation, replay protection, and persistence semantics are unchanged.

The 24-byte probe is intentionally below capacity. Successful delivery would
validate this short payload only; the 78-byte boundary remains a source-level
measurement until separately approved and tested on Mainnet.

## Exact proposed single transfer

- Experiment ID: `chainchat-release153-binary-001`.
- Sender: Alice, using her already-running localhost Wallet RPC.
- Destination allowlist: Bob's exact address only.
- Payload: 24 deterministic bytes, values 0 through 23.
- Hex: `000102030405060708090a0b0c0d0e0f1011121314151617`.
- SHA-256: `1d64add2a6388367c9bc2d1f1b384b069a6ef382cdaaa89771dd103e28613a25`.
- Encoding: one `m` / `S` RPC argument; 38 CBOR bytes measured locally.
- Transfer amount: **1 atomic = 0.00001 DERO**.
- Explicit fee: **181 atomic = 0.00181 DERO**, based on the observed ordinary payment;
  it is an estimate of an acceptable fee, not a network fee-preview result.
- Maximum authorized transaction debit / local experiment reservation:
  **182 atomic = 0.00182 DERO**.
- Maximum application `Transfer` invocations: **one**.
- Proposal SHA-256:
  `9e8e2450e53cf74627d9413b6946a36112071f949d26b70cae17fb6f8c3016b4`.

Expected RPC request, excluding credentials:

```json
{
  "jsonrpc": "2.0",
  "id": "dero-chat",
  "method": "Transfer",
  "params": {
    "transfers": [{
      "destination": "dero1qy9uv73wh4s3ew3s68q5ws6y3nn6sutwr6xs6g7mhzuefe09uyvdcqglpgwya",
      "amount": 1,
      "payload_rpc": [{
        "name": "m",
        "datatype": "S",
        "value": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYX"
      }]
    }],
    "ringsize": 16,
    "fees": 181
  }
}
```

This is a transport probe, not a valid conversation request or ciphertext. The
messenger's normal listener will reject its absent fragment magic; the dedicated
probe retrieves and compares the RPC argument directly. This avoids initiating a
handshake or modifying application cryptographic state.

## Local authorization gate and its limits

`dero_messenger.mainnet_probe` fixes the sender, destination, bytes, fee, amount,
ring size, endpoint, and maximum transaction count. A private SQLite ledger at
`.mainnet/probe.db` stores the exact proposal, its hash, approval hash, budget
reservation, and outcome. The experiment directory is excluded from Git.

Broadcast requires an explicit matching `--approve-sha256` argument **after user
approval of this exact proposal**. The code verifies both wallet addresses and
sender funds, then commits a single-use reservation before the paid RPC. Changed
proposals, incorrect approval hashes, and repeated calls fail closed. A timeout,
exception, or crash consumes the authorization and cannot trigger another paid
call. `reconcile` only reads history; it can recover a unique matching txid and
compare payloads. Never delete or restore the ledger to repeat the experiment.

This local gate is an accidental-spending safeguard, not an OS-level capability
boundary. Other programs or the general messaging CLI could call unlocked RPC.
The wallet and local OS remain trusted to honor the supplied fee and amount.
Release153's official `Transfer` handler itself contains up to two internal
build/send attempts; this app cannot disable them through the inspected RPC.
The gate limits this application's calls and approved transaction values, not
internal wallet behavior or spending by other clients. If any outcome is uncertain,
reconcile and seek a new decision; never automatically resubmit. Actual fees must
be checked from sender history before declaring the budget validated.

No wallet credentials are stored in the ledger. Optional credential variables:
`DERO_ALICE_RPC_USER` / `DERO_ALICE_RPC_PASSWORD` and
`DERO_BOB_RPC_USER` / `DERO_BOB_RPC_PASSWORD`; a common
`DERO_WALLET_USER` / `DERO_WALLET_PASSWORD` pair is a fallback. Do not put values in
Git, command arguments, reports, or chat. The inherited credential environment is
not printed. The project does not ask for wallet passwords or recovery information.

## Commands and delivery evidence

Read-only or local preparation commands:

```bash
.venv/bin/python -m dero_messenger.mainnet_probe health
.venv/bin/python -m dero_messenger.mainnet_probe prepare
```

The `broadcast --approve-sha256 <proposal-hash>` command exists but has **not** been
run. It must not be run until the user explicitly approves the transaction above.
After an approved attempt, poll read-only reconciliation:

```bash
.venv/bin/python -m dero_messenger.mainnet_probe reconcile
```

The reconciler records sender and receiver txid/position, actual fee, block hash,
height/topoheight, received hex/hash, byte equality, confirmation estimate, and
latency from submission start to first observed receipt. Because polling and wallet
indexing add delay, that latency is an observation upper bound, not exact on-chain
propagation time. Repeated reconciliation cannot broadcast. RPC failures are
reported rather than treated as missing confirmation. The normal transport's
readiness check now distinguishes transaction-not-found from other RPC failures.

| Probe evidence | Current result |
| --- | --- |
| Explicit user approval | pending |
| Broadcast / probe txid | not submitted / none |
| Receiver payload and SHA-256 equality | unverified on Mainnet |
| Actual probe fee and inclusion height | unknown |
| Observed delivery latency | not measured |
| Full authenticated handshake | deliberately not started |

## Automated validation

Paid paths are mocked. An autouse test fixture rejects actual HTTP transport use.
Tests cover exact authorization, fixed parameters/budget, changed proposals, wrong
wallets, durable single-use behavior across restarts, uncertain submission without
retry, read-only reconciliation, indexing delays, Release153 limits, legacy packet
reassembly, no-argument RPC encoding, and propagation of authentication errors.
Final results: **44 tests passed**, Ruff lint/format passed (20 Python files), and
the separate-process Alice/Bob simulation passed with the smaller fragments. The
current demo output is retained separately in `demo-release153-output.txt`. No real
paid call occurred during tests or simulation. AGENTS.md remains below 200 lines.
