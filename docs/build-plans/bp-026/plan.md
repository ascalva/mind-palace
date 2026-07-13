---
type: build-plan
id: bp-026
status: ready
design_ref:
  - docs/design-notes/core-query-protocol.md # §3.1 licenses this (draft; independently warranted by findings below)
contract: builder
write_scope:
  - "core/stores/reference_edges.py"      # the schema generalization + dataclass/mint/migration
  - "ops/code_sensor.py"                   # migrate the code↔corpus mint calls; add the corpus→corpus pass
  - "tests/unit/test_reference_edges.py"   # new/updated unit tests for the symmetric schema
  - "tests/integration/test_reference_edge_isolation.py" # keep green — update fixtures to the new mint API ONLY
  - "docs/build-plans/bp-026/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 180k } # schema migration + writer migration + new extractor + verified dry-run
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/findings/finding-0059.md # doc→doc blindness — the primary warrant
  - docs/findings/finding-0061.md # the stale-baseline class this makes measurable
  - docs/findings/finding-0062.md # the direction finding; the reference-graph gap
  - docs/brainstorms/core-query-protocol.md # the algebra whose empirical test this unblocks
re_entry: null
supersedes: null
superseded_by: null
warrant: finding-0059
---

# Build Plan — generalize the reference-edge schema to symmetric endpoints + the doc→doc extractor

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Findings-warranted codebase improvement (findings 0059/0061/0062), minted `proposed` directly
(the third-triage precedent: bp-023/024/025 were minted from findings, not from a ratified
note). `dn-core-query-protocol` (draft) names this as its first licensed consequence (§3.1)
but does NOT gate it — the doc→doc gap stands on the findings alone. The owner chose the
**clean long-term schema** over a minimal reinterpret-the-`code_path`-field bandaid, and to do
the migration now while the store is small-ish (~61k rows) rather than later. `proposed →
ready` is the owner's hand edit.

## 1. Objective

`reference_edges` becomes a **symmetric** `(source_kind, source_ref, …) → (target_kind,
target_ref, …)` edge store — admitting `corpus_to_corpus` (doc→doc) edges as a first-class
direction — and a deterministic `corpus→corpus` extractor projects the authored corpus's own
citation graph (front-matter `design_ref`/`links`/`depends_on`/`warrant`/`supersedes`, inline
note-citations, `[[wikilinks]]`) into it, all while the balance-isolation invariant stays
bit-identically intact.

## 2. Context manifest

1. `core/stores/reference_edges.py` — the current code↔corpus-shaped schema (`_DDL`, the
   `ReferenceEdge` dataclass, `mint()`/`_edge_id`/`_row`, `DIRECTIONS`/`CORPUS_KINDS`/
   `REF_TYPES`, `add_batch`/`all`/`for_commit`). The whole object being generalized.
2. `ops/code_sensor.py:80-109,239-290` — `VALIDATED_PATTERNS`, `extract_references`,
   `_mint_reference_edges`, `_corpus_reference_edges` (the md-side scan the new pass extends);
   `:155-189` `sync()`/`_project()` — the projection pass the new edges mint within.
3. `tests/integration/test_reference_edge_isolation.py` — the B-c falsifier: `build_complex`
   signature is exactly `{view, edges, derived, sim_floor}` (line 122) and no instrument moves
   when reference edges are added. This MUST stay green; the migration only updates its mint
   fixtures to the new API, never relaxes the assertions.
