> Historical working record, archived on 2026-11-12. Pending states and
> commands describe earlier stages; use the [current documentation](../README.md)
> for results and operation. Relative Markdown links have been adjusted.

# Three-wallet Mainnet validation plan

Status: preparation and simulation only, 2026-11-10. No new paid transaction is
authorized or submitted. The prior one-shot probe's ledger remains consumed.
All three actual addresses and running localhost RPC endpoints were checked on
2026-11-11; see the follow-up below. Application profiles/fingerprint verification
and paid-transfer authorization are still pending.

## Evidence and deployment

The completed [probe report](../mainnet-probe-result.json) establishes one encrypted
payload delivery, not an authenticated handshake or fragmented Mainnet delivery.
[Read-only observations](../three-wallet-health.json) at 21:10:26 UTC show both wallet
heights 7884307, Alice unlocked 4362 atomic and Bob unlocked 4501 atomic. Their
addresses match the configured participants. One DERO equals 100,000 atomic units.
Wallet Release153 is user-reported; the exact release source was checked at
`0e8a90770b2817e6857af03f1c5642cb7913815f`. The previously checked remote daemon
reported `3.6.0-152.DEROHE.STARGATE+14082026`. There is no verified wallet-version RPC;
matching source is not binary attestation. Refresh balances, daemon health and
wallet heights before each approved stage.

## Capacity and authenticated identities

See [findings](dero-findings.md), [complete wire format](../protocol.md), and
[serializer output](../release153-capacity.txt). Source tests accept 78 binary bytes,
reject 79, and round-trip the original bytes. This is the capacity of our base64
`m/S` encoding. Native serialized arguments have 111 bytes available. A single
ASCII value in that field can contain 105 bytes; arbitrary binary cannot use those
105 bytes directly. No paid boundary test has been performed.

For the confirmed ring-16 probe, Bob's incoming `sender` is **Bob**, while Alice's
outgoing `sender` is Alice. This is diagnostic metadata, never an authentication
input. The source writes the recipient ring index and decodes it as sender.

Users must compare each participant's application public-key fingerprint and claimed
wallet address through an authenticated external channel. Pin Alice/Bob and
Charlie/Bob in both directions before requesting or accepting. The CLI requires
`--identity` plus explicit verification. There is no automatic TOFU. An Ed25519
signature proves application-key possession, not wallet ownership. Both wallet
addresses, both identities, both ephemeral keys, version, roles and session ID are
covered by the signed transcript and HKDF context. Successfully decrypting replies
confirms possession of the derived keys. No cryptographic protocol change was needed.

## Proposed exact workload and budget

Assume standard 66-character addresses, ring size 16, amount 1 atomic and explicit
fee 181 atomic per transfer, as observed for the probe. These are proposed limits,
not a new live fee quote. Source BuildTransaction uses the supplied nonzero fee;
there is no verified nonbroadcast fee-estimation RPC. Stop if this fee is no longer
accepted; do not raise it or retry automatically.

| Sender → recipient | Operation | Envelope bytes | Transactions | Gross debit DERO |
| --- | --- | ---: | ---: | ---: |
| Alice → Bob | Signed request | 312 | 6 | 0.01092 |
| Bob → Alice | Signed acceptance | 146 | 3 | 0.00546 |
| Charlie → Bob | Signed request | 312 | 6 | 0.01092 |
| Bob → Charlie | Signed acceptance | 146 | 3 | 0.00546 |
| Alice → Bob | `Hello Bob!` | 52 | 1 | 0.00182 |
| Charlie → Bob | `Hello Bob!` | 52 | 1 | 0.00182 |
| Bob → Alice | `Hello Alice!` | 54 | 1 | 0.00182 |
| Bob → Charlie | `Hello Charlie!` | 56 | 1 | 0.00182 |
| Alice → Bob | Exactly 512 ASCII `L` characters | 554 | 10 | 0.01820 |
| Charlie → Bob | `Offline message` | 57 | 1 | 0.00182 |
| **Total** | | | **33** | **0.06006** |

Fees total 5973 atomic (0.05973 DERO); recipient transfers total 33 atomic. The
amounts remain within these three wallets, but the gross-debit budget counts them.
A handshake costs 9 transactions / 0.01638 DERO. A short message up to 16 UTF-8 bytes
costs one; 17 bytes needs two. General message count is `ceil((42 + utf8_bytes)/58)`.
The maximum 4096-byte message needs 72 transactions / 0.13104 DERO and is outside
this experiment. No additional capacity probes, registrations, funding transfers,
retries or session rotations are included in this budget.

