# Documentation

This repository evaluates DERO as one transport for **ChainChat**, a research
project studying blockchain cover channels for private communication.

## Start here

- [Running the PoC](running.md): manual simulation and the Mainnet CLI sequence.
- [Final experiment summary](final-report-source.md): verified results, costs,
  evidence quality and remaining work.
- [Architecture](architecture.md), [protocol](protocol.md),
  [threat model](threat-model.md) and [privacy analysis](privacy-analysis.md).
- [DERO findings](dero-findings.md): official source references, RPC behavior and
  the Release153 payload-capacity measurement.
- [Validation record](validation.md): automated tests and simulation results.

## Mainnet evidence

- [Signed request](alice-request-validation.md): six Alice-to-Bob transfers.
- [Signed acceptance](handshake-validation.md): three Bob-to-Alice transfers.
- [Encrypted message](alice-message-validation.md): two Alice-to-Bob transfers.
- [Bob's local plaintext output](bob-plaintext-confirmation.md): user-provided
  evidence of successful application decryption.
- Matching `*-proposal.json`, `*-result.json` and `*-delivery.json` files preserve
  public transaction details and observations.

The experiment completed one Alice/Bob authenticated Mainnet session and one
message. Charlie's Mainnet session, longer encrypted Mainnet messages and
stopped-wallet recovery remain untested. Three-participant and offline workflows
passed in simulation; see [the recorded output](demo-three-output.txt).

## Historical records and report export

[mainnet-validation.md](mainnet-validation.md) summarizes the completed Mainnet
experiment and links to its evidence.
[three-wallet-plan.md](three-wallet-plan.md) describes a proposed 33-transfer
experiment, not 33 completed Mainnet transfers. Raw snapshots preserve observations
at capture time, including the timeout and wallet-history reconciliation incident.
Superseded working logs and earlier source assumptions live in [archive/](archive/README.md).
Use the current summaries above when assessing what was completed.

For a curated public report export, follow [report-handoff.md](report-handoff.md).
The ZIP is generated locally and excluded from Git. Public records include wallet
addresses, application public keys and TXIDs. Wallet files, private profiles,
credentials and spending ledgers remain local.
