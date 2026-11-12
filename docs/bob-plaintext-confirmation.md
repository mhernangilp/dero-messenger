# Bob's local application decryption evidence

The user ran these commands on 2026-11-11, entering Bob's application passphrase
locally. The agent did not receive the passphrase or open the encrypted profile.

```text
$ env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app sync
Profile passphrase:
Message received in 7449a7ca589687e87c4307cf0fc562f3
Synchronized wallet height 7888203

$ env -u DERO_CHAT_PASSPHRASE .venv/bin/dero-chat --profile .mainnet/bob-app chat read Alice
Profile passphrase:
in: Hello Bob, this is an encrypted message over DERO.
```

The application records a received message only after AES-256-GCM tag validation,
counter replay checks, and UTF-8 decoding. Therefore this user-provided output is
evidence that Bob's local application authenticated and decrypted Alice's intended
plaintext with the session key derived from the signed X25519 exchange. It is not
an independently captured screen recording or a direct inspection of Bob's secret
keys. The same message's two exact ciphertext fragments and TXIDs were verified
separately through Bob's official Wallet RPC in
[alice-message-delivery.json](alice-message-delivery.json). These two evidence
sources support the Mainnet Alice-to-Bob end-to-end claim together.

This demonstrates one message in one direction. A Bob-to-Alice reply using the new
session, Charlie's own authenticated session, ten-fragment encrypted Mainnet message,
and wallet stopped/restarted offline recovery have not been performed on Mainnet.
