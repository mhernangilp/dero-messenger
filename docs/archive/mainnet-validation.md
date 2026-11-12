> Historical working record, archived on 2026-11-12. Pending states and
> commands describe earlier stages; use the [current documentation](../README.md)
> for results and operation. Relative Markdown links have been adjusted.

# Release153 Mainnet validation

## Status and authorization

### Final Alice-to-Bob result (2026-11-11)

The six-fragment signed request, three-fragment signed acceptance and two-fragment
AES-256-GCM message were delivered on Mainnet. The user then ran Bob's local
`sync` and `chat read Alice`; output showed successful receipt in session
`7449a7ca589687e87c4307cf0fc562f3` and plaintext
`Hello Bob, this is an encrypted message over DERO.` See the
[final report source](../final-report-source.md), [message stage](../alice-message-validation.md)
and [verbatim user output](../bob-plaintext-confirmation.md). The eleven-transfer
authenticated session cost 0.02002 DERO gross. All subsequent pending-status
sections below are historical snapshots. Charlie's Mainnet session, longer
encrypted Mainnet delivery and stopped-wallet recovery remain untested.

### Two-fragment session ciphertext delivered

The first AES-GCM session message was prepared locally by Alice and sent in two
approved transfers. Bob's official wallet indexed exact payload bytes for both;
TXIDs and costs are in [the message stage report](../alice-message-validation.md).
Gross debit364 atomic (0.00364 DERO), matching the cap. Alice balance2909 and
Bob3963 atomic after delivery. Ten-confirmation polling passed; Bob's local AES-GCM
read remains the final separate check. The user has been asked to run Bob `sync` and
`chat read Alice` with his own application passphrase. Do not yet claim successful
plaintext decryption without that result.


### Encrypted session message proposal verified and submission in progress

The user locally prepared `Hello Bob, this is an encrypted message over DERO.` with
Alice's established session and authorized at most two paid transfers. Proposal
`2345c72d0c81233550eb497e2b851f7538d51f7a963246e035acf0f0dbed990e`
contains two fragments, 78 and54 bytes, reassembling to a92-byte encrypted envelope
with version1/type3, session `7449a7ca589687e87c4307cf0fc562f3`, counter0 and
valid fragment/full hashes. The plaintext itself is not visible in this public
proposal; user CLI output is evidence of what they prepared, not independent
cryptographic decryption by the agent. Maximum debit364 atomic (amount2, fees362).
Pre-send balances Alice3273/Bob3961 atomic at height7888179. The fixed two-packet
runner uses the shared spending ledger. Bob must locally sync/read using his app
passphrase to verify AES-GCM decryption and plaintext; no such claim is made yet.


### Session message preparation pending local passphrase entry

The user reports Alice's encrypted profile synced and established session
`7449a7ca589687e87c4307cf0fc562f3`; Bob reconciled his three outbox fragments.
The user authorized up to two paid Alice-to-Bob transfers to carry the agreed
UTF-8 text `Hello Bob, this is an encrypted message over DERO.` after local
preparation. `chat send --prepare-only` now encrypts and durably queues the message
without sending, reserving counter0. A two-fragment fixed batch runner has been
implemented, but its approved proposal hash remains an invalid zero placeholder
until the user supplies the exact public proposal. Do not run that runner yet.
Alice's application passphrase is needed locally; it is never requested in chat.
No encrypted session message has yet been broadcast or decrypted in this stage.


### Application sync reported; encrypted message approved for up to two transfers

The user reports Bob reconciled3 response fragments and Alice's local app sync
printed `Session established 7449a7ca589687e87c4307cf0fc562f3` at wallet height
7888139. This is user-provided local application evidence; the agent has not opened
Alice's encrypted profile or directly inspected session keys. The user approved a
subsequent short encrypted Alice-to-Bob message with a strict two-transaction cap.
Added `chat send --prepare-only` to queue the encrypted envelope and reserve the nonce
durably without sending. Test suite:78 passed. The exact encrypted proposal remains
pending local passphrase entry, so no new paid message transfer is claimed here.


