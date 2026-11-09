# DERO Private Messenger

An English-only Python research proof of concept for asynchronous, authenticated,
end-to-end encrypted messaging carried by DERO Stargate transfers. It extends the
idea of blockchain-carried encrypted communication previously explored with
Ethereum, using DERO as transport and storage. No centralized messaging service,
smart contract, remote execution, or mining is involved.

**The simulated Alice/Bob workflow works and is tested.** The official Wallet RPC
adapter is implemented and mock-tested. Read-only checks against the user-managed Mainnet wallets now pass. Application
payload delivery and its costs remain **unverified** pending approval of one probe. No Mainnet transaction has been sent by this project. See
[current Mainnet validation](docs/mainnet-validation.md) before any live experiment.
This is an unaudited PoC, not a production messenger.

## Quick start on Arch Linux

Install OS tools only if missing, then use a virtual environment. The project does
not install packages into system Python.

```bash
sudo pacman -S --needed python python-pip git
cd /path/to/dero-messenger
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python scripts/demo.py
```

The lock file records versions used for validation. Alternatively, resolve compatible
dependencies with `python -m pip install -e '.[dev]'`. Python 3.11+ is declared;
this environment was tested with Python 3.14.9. Arch/Python 3.13-specific execution
has not been separately verified.

`demo.py` launches each command in a separate process, creates two encrypted
profiles in a new temporary directory, verifies their locally obtained public keys,
establishes a session, exchanges messages, and retrieves a message sent while Alice
is offline. It prints `PASS` and the artifact directory. It never uses a real wallet,
network endpoint, funds, or miner. Synthetic `sim:` labels are not DERO addresses.

## Manual two-profile demonstration

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

## Official DERO wallet and daemon setup

