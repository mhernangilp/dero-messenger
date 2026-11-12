> Historical working record, archived on 2026-11-12. Pending states and
> commands describe earlier stages; use the [current documentation](../README.md)
> for results and operation. Relative Markdown links have been adjusted.

# DERO Stargate transport findings

**Live update, 2026-11-10:** one 41-byte AES-GCM encrypted Mainnet probe was sent,
retrieved intact through Bob's Wallet RPC, and decrypted by the application verifier.
Amount 1 atomic plus fee 181 atomic was accepted. See
[Mainnet validation](mainnet-validation.md) for evidence and scope. Full handshake,
fragmentation, and maximum-payload Mainnet tests are still outstanding.

**Release153 update:** the historical investigation below used an older source.
Release153 reduces the argument budget to 111 bytes: measured capacity is now
78 raw packet bytes / 58 fragment-data bytes. Read-only Mainnet checks now succeed.
See [current Mainnet validation](mainnet-validation.md) for the exact release,
measurements, live RPC fix, and pending single-probe authorization. The old 102/82
budget must not be used for Release153 sending.

Research performed on 2026-11-09. These findings distinguish source inspection,
local serializer execution, mocked RPC tests, and live network validation.

## Evidence and version boundary

The inspected official repository HEAD was
`e9df1205b6603c62f0651d0e18e5e77a2584b15e` (commit date 2024-02-29).
The [official releases page](https://github.com/deroproject/derohe/releases)
was inspected; release availability is not proof that the inspected source exactly
matches all deployed Mainnet nodes. No release executable was downloaded.
The [documentation home](https://docs.dero.io/),
[RPC reference](https://docs.dero.io/Developers/rpcapi/),
[wallet guide](https://docs.dero.io/Getting%20Started/cli-wallet/), and
[Linux node guide](https://docs.dero.io/Getting%20Started/Node-linux/) were reviewed.
Source references below are pinned to the inspected commit.

**Current Mainnet compatibility is unverified end to end.** Local connection probes
found no listener on 127.0.0.1 ports 10102, 10103, 20209, or 20210. No funded wallets
or authorized paid transfers were supplied. No Mainnet transaction was sent.

## Wallet installation and operation

The official Go CLI can be built from source on Linux. Arch-specific commands are
in the README; they use vendored dependencies and local output paths. This project
never implements DERO key generation. Create Alice and Bob inside two official
wallet processes, store recovery information outside this application, and use
separate wallet files and RPC ports.

The [CLI option definitions](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/cmd/dero-wallet-cli/main.go)
provide `--wallet-file`, `--generate-new-wallet`, `--daemon-address`, `--rpc-server`,
`--rpc-bind`, and `--rpc-login`. Explicit bindings avoid misleading example ports:
the [network configuration](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/config/config.go)
sets Mainnet daemon RPC to 10102 and wallet RPC to 10103. This project's examples
explicitly select wallet ports 20209 and 20210.

[RPC server implementation](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/rpcserver/rpc_websocket_server.go)
uses loopback by default and supports HTTP Basic authentication from `--rpc-login`.
Bind explicitly to 127.0.0.1; never bind to a public interface. Authentication does
not restrict a compromised local user with the same UID. Credentials passed to the
wallet CLI may be visible through process inspection; use a private OS account.
The Python client rejects remote hostnames, proxy environment variables, URL
credentials, redirects, and non-loopback IPs. Wallet credentials are environment
variables separate from the application encryption passphrase.

## Addresses and RPC contract

[Address implementation](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/rpc/address.go)
encodes a version byte and 33-byte compressed public key with Bech32. Standard
Mainnet addresses use `dero`, integrated addresses `deroi`; Testnet uses `deto` and
`detoi`. The PoC supports standard Mainnet addresses only (66 characters) and
synthetic labels in simulation. `GetAddress` supplies the profile address.

[Wallet RPC structures](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/rpc/wallet_rpc.go)
and the server method map establish these exact names and fields:

| RPC | Used parameters | Relevant result |
| --- | --- | --- |
| `GetAddress` | `{}` | `address` |
| `GetBalance` | `{}` | `balance`, `unlocked_balance` |
| `GetHeight` | `{}` | `height` |
| `MakeIntegratedAddress` | `address`, `payload_rpc: []` | `integrated_address` |
| `Transfer` | `transfers`, `ringsize`, `fees` | `txid` |
| `GetTransfers` | `in`, `out`, `coinbase`, `min_height` | `entries` |
| `GetTransferbyTXID` | `txid` | `entry` (error if not found) |

A transfer entry contains `destination`, integer atomic `amount`, and `payload_rpc`.
The argument format is `{"name":"m","datatype":"S","value":"<base64>"}`.
`Transfer` builds **and submits**; it is not a preview method. Never call it merely
to validate payloads or estimate fees.

For validation, [MakeIntegratedAddress](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/rpcserver/rpc_make_integrated_address.go)
parses the address, replaces arguments with the supplied empty list, and returns
the canonical standard address. This is a read-only round trip that invokes the
official checksum and curve-point parser. `SplitIntegratedAddress` is unsuitable
because it explicitly rejects a standard address.

## Measured payload budget

[Transaction constants](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/transaction/transaction.go)
define a 145-byte encrypted payload: one sender-index byte plus a 144-byte argument
area. The 144 bytes **include serialization overhead**.
[Arguments.MarshalBinary and CheckPack](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/rpc/rpc.go)
serialize a CBOR map whose keys concatenate name and datatype, reject oversized
serialization, and pad shorter encodings. String values are supported; arbitrary
Python byte arrays are not a documented argument type.

The local `scripts/payload_probe.go` was executed using this exact upstream
serializer, with vendored dependencies. It measured:

| Raw packet bytes | Base64 characters | CBOR bytes | CheckPack(144) |
| ---: | ---: | ---: | --- |
| 102 | 136 | 142 | accepted |
| 103 | 140 | 146 | rejected |
| 104 | 140 | 146 | rejected |
| 105 | 140 | 146 | rejected |

For the single `m` string field, the CBOR overhead is six bytes at these lengths:
map marker, `mS` key encoding, and string length encoding. This gives **102 raw
packet bytes**. The application's 20-byte fragment header leaves **82 envelope
bytes per transfer**. Adding ports, comments, or integrated-address arguments
changes the budget and is deliberately unsupported. This is a local source-level
measurement, **not a measurement of acceptance by a current Mainnet wallet/node**.

Reproduce without a node, wallet, or funds:

```bash
git clone https://github.com/deroproject/derohe.git /tmp/dero-payload-check
git -C /tmp/dero-payload-check checkout e9df1205b6603c62f0651d0e18e5e77a2584b15e
cp scripts/payload_probe.go /tmp/dero-payload-check/payload_probe.go
(cd /tmp/dero-payload-check && go run -mod=vendor payload_probe.go)
```

## Sender identity and payload delivery

[Transaction construction](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/transaction_build.go)
places the sender ring index before the packed arguments and encrypts the payload
using a recipient-related shared secret.
[Wallet decoding](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/daemon_communication.go)
decrypts for the receiver, extracts that index, and fills `Entry.Sender` from the
selected ring member. Ring size two has a special case selecting the other member.
The result includes decoded `payload_rpc`, raw `payload`, and `payloaderror`.

A sender field therefore **exists**; it is inaccurate to say DERO never exposes a
sender. However, this investigation did not establish a cryptographic proof that
the sender-selected payload index must identify the actual spending witness for
all accepted transactions. The PoC never uses that field for authentication or
routing replies. It uses the address inside the signed application request.
DERO wallet message-signing integration was not established as a portable RPC
mechanism here. Independent Ed25519 signatures and externally verified public-key
fingerprints are used. They authenticate application identities, not ownership of
DERO addresses. The signed address association is a claim by that identity.

## Retrieval, history, confirmations, and offline recovery

`GetTransfers` exposes `height`, `topoheight`, `txid`, `pos`, `incoming`, and payload
fields. A single txid may have multiple positions, so deduplication uses both.
[GetTransfers handler](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/rpcserver/rpc_gettransfers.go)
reads wallet history. It is not a direct blockchain scan. The official wallet must
be online and must complete its own history synchronization.

[Wallet height methods](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/wallet.go)
distinguish height from topoheight. The app uses wallet block height minus entry
block height plus one as a **confirmation estimate**, with ten required by default
for DERO. It does not treat the estimate as a consensus finality proof. It scans
history from zero each time instead of incorrectly advancing a block-height cursor
using topoheight. The last observed height is persisted for diagnostics.

The official wallet's history code traverses historical balances and blocks,
including restart/rescan handling. Thus offline recovery is feasible when wallet
history or required daemon history remains available. A recent-block scan setting
or a pruned daemon can prevent recovery of old data. Use an archival daemon and
preserve the wallet history and application profile. A fast current balance query
alone is insufficient to recover old messages. Arbitrarily long archival retention
on public remote daemons is unverified. The application accepts old complete
messages; incomplete fragment groups expire 30 days after first local observation.

## Amounts, fees, and submission sequencing

One atomic unit is 0.00001 DERO. The minimum positive integer amount, **1 atomic**,
is used. Zero-value incoming payload discoverability is not assumed: wallet history
distinguishes an incoming transfer using an increase in balance. Current Mainnet
acceptance of a one-atomic transfer has not been tested here.

The inspected [Transfer handler](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/walletapi/rpcserver/rpc_transfer.go)
accepts `fees`. The builder uses a nonzero supplied fee; its automatic formula
involves transfer count, ring size, fee multiplier, and encoded smart-contract data.
For one transfer, ring size 16, multiplier 1, and empty argument map, its formula
gives 121 atomic units. This is the default **source-based estimate**, explicitly
provided as a fee. It is neither a live quote nor a guarantee of acceptance.
The configured fee is shown before every fragment submission.

[GetGasEstimate](https://github.com/deroproject/derohe/blob/e9df1205b6603c62f0651d0e18e5e77a2584b15e/cmd/derod/rpc/rpc_dero_estimategas.go)
runs contract simulation. No ordinary transfer fee-preview RPC was verified; the
app does not misuse gas estimation or invoke a smart contract.

A wallet can have spending-state constraints while a transaction is pending. Before
sending another fragment, the outbox checks whether the previous txid is indexed
through `GetTransferbyTXID`. If it is not, fragments remain queued; rerun
`chat flush` after confirmation. Every actual transfer still asks for consent.
This sequencing is source-informed and mock-tested, not live-validated.

## Remote-daemon exposure

The wallet's daemon communication sends the wallet address to
`DERO.GetEncryptedBalance` and requests historical blocks and transactions.
A remote daemon can observe the connecting IP, queried address, request timing,
requested history, and submitted transaction traffic. This is directly visible in
the inspected calls; further traffic correlation is a reasonable inference, not a
quantified anonymity result. TLS hides traffic from some network observers but
not from the daemon itself. A local archival daemon reduces this trust surface.
No claim is made that DERO privacy automatically hides application use or prevents
traffic analysis, censorship, denial of service, or malicious RPC responses.

## Three-wallet milestone: repeated Release153 measurements (2026-11-10)

Rechecked official tag Release153, commit
`0e8a90770b2817e6857af03f1c5642cb7913815f`, with the actual Go serializer and an
asserting Go test, without invoking Transfer. [Output](../release153-capacity.txt).

| Layer/encoding | Boundary | Meaning |
| --- | ---: | --- |
| Historical documented user data | 144 bytes | Not 144 arbitrary application bytes |
| Release153 V2 argument budget | 111 bytes | `144 - 33` after native ephemeral public key reservation |
| Our `m/S` CBOR with 78 raw bytes in base64 | 110 bytes | Accepted, decoded bytes identical |
| Same with 79 raw bytes | 114 bytes | Rejected before construction |
| Same with 102 raw bytes | 142 bytes | Old 144-byte assumption; rejected on Release153 |
| Single `m/S` ASCII string | 105 / 106 characters | 111 accepted / 112 rejected serialized bytes |
| New application fragment body | 58 bytes | 78 minus 20-byte fragment header |
| Historical application fragment body | 82 bytes | 102 minus 20; receive compatibility only |

Base64 expands to `4*ceil(n/3)` bytes. At these lengths the CBOR map/key/string
headers cost six bytes. `CheckPack` pads to 111; native V2 adds one encrypted ring
index and a 33-byte ephemeral key, filling 145 native payload bytes. Official
`Comment` is an ordinary string argument named `C`, datatype `S`; CLI port arguments
consume additional budget. Our transport sends only `m/S`, with no Comment or ports.
Neither arbitrary bytes in a JSON string nor 144 raw bytes are valid substitutes.

Primary pinned sources:
[argument serializer](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/rpc/rpc.go),
[native payload constants](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/transaction/transaction.go#L65),
[payload construction](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/transaction_build.go#L177),
[Transfer handler](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_transfer.go).

Reproduce in a verified source checkout; this compiles source, does not download or
execute a wallet binary, and does not access wallets:

```bash
git clone --branch Release153 --depth 1 https://github.com/deroproject/derohe /tmp/dero-release153
git -C /tmp/dero-release153 rev-parse HEAD
cp scripts/payload_probe.go scripts/payload_capacity_test.go /tmp/dero-release153/
GOCACHE=/tmp/dero-go-cache go -C /tmp/dero-release153 run -mod=vendor payload_probe.go
GOCACHE=/tmp/dero-go-cache go -C /tmp/dero-release153 test -mod=vendor -run '^TestMessengerRelease153Boundary$' -v .
```

These tests measure the tagged source, not an attestation of the running executable.
Only the earlier short encrypted probe has been delivered on Mainnet; a maximal
78-byte application packet has not yet been submitted as a separate boundary probe.

### `sender` is not a wallet ownership proof

`transaction_build.go:85` identifies witness index 0 as sender and 1 as receiver;
line187 puts `witness_index[1]` into the encrypted payload. The V2 incoming decoder
in [daemon_communication.go:1104](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go#L1104)
calls this value `sender_idx` and exposes its ring address as `entry.Sender`.
There is a ring-size-two special case, irrelevant to our ring size 16. The live
[history capture](../three-wallet-health.json) confirms Bob receives **his own address**
as sender for Alice's known probe. Consequently this metadata cannot identify the
spender or authenticate a handshake, even when payload decryption succeeds.

DERO does have wallet signatures:
[SignData/CheckSignature](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/wallet.go#L641)
and CLI `filesign`/`fileverify`. The
[RPC method map](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/rpcserver/rpc_websocket_server.go)
exposes no corresponding signing/verification method. We have not invoked CLI file
signing or accessed wallet secrets. Under the requested RPC-only workflow the PoC
uses external fingerprint/address verification. A user-created wallet-signed
application identity certificate could be future work, but is not implemented or
claimed here. A self-declared signed application address remains a claim.