### Alice–Bob on-chain transcript delivered

Both signed handshake messages have now been sent and retrieved:6 request transfers
and3 acceptance transfers. Both signatures and transcript binding verify. Total
gross debit0.01638 DERO; fees0.01629 DERO. Bob response alone cost0.00546 DERO,
exactly its cap, without timeout/retry. Balances after response: Alice0.03273,
Bob0.03961 DERO. See [complete handshake stage report](../handshake-validation.md)
and [live transcript verification](../handshake-delivery.json).

Alice's final application sync/key derivation remains a local user action because
her encrypted profile requires her passphrase. Bob has already accepted locally.
No shared-key message confirmation or full three-wallet completion is claimed.
Historical statements below are stage-specific and superseded where indicated.


### Bob acceptance batch approved

User supplied prepared acceptance proposal
`5bc06e0f4b6843113344c5013418840b1f56749fd8edc93cbcc7686857ab6147`
and explicitly authorized completion of the handshake. Scope executed: three
Bob-to-Alice fragments, amount1 + fee181 each, total cap546 atomic. Bob's signature
and request hash were verified before submission. Pre-send balances: Bob4507,
Alice3270 atomic, both at height7888119. Same shared budget ledger; no application
passphrase or wallet file access. User confirmed Bob app accepted/derived keys
locally and Alice outbox reconciled all six earlier packets. Alice's eventual local
key derivation still requires her encrypted profile to be unlocked by the user.


### Alice six-fragment signed request delivered and verified

Final read-only verification on2026-11-11 at16:37:32 UTC succeeded: all six approved
transactions are indexed in both official wallets. Bob-side reassembly produced
312 bytes with the correct envelope hash and valid Alice Ed25519 signature. Identities
and wallet addresses match the pinned proposal. Minimum confirmation estimate1239.
Gross debit0.01092 DERO (fees0.01086, amount0.00006); Alice balance0.03270 and Bob0.04507.
No application retry or additional payment occurred. The fifth-call timeout and
subsequent temporary history disappearance/block-hash change are documented with
preserved evidence, not omitted as successful-run noise.

See [the complete stage report](../alice-request-validation.md) and
[Bob-side verification](../alice-request-delivery.json). This validates fragmented signed
request delivery; the full handshake remains incomplete. Bob's encrypted app must
be synced locally, and his response requires a separate proposal/authorization.
Historical pending sections below describe earlier observations, not current status.


### Fifth-fragment timeout reconciled without retry

The approved batch stopped after a 30-second Transfer RPC ReadTimeout on fragment
index4. Four fragments had already been indexed. Read-only GetTransfers queries
then found exactly one matching fifth packet in each wallet, TXID
`5f9d3c29646f3d90b28c48526d141152b7542df400f0985c9484ece07a5cbfbd`,
height7886836, amount1, fee181. Alice unlocked balance3452 equals4362 minus5×182;
Bob4506 equals4501 plus5. There was no application retry of the uncertain packet.

A narrow reconciliation script verified both exact payloads, directions, amount,
fee, destination and unique TXID before recording it against the existing uncertain
reservation. Reserved cost was not released/reset. Evidence is retained under
`timeout_reconciliation` in `alice-request-result.json`. The original approval
remained limited to six packets; resuming skipped the five existing reservations
and submitted only fragment index5. The timeout remains a recorded experimental
finding, not a reason to retry. Bob's acceptance remains unauthorized.


### Six-fragment approval received

User explicitly replied "Approve" to proposal
`8b4db8fb773155480ecc7ed2fd63747f79994bb0c233aa678ad686d0778379b6`,
six Alice-to-Bob request fragments, maximum1092 atomic. No Bob response or other
transaction is authorized. Before submission, RPC heights7886827/7886826 and
unlocked balances4362/4501 matched expectations. A fixed-proposal runner uses the
existing shared budget ledger; it does not access encrypted profiles or wallet files.
72 automated tests passed before live execution; paid paths were mocked.


