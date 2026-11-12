# Running the DERO PoC

Install the project using the [README](../README.md), activate `.venv`, and run
commands from the repository root. Use a new profile directory for a new experiment.

## Manual simulation


From the repository root with the venv active, use a new directory for each run.
The example environment passphrase is for disposable simulation only. For normal
use, leave it unset and enter a unique passphrase at the hidden prompt. Two users
can have different passphrases; the automated demo uses one only for convenience.

```bash
export DERO_CHAT_PASSPHRASE='simulation-only long demo passphrase'
export COLUMNS=240
mkdir -p .demo/manual

dero-chat --profile .demo/manual/alice setup --address sim:alice --chain .demo/manual/chain.db
dero-chat --profile .demo/manual/bob setup --address sim:bob --chain .demo/manual/chain.db

dero-chat --profile .demo/manual/alice wallet status
dero-chat --profile .demo/manual/bob wallet status

alice_key=$(dero-chat --profile .demo/manual/alice identity | python -c 'import json,sys; print(json.load(sys.stdin)["public_key"])')
bob_key=$(dero-chat --profile .demo/manual/bob identity | python -c 'import json,sys; print(json.load(sys.stdin)["public_key"])')

dero-chat --profile .demo/manual/alice contacts add sim:bob --alias Bob --identity "$bob_key" --verified
dero-chat --profile .demo/manual/bob contacts add sim:alice --alias Alice --identity "$alice_key" --verified
dero-chat --profile .demo/manual/alice contacts list

request_id=$(dero-chat --profile .demo/manual/alice chat request Bob)
dero-chat --profile .demo/manual/bob sync
dero-chat --profile .demo/manual/bob chat requests
dero-chat --profile .demo/manual/bob chat accept "$request_id"
dero-chat --profile .demo/manual/alice sync

dero-chat --profile .demo/manual/alice chat send Bob 'Hello Bob, this is an encrypted message over DERO.'
dero-chat --profile .demo/manual/bob sync
dero-chat --profile .demo/manual/bob chat read Alice

dero-chat --profile .demo/manual/bob chat send Alice 'Hello Alice, I decrypted your message.'
dero-chat --profile .demo/manual/alice sync
dero-chat --profile .demo/manual/alice chat read Bob

# Alice is stopped: no Alice process needs to be running for Bob to send.
dero-chat --profile .demo/manual/bob chat send Alice 'This message waited while you were offline.'
# A fresh Alice process unlocks its persisted state and recovers the message.
dero-chat --profile .demo/manual/alice sync
dero-chat --profile .demo/manual/alice chat read Bob
unset DERO_CHAT_PASSPHRASE
```

For real contacts, compare the SHA-256 fingerprint displayed by `identity` through
an independently trusted channel. `--verified` is an explicit assertion that you
have done so; omit it for an interactive confirmation. This verifies the application
identity association, **not cryptographic ownership of the DERO address**.

Other commands:

```bash
dero-chat --profile .demo/manual/bob chat reject REQUEST_ID
dero-chat --profile .demo/manual/alice chat listen
dero-chat --profile .demo/manual/alice chat outbox
dero-chat --profile .demo/manual/alice chat flush
```

`listen` polls for events and retries temporary RPC failures; Ctrl-C stops it.
`chat read` displays plaintext locally. Aliases stay local. Received data is never
executed. Message command arguments may remain in shell history/process listings;
use a private terminal and suitable shell-history settings for sensitive content.

## Connect official wallets

