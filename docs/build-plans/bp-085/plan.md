---
type: build-plan
id: bp-085
track: fiber-geometry
status: complete
design_ref:
  - docs/design-notes/fiber-geometry.md
contract: builder
write_scope:
  - eval/harness/fiber_survey.py
  - tests/unit/test_fiber_survey.py
  - docs/findings/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual:
    model: opus            # claude-opus-4-8[1m], tier verified via completion usage
    tokens: 218481
    tool_calls: 143
    duration_min: 59
    ratio: 0.87            # well-pinned; S rows deferred by design (embedder vs daemon memory ceiling), not a defect
    session_delta: "weekly all-models pool; the largest build of the wave; duration inflated by embed-timeout probes + 18min serial suite"
depends_on: []
parallelizable_with: [bp-083, bp-086, bp-087, bp-088]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/fiber-geometry.md
  - eval/harness/re_measure.py
  - docs/findings/finding-0140.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — G-A: the fiber-geometry measure-first survey (M1–M8, read-only)

> Graduated from ratified `dn-fiber-geometry` §2.6 / §3. The ONE read-only survey the note
> authorizes — **eval-side readings only, no core writes**. It is the gate for everything else in
> the note: its nulls are findings, not failures. Every reading carries its CN-1 index tuple + grid.
> Several rows are **expected null or thin** on today's corpus (C thin; live census empty at
> bp-080's seal; endorsed-chain corpus barely exists) — a null *parks* the machinery it gates.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only. Read-only, cheap; the note's sequencing constraint is
honored — it queues behind in-flight/sequenced work (bp-082; the dreamer builds' remaining items)
but preempts nothing and blocks nothing. It may run pre- or post-ratification of the ring notes
(disjoint scope).

## 1. Objective

Run the eight measure-first readings M1–M8 (M9/M10 ride along where the stores make them free)
over the live corpus with the built instruments, each CN-1-indexed, and record the results — nulls
explicitly marked as results — as a findings-grade survey that gates PD-a re-entry, the functional
question (σ*-vs-product), the phase model, and the grammar's data track.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/fiber-geometry.md` — §2.0 (the canonical alphabet Σ_move = {S,F,D,C}; the
   F-for-similarity correction, finding-0140), §2.2 (the per-class Hodge honesty table — one full
   S, one provably-degenerate D, two empirical F/C), §2.5 (the block-diagonality fact; PD-a's three
   measured re-entry conditions), §2.6 (the battery table — the authoritative M1–M10 spec, each row:
   what / instrument / gates).
2. `eval/harness/re_measure.py:45-46,180-192` — `assemble_composed_graph(...)` (the pure/injected
   Δ composed-graph assembly the survey builds on) and `MirrorGraph.build(view, sigma=min(grid))`.
3. `core/graph/composed.py:49-53,70,83,105` — `E_SIM`/`E_PROVEN`/`E_STAGED`; `PROVEN_WEIGHT = 1.0`;
   `edge_classes: dict[tuple[int,int], frozenset[str]]` (the per-class attribution the mismatch
   fields read).
4. `core/complex/hodge.py:48,59,84,103,136,157,188` — `edge_index`, `flag_triangles`,
   `boundary_1/2`, `hodge_laplacian_1`, `hodge_decompose`, `harmonic_basis` (M3 triangles, M4 split).
5. `core/complex/curvature.py:25,46` — `forman`, `most_negative_edges` (M5).
6. `core/graph/conductance.py:298,375,393` — `sigma_t_profile`, `chi_s`, `chi_s_all` (M6, M8);
   `CONDUCTANCE_THRESH:91` (magnitudes shipped 0).
7. `core/graph/sigma_star.py:200,215` — `sigma_star`, `pairwise_sigma_star` (M8 bottleneck).
8. `core/graph/census.py:293` — `census` (M10 signature families); the store handles
   `reference_edges` (F) and `versions` (D).

## 3. Investigation & grounding

Touches existing code by READING it only (no core write). Grounded at HEAD (`d08da37`) — every
named instrument verified present: `assemble_composed_graph` (`re_measure.py:180`); `edge_classes`
+ `PROVEN_WEIGHT` (`composed.py:83,70`); `flag_triangles`/`hodge_decompose`/`harmonic_basis`
(`hodge.py:59,157,188`); `forman` (`curvature.py:25`); `chi_s`/`chi_s_all`/`sigma_t_profile`
(`conductance.py:375,393,298`); `sigma_star`/`pairwise_sigma_star` (`sigma_star.py:200,215`);
`census` (`census.py:293`); `long_lived_holes` (`core/complex/topology.py:104`).

- **Q1 — is the composed assembly pure/injectable for read-only use?** Yes —
  `assemble_composed_graph` takes an explicit doc node set and `sigma_floor = min(grid)`
  (`re_measure.py:180-192`), no write handle. The survey injects live-store reads and never writes.