| Wallet | Latest unlocked atomic | Transfer cap | Gross debit cap | Expected final balance* |
| --- | ---: | ---: | ---: | ---: |
| Alice | 4362 | 17 | 3094 | 1272 |
| Bob | 4501 | 8 | 1456 | 3070 |
| Charlie | 3075 (2026-11-11) | 8 | 1456 | 1623 |

*Assumes every planned transfer succeeds, all incoming credits mature, no other
activity and the stated fees. Require each gross debit cap funded before starting;
do not rely on future incoming credits. Refresh and record balances throughout.

The user's observed 0.09225 DERO in approximately one hour at approximately
2.78 kH/s corresponds arithmetically to 50.6868 probe debits, 5.6319 handshakes, or
5.0687 ten-fragment messages. The proposed 0.06006 DERO equals about 39.0634 minutes
of that observed gross reward rate. These are experimental ratios, not a mining
forecast: variance, difficulty, uptime, electricity and hardware costs are omitted.
No mining process is started. One 42.245-second delivery does not establish latency
percentiles or throughput. Wallet indexing, confirmation depth, sequential send
pacing and block variability must be measured for every fragment.

## Spending gate and setup

The normal DERO adapter now refuses paid sends without a shared immutable spending
policy. Simulation and read-only RPC do not require one. `--enable-mainnet` remains
necessary, and every transfer still prompts for human approval. A policy file alone
is not authorization. All three profiles must point at the **same absolute policy
path**; its sibling `.db` is the common durable experiment ledger. Keep both under
`.mainnet/`, excluded from Git. Never copy, reset or replace the ledger to retry.

After Charlie is known and all fingerprints are verified, prepare a private JSON
policy with these fields (replace labels with the actual complete addresses):

```json
{
  "participants": {"ALICE_ADDRESS": 17, "BOB_ADDRESS": 8, "CHARLIE_ADDRESS": 8},
  "max_transactions": 33,
  "max_debit_atomic": 6006,
  "fee_atomic": 181
}
```

Placeholders deliberately fail validation. Example setup for a **new** Alice app
profile, after the completed policy exists (setup is read-only against Wallet RPC):

```bash
.venv/bin/dero-chat --profile .mainnet/alice-app setup --backend dero \
  --wallet-rpc http://127.0.0.1:20209/json_rpc --enable-mainnet \
  --fee-atomic 181 --spending-policy .mainnet/three-wallet-policy.json
```

Use separate Bob/Charlie app profiles, their own RPC URLs and the same policy.
The prompt asks for an **application encryption passphrase**, never a wallet
password. Existing profiles must preserve their identities and keys; use their
existing configuration rather than running setup again. RPC credentials stay in
local environment variables. Do not commit private profiles, policy or ledger.

The ledger records exact fragment digest, source, reserved cost, pre-send unlocked
balance, status and TXID. It commits a reservation before the single RPC call.
An uncertain call consumes the reservation and blocks all three wallets. Duplicates,
changed policies, nonallowlisted destinations and excess cost/count are rejected.
There is deliberately no automatic release or retry API. Resolve uncertainty using
read-only history before adding any recovery procedure; do not reset the ledger.
The gate constrains this application only. Other RPC clients and the official
wallet's internal two-attempt Transfer loop remain trusted limitations; it cannot
promise an absolute wallet-level debit ceiling against those behaviors.

## Live execution and evidence requirements

1. Obtain Charlie's address/endpoint and perform read-only checks for all three.
   Verify standard addresses using the official parser, synchronization, balances,
   and user-reported executable versions. Establish and record external fingerprint
   verification for both contact pairs.
2. Present exact pending fragment bytes/hash, sender, destination, amount, fee,
   RPC parameters and remaining budget for approval. Ciphertexts cannot be listed
   in this document before the real profiles and fresh sessions exist. Approval
   must be explicit for each transfer or an exact, bounded prepared batch. The CLI
   retains per-transfer confirmation even if a batch has been approved in chat.
3. Complete Alice/Bob request and acceptance, short message and reply; then
   Charlie/Bob independently. Bob must display messages under the pinned respective
   contact, not the RPC `sender` field. Use `chat flush` as prior fragments index;
   each newly submitted fragment requires confirmation.
4. Send the ten-fragment message, wait for sufficient confirmations, reconstruct,
   compare the full 512-byte plaintext and its SHA-256. Record all ten TXIDs.
5. Ask the user to stop **Bob's official wallet themselves** and record the time.
   After explicit transfer approval Charlie sends `Offline message`. Keep Bob's
   application profile intact. The user restarts/unlocks Bob's wallet, allows it to
   synchronize, then the app syncs/decrypts. Never stop/start a wallet automatically.
