# Alice–Bob Mainnet handshake transcript

## Verified outcome

All six Alice request fragments and all three Bob acceptance fragments have been
submitted once by the application and retrieved from their recipient's official
Wallet RPC. Reassembly yields a312-byte request and146-byte acceptance. Both
Ed25519 signatures verify, the response binds the exact request hash, and the session,
participant application keys, claimed wallet addresses and ephemeral X25519 public
keys are bound into the authenticated transcript.

Session: `7449a7ca589687e87c4307cf0fc562f3`.
Transcript SHA-256: `ad5616b70f88d28bf42a3d840ce03393c7a83734eaedc57ce781774a789d93d1`.

**The on-chain handshake transport is complete.** Bob's local key derivation is
evidenced by the user's successful `chat accept --prepare-only` output. Alice
subsequently reported `Session established` after local sync. The two-fragment
session-key message was then received and decrypted by Bob's application; see
[the message report](alice-message-validation.md) and [Bob's output](bob-plaintext-confirmation.md).
This supports shared-key agreement between these two application identities.
The agent did not access either application passphrase or secret key.

## Bob's approved response

The user supplied proposal
`5bc06e0f4b6843113344c5013418840b1f56749fd8edc93cbcc7686857ab6147`
and explicitly approved its transactions to complete the handshake. Each transfer
used ring size16, amount1 atomic and fee181 atomic. The three packet lengths were
78,78,50 bytes. Both recipient and sender histories returned identical approved
payload bytes; no Bob-batch timeout or application retry occurred.

| Fragment | TXID | Inclusion height | First observed delivery seconds |
| --- | --- | ---: | ---: |
| 0 | `777a59af8ba5d68c0289ab7f361a57a7e7222f4c6b306081655d29fb89700024` | 7888122 | 52.084 |
| 1 | `b88f3e2524267d548671496c75836e2bf39a225a2f7b65e57e13a977074544a3` | 7888124 | 37.036 |
| 2 | `25f5e7cad62aced871fa29aec1577ba5c7e862008fbb47783811975cb3c480bf` | 7888125 | 8.151 |

Alice's incoming `sender` metadata reports Alice herself for these transfers. That
field is diagnostic only. Bob is authenticated by the acceptance signature under
his externally pinned application key, not by Wallet RPC sender attribution.

## Actual costs and balances

| Stage | Transactions | Transfer amounts DERO | Fees DERO | Gross sender debit DERO |
| --- | ---: | ---: | ---: | ---: |
| Alice request | 6 | 0.00006 | 0.01086 | 0.01092 |
| Bob acceptance | 3 | 0.00003 | 0.00543 | 0.00546 |
| Total | 9 | 0.00009 | 0.01629 | 0.01638 |

The shared ledger contains9 submitted reservations totaling1638 atomic, exactly
matching the approved handshake cost. Proposed experiment budget remaining4368
atomic; this is a limit, not evidence that later stages occurred. Alice unlocked
balance after the response:3273 atomic (0.03273 DERO). Bob:3961 atomic (0.03961 DERO).
Alice had3270 and Bob4507 before this response batch. Funds transferred stay with
participants; the aggregate balance decrease across both wallets is fees1629 atomic.
The prior one-shot182-atomic probe is excluded from these handshake totals.

## Failures and limitations

The earlier request batch's timeout, temporary missing history and changed block
hash remain documented in [the request report](alice-request-validation.md). No
uncertain submission was blindly retried. Response delivery observations include
construction, polling and indexing; they do not establish finality or throughput.
Final read-only verification at 2026-11-11T16:53:40.055709+00:00 found all nine
transactions at ten or more confirmations; results are in `handshake-delivery.json`. Deep-reorg
rollback remains unsupported by the app, and confirmation counts are estimates.

The user observed one `incoming_rejected` warning while Bob processed his history,
followed by successful request reception and acceptance. The generic warning cannot
be uniquely attributed from that output alone. Earlier non-fragment probe payloads
are expected to be rejected by the normal fragment parser; this is a plausible
explanation, not a proven diagnosis. The authenticated request itself was accepted.

No application secrets were printed, no wallet file opened, and no official wallet
process restarted or reconfigured. The later Alice-to-Bob session message succeeded;
Charlie's session, encrypted long-message Mainnet delivery and stopped-wallet
recovery remain pending separate execution.

Bob reconciled his three outbox fragments and Alice locally synced to establish
the session. The current CLI sequence is in [running.md](running.md). Do not replay
these completed batches. Preserve both profiles; wallet seeds cannot restore their
application session keys.

## Evidence

- [Exact response proposal](bob-response-proposal.json).
- [Response submission receipts, timings and balances](bob-response-result.json).
- [Read-only verification of both received envelopes](handshake-delivery.json).
- [Request results and historical diagnostics](alice-request-validation.md).

`response_batch` is restricted to the exact approved response hash and the shared
ledger. Tests cover altered proposals, wrong approval, uncertainty stopping,
read-only mode and restart without resubmission. **77 pytest tests pass**, paid
paths mocked; Ruff lint/format pass. The reproducible `scripts/verify_handshake.py`
performs only read-only transcript checks, not key derivation or broadcasting.
The 77-test count above records this stage; see [validation.md](validation.md) for
the latest 81-test result.
