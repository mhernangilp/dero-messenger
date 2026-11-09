# Threat model and security limits

This is an unaudited research PoC for consenting participants. It provides a tested
implementation of an authenticated encrypted channel under explicit assumptions;
it is not suitable for high-risk production use without independent review.

## Assumptions

Users compare application fingerprints through a trusted channel. Their operating
systems, cryptographic RNG, Python dependencies, and official wallet processes are
trusted. Passphrases are strong and remain private. Profile state is not maliciously
rolled back or cloned for concurrent sending. The user controls Wallet RPC and
confirms costs. A remote daemon may be curious or malicious.

## Attacks considered

| Attack | Defense or limit |
| --- | --- |
| Ciphertext alteration / metadata modification | AES-GCM covers ciphertext and header |
| Handshake substitution | Ed25519 covers roles, identities, addresses, session, and ephemeral keys |
| Reflection / unknown-key-share | Distinct identities, role-bound transcript, directional keys |
| Spoofed wallet sender field | Ignored for authentication and reply routing |
| Replayed messages | Persisted per-session receive counters |
| Replayed accepted/rejected requests | Session identifiers and tombstones retained |
| Duplicate transaction positions | Persistent txid+position deduplication |
| Crash and nonce reuse | Counter and ciphertext committed before submission |
| Delayed / reordered fragments | Persistent bounded assembly and deferred envelopes |
| Disk inspection | Passphrase-derived AES-GCM encrypted state, restricted file permissions |
| Malicious fragment flood | Size, count, lifetime, and profile quotas |
| Public RPC exposure | Client requires explicit loopback IP; wallet must bind to loopback |
| Terminal control injection | CLI escapes nonprintable characters and disables Rich markup |

Finite quotas prevent unlimited application state growth but do not prevent denial
of service: an attacker may fill fragment/request/history quotas or monopolize
wallet history scanning. The RPC response has a 32 MiB streaming limit. SQLite
files, journals, and filesystem allocation have overhead beyond logical quotas.
Authenticated messages and aliases can contain misleading visible text. CLI message
arguments may appear in shell history or process listings; use a private terminal
and avoid storing sensitive message arguments in shell history. A future stdin
input mode would improve this interface.

## Forward secrecy and key lifetime

Fresh ephemeral X25519 keys mean later theft of only an Ed25519 identity key does
not by itself derive an already completed session's keys from its transcript.
However, current and old session keys are retained in the encrypted database for
offline delivery and stored messages. A compromised unlocked endpoint or decrypted
profile exposes those sessions. There is no message-level forward secrecy,
post-compromise healing, or Double Ratchet. Removing ephemeral values from the
current state is not secure deletion from disk backups or Python memory.

Sending rotates to a new handshake after 10,000 messages per direction or 30 days.
Old receive keys remain, so rotation limits key use but does not erase old
compromise exposure. Future work includes a versioned ratchet, explicit key
confirmation, key retirement, encrypted archive separation, and backup-safe nonce
allocation. Never resume sending from an old restored profile; create a fresh
identity/profile and reverify contacts.

## Privacy boundaries

Wallet privacy is separate from application confidentiality. The daemon receives
address-bearing balance queries and observes traffic timing and origin. Transaction
counts and fragment timing can correlate conversations. Native recipient encryption
helps protect payloads on chain, but the application does not rely on it for message
authentication. A recipient sees the signed claimed return address. Simulation
stores handshake identities/addresses without DERO's outer encryption.

Fingerprint verification establishes an application identity association agreed by
users. No cryptographic proof of DERO wallet ownership is produced. Sending to an
incorrect address can lose funds or prevent delivery despite correct encryption.
Local aliases are never transmitted. Wallet credentials, seeds, and application
identity secrets are never logged. The wallet seed is never requested by this app.

## Availability and finality

An offline recipient needs the original application profile and a wallet/daemon
with adequate historical data. Losing the profile loses decryption keys; a wallet
seed alone cannot recover application messages. Public daemons may prune, censor,
lie, or become unavailable. No receipt protocol proves delivery. Confirmation depth
is a configurable heuristic and deep reorganizations are not reconciled.

Incomplete assemblies expire after 30 days of local observation. Paid submissions
can have ambiguous outcomes following a timeout. Explicit retry may incur another
fee. Wallet registration, funding, deployed consensus behavior, and fee acceptance
remain unvalidated on Mainnet in this delivery. No automated mining or paid live
test is included.
