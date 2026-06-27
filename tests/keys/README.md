# Dev/test attestation keys — NOT PRODUCTION SECRETS

`supervisor.seed` and `owner.seed` are base64 Ed25519 **private seeds** used **only by the test
suite** to exercise the signing/verification path (`tests/integration/test_attestation_crypto.py`,
`tests/integrity/test_attestation_signatures.py`). They are derived deterministically from a fixed
phrase, so they are stable and reproducible — and carry **zero production trust**.

Their matching public keys are committed at `ops/attestation/{supervisor,owner}.pub`.

These seeds are **never** read by `build_attestor()` — production signing uses
`get_secret("attestation-signing-key")` (Keychain/Vault), never this directory. The owner
generates real keys and places the private seeds in Keychain (see `ops/attestation/README.md`);
the dev keys here exist so tests and CI have a working signed path without any real secret.
