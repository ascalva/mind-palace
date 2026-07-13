---
type: finding
id: finding-0064
status: open
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-026/plan.md
  - tests/unit/test_interpreter_versions.py
  - ops/code_sensor.py
ftype: spec-defect
origin_plan: bp-026
route: builder
resolution: null
---

# bp-026's Item 19/20 source edit needs a phi_code source-hash RE-PIN (not a version bump)

## What

`tests/unit/test_interpreter_versions.py` (bp-018's interpreter-version ratchet, dn-self-sensing
§3.2 V2) pins, for `phi_code`, a `(version, sha256)` pair over `(ops/code_sensor.py,
ops/code_snapshot.py)`. bp-026 Items 19/20 edit `ops/code_sensor.py` (the writer migration +
the new `_corpus_to_corpus_edges` pass), which IS in this plan's `write_scope`. This changes
the file's source bytes — so the ratchet reds until a **deliberate act**: EITHER bump
`INTERPRETER_VERSION` and pin the new pair (a worldview change — re-projection supersedes) OR
re-pin the sha256 at the same version (a declared refactor — no re-projection). The ratchet
explicitly licenses either, chosen deliberately.

`docs/build-plans/bp-026/plan.md` is silent on `INTERPRETER_VERSION`/the ratchet entirely — no
§2 manifest entry, no §6 interface note, no §11 parked row. That silence is itself the spec gap:
Item 20's acceptance test never anticipated this file's pin existing.

## Why it matters — and why this is a RE-PIN, not a bump

**Corrected resolution (orchestrator scrutiny catch, 2026-07-13).** My first pass over-bumped
`INTERPRETER_VERSION` 1.0.0 → 1.1.0, reasoning that corpus_to_corpus edges are "new sensed
content = a worldview change." That is wrong. The grounding:

- `INTERPRETER_VERSION` stamps **only code observations** — every usage is
  `self.observations.is_projected(sha, INTERPRETER_VERSION)` /
  `self.observations.mark_projected(sha, content, INTERPRETER_VERSION)` (code_sensor.py, in
  `_project` and `backfill_observations`). It governs the `code_observations` store's
  re-projection / supersession semantics, nothing else.
- **Reference edges carry NO version field** at all — the `reference_edges` schema is
  content-keyed (`edge_id` over the endpoint tuple), append-only, and regenerable. φ_doc's
  `corpus_to_corpus` edges are an **unversioned reference-edge lane**.
- bp-026's φ_doc emits reference edges ONLY. It does **not** change any code observation:
  Item 19 kept code↔corpus semantics byte-for-byte identical (the plan's own acceptance bar),
  and the new pass only ADDS reference edges — the SAME commit still yields the SAME code
  observations.
- Therefore a bump would spuriously re-project + archive the **entire unchanged
  `code_observations` store** — a worldview supersession of content identical modulo the
  version stamp. The doctrine's re-projection is for when the SAME input yields DIFFERENT
  versioned output; here the same input yields the SAME output. Bumping is semantically wrong.

So this is a **declared refactor** of φ_code's versioned worldview (the source bytes changed;
the code-observation worldview did not) → **re-pin the sha256 at version 1.0.0**. dn-self-sensing
§2.4 licenses exactly this.

I have REVERTED `ops/code_sensor.py`'s `INTERPRETER_VERSION` back to `"1.0.0"` (in write_scope),
with an inline comment recording this reasoning. That revert makes two of the three tests my
over-bump had reddened GO GREEN with NO edit:
- `tests/unit/test_interpreter_versions.py::test_declared_version_matches_the_pin[phi_code]` —
  PASSES (declared 1.0.0 == pinned 1.0.0).
- `tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive` —
  PASSES **untouched** (its hardcoded `"1.0.0"` literals are valid again now that the real
  version is 1.0.0; this file needs NO change — the second breakage my over-bump caused is
  GONE). Confirmed by direct run this session.

## The ONE remaining out-of-scope fix (orchestrator's, at seal)

`tests/unit/test_interpreter_versions.py::test_source_hash_matches_the_pin[phi_code]` stays RED
by construction (the source bytes DID change), and is the single known-routed red. The pin lives
in `tests/unit/test_interpreter_versions.py`, outside bp-026's write_scope
(`core/stores/reference_edges.py`, `ops/code_sensor.py`, `tests/unit/test_reference_edges.py`,
`tests/integration/test_reference_edge_isolation.py` [fixtures only], `docs/build-plans/bp-026/**`,
`docs/findings/**`) — I cannot land it. **The exact fix** — ONLY the sha256 changes; version
stays 1.0.0:
```python
"phi_code": Interp(version_attr=("ops.code_sensor", "INTERPRETER_VERSION"),
                   sources=("ops/code_sensor.py", "ops/code_snapshot.py"),
                   version="1.0.0",   # UNCHANGED — a re-pin, not a bump
                   sha256="9bd50a2aa34e692e2eec959fa0c92e9a57d71dd4fd847301f8f8ce487f6a563e"),
```
Computed via `source_fingerprint(("ops/code_sensor.py", "ops/code_snapshot.py"))` against this
worktree's edited files (the sha over `(path, NUL, bytes, NUL)` per file). Re-verify against the
actual merged bytes on `main` if the merge is non-trivial (conflicts/reordering) — the recorded
hash is exact for this worktree's HEAD but any post-merge byte drift changes it.

## Re-entry condition

Orchestrator re-pins the `phi_code` sha256 (the one-field diff above, version staying 1.0.0) at
bp-026's seal — `tests/unit/test_interpreter_versions.py` is outside every currently-open plan's
write_scope, so this is a direct orchestrator hand-edit (mirroring how `docs/PROGRESS.md` writes
work). That is the ONLY out-of-scope edit this finding now requires (the `test_code_sensor.py`
fix the over-bump had implied is no longer needed — the revert made it green).

## Routing

`spec-fidelity` — the builder (this session) diagnosed and resolved the in-scope half (reverted
to a re-pin, making two of three tests green untouched); the single remaining out-of-scope
sha256 re-pin is routed to the **orchestrator** to land at seal. Not `design | math |
direction` — a mechanical, pre-computed, single-value fix with a clear correct answer.
