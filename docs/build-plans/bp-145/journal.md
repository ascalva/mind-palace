# bp-145 — journal

## Pre-build notes for whoever picks this up

- ⚑ **Invariant 3 is "absent", not "flagged off".** There must be no `skip_verify`, `force`,
  `unsafe`, or `bypass` anywhere on the path to a stored `→ratified`. Grep the diff for those
  words before committing. Item 26's falsifier is an active scan proving `admit()` is the
  only path — do not settle for inspection.

- ⚑ **`proposed → ready` stays UNSIGNED.** Note §2.5.1 and §2.5.2. Widening
  `PRIVILEGED_TARGETS` here would silently block bp-138/bp-139, which the note declares
  independent. If someone asks for it, that is an amendment to a ratified note — park and
  surface.

- ⚑ **`bless` does not sign.** It consumes an already-signed payload from
  `scripts/sign_transition.py --external`. No agent-reachable code path produces a signature.
  That is what makes `draft → ratified` owner-only in fact rather than by policy.

- ⚑ **Clause 3 (stale pre-image) is easy to forget and is a replay hole.** A signature valid
  over an older `from_content_hash` must be rejected. "The pre-image is part of the signed
  object" (§2.4.1) only helps if admission checks it against the entity's *actual* recorded
  content hash.

- **Both ratchets will be vacuously green until the ceremony.** Item 28 must build synthetic
  red cases (unsigned, wrong key, wrong five-tuple) and observe each fail. Same trap bp-142
  hit; do not repeat it.

- **No `ALTER TABLE`.** bp-140 §6.2 already gave the events table nullable `signature`/`signer`
  columns precisely so this plan needs no migration on an append-only table.

- **Two constants, deliberately different.** bp-141's `PRIVILEGED_TARGETS` (what must not
  become effective while queued) vs bp-144's (what must carry a signature). Each comment must
  name the other. Do not "fix" the divergence.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
