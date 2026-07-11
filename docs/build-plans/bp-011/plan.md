---
type: build-plan
id: bp-011
status: in-progress
design_ref:
  - docs/design-notes/code-observation-projection.md
contract: builder
write_scope:
  - "ops/code_snapshot.py"
  - "ops/code_sensor.py"
  - "tests/**"
  - "docs/findings/**"
  - "docs/build-plans/bp-011/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 350k }   # grind + read-only inventory; bp-007-calibrated
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/brainstorms/doc-code-entanglement.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Rosetta groundwork: the ledger docstring column + the V4 reference inventory

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from the ratified `code-observation-projection.md` (owner blessing 2026-07-11).
This is the note's **B-a + V4**: the cheap precursor (docstrings into the snapshot ledger)
and the read-only feasibility probe (the reference-edge inventory) whose validated
patterns seed bp-013. Readiness blessing is the owner's hand.

## 1. Objective

Every code snapshot carries its docstrings (queryable, with a per-commit coverage metric),
and the cross-reference inventory over docstrings + design notes is measured, precision-
sampled, and journaled — V4's falsifier decided with data.

## 2. Context manifest

1. `docs/design-notes/code-observation-projection.md` — §2.3 (docstring = Rosetta payload,
   references_out types), §3.2 V3/V4, §2.7 razor.
2. `ops/code_snapshot.py` — the AST walk (`parse_source`, `_walk_defs`) and the additive-
   migration pattern (`open_snapshot_db` header columns).
3. `ops/code_sensor.py` — `sync()` (where coverage lands in the report, if anywhere).
4. `docs/brainstorms/doc-code-entanglement.md` — the reference patterns to inventory
   (`design-notes/*.md` citations, `[[note]]` links, backticked `path`/`symbol` mentions).

## 3. Investigation & grounding

- **Q1 — where do docstrings surface in the existing walk?** `_walk_defs` visits every
  def/class node but discards `ast.get_docstring`; `parse_source` builds `FileShape`
  without docstrings. The addition is a per-symbol field + a module-level docstring on the
  FileShape — same walk, no second parse.
- **Q2 — migration pattern?** `open_snapshot_db` already does PRAGMA-checked `ALTER TABLE`
  (the ctype/scope/subject precedent) — the docstring column follows it; `annotate_headers`
  shows the self-healing backfill shape if historical backfill is chosen (PD-d default: yes).
- **Q3 — inventory sources?** Two directions: (a) code → corpus: docstrings mentioning
  `docs/design-notes/*.md`, `[[...]]`, backticked repo paths; (b) corpus → code: design
  notes/findings citing `path.py`, `path.py:line`, backticked dotted symbols. Both greppable
  deterministically; the probe counts, samples ~30 for hand-checked precision, and reports
  per-pattern quality.
- **Q4 — does the probe write anything?** Journal tables + a machine-readable inventory
  file under `docs/build-plans/bp-011/` only. No store, no corpus writes — V4 is read-only.

**Additional risks or questions surfaced during reading:** none — both halves ride
existing, tested machinery.

## 4. Reconciliation

- `ops/code_snapshot.py` module docstring ("records the skeleton — symbols ... imports,
  LOC") → **cross-ref: extension** — mentions docstrings + cites the ratified note.

## 5. Write scope

Prose mirror: the two ops sensor files, tests, findings, own dir. **Out of scope:**
`core/**` (bp-012/013's), `.gitlab-ci.yml`, design notes, the observed store (bp-012).
**Ordering note:** bp-008's builder concurrently owns `ops/type_gate.py` + `tests/**` —
this plan starts only after bp-008 merges (disjoint files but overlapping globs; the
delegate rule wants disjoint write_scope for parallel runs).

## 6. Interfaces pinned inline

Note §2.3 (verbatim, the fields this plan begins to fill):

```
docstring       str     # the Rosetta payload — verbatim, '' if absent
references_out  list    # typed: [{type: note-citation | path-mention | symbol-mention
                        #          | design-ref, target: str, source_line: int}]
```

Existing migration pattern (pinned): `cols = {r[1] for r in db.execute("PRAGMA
table_info(snapshots)")}` → `ALTER TABLE ... ADD COLUMN ... DEFAULT ''`.

V4 falsifier (note §2.7 clause 3, verbatim-condensed): _inventory near-empty or
noise-dominated ⇒ record as no-signal; the ledger remains valuable independently._

## 7. Items

### Item 1 — docstrings into the ledger (B-a)

- **Objective:** per-symbol `docstring` on `symbols` (additive column) + module docstring
  per file row; backfill all history (PD-d default); `sync()` report gains
  `doc_coverage` (documented symbols / total).
- **Files:** `ops/code_snapshot.py`, `ops/code_sensor.py`, new `tests/unit/` file (do NOT
  edit existing tests).
- **Acceptance test:** unit tests on a fixture repo assert docstring capture + coverage
  math; backfill over real history completes; ratchet green.
- **Falsifier:** a docstring visible to `ast.get_docstring` missing from the ledger.
- **Invariant(s):** ledger stays reset-guarded; snapshot idempotency by sha unchanged.
- **Touches stored data?** yes — additive migration on `data/code_snapshots.sqlite`
  (backfill re-runs are idempotent; dry-run on a copied db first, per template rule).
- **Parallelizable?** no **Depends on:** bp-008 merged (scope adjacency)

### Item 2 — the V4 reference inventory

- **Objective:** deterministic scan, both directions (Q3); counts by pattern type;
  ~30-sample hand-checked precision table; verdict against the falsifier; patterns ranked
  for bp-013's extractor.
- **Files:** `docs/build-plans/bp-011/inventory.json` + journal tables; scan script may
  live under `docs/build-plans/bp-011/` (not `scripts/` — it is a probe, not a tool).
- **Acceptance test:** inventory.json parses; journal carries counts + precision + the
  explicit keep/no-signal verdict.
- **Falsifier:** V4's own (pinned above) — an honest no-signal is a SUCCESS outcome.
- **Invariant(s):** read-only over the corpus and code.
- **Touches stored data?** no **Parallelizable?** with Item 1 **Depends on:** none

## 8. Math carried explicitly

N/A — no mathematical object implemented (counting and string extraction).

## 9. Non-goals

The observation store/seam (bp-012); minting any edge (bp-013); docstring format
standardization (parked, PD-c); corpus ingestion of anything.

## 10. Stop-and-raise conditions

Migration failure on the real ledger (restore from the pre-run copy, file finding);
inventory requiring judgment calls on >20% of samples (precision indeterminable —
finding + park Item 2 verdict).

## 11. Parked decisions

| Decision                   | Default recorded        | Rejected alternatives (why)     | Re-entry condition                            |
| -------------------------- | ----------------------- | ------------------------------- | --------------------------------------------- |
| where coverage is surfaced | sync() report line only | telemetry/dashboard (premature) | the site's what's-new/dashboard work wants it |

## 12. Dependency & ordering summary

After bp-008 merges. Item 1 ∥ Item 2. Feeds bp-013 (patterns) and the evolution study
(coverage). bp-012 is independent of this plan but shares the note's family.
