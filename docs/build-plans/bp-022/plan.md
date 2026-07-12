---
type: build-plan
id: bp-022
status: ready
design_ref:
  - docs/design-notes/edge-dynamics.md # Lane A §2.3 (lens-contract entry), §3.1 L-b/L-c
contract: builder
write_scope:
  - "core/dreaming/interpreters.py"
  - "core/complex/temporal.py"
  - "config/loader.py"
  - "config/defaults.toml"
  - "tests/unit/test_thread_lens.py"
  - "tests/unit/test_temporal.py"
  - "tests/integration/test_structural_panel.py"
  - "docs/build-plans/bp-022/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 250k } # lens-mold work (tension_claims/hole_interpreter as templates) + additive snapshot fields; crisp tests
  actual: null
depends_on: [bp-021] # consumes hodge.py's harmonic_basis + the cross-check harness — SATISFIED (bp-021 complete, merged cb953a9, 2026-07-12)
parallelizable_with: [bp-018] # disjoint write_scope (dreaming/temporal/config vs stores/sensor/launcher; only docs/findings/** shared — new files, disjoint ID ranges); asserted at spawn 2026-07-12, graduation-author's amendment
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/brainstorms/edge-dynamics-and-continuum.md
  - docs/design-notes/dreaming-v2-interpreter-panel.md # the panel contract THREAD joins
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — L-b/L-c: the THREAD lens + degree-1 invariants in the temporal record

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-12 from the **ratified** `dn-edge-dynamics` (§2.3's lens-contract
entry, §3.1 L-b/L-c). Investigation and planning produced this; implementation proceeds
item-by-item on owner approval. `proposed → ready` is the owner's hand edit. Second of
the Lane A pair; requires bp-021's `core/complex/hodge.py`.

## 1. Objective

The harmonic threads become visible: a `THREAD` structural lens joins the interpreter
panel (deterministic, gap-family, honest-seam), and the temporal snapshot record gains
the two degree-1 exact invariants — so the dreamer can narrate circulating structure
and the system watches its thread count evolve.

## 2. Context manifest

1. `docs/design-notes/edge-dynamics.md` §2.3 (the lens pinning: routing class,
   persistence ranking, honest seam), §3.1 L-b/L-c falsifiers.
2. `core/dreaming/interpreters.py` — whole file; `hole_interpreter` and
   `tension_claims` are the molds; `STRUCTURAL_INTERPRETERS` the registry;
   `StructuralContext` the input (complex + unthresholded distances).
3. `core/complex/hodge.py` (bp-021) — `harmonic_basis`, `edge_index`, the §6(f)
   scale-matching harness.
4. `core/complex/topology.py` — `Hole` (witness node-index tuple, birth/death,
   `lifetime`), `long_lived_holes`.