6. Record each fragment's TXID, packet hash and message ID/index/count, app identity
   fingerprint, RPC-reported sender separately, amount, actual fee, block/hash/
   topoheight, confirmation estimate, submission/index/reassembly times and balances.
   Verify no duplicate messages on a second sync. Retain an errors/uncertainty log.

The encrypted app state now retains bounded diagnostic incoming metadata (reported
sender, fee, block hash, topoheight, timestamp, packet hash and local observation
time). It never uses these fields for authentication. The shared ledger records
submissions. Collect the corresponding raw public/nonsecret RPC evidence separately;
receipt metadata alone is not proof of finality. Deep reorg rollback is unsupported.

## Reproduction without spending

```bash
.venv/bin/python -m dero_messenger.experiment
.venv/bin/python scripts/demo_three.py
.venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
```

The CLI demonstration uses three separate profiles and processes with synthetic
66-character addresses and a simulated chain. It verifies 33 transfers, independent
sessions, separate conversations, ten-fragment reconstruction and Bob application
restart recovery. Its output is in [demo-three-output.txt](../demo-three-output.txt).
This is not a stopped/restarted official-wallet Mainnet test. Live three-wallet
TXIDs, costs and offline recovery remain pending the missing configuration and
explicit transaction authorization.

## Three-wallet read-only check: 2026-11-11

At 09:06:37 UTC, all three wallet RPC servers passed GetAddress, GetHeight,
GetBalance, standard-address validation via MakeIntegratedAddress, and GetTransfers.
All addresses match the user's supplied values. Each wallet and the configured
remote daemon reported height 7886624. Charlie's earlier height 0 startup display
has resolved without intervention. [Recorded evidence](../three-wallet-health-2026-11-11.json).

| Wallet | RPC port (localhost) | Unlocked DERO | Gross debit cap DERO |
| --- | --- | ---: | ---: |
| Alice | 20209 | 0.04362 | 0.03094 |
| Bob | 20210 | 0.04501 | 0.01456 |
| Charlie | 20211 | 0.03075 | 0.01456 |

Charlie's address is
`dero1qy33m8gwtv4a7quhrv070pwu33zw8d4wvxkn5fcfqevgdu8v3q002qqcn3rj2`.
The daemon reports Release152, Mainnet and status OK; the supplied wallet startup
logs report Release153 for all three. GetTransfers incoming entry counts were
Alice 0, Bob 2 and Charlie 0. Counts alone do not prove that all historical payments
are indexed; no rescan was invoked.

Created `.mainnet/three-wallet-policy.json` with actual addresses and the proposed
limits, permissions 0600. No ledger was created/reset, no application keys generated,
and no Transfer call made. The consumed probe ledger is untouched. No existing
three-wallet application profiles or application passphrase environment were found.

Create the three application profiles locally. Each setup prompts for an application
passphrase (at least 12 characters), distinct in purpose from wallet passwords.
Do not send passphrases to the assistant. Setup performs no paid transaction;
enabling the backend alone is not payment authorization.

```bash
.venv/bin/dero-chat --profile .mainnet/alice-app setup --backend dero --wallet-rpc http://127.0.0.1:20209/json_rpc --enable-mainnet --fee-atomic 181 --spending-policy .mainnet/three-wallet-policy.json
.venv/bin/dero-chat --profile .mainnet/bob-app setup --backend dero --wallet-rpc http://127.0.0.1:20210/json_rpc --enable-mainnet --fee-atomic 181 --spending-policy .mainnet/three-wallet-policy.json
.venv/bin/dero-chat --profile .mainnet/charlie-app setup --backend dero --wallet-rpc http://127.0.0.1:20211/json_rpc --enable-mainnet --fee-atomic 181 --spending-policy .mainnet/three-wallet-policy.json
```

If RPC authentication is configured, export the appropriate local
`DERO_WALLET_USER`/`DERO_WALLET_PASSWORD` for each command without disclosing them.
Keep the public identity and fingerprint output from each setup. Compare/pin these
through the trusted local session before a handshake. Shared policy and funded
wallets do not establish application identity. The first paid proposal will be
Alice's six request fragments, capped at 1092 atomic (0.01092 DERO), and must include
actual stored bytes/hash before approval. Do not invoke `chat request`, `accept`,
`send` or `flush` as part of these setup steps.

## Application identity registration and unpaid handshake preparation

