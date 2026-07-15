---
type: build-plan
id: bp-040
alias: sigma-sweep
status: proposed
design_ref: []            # no design note — warranted by finding-0079 (a direction finding); implements
                          # NO new design: the σ knob + its bound σ∈[0.55,0.75] + "calibrate on the owner's
                          # corpus" already exist (config/defaults.toml:211). This is a measurement instrument.
contract: builder
write_scope:
  - scripts/sigma_sweep.py
  - tests/unit/test_sigma_sweep.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 90k
    rationale: >-
      A small, READ-ONLY analysis script over already-built, test-pinned machinery (`cluster_notes`,
      `note_centroids`, `MirrorView`, `open_vector_store` — all exist and are graded). No new math, no
      store mutation, no re-embed, no model call. Modeled on `scripts/reembed_bodyonly.py` but read-only.
      Deterministic; a synthetic-fixture test. Self-driven lands ~0.5–0.8× (bp-039 = 0.71×). No fable.
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/findings/finding-0079.md
  - docs/findings/finding-0077.md
  - docs/build-plans/bp-036/plan.md
  - core/dreaming/cluster.py
  - config/defaults.toml
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0079.md
---

# Build Plan — `sigma-sweep` (bp-040): a read-only σ-sweep harness for the dreaming threshold

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval** (owner-only `proposed → ready`, by hand). Warranted by **finding-0079** (a `direction`
finding), which asks for exactly this — *"a small harness … that emits the σ-sweep so the choice is
evidence-based and repeatable."* It implements **no new design**: the σ knob, its bound
`σ ∈ [0.55, 0.75]`, and the standing instruction to *"calibrate σ on the owner's own corpus"* already
live in `config/defaults.toml:211`. This is a **measurement instrument** over built, graded dreaming
machinery — so no ratified design note is required (the finding is the warrant).