### Alice request prepared and verified; approval pending

The user supplied six pending fragments for session
`7449a7ca589687e87c4307cf0fc562f3`. Local verification reconstructed the312-byte
request, verified Alice's Ed25519 signature, checked both pinned public identities
and wallet addresses, and matched all six packet hashes and the canonical proposal
hash. Packet lengths are78,78,78,78,78,42 bytes; all meet Release153 limits.
[Exact public proposal](../alice-request-proposal.json).

Proposal SHA-256:
`8b4db8fb773155480ecc7ed2fd63747f79994bb0c233aa678ad686d0778379b6`.
Six Alice→Bob transfers, each amount1 and configured fee181 atomic, ring size16;
fee total1086 atomic, amount total6, gross debit cap1092 (0.01092 DERO).
No new Transfer call was made. Explicit approval is still pending and applies only
to these six packets, not Bob's acceptance or the remaining experiment. Refresh
balances and reconcile existing history/ledger before any authorized submission.

Charlie forgot the first application profile passphrase and created
`.mainnet/charlie-app-v2`. New public identity:
`70b63f35fceecd33719ccb3a8aeaf1fb197a50e84068e0acf77603a0719b1a9a`;
fingerprint `0bd753ed506eb8119801ec8e34559426cb89cd0a388354f2994cd526bb773705`.
Fingerprint recomputation passes; user supplied successful Bob contact pin output.
Old application identity is superseded, not a wallet-address change. The old profile
and shared spending ledger must not be deleted/reset or reused for sending.
Both Alice/Bob contact pins and Charlie→Bob pin were also confirmed in user output.
These are externally established application associations, not wallet ownership proofs.


### Three application profiles created; handshake still unpaid

The user supplied successful setup output for Alice, Bob and Charlie. All three
public-key SHA-256 fingerprints recompute correctly; the app configuration addresses
match the checked wallets. [Identity evidence](../three-wallet-identities.json).
The encrypted application state has not been opened by the agent. Local contact
pin confirmation and Alice request preparation remain pending user passphrase entry.
Added `chat request --prepare-only` and `chat proposal` to prepare/review exact
fragments without submitting. No new Mainnet payment is authorized or submitted.
Final on-chain findings will be appended as actually observed, not inferred from
profile creation. See the latest section of [the plan](three-wallet-plan.md).


### Three wallets now reachable: 2026-11-11 09:06 UTC

Read-only checks passed for Alice20209, Bob20210 and Charlie20211. Addresses match;
wallets and daemon reported height7886624. Unlocked balances:0.04362/0.04501/0.03075
DERO respectively, sufficient for the proposed caps. Charlie's startup height0 has
caught up. Daemon remains Release152; user startup logs show Release153 wallets.
[Health evidence](../three-wallet-health-2026-11-11.json).

