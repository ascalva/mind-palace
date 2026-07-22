---
type: build-plan
id: bp-094
track: code-ingest
status: ready
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - ops/code_sensor.py
  - core/stores/reference_edges.py
  - tests/unit/test_code_sensor*.py
  - tests/unit/test_reference_edges*.py
  - tests/integration/test_reference_edge_isolation.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 350k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0145.md
  - docs/findings/finding-0146.md
  - docs/findings/finding-0147.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# Build Plan — CI-3: the reference layer — shorthand resolvers (L2b) + the code_to_code AST edges

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from ratified `dn-code-ingest-pipeline` §3 CI-3 / §2.4. Proposed →
ready is the owner's hand. Starts only after bp-092's **Item 1 commit** (the import-record
ledger migration it consumes) — full bp-092 seal not required.

## 1. Objective

Fix the resolver blindness (finding-0145/0146): mint `dn-<slug>`/`finding-NNNN`/paired-`§`
shorthand references and statically-resolvable `inherits`/`calls` code_to_code edges — each
pattern gated by a hand-checked precision sample (M-C6), existence-checked against the tree.

## 2. Context manifest

1. `dn-code-ingest-pipeline` §2.4 (L2b rules 1–3 as audited), §2.8 M-C6, F-CI6.
2. `ops/code_sensor.py` — WHOLE (patterns, extract_references, the three edge passes).
3. `core/stores/reference_edges.py` — REF_TYPES/KINDS/DIRECTIONS + the v2 identity.
4. `docs/build-plans/bp-011/` — the V4 precision protocol + probe regexes (the measured bar).
5. bp-092 journal (Item 1) — the import-record schema this consumes.

## 3. Investigation & grounding

- **Q1 — the extractor mints literal note-citations with NO existence check**
  (`extract_references`, `ops/code_sensor.py:243-247`) — the `x.md` false positive's root.
  The audit made the fix an explicit NEW rule: every corpus-target mint gains a tree-
  existence check at that commit (`git ls-tree` walk already in hand, `:414`).
- **Q2 — `code_to_code` is reachable, nothing mints it** (`core/stores/reference_edges.py:
  104-107`); REF_TYPES (`:102`) is the additive vocabulary home for `dn-slug`, `finding-id`,
  `inherits`, `calls`.
- **Q3 — cross-module resolution needs the FULL import records** (audit correction): the
  legacy `imports` table holds roots only (`ops/code_snapshot.py:70-75`, `_module_imports`
  `:140-147`); bp-092 Item 1 lands the full records; v1 mints module-internal + explicit-
  import resolutions ONLY; everything else drops (PD-I).
- **Q4 — paired-`§` rule (audited §2.4-2):** a `§N` binds only to a note already cited in
  the SAME docstring; unpaired drops. 968 tokens are volume for the paired rule, not for
  guessing.
- **Q5 — INTERPRETER_VERSION discipline** (`ops/code_sensor.py:68-86`): new extraction
  patterns change φ_code's output for the same commit ⇒ this IS a version bump (unlike
  bp-026's re-pin — that added a separate lane; this changes code→corpus emissions).
  Bump + `backfill_observations()` posture per the ratchet test
  (`tests/unit/test_interpreter_versions.py`) — the archive-then-replace path exercised.
- **Code does not settle:** whether `inherits`/`calls` targets should carry qualname detail
  on both endpoints at v1 — settled at build by the precision sample (drop detail before
  dropping precision).

