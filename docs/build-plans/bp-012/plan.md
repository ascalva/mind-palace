---
type: build-plan
id: bp-012
status: ready
design_ref:
  - docs/design-notes/code-observation-projection.md
contract: builder
write_scope:
  - "core/stores/code_observations.py"
  - "core/sensing.py"
  - "ops/code_sensor.py"
  - "ops/lifecycle/launcher.py"   # oq-0013: owner-concurred (Item 4 reset registration), 2026-07-11
  - "tests/**"
  - "docs/findings/**"
  - "docs/build-plans/bp-012/**"
session_budget: 1
cost:
  estimate: { model: fable, tokens: 300k }    # core store discipline; bp-009-calibrated, heavier
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/brainstorms/code-as-sensor-stream.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-b: the code-observation store and the projection seam (φ_code lands)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from the ratified `code-observation-projection.md` — its **B-b**: code
observations become real rows in the observed stratum, entering through the sensing-seam
pattern, attested. Readiness blessing is the owner's hand.

## 1. Objective

The code sensor projects per-commit, symbol-grain observations (schema §2.3) through a
filesystem handoff into a dedicated OBSERVED-only store, idempotently by
(commit_sha, path, qualname), each projection attested — and the mirror provably never
sees them.

## 2. Context manifest

1. `docs/design-notes/code-observation-projection.md` — §2.2 (interpreter contract),
   §2.3 (schema, verbatim in §6 below), §2.4 (seam), §2.6 (firewall), B-b falsifier.
2. `core/sensing.py` — `SensedObservation` / `SensingHandoff.collect` / `ObservedView`
   (the pattern; V1: this plan builds the _sibling_, confirming reuse vs parallel at source).
3. `core/stores/derived.py` — the no-provenance-parameter mint discipline to copy.
4. `ops/code_sensor.py` — `sync()` (where projection batches are emitted).
5. `docs/build-plans/bp-006/journal.md` — typing conventions (core is strict; stay green).

## 3. Investigation & grounding

- **Q1 — seam reuse or sibling?** (V1) `core/sensing.py` verified 2026-07-10/11:
  `SensedObservation` is biometric-shaped (`SensedObservation.to_row()` writes
  provenance=OBSERVED); `SensingHandoff.collect` reads handoff files into observations.
  The builder confirms at source whether a generic handoff carries a second payload type
  or whether a parallel `CodeSensingHandoff` (same shape, own file pattern) is cleaner —
  _the code does not fully settle this; the note's default is "same seam family, own
  store/table", and either satisfies it._
- **Q2 — store engine?** (V2) Default **SQLite** (`data/code_observations.sqlite`): the
  repo's convention is SQLite for per-concern append-only ledgers keyed by identity
  (runs, versions, attestations, snapshots); DuckDB is the telemetry/time-series lane.
  Observations are identity-keyed readings, not aggregate series. Rejected-with-record:
  DuckDB (joins against snapshots would be nice, but snapshots are SQLite too).
- **Q3 — writes into the store carry provenance how?** Copy `DerivedStore.add`'s
  discipline verbatim: the store writes `OBSERVED` unconditionally; **no provenance
  parameter exists**; a wrong-class row is unrepresentable at this boundary.
- **Q4 — reset semantics?** Corpus-layer or build-history? The note: observations are
  corpus-side (the observed stratum) → **reset target** (wiped with the corpus), NOT
  reset-guarded like the snapshot ledger. Add to `reset_targets()` — the bp-fix precedent
  (2026-07-11) says sidecars must be listed explicitly.
- **Q5 — attestation shape?** `code_sensor / project_observations`, inputs=[commit sha],
  outputs=[batch content hash], chained (the ingest_commit attestation for the same sha
  becomes its parent automatically via `producers_of`).

**Additional risks or questions surfaced during reading:** the daemon (Ouroboros) does
NOT consume these rows yet — write-side only, like the dispositional stores; say so in
the store docstring to keep the summaries honest (finding-0020 class).

## 4. Reconciliation

- `ops/code_sensor.py` docstring ("event-log-only, outside the knowledge corpus") →
  **banner: correction** — after B-b the stream ALSO projects into the observed stratum;
  the ledger remains the ops-side record. Cite the ratified note.
- `ops/lifecycle/launcher.py` `reset_targets()` → **cross-ref: extension** — the new
  store joins the wipe list (Q4).

## 5. Write scope

Prose mirror: the new store, the sensing seam file (sibling addition only — existing
classes untouched), the sensor (emit + project), tests (new files only), findings, own
dir. **Out of scope:** `MIRROR_READABLE` and every existing view (§2.6 — untouchable);
the reference-edge store (bp-013); any consumer (B-d, Track D); `ops/lifecycle/**` EXCEPT
the one `reset_targets()` line (carried explicitly by Item 4).

**Scope amendment note:** `ops/lifecycle/launcher.py` is added to the effective scope for
Item 4 ONLY — one list entry. The scope-guard front-matter must include it:
this plan's write_scope is amended to add `"ops/lifecycle/launcher.py"` at blessing if
the owner concurs (or Item 4 parks with a finding).