Actual-address private spending policy prepared, without creating/resetting a ledger.
No new Transfer calls or wallet file access. No spending authorization inferred.
Application profiles and fingerprint verification remain prerequisites; see the
[local setup instructions](three-wallet-plan.md#three-wallet-read-only-check-2026-11-11).


### Three-wallet milestone preparation (2026-11-10/11)

No additional paid transaction was submitted. The earlier successful probe below
remains the only verified application-payload Mainnet transfer. Historical pending
probe sections later in this report are superseded by its success, not fresh approvals.

- Official Release153 serializer boundary retested: 78 binary bytes /110 CBOR accepted;
  79 /114 rejected; 105 ASCII characters /111 accepted. Source-based, unpaid tests.
- Current fragment body is58 bytes after20-byte header;102/82 are historical limits.
- Read-only capture at 21:10:26 UTC: both wallet heights7884307; unlocked balances
  Alice4362 and Bob4501 atomic. [Evidence](../three-wallet-health.json).
- Bob's incoming `sender` for the known probe is Bob's address. Source inspection
  confirms the recipient-index/sender-label mismatch; sender metadata is not trusted.
- Explorer independently exposes16 ring candidate addresses including Alice/Bob,
  fee0.00181 DERO, size3.146 kB and block timestamp. [Capture](../probe-public-observations.json).
- Three independent application profiles/processes passed two authenticated sessions,
  separate conversations, ten-fragment reconstruction and offline app recovery over
  a simulated ledger. [Recorded demo](../demo-three-output.txt). Official-wallet stop/
  restart recovery has not been performed on Mainnet.
- Proposed strict total:33 transactions,6006 atomic gross debit. New shared ledger
  required for normal paid sends; existing consumed probe ledger is preserved.
- Final automated results:68 pytest tests pass; Ruff lint/format pass; official
  Go boundary test passes. All paid automated paths are mocked.

See the [complete execution plan](three-wallet-plan.md),
[machine-readable budget](../three-wallet-budget.json),
[updated wire protocol](../protocol.md) and [privacy analysis](../privacy-analysis.md).
Charlie’s address/RPC and externally verified fingerprint associations remain
required. No new handshake, fragment or offline-recovery Mainnet TXIDs exist yet.


### Final result: encrypted Mainnet probe succeeded

On **2026-11-10 at 20:04:57 UTC**, the Bob-side application verifier fetched the
payload from Bob's official Wallet RPC history and successfully authenticated and
decrypted it as **`Hello Bob!`**. This was a real Mainnet transfer, not simulation.
The sender encryption and Bob-side decryption used a temporary PSK supplied locally
in one verifier process, as authorized by the user. The official wallet decrypted
DERO's native payload; the application verifier performed AES-GCM decryption.
The official wallet UI itself is not expected to display the application plaintext.

| Evidence | Observed result |
| --- | --- |
| TXID | `a930ce565116983f5cd4b05bcaf1ebebab3be72294b71b517b74f6dad74c8684` |
| Inclusion height / topoheight | 7,884,098 / 7,884,098 |
| Block hash | `ce3d7c5af0acd309dbbb2b680461b9f0840217063ad1fac769065bcb5817cc1c` |
| Sender / receiver position | 0 / 0 |
| Amount | 1 atomic = 0.00001 DERO |
| Actual fee in wallet history | 181 atomic = 0.00181 DERO |
| Actual total sender debit | 182 atomic = 0.00182 DERO, within budget |
| Payload length | 41 bytes |
| Sent and received SHA-256 | `d2d5805177e989fa7fe38f9075baeb80ca991989aeee4571dd6cf0980860056d` |
| Byte equality | true |
| AES-GCM authentication and plaintext check | passed: `Hello Bob!` |
| Plaintext SHA-256 | `42ba8354db263a6a5a9f74d6b7ceb4c962a3d8fd58a41969e521eb0222455415` |
| Submission start to first observed delivery | 42.245 seconds (polling/indexing upper bound) |
| Confirmation estimate when verified | 1; no irreversible-finality claim |
| Application Transfer calls | one reserved and executed; no application retries |

Machine-readable evidence is in [mainnet-probe-result.json](../mainnet-probe-result.json).
The temporary key existed only until successful verification and was not saved.
The recorded hashes and successful execution evidence are retained; this particular
ciphertext cannot be decrypted again after the key-owning process exits.
The single-use budget is consumed: **do not send another probe or reset its ledger**.

This validates a short encrypted payload, a one-atomic transfer with an explicit
181-atomic fee, actual Wallet RPC submission/retrieval, byte preservation, and PSK
AES-GCM decryption. It does not yet validate the full authenticated handshake,
Mainnet fragmentation, the maximum-size payload boundary, independent application
profiles, offline Mainnet recovery, or deep-reorganization behavior. No handshake
or second paid transaction was attempted. Historical preparation and failure notes
below explain the sequence; their pending/unverified labels are superseded here.


### 2026-11-10: authorized one-shot encrypted probe submitted

The user explicitly asked the agent to choose a symmetric key and send the PoC
message, removing the need for a user-entered application passphrase for this one
experiment. A fresh temporary AES-256-GCM key was generated and held in the same
process for sending and Bob-side verification. No key was printed or persisted.
This authorization covers one `Hello Bob!` probe within 182 atomic units; it does
not authorize a second transfer or the authenticated handshake.

Submission TXID:
`a930ce565116983f5cd4b05bcaf1ebebab3be72294b71b517b74f6dad74c8684`.
New proposal hash:
`18e8b403ca2280a5b552326f80e99c8b3675681ec405770e9e9fe2adec93f3a3`.
The durable gate reserved one call before the sole application `Transfer` invocation.
Subsequent actions are read-only reconciliation. Final delivery evidence will be
recorded below; earlier no-submission statements are historical.

The user's preparation failure also exposed a recoverable initialization bug:
a short passphrase created an empty file, and later code mistook file existence for
successful initialization. Store now rejects short passphrases before creating any
file. Probe preparation can initialize an existing empty store without replacing an
existing encrypted key. A regression test reproduces the exact failed sequence and
verifies successful recovery. **49 tests pass**; Ruff lint and formatting pass.


Latest retry, 2026-11-10 20:00:05 UTC: both already-running Wallet RPC servers
responded successfully outside the network sandbox. Addresses match; both heights
are 7,884,082; Alice/Bob unlocked balances remain 4,544/4,500 atomic units. Address
parsing and retrieval of the known transaction also pass. Initial sandboxed calls
returned ConnectError; the outside-sandbox retry establishes current connectivity.
The local ledger still has zero reserved submission calls and no txid. The new
`.mainnet/encrypted-key.db` does not yet exist. Reopening the official wallets does
not restore the lost, separate application PSK; local encrypted-probe preparation
is still required. No broadcast occurred during this retry.

### 2026-11-10: authorization received, execution blocked before submission

The user explicitly authorized encrypted proposal
`92022135cffed5bb12f6f4b49449c26de48dba1a59329e7de22807833ef08054`.
However, the waiting runner session was unavailable (`Unknown process id 15963`)
and no matching encrypted-probe process was found. Its memory-only key was lost.
The durable ledger still records zero reserved Transfer calls and no transaction ID.
No submission was attempted. The approved ciphertext must not be sent because the
planned Bob-side decryption can no longer be performed. Approval was recorded as
an event tied to that exact old hash, not as authority for different ciphertext.

This exposed a lifecycle flaw in the initial probe design. `encrypted_probe` now
supports `prepare` and `run`, storing its fresh PSK and exact packet in the existing
Scrypt/AES-GCM encrypted Store implementation at `.mainnet/encrypted-key.db` (0600).
The passphrase must be entered locally at the hidden application prompt, separate
from wallet passwords. No wallet process or file is accessed. No replacement key
has been generated in the real experiment yet. Preparation makes no network calls:

```bash
.venv/bin/python -m dero_messenger.encrypted_probe prepare
```

After reviewing and approving the new exact proposal, `run` unlocks that same key
and packet and asks for the proposal digest before any paid call:

```bash
.venv/bin/python -m dero_messenger.encrypted_probe run
```

If the experiment already reserved a submission attempt, `run` skips broadcasting
and only reconciles/decrypts. It never resets the spending ledger. Preparing a new
proposal after any reserved attempt is forbidden. Loss of the encrypted key store
or its passphrase cannot be remedied by regenerating and resending. Backup rollback
is unsupported; preserve the key store and spending ledger together.

Validation: **48 tests passed**; persistent reload preserves the identical key,
nonce, ciphertext, and proposal hash; wrong passphrases fail and a spent/uncertain
ledger cannot be reset. The earlier memory-only preparation notes below are history.


**Latest revision:** the user requested an encrypted `Hello Bob!` instead of the
original deterministic binary packet. The original proposal is superseded and
cannot be submitted through its old approval hash. No funds have been spent.
The exact replacement is in [mainnet-encrypted-proposal.json](../mainnet-encrypted-proposal.json).
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
[wallet health](../mainnet-wallet-health.json) and [daemon health](../mainnet-daemon-health.json).
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