The user supplied successful setup output for all three application profiles.
[Public identity record](../three-wallet-identities.json) contains their keys and
fingerprints. SHA-256 recomputation matches all three supplied fingerprints; profile
configuration addresses match the previously checked wallets. No encrypted profile
was opened by the agent and no wallet file was accessed. These checks do not prove
wallet ownership or independent possession of the application private keys. The
user-controlled local setup output is the explicit external verification channel;
compare it before confirming contact pins.

Run the following contact commands locally and confirm the displayed fingerprints
against your setup output. They do not send transactions. Application passphrases
remain local; never paste them into chat.

```bash
.venv/bin/dero-chat --profile .mainnet/alice-app contacts add dero1qy9uv73wh4s3ew3s68q5ws6y3nn6sutwr6xs6g7mhzuefe09uyvdcqglpgwya --alias Bob --identity f6c46ed9ff2c43a0cdb6e19df0bdf8977fe6f555e92c2f00b74da5a0e42cda4a
.venv/bin/dero-chat --profile .mainnet/bob-app contacts add dero1qynrm8qn82vesxjcecuwr0dt7lg5gy4e0jdrhddup5ms6k70562zqqgq9e8tk --alias Alice --identity 8d4b1c7ae7f4b922148334da6eeda47c4c6d09724687839c12e28b6431e641bc
.venv/bin/dero-chat --profile .mainnet/charlie-app-v2 contacts add dero1qy9uv73wh4s3ew3s68q5ws6y3nn6sutwr6xs6g7mhzuefe09uyvdcqglpgwya --alias Bob --identity f6c46ed9ff2c43a0cdb6e19df0bdf8977fe6f555e92c2f00b74da5a0e42cda4a
.venv/bin/dero-chat --profile .mainnet/bob-app contacts add dero1qy33m8gwtv4a7quhrv070pwu33zw8d4wvxkn5fcfqevgdu8v3q002qqcn3rj2 --alias Charlie --identity 70b63f35fceecd33719ccb3a8aeaf1fb197a50e84068e0acf77603a0719b1a9a
```

Then prepare Alice's request **once**, without broadcasting, and display its public
proposal. Both commands prompt locally for the application passphrase.

```bash
.venv/bin/dero-chat --profile .mainnet/alice-app chat request Bob --prepare-only
.venv/bin/dero-chat --profile .mainnet/alice-app chat proposal
```

Preparation persists the signed request, ephemeral secret and six pending fragments
in encrypted application state. It never calls the transport send path. Re-running
request creates another session, so use `chat proposal` to inspect the existing one.
The proposal contains exact packet bytes, SHA-256 hashes, Transfer parameters and
total intended debit (six transfers, 1092 atomic). It excludes private keys and
passphrases. Its digest is for review; it does not grant authority or replace the
per-transfer spending gate. Share that public proposal for explicit approval before
any `chat flush`. Do not approve unrelated existing outbox items.

This user message establishes completed setup, not payment approval. No new Mainnet
TXIDs exist. The final report will include actual costs, heights, indexed sender
metadata, identity attribution, fragment reassembly and wallet offline recovery
only after they have been observed. Failed or unperformed stages will remain marked.

## Current prepared request and Charlie replacement

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

## After the approved Alice request batch

The exact six-fragment proposal was explicitly approved by the user. A dedicated
`request_batch` runner submits only that immutable proposal through the existing
shared ledger. It does not open encrypted application profiles. A successfully
submitted reservation is never submitted again on runner restart; unknown outcomes
block all spending. The runner checks amount, fee and identical payload bytes in
both official histories before advancing. Its evidence is in `alice-request-result.json`.

Because Alice's encrypted application outbox was prepared separately, reconcile
its stored packets with the ledger and official outgoing history locally:

```bash
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/alice-app chat reconcile
```

This updates only matching outbox statuses/TXIDs; it does not submit transactions.
A packet is marked submitted only after its reserved TXID, destination, amount,
fee, height and exact payload match official outgoing history. Unknown or uncertain
reservations are not silently reset. Do not use `chat flush --retry-uncertain` to
resend this request.

After the fragments reach the app's configured confirmation threshold, Bob can
process them and list the request:

```bash
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app sync
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app chat requests
```

After confirming session `7449a7ca589687e87c4307cf0fc562f3` and Alice's pinned identity,
prepare Bob's response locally without broadcasting:

```bash
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app chat accept 7449a7ca589687e87c4307cf0fc562f3 --prepare-only
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app chat proposal
```

Acceptance preparation derives and stores Bob's directional keys and queues three
response fragments. Alice cannot derive her matching keys until the response is
actually delivered. Bob's three transfers require a new explicit approval; the
Alice batch approval does not cover them. Keep all passphrases local. If sync has
not yet listed the request, wait for confirmations and sync again; do not regenerate
Alice's request.
