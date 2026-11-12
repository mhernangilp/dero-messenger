# Application protocol version 1

This is an experimental protocol, not an audited standard. Integers are unsigned
and big-endian. Bytes described here are independent of the DERO RPC wrapper.
No wallet private key is used by the application.

## Identity verification and roles

Each profile generates a persistent Ed25519 identity. `identity` displays its
32-byte public key and SHA-256 fingerprint. Contacts pin the public key only after
an independent trusted comparison (in person, or through an already authenticated
channel). The required key is an intentional extension of `contacts add <address>`.
An address alone is insufficient for this authenticated protocol.

A signature proves possession of an application identity key, not the associated
DERO wallet. Both parties verify the address-to-application-identity association
externally. Aliases never enter an envelope. Unknown request identities can be
listed but cannot be accepted without the matching pinned contact. There is no
unverified automatic trust-on-first-use fallback.

## Handshake

Every envelope begins with `version:u8 | type:u8 | session:16 bytes` (18 bytes).
Types are request=1, accept=2, encrypted message=3. Session IDs are random 128-bit
values. Participants use distinct application identity keys.

Request layout:

| Field | Bytes |
| --- | ---: |
| Common header | 18 |
| Initiator Ed25519 public key | 32 |
| Intended responder Ed25519 public key | 32 |
| Initiator ephemeral X25519 public key | 32 |
| Initiator address length + ASCII address | 1 + 1..128 |
| Responder address length + ASCII address | 1 + 1..128 |
| Initiator Ed25519 signature | 64 |

The signature covers `domain || request_without_signature`, where domain is the
ASCII string `DERO Private Messenger handshake v1` followed by a zero byte. Address
lengths make this serialization unambiguous. Trailing bytes, unsupported versions,
invalid signatures, reflection to the same identity, and wrong recipients fail.
For two standard 66-character DERO addresses the request is 312 bytes: six
fragments. The source address is used for replies only after identity validation.

Acceptance layout is exactly 146 bytes:

`header | SHA256(full_request):32 | responder_ephemeral:32 | signature:64`

The responder signs `domain || full_request || response_without_signature`.
Both sides therefore authenticate the version, roles, session ID, both identities,
both ephemeral keys, and both claimed wallet addresses. Substitution and
unknown-key-share attempts change the authenticated transcript. Acceptance also
requires a locally pending request with the same identifier and hash.

X25519 rejects an all-zero shared secret through the cryptography library. HKDF
uses SHA-256, `salt=SHA256(full_request || full_response)`, and ASCII info
`dero-chat/v1/A-to-B|B-to-A`. Its 64 output bytes are split into two 32-byte keys:
first initiator-to-responder, then responder-to-initiator. Role-specific keys
prevent reflection. Private ephemeral values are removed from active state when
keys are established. There is no secure-erasure guarantee for Python memory,
SQLite historical pages, OS caches, snapshots, or backups.

Acceptance authenticates the peer but does not provide explicit proof of shared-key
possession. The first successfully decrypted application message provides implicit
key confirmation. Bob may send after acceptance; Alice buffers data that arrives
before the acceptance fragments. A separate confirmation round is future work.
Rejection is local and retains a session tombstone; it sends no transaction.

## Encrypted messages and nonces

`header:18 | counter:u64:8 | ciphertext:1..4096 | GCM_tag:16`

The 26-byte prefix is authenticated additional data. The nonce is the counter
encoded as a 12-byte unsigned big-endian integer, including four leading zero
bytes. AES-256-GCM uses the appropriate directional key. UTF-8 plaintext is bounded
to 4096 bytes. Empty messages are rejected. The total envelope limit is 8192 bytes.

Counter increment, ciphertext, and outgoing fragments commit together in SQLite
before submission. A network failure can consume a counter, which is harmless.
Retries send identical stored ciphertext; they never encrypt a different plaintext
under a previously used nonce. Concurrent state changes serialize with
`BEGIN IMMEDIATE`. Received counters persist only after AEAD and UTF-8 validation;
all seen counters are retained so out-of-order messages are supported. Replay
protection is per session. New sessions derive unrelated keys and reset counters.

