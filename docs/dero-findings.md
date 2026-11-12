# DERO Stargate transport findings

These findings distinguish official source inspection, local serializer tests and
Mainnet observations. The inspected Release153 commit is
[`0e8a90770b2817e6857af03f1c5642cb7913815f`](https://github.com/deroproject/derohe/tree/0e8a90770b2817e6857af03f1c5642cb7913815f).
Wallets were user-reported Release153; the queried daemon reported Release152.
Source inspection does not attest the running executable or all mixed-version behavior.

The Alice/Bob authenticated Mainnet handshake and one encrypted message succeeded;
see [Mainnet validation](mainnet-validation.md). Stopped-wallet recovery and Charlie's
Mainnet session remain untested. The [archived investigation](archive/dero-findings.md)
preserves the earlier source analysis and superseded 102/82-byte assumptions.

## Official wallet and RPC

Use the official [releases](https://github.com/deroproject/derohe/releases),
[documentation](https://docs.dero.io/) and
[RPC reference](https://docs.dero.io/Developers/rpcapi/).
[Running the PoC](running.md) provides the tested CLI workflow. The official wallet
creates and manages wallet keys, signs transactions, synchronizes history and
decrypts native payloads. The app never reads wallet files, seeds or spending keys.

The wallet supports `--wallet-file`, `--daemon-address`, `--rpc-server`, `--rpc-bind`
and optional `--rpc-login`; see the
[CLI definitions](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/cmd/dero-wallet-cli/main.go)
and [RPC server](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_websocket_server.go).
Bind explicitly to `127.0.0.1`; the experiment used ports 20209/20210/20211.
HTTP Basic authentication is supported. Wallet CLI credentials may be visible in
the process list; use a private OS account. Local unlocked RPC access can authorize
spending. The Python client requires explicit loopback IPs and rejects proxies,
URL credentials, redirects and remote endpoints. Credentials stay in the environment.

Standard Mainnet addresses use the `dero` Bech32 prefix and encode a version byte
and 33-byte compressed public key. Integrated addresses use `deroi`; testnet uses
`deto`/`detoi`. This app accepts standard 66-character Mainnet addresses, plus
synthetic labels in simulation. See the
[address implementation](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/address.go).

## Verified RPC contract

The [Wallet RPC structures](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/wallet_rpc.go)
and method handlers define:

| Method | Parameters used | Relevant result |
| --- | --- | --- |
| `GetAddress` | Omit `params` | `address` |
| `GetHeight` | Omit `params` | `height` |
| `GetBalance` | `{}` | `balance`, `unlocked_balance` |
| `MakeIntegratedAddress` | `address`, `payload_rpc: []` | Canonical standard-address round trip |
| `Transfer` | `transfers`, `ringsize`, `fees` | `txid` |
| `GetTransfers` | `in`, `out`, `coinbase`, `min_height` | `entries` |
| `GetTransferbyTXID` | `txid` | `entry`, or not-found error |

The original client sent `{}` to the no-argument handlers and received `-32602`.
Omitting `params` fixed the live incompatibility; regression tests cover both forms.
Address validation uses the official parser via `MakeIntegratedAddress` with no
arguments. `SplitIntegratedAddress` rejects standard addresses and is unsuitable.

Each transfer specifies `destination`, integer atomic `amount`, and `payload_rpc`:

```json
{"transfers":[{"destination":"RECIPIENT_ADDRESS","amount":1,"payload_rpc":[{"name":"m","datatype":"S","value":"BASE64_PACKET"}]}],"ringsize":16,"fees":181}
```

This is an illustrative parameter object with placeholders, not authorization.
**`Transfer` builds, signs and broadcasts.** Never call it for validation or a fee
preview. `GetTransfers` returns decoded recipient `payload_rpc`, transaction IDs,
positions, heights and other history fields after the official wallet indexes them.

## Payload capacity

The documented 144-byte user-data space includes serialization overhead and a
Release153 native reservation. It is not 144 arbitrary application bytes.

| Layer | Bytes | Evidence |
| --- | ---: | --- |
| Native payload | 145 | One encrypted ring index, 33-byte ephemeral key, 111 argument bytes |
| V2 serialized argument budget | 111 | `PAYLOAD0_LIMIT = 144 - 33` |
| Base64 `m/S` packet of 78 raw bytes | 110 CBOR | Accepted and round-trips |
| Base64 `m/S` packet of 79 raw bytes | 114 CBOR | Rejected locally |
| Base64 `m/S` packet of 102 raw bytes | 142 CBOR | Historical 144-byte budget only; rejected by Release153 |
| One ASCII `m/S` value, 105/106 characters | 111/112 CBOR | Accepted/rejected; not arbitrary binary capacity |
| App fragment header/body | 20/58 | 78-byte maximum packet |

Base64 uses `4*ceil(n/3)` characters. At the measured boundary, CBOR map/key/string
headers cost six bytes. `CheckPack` validates and pads the arguments. Official
Comment uses name `C`, datatype `S`; it shares this budget. The interactive wallet
also adds port/payment-ID arguments. This app sends only `m/S`; adding comments,
ports or integrated-address arguments changes the available space.

Pinned sources: [native constants](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/transaction/transaction.go),
[CBOR serializer](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/rpc.go),
[transaction builder](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/transaction_build.go),
[Comment handling](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/cmd/dero-wallet-cli/easymenu_post_open.go).

Reproduce using the official serializer, without a wallet or funds:

```bash
git clone --branch Release153 --depth 1 https://github.com/deroproject/derohe /tmp/dero-release153
git -C /tmp/dero-release153 rev-parse HEAD
cp scripts/payload_probe.go scripts/payload_capacity_test.go /tmp/dero-release153/
GOCACHE=/tmp/dero-go-cache go -C /tmp/dero-release153 run -mod=vendor payload_probe.go
GOCACHE=/tmp/dero-go-cache go -C /tmp/dero-release153 test -mod=vendor -run '^TestMessengerRelease153Boundary$' -v .
```

[Recorded output](release153-capacity.txt) shows the boundary and round-trip tests
passed. Live batches later delivered multiple 78-byte packets intact. The 79-byte
rejection was measured locally; no paid over-limit broadcast was attempted.
Legacy 82-byte app chunks remain readable, but new sends use 58-byte chunks.
Never silently rewrite an old outbox. The cryptographic envelope is unchanged;
see [protocol.md](protocol.md) for complete framing and resource limits.

## Sender identity and native encryption

The official wallet encrypts transaction payloads for the recipient and decrypts
received payloads before returning them through RPC. This native encryption does
not replace application signatures and AES-GCM authentication.

Release153 construction writes `witness_index[1]` (recipient index) into the payload.
The [receiver decoder](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go#L1104)
labels it `sender_idx` and returns that ring member as `Entry.Sender`. The ring-size-2
special case does not apply to this ring-16 experiment. Bob's live Alice receipts
name Bob as sender; Alice's Bob receipts name Alice. This field cannot authenticate
the actual spender. See the [probe history](three-wallet-health.json) and
[handshake evidence](handshake-delivery.json).

The official wallet has [SignData/CheckSignature](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/wallet.go#L641)
and CLI `filesign`/`fileverify`. No equivalent signing RPC was found in the inspected
method map. The app therefore pins independently verified Ed25519 keys and signs
both claimed wallet addresses into its transcript. These signatures establish an
application identity association, not cryptographic proof of wallet ownership.
A wallet-signed identity certificate remains future work.

## History, confirmations and offline recovery

`GetTransfers` reads indexed wallet history; it is not a direct scan by the app.
Deduplication uses `(txid, pos)`. The app scans from height zero on every sync to
avoid delayed-indexing gaps and height/topoheight confusion. It persists the last
observed height for diagnostics. Its confirmation estimate is wallet block height
minus entry block height plus one, with ten required by default; this is not an
irreversible-finality proof. See the
[history handler](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_gettransfers.go)
and [wallet synchronization](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go).

Source supports history synchronization after absence. Offline recovery requires
adequate wallet/daemon history and the original app profile. Recent-scan settings,
pruning or profile loss can prevent recovery. Indefinite public-daemon retention
is unverified. Stopped-wallet Mainnet recovery has not been tested; app restart
recovery passed in simulation. Incomplete app fragments expire after 30 days of
local observation. The app does not roll back accepted messages after deep reorgs.

## Fees, sequencing and daemon exposure

One DERO equals 100,000 atomic units. The experiment accepted amount 1 plus fee
181 atomic per transfer. Zero-amount payload discovery is not established. The
[Transfer handler](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_transfer.go)
uses supplied nonzero fees. The app's legacy default 121 is not the observed
experiment fee. No ordinary transfer fee-preview RPC was verified; contract gas
estimation is unsuitable. Refresh costs and balances before new paid work.

The outbox waits for the preceding TXID to enter wallet history before advancing.
Timeouts can occur after broadcast: the request batch demonstrated successful
read-only reconciliation without a retry. Both the app gate and official wallet
remain trusted components; the wallet handler contains an internal retry loop
outside the app's single-call limit. Never reset a ledger or retry an uncertain send.

The remote daemon sees connecting IPs, address-bearing `DERO.GetEncryptedBalance`
queries, history requests, timing and submitted traffic. The experiment used HTTP,
so loopback Wallet RPC did not secure the remote daemon link. TLS protects some
on-path exposure but not observation by the daemon. A local archival daemon reduces
that trust surface; resistance to correlation remains unmeasured. Public ring
candidate visibility and comparison with Ethereum are in [privacy-analysis.md](privacy-analysis.md).