**Additional risks:** the reference store is 950k rows accumulated; new patterns add rows
per commit going forward — finding-0145's current-view/prune track (PD-5) is SEPARATE; this
plan must not balloon history (new patterns fire on new projections only; no backfill
without the owner's nod — the standing `backfill_observations` discipline).

## 4. Reconciliation

- `ops/code_sensor.py` header + `VALIDATED_PATTERNS` comment ("only the 100%-precision
  patterns are extracted…") → **[cross-ref: extension]**: the new pattern families join with
  their own measured samples recorded beside bp-011's (the comment block extends; the bar is
  unchanged).
- `core/stores/reference_edges.py:96-102` REF_TYPES comment → **[cross-ref: extension]**:
  the four new types documented with their gating samples.

## 5. Write scope

The sensor, the store's vocabulary, and their tests — nothing else. The isolation test file
is carried because it asserts the store's surface (the retrofit rule). OUT: `core/ingest/**`
(CI-1), `eval/**` (CI-2), the snapshot ledger DDL (bp-092 Item 1 owns it — this plan READS
the new import records, never migrates).

## 6. Interfaces pinned inline

- **New REF_TYPES (additive):** `dn-slug`, `finding-id` (corpus targets, existence-checked),
  `inherits`, `calls` (code_to_code, statically resolvable only).
- **Resolutions (§2.4-1, verbatim):** `dn-<slug>` → `docs/design-notes/<slug>.md`;
  `finding-NNNN` → `docs/findings/finding-NNNN.md`; deterministic, collision-free, against
  the tree at the same commit; unresolved ⇒ dropped, never guessed.
- **The existence-check rule (audit, §2.4-3):** EVERY corpus-target mint — the legacy
  literal `note-citation` included — drops targets absent from the tree at that commit.
- **M-C6 gate (F-CI6):** per (pattern, direction), a stratified hand-checked sample at the
  bp-011 protocol; below-bar ⇒ the pattern ships DISABLED (dropped), not tuned.
- **Store identity:** v2 symmetric endpoints; direction DERIVED; append-only INSERT OR
  IGNORE; balance-math isolation (`reference_edges.py:1-10,50-56`) untouched — the
  isolation test must stay green bit-identically.

## 7. Items

### Item 1 — pattern extraction + existence check (reversible; disabled until sampled)

- **Objective:** the three shorthand resolvers + the tree-existence check on all corpus
  mints + the `inherits`/`calls` static resolver (module-internal + full-import-record
  resolution); all NEW patterns behind a mint-gate flag until Item 2's samples pass.
- **Files:** `ops/code_sensor.py`, `core/stores/reference_edges.py`, unit tests.
- **Acceptance test:** fixture docstrings resolve/drop exactly per §6; the `x.md` class
  provably dropped; INTERPRETER_VERSION bumped with the ratchet test updated (the pin
  re-set at the new version per its own protocol).
- **Falsifier:** any unresolved token minted (guessing), or a legacy edge's identity
  changing (append-only violated) ⇒ halt.
- **Invariant(s):** isolation test bit-identical; no model anywhere in the path.
- **Touches stored data?** no (patterns gated off). **Parallelizable?** no.
  **Depends on:** bp-092 Item 1 committed.

### Item 2 — M-C6 precision samples + enable (irreversible mint begins)

- **Objective:** per-pattern stratified samples over the real corpus at HEAD; record per
  the V4 protocol; enable each pattern that clears the bar; run one projection pass and
  count minted edges per type.
- **Files:** journal (samples + verdicts), the flag flips in `ops/code_sensor.py`.
- **Acceptance test:** every ENABLED pattern's sample at/above bar, recorded; below-bar
  patterns listed as dropped with their misses.
- **Falsifier:** **F-CI6** — a below-bar pattern enabled anyway ⇒ the discipline failed;
  revert the flag, finding.
- **Invariant(s):** precision-first; Lane-1 wrong-edge > missing-edge asymmetry.
- **Touches stored data?** yes — `data/reference_edges.sqlite` (new edges, forward-only;
  no backfill without owner nod). **Parallelizable?** no. **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — no mathematical object; deterministic pattern extraction under a measured-precision
protocol.

## 9. Non-goals

No current-view projection or history prune (finding-0145/PD-5's own track). No dynamic
dispatch/attribute-chain call graph (PD-I). No unpaired-`§` resolution (PD-F). No backfill.
No S-fiber work (CI-4). No snapshot-ledger migrations (bp-092's).

## 10. Stop-and-raise conditions

bp-092 Item 1 not yet committed (the import records don't exist). A sample forcing a
protocol judgment call the V4 shape doesn't cover (park the pattern). Any history-balloon
surprise (>2× expected per-commit edge volume). The INTERPRETER_VERSION ratchet firing red
in an unexpected direction.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| PD-F unpaired `§N` | dropped | nearest-cited-note guess (ambiguity, precision-first) | a measured recall case + a clearing sample |
| PD-I fuller call graph | static-only | dynamic resolution now (below bar by construction) | a consumer needs reach AND a method clears the bar |
| qualname detail on code_to_code endpoints | decided at build by sample | pinning now (evidence-free) | Item 2's sample |

## 12. Dependency & ordering summary

Items 1→2. Gated on bp-092 Item 1 (the ledger migration); otherwise independent of CI-1's
lane and CI-2 entirely. Not concurrent with any plan (write-scope discipline). Feeds bp-095
(CI-4 needs the resolved F-edges for the S↔F pairing).