Each direction may send at most 10,000 messages, and sending stops 30 days after
local session establishment. Start a fresh signed handshake to continue. Old
receive keys remain available for offline delivery; counters below 10,000 remain
valid even after 30 days if not previously received. The newest established session
is selected for new sends. This bounds key use but does not implement a ratchet.

Never resume sending from a restored older profile snapshot or copied profile.
Its rolled-back counter could repeat a nonce. Start a new profile/identity and
reverify contacts after rollback. Protection against malicious disk rollback needs
an external monotonic anchor and is outside this PoC.

## Fragmentation and RPC wrapping

New outgoing packets are at most 78 bytes (Release153):

`magic:'DM':2 | SHA256(envelope)[0:16]:16 | index:u8 | count:u8 | chunk:1..58`

Counts are 1..142, indexes start at zero, and every new nonfinal chunk is 58 bytes.
Reassembly verifies the truncated SHA-256 identifier; final envelope authentication
uses Ed25519 or AES-GCM. The digest detects corruption but is not an authenticator.
An active attacker can disrupt assembly; no delivery-availability guarantee exists.

Limits are 64 incomplete groups, 64 deferred complete envelopes, 8192 bytes per
envelope, 128 contacts, 128 sessions, 10,000 locally stored messages, 2048 outgoing
fragments, and 100,000 observed incoming transaction positions per profile. Quotas
fail closed instead of growing indefinitely. They are PoC lifetime limits; archival
and compaction commands are future work. Fragment and deferred-envelope expiration
is 30 days since first local observation, rather than blockchain creation time.
A complete old message can still be received on the first sync after a long absence.
Missing fragments received after expiration cannot resurrect already deduplicated
parts automatically; the sender should send a new application message/session.

Legacy incoming packets with consistently sized 82-byte nonfinal chunks remain
readable. New sends use 58-byte chunks because of a demonstrated Release153 limit;
older receivers must upgrade. Existing oversized outbox packets are not silently
rewritten. This changes fragmentation only, not the authenticated envelope format.

Packets are base64 encoded into one `payload_rpc` string argument named `m` with
datatype `S`. DERO's source serializer encodes 78 packet bytes into 110 CBOR bytes (111-byte limit).
No port argument is used. Receivers recognize the argument and fragment magic.
Signatures and application ciphertext remain independently authenticated after
DERO's recipient payload decryption.

## Versioning

Unknown versions/types are rejected. A future ratchet must use a new protocol
version and define header/key transitions explicitly. Version 1 never silently
interprets new formats or changes identity pins.

## Resource accounting and three-wallet validation

Each incomplete group now rejects a new chunk before its accumulated decoded bytes
exceed 8192, including legacy 82-byte chunks. At most 64 groups therefore retain
524,288 decoded fragment bytes; hex persistence uses up to 1,048,576 characters
plus keys/metadata. The 64 deferred envelopes have the same byte ceiling separately.
Each group has at most 142 indexed entries. Duplicate identical fragments do not
increase state; conflicting counts or content fail. Out-of-order fragments remain
indexed until complete, then all nonfinal chunk sizes must agree and the full
truncated hash must match before protocol authentication. TTL cleanup runs during
reconstruction/draining, not in a background timer.

Stored message text is bounded by 10,000 messages of at most 4096 UTF-8 bytes
(40,960,000 bytes before JSON escaping/metadata); sessions by 128 and each receive
counter set by 10,000; outgoing packets by 2048; observed positions by 100,000.
These are logical limits, not an exact SQLite file-size or process-RSS guarantee.
JSON hex/escaping, SQLite journals, copies during encrypted state transactions and
RPC buffers add overhead. RPC responses are capped at 32 MiB but full-history scans
and sorting can still be costly. Resource exhaustion remains an availability risk.

Standard-address handshakes use 6+3 transactions; message sizes 16/17 UTF-8 bytes
use 1/2; the planned 512-byte message uses 10. The three-profile simulation exercises
independent identity pins and directional keys, reverse-order duplicate fragments
and restart recovery. See three-wallet-plan.md for the distinction from live tests.
