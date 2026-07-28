# bp-144 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **IMPORT `core.attestation.crypto` DIRECTLY.** The owner ruled 2026-07-27 (note §2.4.3):
  *"import it, the bigger issue is that core doesn't depend on anything outside the core."*
  Self-containment is directional — the inward arrow is permitted. Do NOT write a sibling
  verifier, do NOT write a parity test, and do NOT cite `scripts/handoff.py:41-43` as a
  precedent (the note records that it is a stdlib-purity choice, not a self-containment
  instance). The import line is `from core.attestation.crypto import Ed25519Signer,
  public_from_b64, verify` — the same one `core/verdict/payload.py:34` already uses.

- ⚑ **This plan does NOT depend on the registry.** Note §2.5.2. It may run concurrently with
  bp-140/141/142/143/146. If you find yourself importing `ops.registry`, you have left the
  plan — that is bp-145.

- ⚑ **No key ceremony. No key generated for production, enrolled, or committed.**
  `ops/transition_keys/` ships with a README and nothing else. F5 cannot be run by this plan;
  its obligation is to make F5 *cheap to run* when the owner's first touch-to-sign happens.

- ⚑ **Item 21's falsifier is the design-level one.** If `body_hash` changes when only front
  matter changes, §2.3's seam and §2.4's signatures are incompatible — STOP and raise. Do not
  patch around it.

- **`PRIVILEGED_TARGETS` here is `{"ratified"}` only** — narrower than bp-141's set, on
  purpose. §2.5.1: `proposed → ready` carries NO signing requirement. Do not merge the two
  constants.

- **Verification must be label-bound.** Do not try every enrolled key. "Who blessed this"
  must be answerable (oq-0036), and a try-all verifier makes it unanswerable.

- **The trust loader must fail loudly.** `crypto.verify` returns False for every failure
  mode, so a corrupt or empty trust store would look exactly like an attack. Separate the two.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
