# Three-wallet experiment budget and remaining work

The 33-transfer workload below was proposed and simulated; it was not completed
on Mainnet. The completed Alice/Bob session used 11 transfers and 2002 atomic
units gross (1991 in fees). See [the final results](final-report-source.md).
All prior approvals are consumed. Unused budget does not authorize more payments.

## Proposed workload

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

| Wallet | Historical unlocked atomic | Transfer cap | Gross debit cap | Projected final balance* |
| --- | ---: | ---: | ---: | ---: |
| Alice | 4362 | 17 | 3094 | 1272 |
| Bob | 4501 | 8 | 1456 | 3070 |
| Charlie | 3075 (2026-11-11) | 8 | 1456 | 1623 |

These balances were captured before the paid stages on 2026-11-11; refresh them
before considering new work. The projections are not observed final balances.

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

## Remaining Mainnet validation

1. Refresh all three wallet addresses, synchronization and unlocked balances through
   already-running localhost RPCs; verify the current application fingerprints.
2. Propose Charlie's independent handshake and both participants' message costs.
3. Propose a longer encrypted message and record every fragment's TXID, fee,
   inclusion height, received bytes and successful reconstruction.
4. Have the user stop/restart Bob's official wallet for a separately approved
   offline-recovery test. The application must not manage wallet processes.
5. Record actual debits and delivery observations; require approval for each paid
   transfer or an exact immutable batch. Never retry uncertain submissions blindly.

Use [running.md](running.md) for the CLI sequence and spending-policy setup.
The shared ledger reserves before RPC, enforces allowlists/counts/costs and blocks
all participants after an uncertain outcome. It does not constrain other unlocked
RPC clients, wallet internal retries or filesystem rollback. Preserve existing
profiles and ledgers; do not clone/reset them to repeat an experiment.

Historical three-wallet identity, setup and approval notes are in the
[archived plan](archive/three-wallet-plan.md). Public captures are
[health](three-wallet-health-2026-11-11.json),
[identity pins](three-wallet-identities.json) and
[machine-readable proposed budget](three-wallet-budget.json).
