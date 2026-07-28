# bp-150 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **BLOCKED: this plan is not startable until the owner amends
  `docs/design-notes/role-state-and-scoped-handoff.md`.** Its §2.6 (D4) currently decides
  "files as source; the queue as an input, never the source" — the opposite of what this plan
  implements. That note is ratified and agent-immutable; the amendment is an owner hand edit.
  Item 50 verifies it. If D4 still says "files as source", STOP and change nothing.

- ⚑ **The note's table names `dn-role-state-and-scoped-handoff.md`, which does not exist.**
  The real file is `docs/design-notes/role-state-and-scoped-handoff.md`. File a
  `spec-fidelity` finding; do not create a file to match a document.

- ⚑ **`journal-gate` is STILL LIVE during this plan** (bp-149 comes after). Clause (e′) shells
  out to `scripts/handoff.py --check` and asserts on `HANDOFF_STALE_SIGNATURE`. A changed
  `--check` contract blocks every session close in the repo. Prove it end-to-end against a
  fixture repo, not by reading the code.

- ⚑ **Side-effect audit before any `journal-gate` demo run:** `cmd_stop_audit` appends a
  marker line to a journal on the HOOK-FAILURE path. Fixture repo root only. Record the audit.

- ⚑ **Two sources must produce identical bytes.** Registry-sourced and tree-sourced renderings
  of the committed files must be byte-identical when the data agrees. A diff means the
  registry and the tree disagree — that is bp-143's ratchet's business, and re-pointing on
  divergent data hides it.

- ⚑ **Do not delete the tree scanners.** They are the invariant-5 fallback AND the
  recovery-import inputs for bp-141/bp-143. Signatures unchanged — three consumers.

- **Measure the import cost first** (`python -X importtime -c "import ops.registry"`).
  `handoff.py` is shelled out to on every session close by a live hook; dragging
  `cryptography`/`numpy`/LanceDB into that path is a real regression. Lazy-import the signing
  path if needed.

- **Do not restate the idempotence pin.** `scripts/handoff.py:18-27` is the canonical
  statement and `ops/registry/export.py` already cites it. A third statement drifts.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects.

## Entries

_(none yet — this plan is `proposed` AND blocked on an owner amendment; the first entry is
written by the build session, which may not start until Item 50's precondition holds)_