The historical source build below was tested for the wallet CLI at the pinned commit.
For current Mainnet work use official Release153 and the validation guide linked above;
the historical commit predates the required payload-encryption changes. It is a
reproducible source reference, not a statement that this commit matches every
currently deployed node. Check the [official releases](https://github.com/deroproject/derohe/releases)
and [source](https://github.com/deroproject/derohe) before choosing a live version.
Verify release authenticity independently if using downloaded binaries. This project
has not downloaded or run unverified release executables.

```bash
sudo pacman -S --needed go git
mkdir -p .demo/official
cd .demo/official
git clone https://github.com/deroproject/derohe.git
cd derohe
git checkout e9df1205b6603c62f0651d0e18e5e77a2584b15e
go build -mod=vendor -o ../derod ./cmd/derod
go build -mod=vendor -o ../dero-wallet-cli ./cmd/dero-wallet-cli
cd ..
```

Run an archival daemon in a dedicated terminal and let it synchronize. The command
below starts a node, not a miner. Do not use pruning or recent-history scan limits
when testing recovery of old messages.

```bash
./derod --data-dir=./node-data --rpc-bind=127.0.0.1:10102
```

Use two separate terminals to create independent wallets with the official CLI.
Choose passwords inside the wallet, and record recovery information securely outside
this application. Do not paste seeds into `dero-chat`.

```bash
# Terminal A, in .demo/official:
umask 077
./dero-wallet-cli --wallet-file=./alice.wallet --generate-new-wallet --daemon-address=127.0.0.1:10102

# Terminal B, in .demo/official:
umask 077
./dero-wallet-cli --wallet-file=./bob.wallet --generate-new-wallet --daemon-address=127.0.0.1:10102
```

After creation, reopen each wallet with RPC enabled. Use different RPC credentials.
These wallet CLI credentials may be visible in the process list; run under a private
OS account and do not put literal secrets in shell history.

```bash
# Alice terminal:
read -r -s -p 'Alice RPC password: ' alice_rpc_password
./dero-wallet-cli --wallet-file=./alice.wallet --daemon-address=127.0.0.1:10102 --rpc-server --rpc-bind=127.0.0.1:20209 --rpc-login="alice:$alice_rpc_password"

# Bob terminal:
read -r -s -p 'Bob RPC password: ' bob_rpc_password
./dero-wallet-cli --wallet-file=./bob.wallet --daemon-address=127.0.0.1:10102 --rpc-server --rpc-bind=127.0.0.1:20210 --rpc-login="bob:$bob_rpc_password"
```

A remote daemon can instead be selected with `--daemon-address=https://YOUR_DAEMON`.
The wallet RPC endpoint still stays on loopback. The remote daemon sees address
queries and network metadata; see [DERO findings](docs/dero-findings.md). Default
ports in source differ from some help examples, so all bindings above are explicit.
Wallet registration/funding must be completed using official wallet procedures;
no coins are purchased, transferred, or mined automatically by this repository.

## Configure the DERO adapter safely

From the project root, use the venv and leave the application passphrase unset to
receive the hidden prompt. Set the matching wallet RPC credentials in each user's
application terminal. Read-only profiles leave Mainnet sending disabled:

```bash
export DERO_WALLET_USER=alice
read -r -s -p 'Alice RPC password: ' DERO_WALLET_PASSWORD
export DERO_WALLET_PASSWORD
dero-chat --profile .demo/alice-readonly setup --backend dero --wallet-rpc http://127.0.0.1:20209/json_rpc
dero-chat --profile .demo/alice-readonly wallet status
dero-chat --profile .demo/alice-readonly sync
```

`setup` obtains the official wallet address automatically. The backend accepts only
standard Mainnet addresses and validates them with the official RPC parser.
No wallet seeds or spending keys enter the application.

**Only after deciding to authorize paid testing**, create dedicated live profiles:

```bash
# Alice application terminal, with Alice RPC credentials exported:
dero-chat --profile .demo/alice-live setup --backend dero --wallet-rpc http://127.0.0.1:20209/json_rpc --enable-mainnet --confirmations 10 --fee-atomic 121

# Bob application terminal, with Bob RPC credentials exported:
dero-chat --profile .demo/bob-live setup --backend dero --wallet-rpc http://127.0.0.1:20210/json_rpc --enable-mainnet --confirmations 10 --fee-atomic 121
```

Get each identity, independently verify fingerprints, and add contacts using their
actual DERO addresses. Then follow the same request/accept/send/sync/read sequence
as the manual simulation. Each fragment costs a separate transfer: **1 atomic unit
(0.00001 DERO) plus the configured fee**. The default 121-atomic fee is an estimate
from the inspected source, not a live network quote. Live costs and acceptance must
be verified before consenting. Each actual transfer displays destination, amount,
fee, and payload size and requires interactive confirmation. There is no automatic
`--yes` bypass for real transfers.

With Release153, a standard-address request is six fragments, acceptance three, and the example
50-byte greeting two. Submission may pause until the previous transaction enters
wallet history. Inspect and resume with:

```bash
dero-chat --profile .demo/alice-live chat outbox
dero-chat --profile .demo/alice-live chat flush
```

Run `chat flush` again after the previous transfer is indexed until all fragments
show `submitted`; repeat for Bob when he sends. `sync` and `listen` never spend.
Wait for the configured confirmation depth before expecting incoming events.
There is no guarantee that ten estimated confirmations provide irreversible finality.

After a network failure, a fragment may show `sending` because submission could
have succeeded. Inspect official wallet history before deciding to retry. Stop
other processes using that profile, then, only when appropriate:

```bash
dero-chat --profile .demo/alice-live chat flush --retry-uncertain
```

This requires confirmation and can incur a duplicate fee. Stored ciphertext is
reused safely, and the receiver rejects duplicate plaintext delivery.

## Tests, capacity measurement, and implementation status

```bash
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python scripts/demo.py
```

Tests cover X25519/HKDF agreement, transcript authentication, AES-GCM tampering,
replay, reflection-related transcript checks, payload bounds, fragmentation,
missing/duplicate fragments, quotas, expiration, encrypted persistence, wrong
passphrases, nonce state across restart, uncertain submission, offline messages,
reordering, and mocked Wallet RPC calls. They never perform paid transactions.
The exact local validation results are recorded in [validation.md](docs/validation.md).

Release153's own serializer accepted **78 raw packet bytes**, encoded into **110 CBOR
bytes**, and rejected 79 bytes because serialization required 114 bytes against its
111-byte limit. The 20-byte fragment header leaves **58 envelope bytes per transfer**.
This measures the chosen field encoding, not live Mainnet capacity. Reproduction
commands and all source references are in [dero-findings.md](docs/dero-findings.md).

## Security and current limits

- Ed25519 application identities authenticate ephemeral X25519 exchanges; HKDF-SHA256
  derives directional AES-256-GCM keys. Addresses alone cannot authenticate contacts.
- Scrypt-derived AES-GCM protects all local state, including plaintext and keys.
  A wallet seed alone cannot restore application messages. Preserve the profile.
- Never resume sending from a cloned or rolled-back profile: old counters may repeat
  nonces. Start a fresh profile and reverify identities after a backup rollback.
- No Double Ratchet, secure memory erasure, delivery receipts, identity rotation UI,
  archive/compaction UI, or deep-reorg reconciliation exists. Old receive keys remain
  for offline recovery. Sending stops after 30 days or 10,000 messages per direction;
  request a new session to continue.
- Fragment groups expire after 30 days of local observation. State quotas are finite;
  attackers can cause denial of service within those limits. Old complete messages
  can be recovered if the wallet and archival daemon still provide them.
- Whole encrypted state snapshots and full-history scans favor simplicity over
  scale. Profiles have a 2048-outgoing-fragment lifetime quota. Use disposable
  profiles for experiments; do not silently delete replay state to free space.
- Mainnet fee acceptance, minimum positive transfer acceptance, wallet registration,
  deployment-version compatibility, and real offline delivery remain unverified.

See [architecture](docs/architecture.md), [protocol](docs/protocol.md),
[threat model](docs/threat-model.md), and [AGENTS.md](AGENTS.md) before extending the
project. Future priorities are authorized live interoperability tests, independent
cryptographic review, reorg-aware history, ratcheting, archival storage, and a safer
stdin-based message-entry mode.
