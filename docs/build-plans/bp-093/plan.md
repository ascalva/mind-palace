---
type: build-plan
id: bp-093
status: proposed
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - eval/harness/**
  - eval/code_probes.py
  - core/origin_view.py
  - tests/unit/test_code_retrieval*.py
  - tests/unit/test_origin*.py
  - tests/integration/test_code_mirror*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on:
  - bp-092
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0147.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# Build Plan — CI-2: the isolation + retrieval proof (M-C3/M-C4/M-C5) + the PD-J node-keyed C reader

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from ratified `dn-code-ingest-pipeline` §3 CI-2 (split kept — CI-1 is
already the largest plan; "may merge" declined at graduation). Proposed → ready is the
owner's hand.

## 1. Objective

Prove the code lane earns its keep — retrieval beats the docstring-only baseline (M-C3),
the cross-space geometry is informative (M-C4), readers scale (M-C5) — and land the PD-J
node-keyed authorship reader (code chunk → producing dialogue).

## 2. Context manifest

1. `dn-code-ingest-pipeline` §2.1b (PD-C re-entry), §2.3-1 (authorship via origin), §2.5b
   (the C∘commit-keying sibling join — the audit-corrected grounding), §2.8 (M-C3/4/5).
2. `core/origin_view.py` — WHOLE (the edge-scoped view the PD-J reader sits beside).
3. `core/stores/causal_edges.py` — the C-edge row shape (`pair_cut_sha`, witnesses).
4. bp-092's journal — seed results, chunk census, store scale.
5. `eval/harness/` — the readings' home conventions.

## 3. Investigation & grounding

- **Q1 — origin(e) is edge-scoped;** a code-chunk join is NEW (audit-confirmed):
  `core/origin_view.py:34-39,81-88` — reference-edge ids only. The PD-J reader is hop 2
  alone: the C-edge whose `pair_cut_sha` equals the chunk's snapshot commit — a free
  function beside `origin`, same read-only/no-store discipline (F-AL7 kin).
- **Q2 — code chunks carry `(digest=blob_sha)` but the COMMIT key needs the ledger join:**
  blob→commit(s) via `files` (`ops/code_snapshot.py:49-59`); a blob can appear at many
  commits — the reader returns the earliest-witnessed producing edge, deterministic
  (`min (event_order, edge_id)`, the `origin` tie-break reused, `origin_view.py:103-110`).
- **Q3 — the golden probe set does not exist;** built here: ~15 "find the code that does X"
  queries with known-answer paths, fixture-pinned (never in `eval/golden/**` — that is the
  frozen owner set, denylist).
- **Q4 — baseline = docstring-only retrieval:** semantic_search over a docstring-corpus
  projection (the L1/codedoc layer alone), same k, same embedder — the honest comparator
  the note names.

**Additional risks:** M-C4 verdict gates CI-4 AND PD-C; a degenerate geometry here is a
FINDING with re-entry (embedder bump path, `vectorstore.reset`), never a silent tune.

## 4. Reconciliation

- `core/origin_view.py` module docstring ("scoped to the durable-edge kind…") →
  **[cross-ref: extension]**: the new reader's docstring names itself the PD-J sibling
  (node-grain, ledger-joined), cites §2.5b, and states it does NOT widen `origin(e)`.

## 5. Write scope

Eval-side readings + the one core reader + plan-specific test files. OUT: everything CI-1
touched (bp-092 sealed first), `ops/**`, `core/stores/**`, the mirror, golden. The F-CI5
ratchet lives in bp-092; this plan only CONSUMES its green.

## 6. Interfaces pinned inline

- **PD-J reader signature (pinned):**
  `def code_origin(blob_sha: str, *, snapshots: sqlite3.Connection, causal_edges: CausalEdgeStore) -> CausalEdge | None`
  — read-only, mints nothing, returns the earliest witnessed C-edge whose `pair_cut_sha`
  is a commit carrying that blob; `None` = owner hand edit / pre-agent history (a
  legitimate answer, not a failure).
- **M-C3 protocol:** per-query rank of the known-answer path, code-lane vs docstring-only;
  the lane must beat the baseline on the majority with no catastrophic regressions
  (F-CI3's bar; ties journal-argued).
- **M-C4 protocol:** cross-class (code↔note) cosine distribution vs within-class; verdict
  "informative" iff cross-class mass is non-degenerate (not bimodally separated) — gates
  CI-4 and PD-C.
- **M-C5:** `all_rows`/search latency at the seeded scale; the Python-side-filter posture
  re-checked.

## 7. Items

### Item 1 — the golden probes + M-C3/M-C4/M-C5 readings (read-only)

- **Objective:** build the probe fixture; run the three measurements; record verdicts.
- **Files:** `eval/code_probes.py`, `eval/harness/**` additions, journal.
- **Acceptance test:** readings reproducible (fixed seed/cut, CN-1-style index recorded);
  M-C3 table complete per probe.
- **Falsifier:** **F-CI3** — the lane fails to beat the baseline ⇒ record no-signal, open
  PD-D (grain) re-entry, and CI-4/PD-C dispositions per §6; the plan still seals (a null is
  a result).
- **Invariant(s):** read-only; no store writes. **Touches stored data?** no.
- **Parallelizable?** with Item 2. **Depends on:** bp-092 sealed.

### Item 2 — the PD-J node-keyed reader (reversible)

- **Objective:** `code_origin` per §6 + tests (fixture ledger + causal edges; the F-AL7
  discipline: result re-derivable from witnesses + commit keys alone; nothing minted).
- **Files:** `core/origin_view.py`, tests.
- **Acceptance test:** fixture round-trip (agent-produced blob → its dialogue edge;
  owner-edit blob → None); no new store handles; read-only asserted.
- **Falsifier:** a result requiring facts no row carries ⇒ the composition claim fails —
  reopen §2.5b by finding, do not patch with a store.
- **Invariant(s):** E_disp discipline (never enters A_geom); `origin(e)` untouched.
- **Touches stored data?** no. **Parallelizable?** with Item 1. **Depends on:** bp-092.

## 8. Math carried explicitly

- **M-C4 cross-space geometry** — *measures:* separation vs mixing of code/note cosine
  neighborhoods in one embedding space. *valid when:* single embedder version across both
  populations (A7 cut). *fails its keep if:* it cannot discriminate "informative" from
  "degenerate" on the real corpus (then PD-C's gate needs a sharper statistic — finding).

## 9. Non-goals

No embedder swap (PD-C re-enters only on this plan's evidence, lands elsewhere). No S↔F
lens (CI-4). No resolver work (CI-3). No origin(e) widening. No new stores.

## 10. Stop-and-raise conditions

bp-092 not sealed. Golden-set questions needing owner taste (park that probe, continue).
Any temptation to tune retrieval params to pass F-CI3 — the bar is the design's, not the
builder's; a miss is a finding.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| PD-C code-tuned embedder | qwen3-embedding:4b, one space | dual-space + alignment (no geometry across; machinery-ahead-of-need) | F-CI4 fires or M-C3/M-C4 show material deficit vs an offline baseline |
| PD-D sub-symbol grain | symbol partition | statement/block chunks now (no evidence) | F-CI3 fires AND error analysis blames oversized atoms |

## 12. Dependency & ordering summary

Hard after bp-092 (needs the seeded store). Items 1‖2 parallel (disjoint files). Feeds
bp-095 (CI-4): its M-C4-signal gate reads THIS plan's journal verdict.