4. `ops/lifecycle/launcher.py:524` — the store registered for `reset_targets()` (corpus-class
   wipe; the migration's sanctioned mechanism).
5. `docs/build-plans/bp-020/plan.md` §6(c)/§11 — the dry-run-then-orchestrator-live backfill
   pattern this plan reuses for the re-projection (builders never touch the live `data/`).

## 3. Investigation & grounding

- **Q1 — who reads the store's fields today?** NOBODY. At-HEAD grep: the only writer is
  `code_sensor.py`; the only other toucher is `launcher.py:524` (reset registration); no
  instrument reads `.code_path`/`.corpus_ref`/`.direction` (the docstring's named consumers —
  detangling instruments, Item-10 s(C,D) — are unbuilt, finding-0020 class). **So the schema
  change has near-zero reader blast radius** — the migration touches the store + its sole
  writer + the isolation test's fixtures, nothing else.
- **Q2 — is the data precious?** NO. The store is corpus-class (`reset_targets()`,
  `launcher.py:524`) — a **deterministic projection of git history**, regenerable by wipe +
  re-project. So the migration strategy is wipe+reproject under the new schema, NOT fragile
  in-place row surgery (Q1 makes this safe; Q2 makes it correct-by-construction).
- **Q3 — what preserves the isolation invariant?** The migration adds NO handle to
  `build_complex` and touches nothing under `core/complex/**` (grep-verified: reference_edges
  is imported only by `code_sensor`, the launcher, and the isolation test). The B-c falsifier
  (`test_reference_edge_isolation.py`) therefore stays green by construction; the plan asserts
  it explicitly (§7 Item acceptance).
- **Q4 — doc→doc precision.** Front-matter refs (`design_ref`, `links`, `depends_on`,
  `warrant`, `supersedes`, `superseded_by`) are **structured YAML → ~100% precision** (parse,
  don't regex). Inline note-citations reuse `code_sensor`'s `_RE_NOTE_CITATION`
  (`docs/(design-notes|findings|brainstorms)/…\.md`); `[[wikilinks]]` are explicit. Unlike the
  code sensor's fuzzy docstring prose, the corpus→corpus surface is high-precision — and the
  grep-oracle (Thread-C loop) is the crisp acceptance checker.

**Additional risks surfaced during reading:** the `edge_id` content-identity (`_edge_id`) is
computed from the endpoint tuple; generalizing the tuple changes the formula → existing
edge_ids would differ. Because the migration is **wipe+reproject** (not in-place), this is a
non-issue: every edge is re-minted under the new formula from scratch, idempotence preserved
(re-running the projection is still a no-op). The plan must NOT attempt to preserve old
edge_ids across the schema change.

## 4. Reconciliation

- `core/stores/reference_edges.py` — the code↔corpus schema is **generalized, not replaced
  silently**: the module docstring and `_DDL` gain a **[banner: schema v2]** note recording
  the old shape, why it generalized (doc→doc, findings 0059/0062), and that v1 rows are
  regenerated by re-projection (no lossy in-place migration). The append-only, isolation, and
  reset semantics are preserved verbatim in prose.
- `ops/code_sensor.py` — `_mint_reference_edges`/`_corpus_reference_edges` **[cross-ref:
  extension]**: the same md scan now also emits `corpus_to_corpus`; the code↔corpus mint calls
  are migrated to the symmetric `mint()` signature. No behavior removed.

## 5. Write scope

In: the store (schema + dataclass + mint + migration note), `code_sensor` (writer migration +
the corpus→corpus pass), the store's unit tests, the isolation test's **fixtures only**, own
plan dir, findings. Out, deliberately: `core/complex/**` (the isolation invariant — the store
must never gain a handle there); `build_complex`'s signature (pinned by the isolation test);
the live `data/reference_edges.sqlite` (the wipe+reproject is orchestrator-run at seal from the
main checkout — builders never touch live `data/`, finding-0031); design notes; the foundation
denylist.

## 6. Interfaces pinned inline

**(a) Current schema (v1, being generalized — `reference_edges.py:83-99`):**

```
reference_edges(edge_id, direction {code_to_corpus|corpus_to_code}, ref_type, commit_sha,
                code_path, qualname, corpus_ref, corpus_kind {path|digest}, source_line, created_at)
```

**(b) Target schema (v2 — symmetric endpoints):**

```sql
CREATE TABLE reference_edges (
    edge_id      TEXT PRIMARY KEY,   -- content-id over (source endpoint, target endpoint, ref_type, line)
    commit_sha   TEXT NOT NULL,      -- time coordinate: the commit the reading landed at (unchanged)
    ref_type     TEXT NOT NULL,      -- REF_TYPES (unchanged vocabulary)
    source_kind  TEXT NOT NULL,      -- 'code' | 'corpus'
    source_ref   TEXT NOT NULL,      -- code: file path ; corpus: repo-relative doc path (or digest)
    source_detail TEXT NOT NULL DEFAULT '',  -- code: qualname ('' = module grain) ; corpus: '' | 'digest'
    target_kind  TEXT NOT NULL,      -- 'code' | 'corpus'
    target_ref   TEXT NOT NULL,      -- symmetric to source_ref
    target_detail TEXT NOT NULL DEFAULT '',  -- symmetric to source_detail
    source_line  INTEGER NOT NULL,   -- line in the SOURCE artifact (unchanged)
    created_at   TEXT NOT NULL
);
-- indices on commit_sha, source_ref, target_ref (the retrieval-by-either-endpoint queries).
```

- `KINDS = ("code", "corpus")`. `direction` becomes a **derived** read-only convenience:
  `f"{source_kind}_to_{target_kind}"` (a property/helper, NOT a stored column) so
  `DIRECTIONS` extends to `code_to_corpus | corpus_to_code | corpus_to_corpus` (and
  `code_to_code` is reachable but unused — do not mint it here).
- `mint()` keeps closed-vocabulary validation (`source_kind`/`target_kind` ∈ `KINDS`, `ref_type`
  ∈ `REF_TYPES`, `source_line ≥ 1`) and recomputes `_edge_id` over the symmetric tuple.
- `all()`/`for_commit()` unchanged in spirit; add `all(source_ref=…)` / `all(target_ref=…)`
  filters (the "references TO doc X" query — the whole point).

**(c) The corpus→corpus extractor (new pass in `code_sensor`, or a `_corpus_to_corpus_edges`
method it calls in the md scan):** for each `docs/**/*.md` at the projected sha —
- parse front-matter; for each of `design_ref, links, depends_on, warrant, supersedes,
  superseded_by` whose value is a `docs/….md` path → a `corpus_to_corpus` edge
  (ref_type `design-ref` for `design_ref`, else `note-citation`), `source_line` = the
  front-matter key's line;
- inline `_RE_NOTE_CITATION` matches in the body → `note-citation` edges;
- `[[name]]` wikilinks resolving to a known doc → `note-citation`.
Define a `CORPUS_TO_CORPUS_VALIDATED` pattern set analogous to `VALIDATED_PATTERNS`; front-matter
patterns are high-precision (structured). Self-loops (a doc citing itself) are dropped.

**(d) The migration (Item 21, orchestrator-executed at seal, main checkout):** wipe +
re-project — `reset_targets()` the store, then re-run the projection/backfill over full main
history so v1 code↔corpus edges regenerate under v2 AND the new corpus→corpus edges land. Same
dry-run-first, orchestrator-at-seal discipline as bp-020 §6(c)/§11 (builders never touch live
`data/`). Verify: total count ≥ prior 61,380 (v1 rows regenerated) + the new corpus→corpus rows;
a grep-oracle recall check on a sample of docs; determinism (second run adds 0);
`test_reference_edge_isolation.py` green.

## 7. Items

_(family numbering continues the global sequence from bp-025's Item 17)_

### Item 18 — the symmetric schema (store, dataclass, mint, migration note)

- **Objective:** `reference_edges.py` implements §6(b): symmetric endpoints, `KINDS`, derived
  `direction`, generalized `mint()`/`_edge_id`/`_row`/`add_batch`/`all`, the v2 banner note.
- **Files:** `core/stores/reference_edges.py`, `tests/unit/test_reference_edges.py`
- **Acceptance test:** `uv run pytest -q tests/unit/test_reference_edges.py` green: a round-trip
  of a `corpus_to_corpus` edge and a `code_to_corpus` edge (mint → add_batch → all → equal);
  `direction` derives correctly for all three; `all(target_ref=…)` returns the citing sources;
  closed-vocabulary validation still raises on a bad `kind`.
- **Falsifier:** the schema keeps a `code_path`/`corpus_ref` field (asymmetric residue), or
  `direction` is stored rather than derived, or a `corpus_to_corpus` edge cannot be minted.
- **Invariant(s):** append-only INSERT-OR-IGNORE on `edge_id`; no import of `core/complex/**`;
  no handle exposed to `build_complex`.
- **Touches stored data?** no (schema/code only; the live store is migrated in Item 21)
- **Parallelizable?** no **Depends on:** none

### Item 19 — migrate the code sensor's writer to v2 (code↔corpus unchanged in meaning)

- **Objective:** `_mint_reference_edges`/`_corpus_reference_edges` mint under §6(b) — the same
  code↔corpus edges, now as `(source_kind, target_kind)` pairs; no code↔corpus behavior change.
- **Files:** `ops/code_sensor.py`, `tests/integration/test_reference_edge_isolation.py` (mint
  fixtures → new API only; assertions untouched)
- **Acceptance test:** `uv run pytest -q tests/integration/test_reference_edge_isolation.py`
  green (the B-c falsifier: no instrument moves; `build_complex` params still exactly
  `{view, edges, derived, sim_floor}`); a code_sensor unit/integration test shows a
  code↔corpus edge now lands with `source_kind='code'`, `target_kind='corpus'`.
- **Falsifier:** the isolation test reddens (a handle leaked to the complex), or a code↔corpus
  edge changes its endpoints' meaning, or `build_complex`'s signature changed.
- **Invariant(s):** the balance-isolation bright line (B-c) holds bit-identically.
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** Item 18

### Item 20 — the corpus→corpus extractor (φ_doc pass)

- **Objective:** §6(c) — the doc→doc citation edges from front-matter + inline note-citations +
  wikilinks, high-precision, minted within the projection pass.
- **Files:** `ops/code_sensor.py` (the `_corpus_to_corpus_edges` pass + `CORPUS_TO_CORPUS_VALIDATED`),
  `tests/unit/test_reference_edges.py` or a sensor test
- **Acceptance test:** over a fixture repo, the pass emits the exact expected `corpus_to_corpus`
  edges (a plan's `design_ref` → the note; a finding's `links` → its targets; a `[[wikilink]]`);
  a **grep-oracle** check — the extracted edge set for a doc equals an independent grep of that
  doc's references (precision AND recall), the Thread-C self-grading loop in miniature; zero
  self-loops; determinism (re-extract → identical).
- **Falsifier:** the grep oracle finds a front-matter `design_ref`/`links` the extractor missed
  (recall gap) or the extractor emits a reference grep cannot confirm (precision gap); either
  fires the finding (the extractor regressed or a doc drifted) — file it, do not fudge.
- **Invariant(s):** structured front-matter parsed (not regex-approximated); still no complex
  handle; append-only.
- **Touches stored data?** no (fixture repos only)
- **Parallelizable?** no **Depends on:** Item 18 (the schema it mints into)

### Item 21 — the live migration (wipe + re-project; orchestrator-executed at seal)

- **Objective:** §6(d) — re-project the live store under v2 so v1 code↔corpus regenerates AND
  corpus→corpus lands; the builder delivers the verified DRY-RUN + the exact command, the
  orchestrator runs the live wipe+reproject at seal from the main checkout.
- **Files:** `docs/build-plans/bp-026/journal.md` (the dry-run inventory + the live counts)
- **Acceptance test:** dry-run (tmp store, real repo) reports: v1-equivalent code↔corpus count
  regenerated (≈ prior 61,380 at the same HEAD) + a non-zero corpus→corpus count; zero
  warnings; determinism (two runs identical). Live (orchestrator): counts equal the dry-run at
  the same HEAD; `test_reference_edge_isolation.py` green post-migration; a second re-project
  adds 0 (idempotence). A `references_to(<a well-cited design note>)` query now returns the
  citing plans/findings (the finding-0059 capability, live).
- **Falsifier:** live counts diverge from the dry-run at identical HEAD; or the isolation test
  reddens post-migration; or the doc→doc recall on a sampled doc misses a known citation.
- **Invariant(s):** builders never touch the main checkout's live `data/` (the run is the
  orchestrator's at seal); corpus-class reset semantics unchanged.
- **Touches stored data?** YES — the plan's only such item; the Item 21 dry-run is the mandated
  verification pass, and the store is corpus-class (a wrong write is recoverable by wipe +
  re-projection).
- **Parallelizable?** no **Depends on:** Items 18, 19, 20

## 8. Math carried explicitly

N/A — a schema generalization + a deterministic extractor; no mathematical object implemented.
(The edges this lands are the *prerequisite substrate* for the dn-core-query-protocol algebra's
empirical test, but this plan builds none of that math.)

## 9. Non-goals

Any consumer of the doc→doc edges (a `references_to` query surface, the reference agent, the
alignment instrument — all later, dn-core-query-protocol); assembling these edges into a
citation complex for the bicomplex math (a separate, deliberate construction — the note's §1.3
item 7); the `code_to_code` direction (reachable in the schema, not minted here); any change to
the balance/complex math; symbol-mention/design-ref precision expansion on the code side (v1's
validated patterns are inherited unchanged).

## 10. Stop-and-raise conditions

If the grep oracle shows the extractor systematically missing a front-matter key class, STOP
and widen the parse (front-matter must be parsed, never regex-approximated) — but if it misses
an *inline prose* reference grep finds, that is a precision/recall trade to record as a finding,
not silently chase. If migrating the writer reddens the isolation test, STOP — a handle leaked
to the complex; the fix is at the store boundary, never by relaxing the test (§3 Q3). If the
live re-project diverges from the dry-run, STOP, wipe per corpus-class semantics, re-investigate.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| schema shape | symmetric `(source_*, target_*)` v2, direction derived | reinterpret `code_path` as the source-doc path under a new `corpus_to_corpus` direction (the bandaid — asymmetric residue, field names that lie; the owner rejected it) | never — the owner chose the clean schema |
| migration strategy | wipe + re-project (corpus-class reset semantics; Q1/Q2 make it safe+correct) | in-place row transform recomputing edge_ids (fragile identity surgery for zero benefit — the store is a deterministic projection) | a future non-regenerable stratum lands in this store |
| φ_doc home | extend `code_sensor`'s md scan (least wiring, same projection pass, same store) | a separate `ops/doc_sensor.py` interpreter module (cleaner separation, but duplicates the sync/projection wiring for no current benefit) | φ_doc grows patterns/precision logic heavy enough to warrant its own interpreter versioning |
| `code_to_code` direction | reachable in the schema, NOT minted | mint code→code call edges now (out of scope; no warrant) | a call-graph reference need appears |

## 12. Dependency & ordering summary

Item 18 → 19 → 20 → 21; strictly serial, blast-radius ascending (schema → writer migration →
new extractor → the single live re-projection). No cross-plan dependency (disjoint from every
other plan; the store is imported only by `code_sensor` + the launcher + the isolation test).
After Item 21 the doc→doc citation graph is live — findings 0059/0061 flip on seal, the "who
cites this" query works, and the dn-core-query-protocol algebra's empirical test (the §2.5
flatness measurement) has its prerequisite substrate.
