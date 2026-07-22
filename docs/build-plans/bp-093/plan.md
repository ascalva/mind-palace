---
type: build-plan
id: bp-093
track: code-ingest
status: complete
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - eval/harness/**
  - eval/code_probes.py
  - tests/unit/test_code_retrieval*.py
  - tests/integration/test_code_mirror*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on:
  - bp-092
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0147.md
  - docs/findings/finding-0151.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# Build Plan — CI-2: the isolation + retrieval proof (M-C3 / M-C4 / M-C5)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from ratified `dn-code-ingest-pipeline` §3 CI-2. **Scope reduction
(owner ruling 2026-07-21, warrant finding-0151):** the PD-J `code_origin` node-keyed
authorship reader — originally CI-2's optional rider — is **PULLED**. At the current C-edge
population (78 commit-anchored of 4,160; the rest are `pair_cut_sha=''` working-tree writes)
it resolves almost nothing; the owner ruled the code→dialogue authorship channel must be
delivered *properly* via a dedicated integrator design pass (finding-0151, a Fable pass
scheduled AFTER the build tracks) and completed WITH the code-ingest program, not shipped
thin here. This is a reduction of an already-blessed plan (never a widening) and needs no
re-bless. CI-2 keeps only its retrieval/geometry/scale proof.

## 1. Objective

Prove the code lane earns its keep — retrieval beats the docstring-only baseline (M-C3), the
cross-space geometry is informative (M-C4), readers scale at ~7k rows (M-C5).

## 2. Context manifest

1. `dn-code-ingest-pipeline` §2.1b (PD-C re-entry), §2.8 (M-C3/M-C4/M-C5).
2. bp-092's journal — seed results, chunk census, store scale.
3. `eval/harness/` — the readings' home conventions.
4. `core/ingest/index.py:115-138` — `semantic_search` / grouped search (the read surface probed).

## 3. Investigation & grounding

- **Q1 — the golden probe set does not exist;** built here: ~15 "find the code that does X"
  queries with known-answer paths, fixture-pinned (never in `eval/golden/**` — the frozen
  owner set, denylist).
- **Q2 — baseline = docstring-only retrieval:** semantic_search over the L1/codedoc layer
  alone, same k, same embedder — the honest comparator the note names.
- **Code does not settle:** the working σ for the M-C4 cross-space read — chosen from the
  measured distribution, recorded (CN-1 index discipline).

**Additional risks:** M-C4's verdict gates CI-4 (bp-095) AND PD-C; a degenerate geometry is
a FINDING with a re-entry (embedder bump path), never a silent tune.

## 4. Reconciliation

N/A — read-only against sealed surfaces; nothing corrected or extended (the one core reader
this plan used to carry is pulled — §0).

## 5. Write scope

Eval-side readings + plan-specific test files. OUT: everything CI-1 touched (bp-092 sealed
first), `ops/**`, `core/**` entirely (the PD-J reader is pulled, so no `core/origin_view.py`),
the mirror, golden. The F-CI5 isolation ratchet lives in bp-092; this plan only CONSUMES its
green.

## 6. Interfaces pinned inline

- **M-C3 protocol:** per-query rank of the known-answer path, code-lane vs docstring-only; the
  lane must beat the baseline on the majority with no catastrophic regressions (F-CI3's bar;
  ties journal-argued).
- **M-C4 protocol:** cross-class (code↔note) cosine distribution vs within-class; verdict
  "informative" iff cross-class mass is non-degenerate (not bimodally separated) — gates CI-4
  and PD-C.
- **M-C5:** `all_rows`/search latency at the seeded scale; the Python-side-filter posture
  (`core/stores/vectorstore.py:128-140`) re-checked.

## 7. Items

### Item 1 — the golden probes + M-C3/M-C4/M-C5 readings (read-only)

- **Objective:** build the probe fixture; run the three measurements; record verdicts.
- **Files:** `eval/code_probes.py`, `eval/harness/**` additions, journal.
- **Acceptance test:** readings reproducible (fixed seed/cut, CN-1-style index recorded);
  M-C3 table complete per probe; M-C4 verdict (informative | degenerate) stated for CI-4/PD-C.
- **Falsifier:** **F-CI3** — the lane fails to beat the baseline ⇒ record no-signal, open
  PD-D (grain) re-entry, and CI-4/PD-C dispositions per §6; the plan still seals (a null is a
  result). **F-CI4** — M-C4 degenerate ⇒ CI-4 (bp-095) supersedes on that finding; PD-C
  re-enters.
- **Invariant(s):** read-only; no store writes; mirror reached only via explicit CODE-inclusive
  provenance sets, never MIRROR_READABLE.
- **Touches stored data?** no. **Parallelizable?** n/a (single item). **Depends on:** bp-092
  sealed.

## 8. Math carried explicitly

- **M-C4 cross-space geometry** — *measures:* separation vs mixing of code/note cosine
  neighborhoods in one embedding space. *valid when:* single embedder version across both
  populations (A7 cut). *fails its keep if:* it cannot discriminate "informative" from
  "degenerate" on the real corpus (then PD-C's gate needs a sharper statistic — finding).

## 9. Non-goals

No embedder swap (PD-C re-enters only on this plan's evidence, lands elsewhere). No S↔F lens
(CI-4). No resolver work (CI-3). No authorship reader (PULLED — finding-0151's integrator
track owns it). No new stores.

## 10. Stop-and-raise conditions

bp-092 not sealed. Golden-set questions needing owner taste (park that probe, continue). Any
temptation to tune retrieval params to pass F-CI3 — the bar is the design's, not the builder's;
a miss is a finding.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| PD-C code-tuned embedder | qwen3-embedding:4b, one space | dual-space + alignment (no geometry across; machinery-ahead-of-need) | F-CI4 fires or M-C3/M-C4 show material deficit vs an offline baseline |
| PD-D sub-symbol grain | symbol partition | statement/block chunks now (no evidence) | F-CI3 fires AND error analysis blames oversized atoms |
| PD-J code→dialogue authorship reader | **MOVED OUT** to the integrator track (finding-0151) | shipping it thin here (useless at 78/4,160 C-coverage) | the integrator densification design pass ratifies + graduates |

## 12. Dependency & ordering summary

Hard after bp-092 (needs the seeded store). Single item now (the parallel PD-J item is pulled).
Feeds bp-095 (CI-4): its M-C4-signal gate reads THIS plan's journal verdict.
