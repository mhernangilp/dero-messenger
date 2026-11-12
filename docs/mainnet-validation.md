# Mainnet validation

The final result is documented in [final-report-source.md](final-report-source.md).
Alice and Bob completed an authenticated handshake and one encrypted message on
2026-11-11. The 11 transfers cost 0.02002 DERO gross; Bob reported decrypting
`Hello Bob, this is an encrypted message over DERO.` in his local application.

## Evidence by stage

| Stage | Transfers | Gross debit | Detailed evidence |
| --- | ---: | ---: | --- |
| Earlier pre-shared-key probe | 1 | 0.00182 DERO | [Probe result](mainnet-probe-result.json) |
| Alice signed request | 6 | 0.01092 DERO | [Request report](alice-request-validation.md) |
| Bob signed acceptance | 3 | 0.00546 DERO | [Handshake report](handshake-validation.md) |
| Alice encrypted session message | 2 | 0.00364 DERO | [Message report](alice-message-validation.md) |

The earlier probe is separate from the 11-transfer authenticated session. Its TXID
is `a930ce565116983f5cd4b05bcaf1ebebab3be72294b71b517b74f6dad74c8684`,
height 7884098. It authenticated/decrypted `Hello Bob!` with a temporary pre-shared
key, observed fee 181 atomic, amount 1 atomic and delivery about 42.245 seconds.
The temporary key was not saved. It did not test the authenticated handshake.

The stage reports retain all session TXIDs, heights, hashes, fees, confirmations
and the request-batch timeout/reconciliation incident. [Bob's supplied CLI output](bob-plaintext-confirmation.md)
completes the session-message decryption evidence; secret profiles were not opened
by the agent. Raw JSON snapshots retain the status at capture time, including
pending flags that later observations superseded.

## Deployment and source compatibility

Wallet startup logs reported Release153 (`3.6.0-153.DEROHE.STARGATE+21082026`);
remote daemon GetInfo reported Release152 (`3.6.0-152.DEROHE.STARGATE+14082026`).
The inspected Release153 commit was `0e8a90770b2817e6857af03f1c5642cb7913815f`.
This is source and user-reported version evidence, not executable attestation.

Read-only checks matched all three wallet addresses, synchronization and unlocked
balances; see [the health capture](three-wallet-health-2026-11-11.json).
[DERO findings](dero-findings.md) documents verified RPC formats, native payload
serialization and the 78-byte packet limit. Maximal 78-byte packets were delivered
in the live batches; 79-byte rejection was tested locally, without a paid call.

## Scope and operation

Charlie's Mainnet session, a longer encrypted Mainnet message, a Bob-to-Alice
session reply and stopped-wallet recovery remain untested. The full three-profile
workflow passed in simulation. Confirmation counts are estimates; deep-reorg
rollback and resistance to traffic analysis are not established.

All historical paid approvals are consumed. For a new experiment use the
[manual workflow](running.md) and a separately approved budget. Never replay old
batches, reset ledgers or automatically retry an uncertain submission.
The [archived working log](archive/mainnet-validation.md) preserves the sequence
of preparation, authorization, failed checks and later success.