**READ-ONLY.** The harness mutates nothing — no store write, no config write, no re-embed, no re-dream,
no model call. It reads the live vector store, projects the AUTHORED-only `MirrorView`, and re-runs ONLY
the clustering step (`cluster_notes`) across a σ grid. σ affects clustering alone; the embeddings are
fixed (already body-only/clean since bp-036 + the owner's 2026-07-14 re-embed, finding-0077 resolved).
Model tier **opus**; no fable, no xhigh.

## 1. Objective

Produce, on the owner's live clean mirror graph, a σ-sweep table over `σ ∈ [0.55, 0.75]` — at each σ:
the edge count, the clusters (count, sizes, titles), and the near-threshold pairs (those within a band
of σ, i.e. the notes on the bubble) — so the owner can pick σ by the curve and set it by hand in
`config/local.toml`.

## 2. Context manifest

Read whole, in order:

1. `docs/findings/finding-0079.md` — the warrant: what to sweep (edges, clusters, near-threshold pairs),
   why (σ was calibrated on the id::-polluted graph; the clean graph needs a lower σ; art cluster @
   0.46–0.57, two near-core notes 0.005–0.018 below 0.62), and the methodology (sweep [0.55,0.75], pick
   by the curve, repeatable).
2. `core/dreaming/cluster.py` — the clustering the sweep re-runs. `NoteVector` (the per-note centroid +
   title/digest), `note_centroids(rows)` (:57), `similarity_matrix(notes)` (:80, normalized `m @ m.T`),
   `cluster_notes(notes, *, threshold, min_size)` (:89, union-find single-linkage at σ, `>= min_size`,
   largest-first), `Cluster` (its fields: members/titles/digests), `near_duplicate_pairs(notes, *,
   threshold)` (:129, the near-threshold-pair pattern to model the "on the bubble" reporter on).
3. `core/dreaming/dreamer.py` — the LIVE read path to mirror EXACTLY: `MirrorView.project(self.store).
   rows()` (:110) → `note_centroids(rows)` (:112) → `cluster_notes(..., threshold=dcfg.
   similarity_threshold, min_size=dcfg.min_cluster_size)`. The sweep reproduces this read, varying only σ.
4. `core/mirror.py` — `MirrorView.project(source)` (:72), the AUTHORED-only firewall the sweep must read
   through (never raw rows — the dreamer's own discipline).
5. `core/stores/vectorstore.py` — `open_vector_store(config)` (:116), `VectorStore.all_rows()` — the
   read surface (the sweep opens it read-only; never `.reset()`/`.add()`).
6. `config/defaults.toml` §`[dreaming]` (:205) — `similarity_threshold = 0.62` (:215), the bound
   `σ ∈ [0.55, 0.75]` (:211), `min_cluster_size = 2` (:216), `near_dup_threshold = 0.93` (:220). Load via
   `get_config()`; the sweep reads these defaults, changes none.
7. `scripts/reembed_bodyonly.py` — the SHAPE to model on (gate/report/`main()` wiring, injectable stores,
   dry-run default) — but bp-040 is READ-ONLY: no `seal()`, no daemon-down refusal (a read needs neither),
   no `reset`, no re-embed, no re-dream. Copy the CLI/report scaffolding, drop every mutation.

## 3. Investigation & grounding

- **Q1 — Does σ require re-embedding? NO.** σ is only the clustering `threshold` (`cluster_notes(...,
  threshold=σ)`, `cluster.py:89`,:111-114) over FIXED centroids (`note_centroids`, :57). The embeddings do
  not change with σ, so a sweep re-runs only the cheap NumPy clustering per σ — no re-embed, no daemon-down,
  no model call. `[grounds: cluster.py:80-126 is pure NumPy over centroids.]`

- **Q2 — Is the live graph clean (body-only)? YES.** bp-036 (sealed) wired `strip_properties` into the
  embed derivation (`core/ingest/pipeline.py:33,57`) — ALL `key::` props stripped before embedding — and
  the owner ran `scripts/reembed_bodyonly.py --confirm` (2026-07-14) so the live vectors are body-only
  (finding-0077, resolved). So the sweep runs on the honest content-only graph; this is precisely the
  graph finding-0079 wants σ calibrated against.

- **Q3 — What does the sweep read, exactly like the dreamer?** `MirrorView.project(open_vector_store(cfg))
  .rows()` → `note_centroids(rows)` (`dreamer.py:110-112`). The sweep reproduces this ONCE (centroids are
  σ-independent), then loops `cluster_notes(notes, threshold=σ, min_size=dcfg.min_cluster_size)` over the
  grid. Edge count at σ = `#{(i,j): i<j, cos[i,j] >= σ}` from `similarity_matrix(notes)` (:80). Near-
  threshold pairs at σ = pairs with `σ - band <= cos < σ + band` (the ones a small σ move flips).

- **Q4 — Corpus size / cost?** 13 authored notes (finding-0077/0079; the vault). A full σ-grid sweep is
  sub-second (13×13 cosine matrix, ~20 σ steps). No performance concern; no daemon-down needed (read-only).

**Additional risks surfaced:** (a) reading `vectors.lance` while the daemon is mid-ingest could catch a
transient state — MITIGATION: the harness prints the corpus size + a note to run it when the daemon is
idle (or just after a deploy settles); it does NOT require daemon-down (read-only). (b) `min_cluster_size`
and the near-threshold `band` are sweep parameters — defaulted from config / a sensible band (0.02), CLI-
overridable; NOT written back anywhere.

## 4. Reconciliation

`N/A — nothing corrected or extended.` The harness is a NEW, additive, read-only script; it changes no
existing code path, no config, no store. (It merely re-uses `cluster_notes` etc. as a library.)

## 5. Write scope

- `scripts/sigma_sweep.py` — **NEW**: the read-only σ-sweep report tool.
- `tests/unit/test_sigma_sweep.py` — **NEW**: deterministic tests over synthetic centroids.

**Deliberately OUT of scope:** `config/**` (the σ VALUE is an owner-gated hand edit to `config/local.toml`
— never written by an agent or this tool); `core/**` (the dreaming machinery is reused as a library, never
modified); `data/**` + `scripts/reembed_bodyonly.py` (no re-embed, no re-dream, no store mutation); every
design note; the denylist. The tool NEVER calls `.reset()`, `.add()`, `dreamer.dream()`, or the embedder.

## 6. Interfaces pinned inline

```python
# scripts/sigma_sweep.py — READ-ONLY. Model the CLI/report scaffolding on reembed_bodyonly.py, drop
# every mutation (no seal/daemon-refusal/reset/re-embed/re-dream).

# REUSED unchanged (core/dreaming/cluster.py — read the module for NoteVector/Cluster exact fields):
#   note_centroids(rows) -> list[NoteVector]           # per-note averaged centroid + title/digest
#   similarity_matrix(notes) -> np.ndarray             # normalized centroids, m @ m.T  (cosine)
#   cluster_notes(notes, *, threshold, min_size) -> list[Cluster]   # single-linkage components at σ
#   near_duplicate_pairs(notes, *, threshold) -> [...] # the near-pair pattern to model the bubble reporter
# REUSED (the live read path, EXACTLY as the dreamer, dreamer.py:110-112):
#   MirrorView.project(open_vector_store(cfg)).rows()  -> the AUTHORED-only rows
# REUSED (config, read-only): get_config().dreaming -> DreamingConfig(similarity_threshold=0.62,
#   min_cluster_size=2, near_dup_threshold=0.93);  bound σ ∈ [0.55, 0.75] (defaults.toml:211)

def sweep(notes, *, lo=0.55, hi=0.75, step=0.01, min_size=2, band=0.02) -> list[SigmaRow]:
    """For each σ in the grid, from FIXED centroids: edge count, clusters (count/sizes/titles), and the
    near-threshold pairs (|cos - σ| < band — the notes on the bubble). Pure function of the cosine
    matrix; no I/O. `edges(σ)` is non-increasing in σ (the sweep's own invariant)."""
    ...

# @dataclass SigmaRow: sigma, n_edges, n_clusters, cluster_sizes, cluster_titles, near_threshold_pairs
# main(): get_config() -> open_vector_store (READ) -> MirrorView.project -> note_centroids -> sweep()
#   -> print a table (σ | edges | clusters | sizes | bubble-pairs) + optionally write a JSON report to a
#   path arg. NO --confirm needed (read-only). Prints corpus size + "run when the daemon is idle".
```

## 7. Items

### Item 1 — `sweep()` + the report types (the pure, testable core)
- **Objective:** `sweep(notes, *, lo, hi, step, min_size, band)` — from the fixed centroids, per σ:
  `n_edges`, the clusters (count/sizes/titles via `cluster_notes`), and near-threshold pairs
  (`σ-band ≤ cos < σ+band`). A pure function of the notes (their cosine matrix) — no I/O.
- **Files:** `scripts/sigma_sweep.py`, `tests/unit/test_sigma_sweep.py`.
- **Acceptance test:** over a SYNTHETIC fixture of hand-placed centroids with known pairwise cosines
  (e.g. a tight triple @ ~0.7, a bubble pair @ ~0.61, an isolate), `sweep(lo=0.55, hi=0.75, step=0.05)`
  yields: `n_edges` **non-increasing** in σ; the bubble pair present in `near_threshold_pairs` at σ≈0.62
  and absent far from it; the triple forms one cluster at σ≤0.7 and splits above; cluster titles match.
- **Falsifier:** `n_edges` rises as σ increases (the monotonicity invariant broken → a threshold-sense
  bug); OR a σ change re-embeds / mutates any store (it must be pure over fixed centroids).
- **Invariant(s):** read-only/pure (no store, no model, no config write); AUTHORED-only (reads via
  `MirrorView`, never raw rows); deterministic (fixed grid, no `Math.random`).
- **Touches stored data?** No.  **Parallelizable?** No (Item 2 wraps it).

### Item 2 — `main()`: wire the live read + emit the table/JSON
- **Objective:** open the live vector store READ-ONLY, project `MirrorView`, compute centroids once, run
  `sweep()`, print a σ-table (σ | edges | clusters | sizes | bubble-pairs) + the corpus size, and
  optionally write a JSON report to a `--out` path. CLI overrides: `--lo/--hi/--step/--min-size/--band`.
- **Files:** `scripts/sigma_sweep.py`.
- **Acceptance test:** `uv run scripts/sigma_sweep.py --lo 0.55 --hi 0.75 --step 0.01` on the live store
  prints a well-formed table with one row per σ, the current σ=0.62 row flagged, and the corpus note
  count; `--out report.json` writes valid JSON of the same rows; the run performs ZERO writes to any
  store/config (verifiable: no mtime change on `data/**` or `config/**`).
- **Falsifier:** the run writes to any store/config, calls the embedder, or calls `dreamer.dream()` (any
  mutation or model call means it overreached the read-only contract); OR it reads raw (non-authored) rows.
- **Invariant(s):** read-only (Inv 4 flavor — reports data, takes no action); AUTHORED-only firewall; no
  network, no vault.
- **Touches stored data?** No (opens the store read-only).  **Depends on:** Item 1.

## 8. Math carried explicitly

- **Single-linkage clustering at σ** — *measures:* the theme clusters as connected components of the
  graph `E_sim(σ) = {(u,v) : cos(centroid_u, centroid_v) ≥ σ}` over note centroids (`cluster_notes`,
  `cluster.py:89`). *valid when:* centroids are unit-normalized (they are — `similarity_matrix` normalizes)
  so `m @ mᵀ` is cosine, and σ is in a regime where components are meaningful (the `σ ∈ [0.55, 0.75]`
  bound). *fails its keep if:* `n_edges(σ)` is not monotone non-increasing in σ (a threshold-sense bug),
  or the swept components disagree with `cluster_notes` at the same σ (the sweep must call the SAME
  clustering the dreamer uses — never a re-implementation that could drift).

## 9. Non-goals

- **No re-dreaming per σ.** The 27b synthesis call (~290s/cluster) makes per-σ re-dreaming impractical
  and unnecessary for calibration — the GRAPH structure (edges/clusters/bubble-pairs) is the calibration
  signal. Re-dreaming happens ONCE at the owner's chosen σ, via the existing `scripts/reembed_bodyonly.py`
  (or a lighter re-dream), as a separate owner-run step. This harness stops at the graph report.
- **No config write.** The σ VALUE is an owner-gated hand edit to `config/local.toml` (never auto-modified,
  finding-0079). The tool RECOMMENDS nothing binding — it reports the curve; the owner decides.
- **No re-embed, no store mutation, no model call, no daemon control.** Pure read over fixed centroids.
- **No new clustering math.** It calls the built `cluster_notes`/`similarity_matrix`; it does not
  re-implement or "improve" the clustering (that would be a separate designed change).
- **No `[dream_rnd]` path.** The sweep targets the LIVE dreamer's single-linkage clustering, not the
  flag-off R&D graph track.

## 10. Stop-and-raise conditions

- The sweep cannot read the store without the daemon (a lock / exclusive handle) → **file a `codebase`
  finding**; do not bring the daemon down from within the tool (a read should not need it; if it does,
  that is a finding, not a workaround).
- The swept components disagree with `cluster_notes` at the same σ → **stop**; the sweep MUST call the
  same clustering the dreamer uses, never a re-implementation (§8 falsifier).
- The tool would need to write config to "apply" a σ → **must not**; the σ change is the owner's hand edit.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Re-dream at each σ | NO — report graph structure only; re-dream once at the chosen σ | re-dream every σ (rejected: ~290s/cluster × grid — impractical, and the graph is the calibration signal) | the owner wants to see actual dreams across σ (a separate, budgeted run) |
| The σ grid + band | `[0.55, 0.75]` step 0.01, band 0.02 (CLI-overridable) | a coarser/finer fixed grid (deferred: CLI covers it) | the owner wants a different resolution |
| Where the harness lives | `scripts/sigma_sweep.py` (a script, like `reembed_bodyonly.py`) | a mirror/dreamer method (deferred: a report tool is not a library method; keep the read path a script) | a consumer needs the sweep as a library call |
| Auto-recommending a σ | NO — report only; the owner picks | emit a "recommended σ" (rejected: a taste call on the owner's own corpus, finding-0079 — the tool informs, never decides) | the owner asks for a heuristic pick (e.g. knee-of-curve) |

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (pure `sweep()` + tests — zero I/O) → **Item 2** (the live read wiring +
table/JSON emit). Both in `scripts/sigma_sweep.py` + one new test file → **one session, not parallel.**
`depends_on: []`. Model **opus** (small, read-only, deterministic; no fable, no xhigh). After the build:
the OWNER runs the tool (read-only; ideally after this deploy settles / daemon idle), reads the curve,
sets σ by hand in `config/local.toml`, and re-dreams once at the chosen σ — none of which is this plan.
