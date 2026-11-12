# First authenticated-session message on DERO Mainnet

Alice's application profile was locally synced by the user after the signed
request/acceptance. The user reported `Session established
7449a7ca589687e87c4307cf0fc562f3`, then locally prepared the plaintext
`Hello Bob, this is an encrypted message over DERO.` using
`chat send --prepare-only`. That command durably reserved counter0 and queued
ciphertext without a paid call. The user explicitly authorized at most two paid
Alice-to-Bob fragments for this message, gross debit cap364 atomic units.

The public proposal hash is
`2345c72d0c81233550eb497e2b851f7538d51f7a963246e035acf0f0dbed990e`.
Both packet SHA-256 values, the92-byte reassembled envelope hash, version1/type3,
expected session ID and counter0 were verified before submission. The envelope's
ciphertext and GCM tag cannot be decrypted from this public evidence without the
session key. The prepared plaintext is attested by the user's CLI action; Bob's
later local decryption independently completed that check.

## Delivered fragments

| Fragment | TXID | Inclusion height | Packet bytes | First observed delivery seconds |
| --- | --- | ---: | ---: | ---: |
| 0 | `63236a39daab2d6052b47b8ccecdc3c49951c43cdd7d0a7aea1954e239629aca` | 7888180 | 78 | 22.028 |
| 1 | `6a752eba6614c80ed3819edd5086eede15a844434b144e4b69c7cadb9cbcca9e` | 7888181 | 54 | 11.937 |

Both official histories indexed the exact approved payload bytes. Amount1 atomic
and fee181 atomic per transaction. Total amount2 atomic=0.00002 DERO, fees362
atomic=0.00362 DERO, and Alice gross debit364 atomic=**0.00364 DERO**. No
application retry occurred. Alice unlocked balance3273→2909 atomic; Bob3961→3963.
The shared ledger now has11 submitted reservations and total gross debit2002
atomic=0.02002 DERO across the two signed handshake messages and this encrypted
message. Budget remaining4004 atomic under the original6006 cap; this is not
additional authorization.

The observed22.028 and11.937 seconds per fragment include wallet processing,
polling and indexing. They do not establish network latency percentiles or
irreversible finality. At final read-only verification (2026-11-11T17:10:28.563301+00:00), both fragments had at
least ten confirmations. Bob-side fragment hash/reassembly and confirmation evidence
are in [read-only delivery evidence](alice-message-delivery.json).

## Bob's local decryption result

The user ran these read-only application commands with Bob's passphrase entered
locally. The agent did not receive the passphrase or access Bob's encrypted profile:

```bash
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app sync
env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app chat read Alice
```

The user reported `Message received in 7449a7ca589687e87c4307cf0fc562f3`
at wallet height 7888203 and `in: Hello Bob, this is an encrypted message over
DERO.` from `chat read Alice`. This is user-provided application evidence of
successful AES-256-GCM decryption and replay validation, combined with the
separately verified ciphertext receipts. The verbatim output and evidence limits
are in [Bob's plaintext confirmation](bob-plaintext-confirmation.md). No Bob
reply, Charlie Mainnet session, long encrypted Mainnet message or stopped-wallet
recovery is claimed here.

[Exact proposal](alice-message-proposal.json) ·
[submission and actual costs](alice-message-result.json) ·
[authenticated handshake stage](handshake-validation.md).
