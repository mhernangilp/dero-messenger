# Final report handoff

Run `python scripts/build_report_packet.py` from the repository root, then upload
the generated `docs/report-evidence.zip` to ChatGPT to draft a final academic or
engineering report. The generated ZIP is excluded from Git. It contains a curated, public-only snapshot:
the report source, stage reports, read-only transaction evidence, protocol and
privacy documentation, validation output, and selected implementation files. Its
`MANIFEST.json` records SHA-256 hashes for every included file. The packet contains
public wallet addresses, application public keys, TXIDs and transaction payloads.
It contains no wallet database, seed, real credential, application profile,
spending policy, spending ledger or private environment file. The manual simulation
and demo source contain explicitly disposable passphrases used only for local demos.
Historical working logs are archived separately and excluded from this report packet.

If the ChatGPT interface does not inspect ZIP contents, upload these files
individually, in this order:

1. [final-report-source.md](final-report-source.md) — consolidated claims, costs,
   caveats and links to supporting evidence.
2. [bob-plaintext-confirmation.md](bob-plaintext-confirmation.md) — user-provided
   CLI output completing the Mainnet decryption demonstration.
3. [alice-request-validation.md](alice-request-validation.md),
   [handshake-validation.md](handshake-validation.md) and
   [alice-message-validation.md](alice-message-validation.md) — all eleven
   authenticated-session transactions and their measured costs.
4. [dero-findings.md](dero-findings.md), [protocol.md](protocol.md) and
   [threat-model.md](threat-model.md) — source research and security design.
5. [privacy-analysis.md](privacy-analysis.md), [validation.md](validation.md)
   and [demo-three-output.txt](demo-three-output.txt) — privacy limits and
   simulated three-wallet results.
6. For a transaction audit, attach [alice-request-result.json](alice-request-result.json),
   [bob-response-result.json](bob-response-result.json),
   [alice-message-result.json](alice-message-result.json) and
   [alice-message-delivery.json](alice-message-delivery.json).

Suggested prompt:

> Write a final English report on this DERO Private Messenger proof of concept.
> Use the uploaded evidence as the source of truth. Separate official source-code
> findings, local simulation, official Wallet RPC observations and user-provided
> CLI output. Explain the protocol, Release153 payload-size derivation,
> eleven-transfer authenticated Alice/Bob Mainnet demonstration, exact costs,
> privacy limits, RPC timeout/reconciliation incident and remaining work. Include
> TXIDs and heights from the stage reports. Do not claim a Charlie Mainnet
> session, long encrypted Mainnet message, stopped-wallet offline recovery,
> wallet-address ownership proof or a formal security audit. Cite the uploaded
> filenames next to factual claims and flag any claim the files cannot verify.

The public explorer exposes candidate ring members, including Alice and Bob, but
does not identify their roles from those candidate addresses alone. The
`GetTransfers.sender` field was unreliable in this Release153 deployment. The
application identity fingerprints were checked out of band; they do not prove
control of the associated DERO wallet addresses.

Do not upload `.mainnet/`, `wallets.txt`, wallet `.db` files, `.env` files,
application profile databases, passphrases, seeds, private keys or the local
spending ledger. The evidence packet can be rebuilt with
`python scripts/build_report_packet.py`.
