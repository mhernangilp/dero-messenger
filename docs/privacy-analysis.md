# Observable metadata: DERO and Ethereum

This comparison concerns ordinary DERO Stargate transfers versus ordinary Ethereum
L1 transactions. It is not an anonymity proof, and excludes optional Ethereum
privacy protocols. Application AES-GCM protects content; it cannot remove public
transaction metadata or hide a network endpoint from its directly connected server.

## Confirmed Mainnet case study

[The public explorer](https://explorer.dero-node.net/tx/a930ce565116983f5cd4b05bcaf1ebebab3be72294b71b517b74f6dad74c8684)
was fetched read-only. [Extracted observations](probe-public-observations.json)
include the HTML SHA-256 and all 16 candidate ring-member addresses. Both Alice and
Bob appear in that list. The page shows fee 0.00181 DERO, size **3.146 kB** (the
explorer's rounded display, not a byte-exact measurement), inclusion block 7884098,
built height 7884093, timestamp 2026-11-10 20:04:48 UTC and 209 confirmations at
observation. It does not publicly decode `Hello Bob!`.

Our wallet-side evidence separately reveals amount 0.00001 DERO and the agreed
roles Alice→Bob. Those roles come from this controlled experiment, not merely the
public ring list. Publication of the experiment itself discloses the pairing.
An address being listed as a candidate is not proof it spent or received funds.
Conversely, saying addresses are completely invisible would be false. We do not
claim a uniform 1/16 sender probability or independence of candidates: decoy
selection, source constraints and outside information can affect inference.

## Comparison

| Observable | DERO normal ring-16 transfer | Ethereum ordinary transaction |
| --- | --- | --- |
| Transaction hash | Public stable identifier; enables correlation with disclosed records | Public stable identifier |
| Block/height | Public inclusion, built-block references and confirmation estimates | Public inclusion and block number |
| Timestamps | Public block timestamp; wallet/index time also observable locally | Public block timestamp; no exact private send-time guarantee |
| Transaction size | Serialized size and number of asset payloads/ring size observable | Encoding/calldata length observable |
| Fees | Public statement fee, 0.00181 DERO in this case | Gas usage/effective price and resulting fee observable |
| Addresses | Public candidate ring addresses include real participants and decoys | Sender and destination fields directly exposed |
| Amount | Normal confidential transfer amount not presented in plaintext publicly; endpoints know it | Value field public |
| Destination | Included among candidates; normal proof does not label the recipient directly | Destination address or contract creation public |
| Payload | Native recipient encryption; app additionally authenticates/encrypts messages | Input data public unless the app encrypts it; encrypted bytes/length remain public |
| Network | Daemon sees client IP, timing, balance/address queries and submitted transaction | RPC provider sees client IP, requests and submitted transaction |

DERO public burn values and public smart-contract arguments are separate from normal
confidential transfer amounts; this PoC uses neither. A zero displayed burn is not
proof that no normal amount was transferred. The source defines native encrypted
payload handling and public statement fees/ring members:
[transaction structures](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/transaction/transaction.go),
[transaction construction](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/transaction_build.go).

For Ethereum, sender, recipient, value and input data are defined by the official
[transaction documentation](https://ethereum.org/en/developers/docs/transactions/).
The fee comparison follows the official
[gas documentation](https://ethereum.org/en/developers/docs/gas/). Public inclusion,
block timestamps, transaction objects and receipts can be queried through the
[JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/).
This comparison does not assume Ethereum's consensus is Proof of Work; contemporary
Ethereum uses Proof of Stake. DERO's PoW does not by itself establish stronger
application authentication or network anonymity.

## Network, endpoint and fragmentation limits

The official wallet requests encrypted balances using address-bearing queries and
broadcasts transactions through its configured daemon. The current remote daemon
can associate an IP connection with those requests even though it cannot simply
decrypt application messages. See
[wallet daemon communication](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go).
The configured daemon endpoint is HTTP; on-path visibility/integrity is a concern.
Loopback Wallet RPC protects the local RPC binding, not the remote daemon link.
We have not tested Tor, traffic padding, malicious-daemon resilience or resistance
to timing correlation.

Fixed native payload padding obscures the exact application length within a single
transfer from a passive chain reader. Multi-fragment messages create more paid
transactions; their timing, repeated candidate membership and subsequent replies
may support correlation. Ring membership does not prove a relationship, but it
also does not prevent intersection or external-information attacks. No numerical
anonymity bound is claimed. A recipient can disclose plaintext and identity claims;
a compromised unlocked application can expose retained session keys. Publicly
posting fingerprints, TXIDs, timing and wallet addresses weakens experimental
privacy deliberately in exchange for reproducible evidence.
