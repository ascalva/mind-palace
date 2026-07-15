---
type: build-plan
id: bp-040
alias: dream-calibrate
status: proposed
design_ref: []            # no design note — warranted by finding-0079 (σ) + the owner's 2026-07-15
                          # directive to bring the full dreamer online. Implements NO new design: the σ
                          # knob (config/defaults.toml:211,229) and dream_v2 (built, tested, flag-off)
                          # both exist. This is an OFF-LOOP evaluation harness over built machinery.
contract: builder
write_scope:
  - scripts/dream_calibrate.py
  - tests/unit/test_dream_calibrate.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 150k
    rationale: >-
      An off-loop harness over already-built, TESTED machinery: the σ-graph sweep (`cluster_notes`/
      `similarity_matrix`/`MirrorGraph`) + running `dream_v2` at candidate σ into SCRATCH stores
      (inject-a-scratch-store pattern straight from `tests/integration/test_dream_v2.py`). No new math,
      no live-store/config write, no live-loop wiring. Bigger than a pure σ-sweep (adds the dream_v2
      runner + report + a fake-synth test) but all reuse. Self-driven ~0.5–0.8× (bp-039 = 0.71×). No
      fable. NB the RUN's 27b synthesis is LOCAL Ollama compute (~290s/cluster), NOT Claude budget.
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/findings/finding-0079.md
  - core/dreaming/dreamer.py
  - core/dreaming/rnd.py
  - core/dreaming/adjudicator.py
  - config/defaults.toml
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0079.md
---

# Build Plan — `dream-calibrate` (bp-040): an off-loop σ-sweep + full-dreamer (`dream_v2`) evaluation harness

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval** (owner-only `proposed → ready`, by hand). Warranted by **finding-0079** (σ re-calibration on
the clean graph) + the owner's 2026-07-15 directive to bring the **full dreamer** (`dream_v2` / the
`[dream_rnd]` topological R&D track) online. It implements **no new design**: the σ knob + its bound
`σ ∈ [0.55, 0.75]` (`config/defaults.toml:211`), and `dream_v2` itself (built, unit- + integration-
tested, `test_dream_v2_end_to_end`), already exist. The finding + directive are the warrant.

