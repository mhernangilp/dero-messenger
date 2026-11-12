# Alice signed request: Mainnet delivery verified

## Result and scope

On 2026-11-11 at16:37:32 UTC, the read-only verifier fetched all six transactions
from Bob's official Wallet RPC. It reconstructed the312-byte request and verified
Alice's Ed25519 signature, both pinned application identities, both wallet addresses,
session ID and the full envelope hash. No application private key or wallet file
was needed. Bob subsequently synced his encrypted application profile locally;
the agent did not receive his passphrase or access his keys.

Session: `7449a7ca589687e87c4307cf0fc562f3`.
Envelope SHA-256: `2d5e6a3ce88fd4744f1cf27abdff5409f2e3fa5c7a6cf67e0dd1342ed32a53b8`.
Approved proposal: `8b4db8fb773155480ecc7ed2fd63747f79994bb0c233aa678ad686d0778379b6`.

This validates fragmented, signed request transport on Mainnet, including five
maximal78-byte packets. The later [acceptance](handshake-validation.md) and
[encrypted message](alice-message-validation.md) completed the Alice/Bob session.
Charlie's Mainnet conversation and stopped-wallet recovery remain untested.

## Transactions and costs

Each transaction transferred1 atomic unit to Bob and charged181 atomic in fees.
All six were found exactly once by packet matching in each wallet's latest history.

| Fragment (zero-based) | TXID | Inclusion height | Packet bytes |
| --- | --- | ---: | ---: |
| 0 | `b39b2ef6bbfbcaa85bfd159ad0f194ddd9e1d2df7504a677a60653c73126a7d5` | 7886830 | 78 |
| 1 | `4f29dc7a25ed9e85689dc7d54ca9ee1298067f59108babcd948e16efe029434a` | 7886832 | 78 |
| 2 | `2943cc0234690167d6767bc99c4f76ef7c0f455590f3d32e7db74548a4d399bc` | 7886833 | 78 |
| 3 | `317c756962cc3cf9a988be6b43fbb445db7cdf359b608a784a722a1939cb9df7` | 7886834 | 78 |
| 4 | `5f9d3c29646f3d90b28c48526d141152b7542df400f0985c9484ece07a5cbfbd` | 7886836 | 78 |
| 5 | `b20aa962d7c559ea8c425b846a38d27ee4dd57adad98fe6c5ecb18260350a989` | 7886843 | 42 |

Total fees1086 atomic =0.01086 DERO; transferred amount6 atomic =0.00006 DERO;
Alice's total debit1092 atomic =**0.01092 DERO**, exactly the authorized cap.
Alice balance4362→3270; Bob4501→4507 atomic. Latest unlocked balances match these
balances. The shared experiment ledger has six submitted reservations consuming1092
atomic, leaving4914 atomic of the proposed6006 cap. Remaining budget is not spending
authorization. The older182-atomic PSK probe used a separate already-consumed ledger.

Bob's RPC reports Bob's address as `sender` on all six entries. Alice's application
identity comes from the verified signed request and externally pinned key, not that
field. No wallet-ownership proof is claimed.

## Timing and failure observations

Initial submission-to-index observations for fragments0–3 were approximately
42.166,16.939,17.836 and18.513 seconds. These include wallet construction, polling
and indexing, and are not latency percentiles or finality measurements.

Fragment4's Transfer call timed out at the client's30-second limit. The gate blocked
further spending. Read-only history found its exact bytes once in both wallets and
matched the amount, fee, destination and TXID. The reservation was marked submitted
without resetting its cost or repeating the Transfer call. Only then was fragment5
submitted under the original batch authorization. The recorded190.897-second
observation for fragment4 includes timeout handling and operator reconciliation;
it should not be reported as ordinary transport latency.

Later, both wallets temporarily omitted fragments4/5 despite balances reflecting
all six transfers. The runner eventually stopped with ConnectError during polling.
Following the conversation interruption, read-only checks found all six entries.
Fragment4's recorded block hash changed from
`e492ba53a0889da9e27493ebec8ccceaa2716dd513368bd5c73ad34bbd179849` to
`de1ba6a98eac70002e1f85fcde665cf0554d051785bac6f1aa8e9c13dd27bb08` at the same
reported height7886836. Its recorded timestamp also changed slightly. Earlier and
later evidence are retained; no historical observation is silently treated as final.

Release153's
[history synchronization code](https://github.com/deroproject/derohe/blob/0e8a90770b2817e6857af03f1c5642cb7913815f/walletapi/daemon_communication.go#L585)
truncates cached entries when the daemon's block hash at a topoheight differs, then
resynchronizes. This is consistent with the observed removal/reappearance and block
hash change. We did not capture daemon consensus logs or wallet debug logs and
cannot prove the full causal chain. In particular, a balance change alone is not
payload-delivery evidence. Do not classify disappearing history as a failed payment
and resend it.

Fragment5's exact delivery latency was not measured continuously because of the
RPC/history interruption and later user-session continuation. Its eventual receipt
is verified, but neither the delayed verification time nor its block timestamp is
an exact propagation latency. At final verification Bob height7888081 gave minimum
confirmation estimate1239 across all fragments, comfortably above the app threshold10;
this is still not a mathematical irreversible-finality guarantee.

## Evidence and reproduction

- [Approved exact public proposal](alice-request-proposal.json).
- [Submission/result record](alice-request-result.json), including timeout reconciliation.
- [Record before final reconciliation](alice-request-result-before-final-reconciliation.json).
- [Intermediate missing-history diagnostics](alice-request-indexing-diagnostic.json).
- [Latest exact history matches](alice-request-history-latest.json).
- [Independent Bob-side reassembly/signature verification](alice-request-delivery.json).

The application spending gate was checked read-only: six reservations, each cost182,
all submitted. No duplicate application Transfer call, wallet restart, rescan, wallet
file access or extra paid transaction was performed by the agent. The official wallet's
internal retry behavior remains outside the application's control; actual histories
and balance deltas show the expected six payments for this experiment.

`python scripts/verify_alice_request.py` repeats only read-only Bob-side verification.
Do not rerun the batch sender or reset any ledger as a way to verify delivery.
Subsequent stages are recorded in [the final report source](final-report-source.md).
For a new, separately approved experiment, use [running.md](running.md).