**APPLIED 2026-07-11 (owner concurred via oq-0013):** `"ops/lifecycle/launcher.py"` is
now in the front-matter `write_scope` (one entry). Item 4 proceeds — the single
`reset_targets()` line + comment + the additive seed line in the existing reset test.
The rest of `ops/lifecycle/**` stays out of scope.

## 6. Interfaces pinned inline

Schema (note §2.3, VERBATIM — the store's columns):

```
CodeObservation:
  commit_sha      str     # the reading's time coordinate (git's own content address)
  path            str     # file within the tree
  qualname        str     # symbol (module-level = "")
  kind            str     # module | class | function | async_function
  signature       str     # unparsed arg list ('' for classes/modules)
  docstring       str     # the Rosetta payload — verbatim, '' if absent
  references_out  list    # typed: [{type: note-citation | path-mention | symbol-mention
                          #          | design-ref, target: str, source_line: int}]
  provenance      OBSERVED (structural; the store writes nothing else)
```

Interpreter contract (§2.2): deterministic; sole path in; transform-attributed;
re-interpretation = versioned supersession at the same (commit, symbol) key.

B-b falsifier (note §3.3, verbatim): _"a second projection of the same commit changes
row count."_

Mint discipline to copy (`core/stores/derived.py:177` family): no provenance parameter;
INSERT OR IGNORE on the identity key.

## 7. Items

### Item 3 — the store

- **Objective:** `core/stores/code_observations.py` — OBSERVED-only writer, identity key
  (commit*sha, path, qualname), `references_out` as JSON column, open*\* helper.
- **Files:** the store, `tests/unit/test_code_observations.py` (new).
- **Acceptance test:** unit tests: idempotent double-insert; no provenance param exists;
  a reader filtered to OBSERVED sees all rows. Core stays mypy-green; ratchet green.
- **Falsifier:** any API surface that accepts a provenance value.
- **Invariant(s):** MIRROR_READABLE untouched; import-firewall green (stdlib+sqlite only).
- **Touches stored data?** creates a new store file — no existing data.
- **Parallelizable?** no **Depends on:** none

### Item 4 — reset registration

- **Objective:** the store joins `reset_targets()` (corpus layer, Q4).
- **Files:** `ops/lifecycle/launcher.py` (one list entry + comment), lifecycle test seed
  (extend the sidecar list in the existing reset test — this is the ONE permitted edit
  to an existing test, it is additive).
- **Acceptance test:** `test_reset_wipes_corpus_but_never_the_vault_raft` extended seed
  passes.
- **Falsifier:** reset leaves the store behind (the versions.sqlite defect class).
- **Invariant(s):** `_RESET_GUARD` untouched.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** Item 3, scope
  amendment (§5)

### Item 5 — the projection (φ_code emits)

- **Objective:** `sync()` gains the projection pass: for each newly-ingested commit,
  emit the observation batch (reusing the snapshot walk's shapes + Item 1's docstrings if
  bp-011 landed; else docstring='' and a journal note) through the handoff → collect →
  store; attest `project_observations` per Q5. Idempotent re-runs.
- **Files:** `ops/code_sensor.py`, `core/sensing.py` (sibling seam per Q1), tests (new).
- **Acceptance test:** end-to-end fixture: tmp repo commit → sync → rows in the store ==
  symbol count; second sync → row count UNCHANGED (the falsifier, inverted); attestation
  chain shows ingest_commit → project_observations parentage.
- **Falsifier:** B-b's, verbatim (pinned §6).
- **Invariant(s):** §2.6 firewall set — MirrorView untouched, OBSERVED mirror-opaque
  (assert in test: a MirrorView over a source containing observation rows refuses them).
- **Touches stored data?** yes — writes the new store (dry-run: fixture repo first).
- **Parallelizable?** no **Depends on:** Items 3, 4

## 8. Math carried explicitly

N/A — no mathematical object implemented (an identity-keyed projection; the footprint
math α̂ arrives with consumers, not here).

## 9. Non-goals

Reference EDGES (bp-013); any consumer/detangler (B-d, Track D); backfilling
observations over history (PD-d covers the LEDGER; observation backfill is a one-line
follow-up once idempotency is proven — journal it as available, do not run it against
all 190 commits in-session without measuring one batch first).

## 10. Stop-and-raise conditions

Q1 resolves to "the handoff cannot carry a second payload without touching
`SensedObservation` itself" (park Item 5's seam half, finding — the biometric contract
must not be modified under this plan); the scope amendment (§5) is declined (Item 4
parks); core mypy-green breaks in a way requiring changes outside scope.

## 11. Parked decisions

| Decision                           | Default recorded   | Rejected alternatives (why)                        | Re-entry condition                       |
| ---------------------------------- | ------------------ | -------------------------------------------------- | ---------------------------------------- |
| observation backfill (all history) | available, not run | run in-session (unmeasured cost)                   | one-batch timing journaled; owner nod    |
| a₂ relabel                         | OBSERVED now       | wait for axis (blocks value on an unratified note) | axis ratification (the note's cross-map) |

## 12. Dependency & ordering summary

Item 3 → 4 → 5. Runs after bp-008 merges (tests/\*\* adjacency); independent of bp-011
(docstring column enriches but does not gate — Item 5 degrades gracefully). Gates bp-013
(edges need observation nodes). B-d stays gated on Track D.