**OFF-LOOP + SCRATCH-ONLY (the owner's "see it off-loop first" ruling).** This harness runs the full
dreamer OUTSIDE the live cron loop and writes ONLY to a scratch directory + a report file — never
`data/derived.sqlite`, never `config/**`, never the live daemon. It exists so the owner can SEE how the
topological dreamer's output changes with connectivity (σ), and confirm it runs end-to-end, **before** a
separate follow-up plan wires it live (replacing Phase-7, the owner's ruling). Model tier **opus** for
the build; no fable, no xhigh. The harness's own dream synthesis is the **local 27b Ollama** model.

## 1. Objective

Produce, off the live loop and into a report, (a) a σ-connectivity sweep of the authored mirror graph
over `σ ∈ [0.55, 0.75]` (edges, components, near-threshold "bubble" pairs, surfaced candidate σ values),
and (b) the **full dreamer `dream_v2`'s output at a few candidate σ values** — the topological lenses,
adjudicated claims (confidence/methods/evidence), and the narrated dream texts — so the owner can see
how dreams change with connectivity and pick σ, with nothing written to the live store.

## 2. Context manifest

Read whole, in order:

1. `docs/findings/finding-0079.md` — the σ warrant (sweep [0.55,0.75], record graph + dreams, pick by
   the curve, repeatable). The owner extends it: use the FULL dreamer (`dream_v2`), replace Phase-7.
2. `core/dreaming/dreamer.py` — BOTH dreamers. `Dreamer` is a plain `@dataclass` (`:80-101`; fields
   `store, synthesize, derived, snapshots, edge_store, attestor, threshold, min_cluster_size,
   max_clusters, clusterer, judge`). **`dream_v2(self, *, config=None) -> list[Theme]`** (`:168`): σ =
   `config.dream_rnd.sigma` (`:185,196`); writes per kept candidate to `self.derived.add(...)` (`:229`),
   optional `self.attestor.emit` (`:222`, skip with `attestor=None`), one `self.snapshots.write` (`:243`,
   skip with `snapshots=None`). `Theme` (`:72-77`) = `{titles, summary, check, artifact}`. `clusters()`
   (`:104`, the Phase-7 read) + `cluster_notes` (the retiring single-linkage). DO NOT use `build_dreamer`
   (`:265` — it opens the LIVE stores); construct `Dreamer` directly with scratch sinks.
3. `core/dreaming/rnd.py` — `require_rnd_enabled(config)` (`:31`) reads `config.dream_rnd.enabled`, raises
   `DreamRnDDisabledError` when false. Enable IN-PROCESS (no file edit) via `dataclasses.replace` (the
   test idiom, `tests/integration/test_dream_v2.py:71-73`).
4. `core/dreaming/adjudicator.py` — R1: `DreamLogEntry` (`:46-58`: statement, methods, evidence,
   grounding g, agreement, confidence c, terminates_in_authored, members); confidence law `:118`;
   **`run_dream_rnd(view, derived, *, config)`** (`:138`) — the MODEL-FREE path that persists
   `DreamLogEntry`s as `DREAM_LOG` artifacts (no synthesis call) — the deterministic per-σ structural view.
5. `core/dreaming/interpreters.py` — the R0 panel: `Claim` (`:67-76`); the 8 live lenses (community,
   centrality, density, bridge=Forman–Ricci, hole=persistent H₁, theme=DC-SBM, thread=Hodge harmonic,
   tension=frustrated triangles); `change_point` is an honest empty-emitter (`:269`, non-blocking).
6. `core/dreaming/graph.py` — `MirrorGraph.build(view, *, sigma)` (`:33`, σ-adjacency `sim >= sigma`) —
   the σ-graph dream_v2 reasons over; the connectivity the sweep reports.
7. `core/dreaming/cluster.py` — `note_centroids(rows)` (`:57`), `similarity_matrix(notes)` (`:80`,
   cosine), `cluster_notes(notes, *, threshold, min_size)` (`:89`), `near_duplicate_pairs` (`:129`) — the
   pure pieces for the σ-connectivity sweep (edges/components/bubble pairs).
8. `config/loader.py` — `DreamRndConfig` (`:87-102`: enabled, sigma, min_degree, …, sbm_k_max); it is a
   field of `Config` (`:263`). `load_config()` / `get_config()`. The harness reads config, edits NONE.
9. `tests/integration/test_dream_v2.py` — the pattern to reuse: `_RowSource` (`:44`, duck-typed
   `all_rows`), `_CountingSynth` (`:55`, a fake synthesizer for model-free tests), `dataclasses.replace`
   flag-enable (`:71`), scratch `DerivedStore(tmp_path/…)` (`:80`), and the end-to-end assertions (`:91`).
10. `scripts/reembed_bodyonly.py` — the CLI/report scaffolding + `_artifact_to_dict` JSON serialization
    (`:60`) to reuse; but bp-040 is OFF-LOOP (no `reset`, no live-store write, no re-embed).

## 3. Investigation & grounding

- **Q1 — Is `dream_v2` end-to-end complete? YES.** `test_dream_v2_end_to_end` (`tests/integration/
  test_dream_v2.py:91-119`) runs it green: `themes` non-empty, all self-checks pass, one `DREAM` artifact
  per theme (INTERPRETED, `derived_from ⊆ authored`, `data.loop=="v2"`, `0 < confidence ≤ 1`, methods
  non-empty), `snapshots.count()==1`. All 8 lenses are implemented; `change_point` returns `[]` by design
  (`interpreters.py:269`) and does not block. **The tension lens** only fires with a signed `edge_store`
  injected (`interpreters.py:301`); absent one, it honestly emits nothing (not a bug). So dream_v2 runs
  off-loop as-is; the harness may pass `edge_store=None` (v1) — tension simply stays quiet.

- **Q2 — Can it run off-loop without touching the live store? YES.** Construct `Dreamer` directly (NOT
  `build_dreamer`) with `derived=DerivedStore(scratch/"derived.sqlite")`, `snapshots=None`, `attestor=
  None`, `edge_store=None` (`test_dream_v2.py:80` idiom). Every write sink is a constructor field, so all
  writes land in scratch. `store` is duck-typed (`all_rows(provenances=…)`) — feed the live `VectorStore`
  READ-ONLY (dream_v2 only reads it via `MirrorView.project`). `[grounds: dreamer.py:80-101,186,229-247.]`

- **Q3 — Enabling `[dream_rnd]` off-loop.** In-process only: `cfg = dataclasses.replace(load_config(),
  dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True, sigma=<σ>))` (`test_dream_v2.py:71-73`).
  **The on-disk `config/defaults.toml` flag stays `false`** — this harness never flips the live flag (that
  is the follow-up live-wiring plan, owner-gated). So running the harness does NOT enable dream_v2 in the
  daemon.

- **Q4 — σ for dream_v2 vs the sweep.** dream_v2 reads σ from `config.dream_rnd.sigma` (`dreamer.py:196`
  → `MirrorGraph.build(view, sigma=rnd.sigma)`), and σ propagates to the whole panel (`sim_floor`,
  community threshold). So "dream_v2 at σ" = rebuild the config with `dream_rnd.sigma=σ`. The σ-CONNECTIVITY
  sweep (Item 1) reports the same σ-adjacency (`sim >= σ`) dream_v2 clusters over — a dreamer-agnostic
  connectivity map. (Phase-7 single-linkage clusters are reported only as a reference; Phase-7 is retiring.)

- **Q5 — Model dependency + cost.** dream_v2's structural pipeline (graph→panel→adjudicate) is
  deterministic/model-free, but each kept candidate calls `self.synthesize` = the **local 27b**
  (`~290s/cluster`, `cron.py:12`). So NARRATED dreams need the model pulled; the MODEL-FREE structural
  claims (lenses, holes/threads/bridges, confidence) come from `run_dream_rnd`/the panel with NO model.
  The harness offers both: cheap deterministic structural sweep across the grid + narrated dreams at a few
  candidates. Corpus = 13 notes; a candidate run is ≤ `max_clusters=8` syntheses.

**Additional risks:** (a) Ollama contention — running the 27b while the daemon also dreams risks RAM
eviction (finding-0069). MITIGATION: the harness prints a "run with the daemon idle/down" note; it does
NOT control the daemon. (b) `run_dream_rnd` writes `DREAM_LOG` artifacts — point it at a SCRATCH store too.

## 4. Reconciliation

`N/A — nothing corrected or extended.` The harness is a NEW, additive, off-loop script; it reuses
`dream_v2`/`run_dream_rnd`/`cluster_notes` as libraries and changes no existing code path, no config, no
live store. The LIVE-wiring of dream_v2 (flipping the flag, retiring Phase-7 from cron) is a SEPARATE
follow-up plan (§12) — this plan touches none of it.

## 5. Write scope

- `scripts/dream_calibrate.py` — **NEW**: the off-loop σ-sweep + dream_v2 evaluation harness.
- `tests/unit/test_dream_calibrate.py` — **NEW**: deterministic tests (synthetic centroids + a FAKE
  synthesizer), asserting scratch-store isolation (no `data/**` write) + report shape.

**Deliberately OUT of scope:** `config/**` (never flip `[dream_rnd] enabled` on disk, never write the σ
value — both are owner-gated; the harness enables the flag ONLY in-process for its own run); `core/**`
(dreaming machinery reused as a library, never modified); `scheduler/**` + `ops/lifecycle/launcher.py`
(the LIVE wiring of dream_v2 is the follow-up plan, not this); `data/derived.sqlite` + any live store
(scratch dir only); the denylist. The harness NEVER writes the live derived store, config, or cron.

## 6. Interfaces pinned inline

```python
# scripts/dream_calibrate.py — OFF-LOOP. Reuse reembed_bodyonly.py's CLI/report/_artifact_to_dict
# scaffolding, but NO reset / NO live-store write / NO daemon control.

import dataclasses
from config.loader import load_config
from core.stores.derived import DerivedStore
from core.dreaming.dreamer import Dreamer, Theme
from core.dreaming.cluster import note_centroids, similarity_matrix, cluster_notes
from core.dreaming.graph import MirrorGraph
from core.dreaming.adjudicator import run_dream_rnd     # model-free structural claims (DREAM_LOG)
from core.stores.vectorstore import open_vector_store

# --- Item 1: σ-connectivity sweep (pure, read-only, no model) ---
def sweep_connectivity(notes, *, lo=0.55, hi=0.75, step=0.01, band=0.02) -> list[SigmaRow]:
    """Per σ from FIXED centroids: n_edges (#pairs cos>=σ, the MirrorGraph adjacency), n_components,
    component sizes, near-threshold 'bubble' pairs (σ-band <= cos < σ+band). Pure fn of the cosine
    matrix; edges non-increasing in σ. Also surfaces candidate σ (where component structure transitions)."""
    ...

# --- Enable dream_rnd IN-PROCESS for one σ (never touches config files) ---
def _rnd_config_at(sigma: float):
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True, sigma=sigma))

# --- Item 2: run the FULL dreamer off-loop at a σ, into SCRATCH stores ---
def dream_v2_at(sigma: float, *, scratch_dir, synthesize, structure_only: bool):
    """structure_only=True  -> run_dream_rnd(view, DerivedStore(scratch/'log.sqlite'), config=cfg):
                               MODEL-FREE — persists DreamLogEntry as DREAM_LOG; read them back for the report.
       structure_only=False -> Dreamer(store=open_vector_store(cfg) [READ], synthesize=synthesize,
                               derived=DerivedStore(scratch/'dreams.sqlite'), snapshots=None, attestor=None,
                               edge_store=None).dream_v2(config=_rnd_config_at(sigma)) -> list[Theme];
                               capture each Theme's summary (dream text)+artifact.data (statement/confidence/
                               methods/grounded). NEVER data/derived.sqlite."""
    ...
# synthesize (narrated mode): lambda messages: build_model_server(cfg).chat("synthesis", messages)
#   (test_dream_v2_live.py:51). For a fast dry-run / tests: a fake synth echoing titles (_CountingSynth).

# main(): open vector store READ -> MirrorView centroids -> sweep_connectivity() (print table + JSON);
#   then for each --candidate σ: dream_v2_at(..., structure_only per --no-model) -> append to a markdown
#   + JSON report at --out. Flags: --lo/--hi/--step, --candidates a,b,c, --no-model, --out DIR.
#   Prints corpus size + "run with the daemon idle/down (Ollama contention, finding-0069)".
```

## 7. Items

### Item 1 — σ-connectivity sweep (pure, read-only) + candidate surfacing
- **Objective:** `sweep_connectivity(notes, *, lo, hi, step, band)` — per σ from fixed centroids:
  `n_edges` (σ-adjacency), `n_components` + sizes, near-threshold bubble pairs; surface candidate σ
  (component-structure transition points). Pure function of the cosine matrix; + a `main()` path that
  reads the live vectors READ-ONLY and prints a table + writes JSON.
- **Files:** `scripts/dream_calibrate.py`, `tests/unit/test_dream_calibrate.py`.
- **Acceptance test:** over a synthetic fixture (a tight triple @~0.7, a bubble pair @~0.61, an isolate),
  `sweep_connectivity(lo=0.55,hi=0.75,step=0.05)`: `n_edges` non-increasing in σ; the bubble pair in
  `near_threshold` at σ≈0.62, absent far away; components merge/split at the right σ; candidate σ includes
  the transition. A live smoke asserts ZERO writes to `data/**`/`config/**` (mtime unchanged).
- **Falsifier:** `n_edges` rises with σ (threshold-sense bug); OR any write to a live store/config.
- **Invariant(s):** read-only/pure; AUTHORED-only (via `MirrorView`); deterministic (fixed grid, no random).
- **Touches stored data?** No.  **Parallelizable?** No (Item 2 shares the harness).

### Item 2 — off-loop `dream_v2` runner at candidate σ (SCRATCH-only)
- **Objective:** `dream_v2_at(sigma, …)` — enable `dream_rnd` IN-PROCESS (`dataclasses.replace`), run the
  full dreamer into SCRATCH stores (`derived=DerivedStore(scratch/…)`, `snapshots=None`, `attestor=None`,
  `edge_store=None`), and capture per-candidate: the narrated dream text (`Theme.summary`) + the structural
  fields (`artifact.data`: statement/confidence/methods/grounded). A `structure_only`/`--no-model` mode
  uses `run_dream_rnd` (model-free) for the deterministic lens/claim view across the grid.
- **Files:** `scripts/dream_calibrate.py`.
- **Acceptance test:** with a FAKE synthesizer (echo titles, like `_CountingSynth`) and a `tmp` scratch
  dir, `dream_v2_at(0.60, structure_only=False)` returns themes, writes ONLY under the scratch dir, and
  `data/derived.sqlite` is byte-unchanged (assert mtime/size); the captured report rows carry
  `confidence ∈ (0,1]`, non-empty `methods`, and `derived_from ⊆` the authored digests; `structure_only=
  True` produces the same claims WITHOUT any synth call (call count 0). A live/manual run at 2–3 candidate
  σ with the real 27b is the owner-facing artifact (documented in §12, not a unit test).
- **Falsifier:** any write to `data/derived.sqlite`/config/the live daemon (off-loop contract broken); OR
  enabling `dream_rnd` on disk; OR the run needs `build_dreamer` (which opens live stores) instead of a
  directly-constructed `Dreamer`.
- **Invariant(s):** off-loop + scratch-only; INTERPRETED provenance preserved (dream_v2's structural
  firewall); AUTHORED-only reads; the on-disk `[dream_rnd] enabled` stays `false`.
- **Touches stored data?** No (scratch dir only; live vectors read-only).  **Depends on:** Item 1.

### Item 3 — the report + CLI wiring
- **Objective:** `main()` — read the live vectors READ-ONLY, run Item 1's sweep (table + JSON), then for
  each `--candidate` σ run Item 2 and append a **markdown + JSON report** (per σ: the connectivity row +
  the dreams/claims) to `--out`. Flags `--lo/--hi/--step/--candidates/--no-model/--out`. Print corpus size
  + the "daemon idle/down" note.
- **Files:** `scripts/dream_calibrate.py`.
- **Acceptance test:** `uv run scripts/dream_calibrate.py --candidates 0.56,0.60,0.62 --no-model --out /tmp/rep`
  produces a well-formed markdown+JSON report with one section per candidate σ (structural claims, since
  `--no-model`), the σ-table, and the corpus count; ZERO writes outside `--out` + the scratch dir.
- **Falsifier:** the report writes into `data/**` or `config/**`; OR `--no-model` still calls the 27b.
- **Invariant(s):** all output confined to `--out` + scratch; read-only over live data.
- **Touches stored data?** No.  **Depends on:** Items 1, 2.

## 8. Math carried explicitly

- **σ-adjacency connectivity** — *measures:* the authored similarity graph `E(σ) = {(u,v): cos ≥ σ}` and
  its connected components — the "levels of connectivity" the owner wants to reason about
  (`MirrorGraph.build`, `graph.py:39`). *valid when:* centroids are unit-normalized (they are). *fails its
  keep if:* `n_edges(σ)` is not monotone non-increasing in σ.
- **dream_v2's adjudicated confidence** `c(κ) = min{1, γ^d·g·(1+λ(|Agr|−1))}` (`adjudicator.py:118`) —
  *measures:* how much a structural claim, corroborated by `|Agr|` independent lenses and grounded `g` in
  authored notes, is worth surfacing. *valid when:* it terminates in authored evidence (`g>0`; else
  `c=0`). *fails its keep if:* a surfaced dream's `derived_from` is not a subset of authored digests (the
  INTERPRETED firewall broken) — the harness asserts `derived_from ⊆ authored` per captured theme. **The
  harness does NOT re-derive or alter this math** — it runs the built `dream_v2`/`adjudicate` and reports.

## 9. Non-goals

- **No live-loop wiring.** Flipping `[dream_rnd] enabled` on disk, wiring `dream_v2` into
  `scheduler/cron.py`, and retiring Phase-7 `dream()` are the SEPARATE follow-up plan (§12), owner-gated.
  This harness enables the flag ONLY in-process for its own off-loop run.
- **No live-store / config write.** All output → `--out` + a scratch dir. `data/derived.sqlite`,
  `config/local.toml` (the σ value), and `config/defaults.toml` (the flag) are untouched — the σ value is
  the owner's hand edit after reading the curve.
- **No auto-recommended σ.** The harness reports the connectivity curve + the dreams at candidates; the
  owner picks σ (a taste call on their own corpus, finding-0079).
- **No re-embed.** The embeddings are fixed (body-only since bp-036); σ only re-clusters.
- **No new dreaming math or lenses.** It runs the built `dream_v2`/`run_dream_rnd`; it neither
  re-implements the panel nor "fixes" the `change_point` empty-emitter (that is dream_v2's own backlog).
- **No tension-lens edge store (v1).** `edge_store=None` — the tension lens stays quiet; wiring a signed
  contradiction store is a later concern, not this evaluation harness.

## 10. Stop-and-raise conditions

- `dream_v2` cannot run off-loop without a live store / the daemon → **file a `codebase` finding**; the
  off-loop contract (scratch stores, directly-constructed `Dreamer`) must hold — do not fall back to
  `build_dreamer` or the live daemon.
- A captured dream's `derived_from` is not ⊆ authored digests → **stop, file a `codebase` finding**: the
  INTERPRETED/authored firewall is load-bearing (do not paper over it).
- The harness would need to flip `[dream_rnd] enabled` on disk or write config to run → **must not**; the
  flag is in-process only, and the σ value is the owner's hand edit.
- Running reveals `dream_v2` is NOT actually end-to-end (a stub fires) despite the passing test → **file a
  `spec-defect` finding** and surface it; the follow-up live-wiring plan must not proceed on a broken v2.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Narrated dreams vs model-free claims per σ | BOTH — model-free structural claims across the grid (cheap) + narrated dreams at a FEW `--candidates` (27b) | narrate every σ (rejected: ~290s/cluster × grid — impractical) | the owner wants narrated dreams at more σ values (a longer local run) |
| Tension lens (signed edges) | OFF (`edge_store=None`) — the lens stays quiet | wire a contradiction edge store now (deferred: not needed to evaluate σ/connectivity) | the owner wants the tension/contradiction lens in the evaluation |
| Where the harness lives | `scripts/dream_calibrate.py` (a script, like `reembed_bodyonly.py`) | a mirror/dreamer method (deferred: an eval tool is not a library method) | a consumer needs the sweep as a library call |
| Auto-recommending a σ | NO — report only; the owner picks | a knee-of-curve heuristic (rejected: a taste call on the owner's corpus, finding-0079) | the owner asks for a heuristic pick |

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (pure σ sweep — zero I/O) → **Item 2** (off-loop dream_v2 runner, scratch
stores) → **Item 3** (report + CLI). All in `scripts/dream_calibrate.py` + one new test file → **one
session, not parallel.** `depends_on: []`. Model **opus** (a harness over built, tested machinery — no
fable, no xhigh).

**After the build (owner-run, not this plan):** the OWNER (or the orchestrator, daemon idle) runs
`dream_calibrate` at a few candidate σ with the real 27b, reads the report (connectivity curve + how the
full dreamer's dreams change with σ), and picks σ.

**The follow-up this plan enables (NOT authored yet — graduate AFTER the owner sees the harness output):**
- **`bp-041` — wire the full dreamer live, replacing Phase-7** (owner ruling 2026-07-15). Flip
  `[dream_rnd] enabled = true` (owner-gated config), wire `dream_v2` into `scheduler/cron.py` +
  `ops/lifecycle/launcher.py` REPLACING the Phase-7 `dream()` handler, set the live σ (the owner's chosen
  value), and validate in the daemon. Warrant = this evaluation + the owner directive. `depends_on:
  [bp-040]`. Its open questions (settle at ITS graduation): whether to keep `dream()` as a fallback, the
  live snapshot/attestation wiring for v2, and the cadence — none inferred here.