5. `core/complex/temporal.py` — `StructuralSnapshot` (fields + `structural_axes`),
   `compute_snapshot`, `SnapshotStore` (DuckDB; `trajectory`'s allowed-metric list).
6. `config/loader.py:93-96` + `config/defaults.toml:245` — where the structural-lens
   bounds live (`hole_min_persistence` is the sibling the new constant mirrors).

## 3. Investigation & grounding

- **Q1 — how does a structural lens register and fire?** `STRUCTURAL_INTERPRETERS`
  (dict, method-name → `(ctx, cfg) -> list[Claim]`) is iterated by `collect_claims`
  (`core/dreaming/interpreters.py:278-291`); `run_panel` and the dreamer's loop both
  route through it, so registration alone wires the dream path — `dreamer.py` needs NO
  edit (verified: it imports `build_structural_context`/`collect_claims`, not
  individual lenses).
- **Q2 — what carries the narration?** The `Claim.statement` text itself (the
  `tension_claims` precedent formats titles into prose, `:257-277`) — the note's §5
  narration question resolves to: the statement IS the vocabulary; no dream-prompt
  change in this plan.
- **Q3 — does `Hole` carry enough to localize a thread?** Yes: `long_lived_holes`
  yields `Hole` objects with a witness tuple of node indices (`topology.py:29-43,
  70-104`) mapping to digests via `ReasoningComplex.nodes`; birth/lifetime give the
  persistence rank. The carrying cycle is the witness — existing machinery, not new
  cycle extraction (the note's L-b "localized to carrying cycles" lands on the hole
  witnesses the threads orbit, §2.2's kernel≅H₁ identification).
- **Q4 — can the DuckDB snapshot store take new columns additively?**
  `SnapshotStore.__post_init__` runs DDL on open (`temporal.py:123-128`); DuckDB
  supports `ALTER TABLE … ADD COLUMN IF NOT EXISTS` — pinned §6(d) as the on-open heal
  (the house healing-on-open pattern). `trajectory()` validates against an
  allowed-metric list (`:144-155`) — extended, not bypassed.
- **Q5 — scale consistency between lens inputs.** `StructuralContext` carries the
  σ-thresholded complex AND the unthresholded distance matrix. The kernel is computed
  at σ (on `ctx.complex.A`); holes at `thread_min_persistence` over all scales. The
  two are consistent by bp-021's Q4 harness at matching scale; the lens's honest-seam
  rule (§6(b) step order) makes β₁ = 0 short-circuit BEFORE any hole pairing, so a
  scale mismatch can never fabricate a thread.

**Additional risks surfaced during reading:** `compute_snapshot` is called with
`distances=None` in some paths (`temporal.py:80-99` guards `h1` on it) — the new
invariants must degrade to `None` the same way; the drift-axes surface
(`structural_axes`, `:71-73`) is a CONSUMED contract (eval drift profile) — do NOT add
the new fields to it (additive observation, not a new drift axis; that would silently
change eval behavior).

## 4. Reconciliation

- `core/dreaming/interpreters.py:1-31` (module docstring's lens inventory) →
  **[cross-ref: extension]** carried by Item 5: the structural-lens list gains
  `thread` (harmonic H₁ flow — a gap-family sibling of `hole`, never a contradiction).
- `core/complex/temporal.py:3-13` (docstring: "time series of structural invariants")
  → **[cross-ref: extension]** carried by Item 6: the invariant list gains the two
  degree-1 entries with the dn-edge-dynamics pointer.
- No corrections — nothing existing is wrong.

## 5. Write scope

In: the interpreter panel module, the temporal module, the two config files (one
dataclass field + one parse line + one toml line), three test files, own plan dir,
findings. Out, deliberately: `core/dreaming/dreamer.py` (Q1 — registration suffices),
`core/complex/hodge.py` (bp-021's; a needed change there is a spec-defect finding),
`eval/**` (the drift-axes contract stays untouched — §3 risk), design notes, the
foundation denylist.

## 6. Interfaces pinned inline

**(a) Config (the `hole_min_persistence` sibling, `loader.py:93-96` +
`defaults.toml:245`):**

```python
thread_min_persistence: float  # min H1 lifetime for a thread's carrying hole (cosine-distance units)
```

```toml
thread_min_persistence = 0.15 # min H1 lifetime (cosine-distance units) for a THREAD's carrying cycle
```

**(b) The lens (registered as `THREAD = "thread"` in `STRUCTURAL_INTERPRETERS`):**

```python
def thread_interpreter(ctx: StructuralContext, cfg: DreamRnDConfig) -> list[Claim]:
    # 1. H = harmonic_basis(ctx.complex.A); beta1 = H.shape[1]
    # 2. if beta1 == 0: return []            ← the honest seam FIRST (β₁=0 ⇒ nothing,
    #                                          regardless of what the filtration shows)
    # 3. holes = long_lived_holes(ctx.distances, min_persistence=cfg.thread_min_persistence)
    # 4. for each hole, persistence-ranked, up to min(len(holes), beta1):
    #      witness digests = [ctx.complex.nodes[i] for i in hole.witness]
    #      flow = max over harmonic columns of mean |h[e]| on witness-cycle edges
    #             present in the σ-skeleton (edge_index from hodge.py)
    #      Claim(method=THREAD,
    #            statement=f"a circulating thread — '{t1}', '{t2}', … form a closed
    #                       loop orbiting a gap you have not stated (persistence {p:.2f})",
    #            support=witness digests, data={"persistence": …, "flow": …,
    #                                           "witness": […]})
```

Routing class pinned: **gap-family, never contradiction** (dissonance stays with the
signed machinery — the note §2.3's routed-split inheritance). Support ⊆ witness — the
L-b falsifier's second clause, by construction.

**(c) Snapshot fields (`StructuralSnapshot`, additive, degrade-to-None):**

```python
dim_ker_l1: int | None = None                 # β₁ of the σ-flag complex (exact, degree 1)
harmonic_persistence_total: float | None = None  # Σ lifetime over holes ≥ thread_min_persistence
```

`compute_snapshot` computes both only when `distances is not None` (the existing `h1`
guard's pattern); signature gains `thread_min_persistence: float = 0.15` keyword.
**NOT added to `structural_axes()`** (§3 risk — the drift contract is consumed).

**(d) Store migration (`SnapshotStore.__post_init__`, on-open heal):**
`ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS dim_ker_l1 INTEGER;` + `… ADD COLUMN IF
NOT EXISTS harmonic_persistence_total DOUBLE;` — idempotent, existing rows read back
NULL → `None`. `trajectory()`'s allowed-metric list gains both names.

## 7. Items

_(Lane A numbering continues from bp-021)_

### Item 4 — the config constant

- **Objective:** §6(a) — field, parse line, toml default.
- **Files:** `config/loader.py`, `config/defaults.toml`
- **Acceptance test:** config loads; `DreamRnDConfig.thread_min_persistence == 0.15`
  from defaults; existing config tests green.
- **Falsifier:** a `local.toml` missing the key crashes the loader (the parse must
  follow the house default-merge pattern, not a bare dict index — verify against how
  the sibling keys behave on a minimal local.toml).
- **Invariant(s):** no other config field's parse changes.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 6) **Depends on:** none

### Item 5 — `thread_interpreter` + registration

- **Objective:** §6(b) exactly; module-docstring extension (§4).
- **Files:** `core/dreaming/interpreters.py`, `tests/unit/test_thread_lens.py`,
  `tests/integration/test_structural_panel.py`
- **Acceptance test:** on a synthetic MirrorView whose notes form an empty cycle
  (β₁ = 1): exactly one THREAD claim, support == the witness digests, persistence in
  data. On a filled/acyclic corpus (β₁ = 0): ZERO claims even with holes present below
  scale (the seam order pinned). Panel integration: `collect_claims` returns THREAD
  claims alongside the existing lenses; every existing panel test green unchanged.
  Determinism: two runs, identical claims.
- **Falsifier:** the note's L-b falsifier verbatim — a THREAD claim on a β₁ = 0
  complex (fabricated thread), or a claim whose support includes a note not on its
  carrying cycle.
- **Invariant(s):** model-free; MirrorView-only input (structural firewall unchanged);
  no existing lens's output changes; adjudication untouched (note PD-f).
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** Item 4, bp-021

### Item 6 — degree-1 invariants in the temporal record

- **Objective:** §6(c,d); docstring extension (§4).
- **Files:** `core/complex/temporal.py`, `tests/unit/test_temporal.py`
- **Acceptance test:** `compute_snapshot` on the synthetic fixtures yields the known
  β₁ in `dim_ker_l1` and the expected persistence sum; `distances=None` yields None
  for both (no crash); a PRE-EXISTING store file (fixture without the columns) opens,
  heals, reads old rows with `None`, writes new rows with values;
  `trajectory("dim_ker_l1")` returns the series; `structural_axes()` output
  BYTE-IDENTICAL to before (the drift contract pinned by test).
- **Falsifier:** the note's L-c falsifier verbatim — a snapshot series recomputed from
  the same inputs differs run-to-run, or any existing invariant's value is perturbed
  by the new fields.
- **Invariant(s):** detection-only ("nothing here alters anything" stays literally
  true); DuckDB stays the engine (telemetry lane — this is the time-series exception,
  already ruled); `structural_axes` unchanged.
- **Touches stored data?** yes — the on-open ALTER against the live snapshot store.
  Dry-run: the fixture-file heal test proves the migration before merge; the live file
  heals on first open after merge (additive, NULL-backfilled, reversible by column
  drop).
- **Parallelizable?** yes (with Item 4; needs bp-021 only for the kernel call)
  **Depends on:** bp-021

## 8. Math carried explicitly

- **thread (harmonic class, persistence-ranked)** — _measures:_ circulating structure:
  a closed loop of pairwise-related notes orbiting an unstated gap, with per-edge flow
  magnitude from the harmonic basis. _valid when:_ β₁ > 0 at the σ scale AND a
  long-lived hole pairs with it (both machineries agree something is there). _fails
  its keep if:_ over a month of dreams, THREAD claims are never adjudicated
  informative (owner-facing signal test — then the corpus has no narratable threads
  yet; the lens stays honest and quiet, the temporal series keeps the count).
- **dim ker L₁ / harmonic persistence total (snapshot invariants)** — _measure:_ the
  thread count and its filtration weight, over time. _valid when:_ computed from the
  same complex build as every other snapshot invariant (one pass, one σ). _fails its
  keep if:_ the series never moves across months of snapshots (a flatline carries no
  temporal information — record as no-signal per the note's §2.8-style razor).

## 9. Non-goals

Dream-prompt/narration template changes (Q2 — statements carry it); adjudication
changes (PD-f); weighted L₁ (bp-021 parked); reference-edge cochain projection (note
§5 open question — waits for its own gate); any P5 rung (Lomb–Scargle, DMD, actions —
data-gated); Lane B / observed strata (gated, Track D); eval/drift changes.

## 10. Stop-and-raise conditions

`hodge.py` needs any change (bp-021's seam broke — spec-defect finding, never edit it
from here); the β₁-vs-holes pairing produces persistent disagreement on real data
(math-type finding to the orchestrator — the scale-matching assumption needs a design
look, do not paper over with tolerance); `structural_axes` cannot stay unchanged (the
drift contract is implicated — stop, that is an eval-plane design question); the live
snapshot store's heal fails (stop before any write path ships).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| thread constant value | 0.15 (mirrors hole_min_persistence) | a distinct tuned value (no data to tune on yet — the temporal series is what will provide it) | a quarter of snapshot data shows the hole and thread scales should diverge |
| flow detail in claims | scalar max-mean magnitude in `data` | full per-edge flow vectors (payload bloat into the dream context; the adjudicator doesn't consume it) | a consumer (P5 rung or adjudicator) needs the vector |
| snapshot β₁ source | kernel dim at σ (hodge.py) | reuse ripser alive-count (couples the snapshot to the persistence pass's cost; kernel is cheaper at fixed scale and bp-021's harness guarantees agreement) | the harness ever reports sustained disagreement |

## 12. Dependency & ordering summary

{Item 4 ∥ Item 6-prep} → Item 5; Item 6's store heal is the only stored-data touch
(fixture-proven first, additive, NULL-safe). Cross-plan: **depends_on bp-021**
(harmonic_basis, edge_index, the harness). After this plan, Lane A is live end-to-end:
threads narrate through the existing dream path and the temporal record carries the
degree-1 series that P5's rungs will one day read — each rung entering by the note's
§2.5 ladder, its own plan, its own gate.