Use official [DERO releases](https://github.com/deroproject/derohe/releases).
The experiment used wallet Release153, source commit
`0e8a90770b2817e6857af03f1c5642cb7913815f`. Source analysis and capacity
reproduction commands are in [dero-findings.md](dero-findings.md).

Register, fund and synchronize wallets using the official software. Start and
unlock them yourself in separate terminals. Keep their RPC servers on loopback:

```bash
# Alice terminal; replace YOUR_DAEMON:PORT with your chosen daemon.
dero-wallet-cli-linux-amd64 --wallet-file /path/to/alice.db \
  --daemon-address YOUR_DAEMON:PORT --rpc-server --rpc-bind 127.0.0.1:20209

# Bob terminal.
dero-wallet-cli-linux-amd64 --wallet-file /path/to/bob.db \
  --daemon-address YOUR_DAEMON:PORT --rpc-server --rpc-bind 127.0.0.1:20210
```

Use a private OS account; access to an unlocked Wallet RPC can authorize spending.
If Wallet RPC authentication is enabled, supply `DERO_WALLET_USER` and
`DERO_WALLET_PASSWORD` securely in the corresponding application terminal. See
[.env.example](../.env.example) for variable names; the app does not load `.env`
automatically. Never put real credentials in Git or command arguments.

First create read-only application profiles against the already-running wallets:

```bash
unset DERO_CHAT_PASSPHRASE
dero-chat --profile .mainnet/alice-readonly setup --backend dero \
  --wallet-rpc http://127.0.0.1:20209/json_rpc
dero-chat --profile .mainnet/alice-readonly wallet status
dero-chat --profile .mainnet/alice-readonly sync
```

Repeat for Bob with a separate profile and port 20210. `setup` obtains the address
from Wallet RPC and prompts for an **application** passphrase, never a wallet
password. Check the returned addresses, synchronization and unlocked balances.
A lost application passphrase cannot be reset while retaining its encrypted keys.

## Paid Mainnet workflow

The completed experiment is recorded in [final-report-source.md](final-report-source.md).
Historical approved batches and their ledgers are consumed. The `*_batch` modules
and `reconcile_request_timeout.py` are experiment-specific records, not instructions
for a new run. Use fresh profiles and a separate budget for a new experiment;
never clone or reset the previous experiment's ledger or send from restored state.

For a new Alice/Bob request, acceptance and the 50-byte greeting below, the
historical workload was 6 + 3 + 2 transfers. At the observed fee of 181 atomic
units plus amount 1, gross debit was 2002 atomic units (0.02002 DERO).
Refresh fees and balances; 181 is an experimental observation, not a live quote.
There is no verified fee-estimation RPC in this integration.

Create `.mainnet/policy.json` with restrictive permissions and this structure.
Replace both address placeholders with the actual standard wallet addresses:

```json
{
  "participants": {"ALICE_ADDRESS": 8, "BOB_ADDRESS": 3},
  "max_transactions": 11,
  "max_debit_atomic": 2002,
  "fee_atomic": 181
}
```

Both participants must use the same policy path and durable ledger. For new profiles:

```bash
dero-chat --profile .mainnet/alice-new setup --backend dero \
  --wallet-rpc http://127.0.0.1:20209/json_rpc --enable-mainnet \
  --confirmations 10 --fee-atomic 181 --spending-policy .mainnet/policy.json
dero-chat --profile .mainnet/bob-new setup --backend dero \
  --wallet-rpc http://127.0.0.1:20210/json_rpc --enable-mainnet \
  --confirmations 10 --fee-atomic 181 --spending-policy .mainnet/policy.json
```

Run `identity` on each profile. Compare fingerprints and the claimed addresses
through an independently trusted channel, then pin each other's application keys:

```bash
dero-chat --profile .mainnet/alice-new contacts add BOB_ADDRESS --alias Bob --identity BOB_PUBLIC_KEY
dero-chat --profile .mainnet/bob-new contacts add ALICE_ADDRESS --alias Alice --identity ALICE_PUBLIC_KEY
```

Prepare once, review the exact public proposal, and approve each transfer before
submission. `--prepare-only`, `chat proposal`, `sync`, `chat read` and
`chat reconcile` do not broadcast:

```bash
dero-chat --profile .mainnet/alice-new chat request Bob --prepare-only
dero-chat --profile .mainnet/alice-new chat proposal
# After reviewing the proposal: approve each displayed transfer interactively.
dero-chat --profile .mainnet/alice-new chat flush
```

Inspect `chat outbox`. If submission pauses for indexing, wait for the known TXID
to enter wallet history, then flush the remaining pending fragments. Once all six
request fragments are confirmed:

```bash
dero-chat --profile .mainnet/bob-new sync
dero-chat --profile .mainnet/bob-new chat requests
# Replace REQUEST_ID with the received session identifier.
dero-chat --profile .mainnet/bob-new chat accept REQUEST_ID --prepare-only
dero-chat --profile .mainnet/bob-new chat proposal
dero-chat --profile .mainnet/bob-new chat flush
```

Complete the three response fragments with the same review and indexing checks,
then derive Alice's session keys and prepare the greeting:

```bash
dero-chat --profile .mainnet/alice-new sync
dero-chat --profile .mainnet/alice-new chat send Bob \
  'Hello Bob, this is an encrypted message over DERO.' --prepare-only
dero-chat --profile .mainnet/alice-new chat proposal
dero-chat --profile .mainnet/alice-new chat flush
# After both message fragments are submitted, indexed and confirmed:
dero-chat --profile .mainnet/bob-new sync
dero-chat --profile .mainnet/bob-new chat read Alice
```

Expected plaintext: `in: Hello Bob, this is an encrypted message over DERO.`
Every fragment is a paid transaction requiring explicit approval. The shared gate
reserves cost before RPC submission. An uncertain result blocks further spending:
stop, inspect history and reconcile the existing TXID. Never automatically retry,
reset the ledger or rerun an old batch. `chat reconcile` records known submissions
without broadcasting; it cannot resolve every wallet-history failure automatically.
