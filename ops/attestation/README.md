# Attestation public keys

Ed25519 **public** keys for verifying attestation signatures (the runtime proof layer —
`core/attestation/`, design-notes/attestation-layer.md). Public keys are non-secret and belong
in the repo; the matching **private** seeds live only in Keychain/Vault and are never committed.

| File | Signs | Private seed lives in |
|------|-------|-----------------------|
| `supervisor.pub` | every agent attestation (dream/curate/ingest) | `get_secret("attestation-signing-key")` — Keychain (Step 3) → Vault KV (Step 4+) |
| `owner.pub` | **gate-decision** attestations only (non-repudiable owner approval) | `get_secret("attestation-owner-key")` — Keychain, hardware-bound if possible |

The verifier (`core/attestation/verify.py`) selects the public key by the attestation's `signer`
field and **requires `signer == "owner"` for gate actions** (`gate_approve` / `gate_reject`).

## ⚠️ The committed keys here are DEV keys, not production

`supervisor.pub` / `owner.pub` as committed match the **dev** seeds in `tests/keys/` so the
signed path is verifiable out of the box (CI, local dev, `scripts/verify_attestation.py`). They
carry **no production trust**.

**Production key placement is owner-operated** (full steps in the runbook, Step 6):
1. `python scripts/gen_attestation_keys.py supervisor` — prints a fresh base64 seed and writes
   the new `supervisor.pub` here. Place the printed seed in Keychain under
   `attestation-signing-key` (never commit it). Repeat for `owner`.
2. Commit the regenerated `*.pub` files (they're public).
3. Set `[attestation] enabled = true` in config. Signing then activates; turning it on without a
   placed key is a hard error (fail-closed), never a silent unsigned run.