- **Q2 — is C non-empty on the live corpus?** The note records the **live census read came back
  empty** at bp-080's seal (§2.0 table). The code does not settle whether it is empty at *this*
  HEAD — Item 7 measures it; an empty C is a *result* (M1 population census), and it parks the
  C-dependent rows (M2's S↔C, M5's C-conditioning) as expected-null, narrated as such (never as
  structure).
- **Q3 — weighted vs combinatorial Hodge inner product.** The built `hodge.py` uses the
  *combinatorial* (unweighted) inner product (§2.1-3, PD-b parked). M4's split is read
  **qualitatively** only; a quantitative transport attribution would be PD-b's re-entry — out of
  scope, flagged in the finding.

**Additional risks:** the "silence narrated as structure" failure — an expected-null row's absence
of data must be reported as "expected null (C thin)", never as a measured zero-signal claim. Every
reading MUST carry its CN-1 index tuple + grid or it is malformed (the battery's own falsifier).

## 4. Reconciliation

N/A — nothing corrected or extended in committed code. The survey is additive eval-side machinery
+ a findings artifact; it consumes ratified instruments unchanged and edits no ratified text (A8).
The alphabet correction (finding-0140, F-for-similarity) is *consumed* by the survey's labeling,
not re-litigated.

## 5. Write scope

`eval/harness/fiber_survey.py` (the new survey module: assembles the per-class graphs, runs M1–M8,
emits CN-1-indexed readings), `tests/unit/test_fiber_survey.py` (proves the survey runs on a small
fixture and that each reading carries its index — a smoke/honesty test, not a corpus assertion),
and `docs/findings/**` (the survey's output IS one or more findings — the nulls-as-results record;
per the routing rule, `math`/`direction` findings route to the orchestrator). Deliberately OUT of
scope: all of `core/**` (read-only; the survey imports instruments, never edits them), every store
schema, the ratified notes.

## 6. Interfaces pinned inline

```python
# eval/harness/re_measure.py:180
def assemble_composed_graph(doc_ids, *, view, sigma_floor, ...) -> ComposedGraph: ...
# core/graph/composed.py:83
    edge_classes: dict[tuple[int, int], frozenset[str]]   # per-pair class tags: {"E_sim","E_proven","E_staged"}
# core/complex/hodge.py
def flag_triangles(A) -> np.ndarray                       # M3 per-class triangle census
def hodge_decompose(c, A) -> HodgeParts                   # M4 gradient/curl/harmonic split (combinatorial i.p.)
# core/complex/curvature.py:25
def forman(A) -> dict[tuple[int,int], float]              # M5 Forman curvature
# core/graph/conductance.py
def chi_s(spine, stratum, *, window=None) -> float | None # M6 per-region churn ratio
def sigma_t_profile(...) -> ...                           # M8 (σ,t) conductance profile
# core/graph/sigma_star.py:200
def sigma_star(...) -> ...                                # M8 bottleneck ultrametric (no hop pricing)
```
**The battery spec (§2.6) is the authoritative per-item definition** — each item below names its
row id, instrument, and what it gates; the note's table is copied into the survey module's
docstring verbatim so the builder reads no design from a pointer.

## 7. Items

All read-only (blast radius: sensing only). Each emits a CN-1-indexed reading into the survey
output; an expected-null row records "null — <reason>" as its result.

### Item 7 — M1: skeleton overlap + per-class population census
- **Objective:** pairwise support Jaccard on shared nodes for S/F/D/C + population counts.
- **Files:** `eval/harness/fiber_survey.py`.
- **Acceptance test:** the survey emits M1 with the four populations and the pairwise overlaps,
  CN-1-indexed; runs green on the fixture in `test_fiber_survey.py`.
- **Falsifier:** a reading emitted without its index tuple/grid ⇒ malformed (the battery falsifier).
- **Invariant(s):** no core write; `E` stays a set (no language-walk).
- **Touches stored data?** Reads only. **Parallelizable?** Yes. **Depends on:** none.

### Item 8 — M2/M3: mismatch densities + cross-class gradient correlation + conditional minting; per-class triangle census
- **Objective:** S↔C, S↔F mismatch densities; cross-class gradient-potential correlation;
  conditional minting intensities (C/F on high-cos pairs; `E[Δw_S | D-event]`); per-class triangle
  census (D MUST be 0 — covering-only integrity; F/C empirical).
- **Files:** `eval/harness/fiber_survey.py`.
- **Acceptance test:** M2/M3 readings emitted, CN-1-indexed; the D-triangle count is reported (a
  nonzero D count is flagged as a **data-integrity violation** per ML owner decision 3, not
  swallowed).
- **Falsifier:** C-empty rows narrated as measured-zero structure rather than expected-null.
- **Invariant(s):** combinatorial Hodge read qualitatively only (PD-b honored).
- **Touches stored data?** Reads only. **Parallelizable?** Yes. **Depends on:** Item 7.

### Item 9 — M4/M5: S-field Hodge split + Forman-vs-churn
- **Objective:** S-field gradient/curl/harmonic energy fractions; `forman()` on the σ-graph
  conditioned on per-region D-minting rate (the clique-positive vs hub-negative sign question).
- **Files:** `eval/harness/fiber_survey.py`.
- **Acceptance test:** M4/M5 readings emitted, CN-1-indexed; the Forman sign summary recorded.
- **Falsifier:** a quantitative transport claim drawn from the combinatorial split (PD-b's line).
- **Invariant(s):** read-only; no Ollivier (behind Forman, not licensed).
- **Touches stored data?** Reads only. **Parallelizable?** Yes. **Depends on:** Item 7.

### Item 10 — M6/M7/M8: thermometer, phase signature, σ-sweep
- **Objective:** M6 D-minting rate per region vs the churn stats CN-4's a_seq consumes + per-region
  χ_s; M7 dead-vs-live three-field signature + metric-mismatch field; M8 the owed σ-sweep
  (oq-0024) + bottleneck-vs-product chain divergence, scored against endorsed chains where any exist.
- **Files:** `eval/harness/fiber_survey.py`.
- **Acceptance test:** M6/M7/M8 readings emitted, CN-1-indexed; M8 records whether bottleneck- and
  product-optimal chains diverge on the real corpus (or "no endorsed chains — deferred").
- **Falsifier:** M8 silently drops the endorsed-chain scoring where the corpus is empty instead of
  recording the absence.
- **Invariant(s):** no silent change to `sigma_star`/`conductance` (the clock-curvature park honored).
- **Touches stored data?** Reads only. **Parallelizable?** Yes. **Depends on:** Item 7.

### Item 11 — synthesize the survey finding(s) (nulls as results)
- **Objective:** write the survey's readings into `docs/findings/` as a `math`/`direction` finding
  recording every M-row's result — nulls explicitly — and its gate disposition (PD-a cond. 1/2,
  FG-b, FG-f, etc.).
- **Files:** `docs/findings/finding-0142.md` (or next free id).
- **Acceptance test:** the finding names each M-row, its reading (or "expected null — <reason>"),
  and the parked-decision it gates; routes to the orchestrator per the routing rule.
- **Falsifier:** a gate declared "resolved" off an expected-null row (silence as signal).
- **Invariant(s):** records-not-causes vocabulary throughout.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 7–10.

## 8. Math carried explicitly

- **Per-class flag-complex Hodge (S full; D degenerate; F/C empirical)** — *measures:* gradient/
  curl/harmonic energy of a class's weight cochain. *valid when:* the class's skeleton is the
  flag complex the instrument builds; D's curl ≡ 0 is provable (triangle-free Hasse). *fails its
  keep if:* a nonzero D-triangle appears (data-integrity violation, M3) or the combinatorial split
  is used for quantitative transport (PD-b).
- **σ* (bottleneck ultrametric) vs max-product (−log w) path** — *measures:* which chains are
  optimal under each functional. *valid when:* the σ-sweep grid is declared (CN-1). *fails its
  keep if:* the two never diverge on the real corpus (then hop-pricing merely complements, FG-b
  default stands) — a *result*, recorded, not a failure.
- **Mismatch densities (S↔C, S↔F) and metric-mismatch field** — *measures:* causation/citation
  without resemblance; effective-vs-ambient distance ratio. *valid when:* per-class attribution is
  intact (`edge_classes`). *fails its keep if:* fused with each other (different objects — §2.2).

## 9. Non-goals

No grammar build (automaton/product walk — FG-d, waits for the explainable-retrieval consumer). No
sheaf/bundle operator (FG-a's three conditions). No Ollivier, no horizon scan, no velocity/spectral
tier build, no CN-4 magnitude change (all parked/gated). No core write of any kind. No `E`
set→language extension.

## 10. Stop-and-raise conditions

- A nonzero D-triangle count (M3) ⇒ **raise** a data-integrity finding (covering-only supersession
  violated) — this is a real corpus defect, not a survey artifact.
- An instrument returns an unexpected shape (e.g. `chi_s` needs a spine the survey can't build
  read-only) ⇒ file a `codebase` finding and mark that M-row "instrument-blocked", continue others.
- Any temptation to write to `core/**` to make a reading work ⇒ stop; the survey is read-only.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| FG-a sheaf/bundle Laplacian | per-class runs + scalar cross-stats | build the coupled operator now (block-diagonal or invented mixing maps — apophenia) | M1/M2 meet PD-a's three conditions |
| FG-b hop-priced functional | bottleneck σ* stands | silently change σ* | M8 shows material divergence AND product predicts endorsed chains better |
| FG-g weighted Hodge i.p. (PD-b) | combinatorial, qualitative | quantitative transport off combinatorial split | M4 consumed quantitatively |
| M9/M10 | ride along where free | force them if stores don't make them cheap | their gating consumer graduates |

## 12. Dependency & ordering summary

Item 7 (M1) first (populations gate the rest); Items 8/9/10 parallelizable after 7; Item 11
synthesizes after all readings. No dependency on any other plan; parallelizable with bp-083,
bp-086, bp-087, bp-088 (disjoint write scopes — this is eval-side + findings only). Blast radius:
read-only sensing throughout.
