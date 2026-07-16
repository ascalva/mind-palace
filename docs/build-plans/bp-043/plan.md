---
type: build-plan
id: bp-043
alias: run-ledger-shadow
status: complete
design_ref:
  - docs/design-notes/evaluation-harness.md
contract: builder
write_scope:
  - core/stores/runledger.py
  - core/dreaming/shadow.py
  - scheduler/cron.py
  - tests/unit/test_runledger.py
  - tests/unit/test_shadow_runner.py
  - tests/integrity/test_shadow_isolation.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
    rationale: >-
      A NEW SQLite/WAL ledger (two append-only tables, content-addressed claim_id, novel-on-insert)
      + a NEW ShadowRunner that drives BOTH dream pipelines over one snapshot, writes claims to the
      ledger AND the registered metric readings (guardrails + dream_v2 structural axes) through the
      E1 eval store + a trough job + dedup/isolation tests. Touches EXISTING code lightly (reads the
      two dream pipelines, adds one cron job) so it carries a real §3 grounding pass. Larger than
      bp-039 (240k est / 170k actual): the pipeline-driving + digest/fingerprint + the metric-
      evaluation-into-eval-store surface. Calibrated ~260k opus. Deterministic — NO fable, NO xhigh.
      Self-driven ~0.5–0.8×; delegated ~1.6×.
  actual:
    model: opus
    tokens: ~180k
    ratio: ~0.82
    dollars: ~13         # APPROX per-plan share of the $25.01 session (larger build + first-delegation
                         # setup + finding-0086 review); drew ZERO credits (weekly-covered)
    session_delta: "DELEGATED supervised build (worktree-agent-a382dc69444c1797a). Builder
      self-reported usage (completion notification): 180,003 tokens, 89 tool-uses, ~20.5 min
      wall (1,227,159 ms), model claude-opus-4-8, single continuous pass (no fable/xhigh, not
      interrupted/degraded). ~180k / 220k front-matter est = 0.82× (vs the ~260k rationale =
      0.69×) — UNDER the ~1.6× delegated-wave margin (bp-020 1.50×, bp-026 1.56×): a fully-pinned
      §6, greenfield ledger + a runner following the model-free path the plan already specified,
      so little rediscovery. Orchestrator supervision (review + independent 5-leg gate + merge)
      is additional main-loop context not counted here. Dollar/session-delta backfill owed from
      an owner /usage read at session end (bp-042 precedent, commit 6aa6fa6)."
    week_delta: "MEASURED (owner /usage, session end): whole session $25.01 / 239.4k opus output,
      week 1%->3% (+2%) for BOTH delegated builds + all orchestrator supervision; drew ZERO usage
      credits (81%/$122.94 UNCHANGED — weekly-covered, same as the bp-042/045 session). Per-plan $
      is an honest split, not an isolated measurement (bp-039/bp-042 precedent)."
    loc: "~1046 added (runledger 205 + shadow 260 + cron +23 + 3 test files ~397 + journal 113 +
      finding-0086 48); 0 existing runtime lines changed (cron.py purely additive — enqueue_dream/
      dream_handler/cron_handlers untouched, the whole-plan falsifier)"
    # GREEN attested SEPARATELY on the MERGED tree (5-leg): ruff `.` PASS; mypy `core agents eval
    # ops scheduler scripts` == 0 (192 files, 190→192 = +runledger +shadow); argless mypy == 69
    # UNCHANGED (baseline HELD); ops.type_gate OK; pytest -q -m 'not live' == 1202 passed / 7
    # skipped / 9 deselected(live) / 0 failures (+17 new: 7 runledger + 5 shadow + 5 isolation).
    # Falsifiers held: claim_id excludes surface_text+confidence (content-address); novel cross-run
    # not per-run; one corpus_digest for both pipeline runs; live derived store row-count unchanged;
    # [dream_rnd] disk flag still False; model-free (synthesize never called); isolation AST tooth
    # green with two negative controls. Process: finding-0086 (structural_axes.* registry gap,
    # spec-fidelity, builder-resolved — registration owed to a follow-up with registry.py in scope);
    # shadow machinery built but NOT activated in the live loop (cron_handlers untouched) — the
    # deploy-gated RUN wires SHADOW_KIND->shadow_handler(runner) + calls enqueue_shadow on a tick.
depends_on:
  - bp-042
parallelizable_with:
  - bp-044                           # disjoint write_scope (core/stores + core/dreaming vs eval/harness/report)
created: 2026-07-15
updated: 2026-07-16
started: 2026-07-16
completed: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md   # the L1 protocol annex (carried)
  - core/dreaming/dreamer.py
  - core/dreaming/interpreters.py
  - scheduler/cron.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `run-ledger-shadow` (bp-043): the run ledger + shadow runner (E2, carried from Track L L1)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval**. Authority-to-act (owner ratified `dn-evaluation-harness` and directed graduation) is
separate from the readiness blessing (owner-only `proposed → ready`) — no agent flips readiness.

Graduated from ratified `dn-evaluation-harness` §3 **E2** (*"the run ledger + shadow runner (Track L
L1, carried): `core/stores/runledger.py`, `ShadowRunner` (both pipelines, one snapshot, one digest),
trough wiring, content-addressed claims. Live surface provably unchanged."*). The L1 stage shapes
are the **protocol annex of record** in the superseded `live-adoption-and-longitudinal-harness.md`
§2 — carried verbatim where the harness note does not amend. This plan builds the ledger + runner;
it wires NO new dreamer behavior and flips NO flag. Model **opus**; **no fable, no xhigh**.

**The load-bearing property:** the two dream pipelines are two derived functors over one raw corpus
(family-2 discipline); the same corpus digest in yields two diffable claim sets out. The whole-plan
falsifier: **the live dream surface changes** — building this plan alters what the nightly `dream()`
produces or writes (it must not: shadow reads only a `MirrorView` snapshot and writes only the
ledger).

## 1. Objective

Give the harness an append-only **run ledger** (`core/stores/runledger.py`, SQLite/WAL,
scheduler-single-writer) with `dream_runs` + `dream_claims`, content-addressed `claim_id` and
`novel`-on-insert, and a **`ShadowRunner`** — the harness's single-config *run producer* — that
executes BOTH dream pipelines (Phase-7 `dream()` + topological `dream_v2()`) against ONE `MirrorView`
snapshot in one trough window, writing **claims to the ledger** and the **registered metric readings
(guardrails + dream_v2 structural axes) through the E1 eval store**, with the live dream surface
provably unchanged.

**Scope reconciliation (a soft seam the note draws, resolved here).** `dn-evaluation-harness` §3 says
the first overnight dual-dreamer A/B needs `E1 + E2 + E5(A2) + E4` (no E3a), while §2.9 calls that
run "the first *sweep* instance" (§2.6 = E3a). Reconciled: the milestone A/B is the **single-config**
dual-pipeline comparison — ONE snapshot, phase7 vs dream_v2, the built guardrails + dream_v2's
structural axes — produced by this ShadowRunner (annex "one snapshot, one digest"). The **σ-grid**
version (`sweep.dreamer-sigma-ab`, a grid over the σ lever with the admissibility filter and
`TuningProposal`) is E3a's declarative sweep engine, deferred. This runner is the single-config
special case; E3a generalizes it. The σ-sweep-inside-shadow (annex option) is therefore **not** built
here (§11).

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/evaluation-harness.md` — **§2.2** ("The run ledger — carried from Track L L1
   … claims content-addressed `claim_id = sha256(kind ‖ canonical(support_set) ‖ polarity)`,
   excluding surface wording and confidence … `novel` computed on insert; re-emitted claims inherit
   prior verdicts. Build status … NOT built"), **§2.1** (the unified key — `config_fingerprint`,
   `corpus_ref`), **§2.10** (eval-isolation + mirror-firewall the shadow run honors).
2. `docs/design-notes/live-adoption-and-longitudinal-harness.md` §1 (the content-addressed-claims
   addition, `:60-66`) and **§2 (L1)** (`:70-101`) — the protocol annex: the exact `dream_runs` /
   `dream_claims` column lists, the "two functors, one raw" principle, the σ-sweep-inside-shadow
   option, and the "Done when" checklist. **This is the carried spec — honor its columns verbatim.**
3. `core/dreaming/dreamer.py` — the two pipelines: `Dreamer.dream()` (Phase-7, `:126`) and
   `dream_v2()` (`:168`, gated `[dream_rnd] enabled`, produces `Theme`s from adjudicated entries),
   and `build_dreamer` (`:265`). The ShadowRunner drives both against one snapshot; note dream_v2's
   in-process enable pattern (bp-040 journal: `replace(cfg.dream_rnd, enabled=True)`; NEVER flip the
   disk flag).
4. `core/dreaming/interpreters.py` — the `Claim` type (`:67`: `method, statement, support (authored
   digests), data`; **no confidence** — ranking is the adjudicator's) and the interpreter methods
   (`COMMUNITY/THEME/HOLE/THREAD/TENSION`, `:60-64`) that become the `kind` in `claim_id`. `dream_v2`
   collects claims via `collect_claims`; the Phase-7 path's claims map from `community_interpreter`
   (`:83`).
5. `scheduler/cron.py` — the trough wiring precedent: `DREAM_KIND = "dream"` (`:35`),
   `enqueue_dream` (`:61`), `handlers()` (`:57`), background-priority + `HEAVY_TIERS` foreground gate.
   The shadow job is a NEW additive enqueuer, background priority; the live `enqueue_dream` is
   untouched.
6. `core/stores/telemetry.py` — the SQLite/DuckDB store-shape precedent (writer/reader split,
   `open_*` factory). (The run ledger is SQLite/WAL per the A-4 routing pin, not DuckDB.)
7. `docs/build-plans/bp-039/plan.md` — house style.

## 3. Investigation & grounding

- **Q1 — Does `core/stores/runledger.py` exist? NO / confirmed.** `ls core/stores/runledger.py` →
  no such file (2026-07-15); `grep ShadowRunner` → 0 hits. The note's "NOT built" claim holds; Track
  L's "Built:" headers were spec, not reality. Greenfield store + runner.
- **Q2 — Do `config_fingerprint` / `corpus_digest` exist to reuse? NO.** `grep config_fingerprint\|
  corpus_digest\|merkle` over `core/ ops/ scheduler/` → 0 hits. **The code does not settle their
  computation — this plan settles it (§6):** `corpus_digest` = Merkle root over the `MirrorView`
  snapshot's chunk digests (the mirror rows already carry `digest` — `dreamer.py:110` projects them);
  `config_fingerprint` = sha256 of the resolved dreaming lever values (`ops/levers.py` — the four
  `[dreaming]` levers; the full tuning manifest is E3's, so here fingerprint the *dreaming* config
  subset and document that E3 widens it). If the builder finds the mirror rows carry no stable
  digest, STOP and file a `codebase` finding (§10).
- **Q3 — The claim `kind` / `support_set` / `polarity` for `claim_id`.** `kind` = the interpreter
  `method` (`interpreters.py:60-64`); `support_set` = `Claim.support` (authored digests), canonicalized
  = `sorted(set(support))`; **polarity is NOT a field on `Claim` today** (`interpreters.py:67-76`).
  **The code does not settle polarity — this plan settles it:** polarity ∈ {`+`, `−`} derived from
  the method (TENSION/frustration = `−`; THEME/HOLE/THREAD/COMMUNITY = `+`), pinned as a small
  method→polarity map in `runledger.py` and documented; a method with no mapping defaults `+` and is
  flagged. If a future interpreter needs a genuine per-claim polarity, that is a `Claim` extension
  (parked, §11), not this plan.
- **Q4 — Can the ShadowRunner drive both pipelines without touching the live store?** YES — the
  bp-040 journal grounds the off-loop pattern: construct a `Dreamer` (or reuse `build_dreamer`'s
  wiring) with a **scratch** `DerivedStore` and read-only `MirrorView` over the live `VectorStore`;
  `dream_v2` enabled in-process via `replace(cfg.dream_rnd, enabled=True)`, never the disk flag. The
  shadow run extracts *claims* (not stored dreams), so it need not even persist a scratch derived
  store — it reads the mirror, runs the interpreters/adjudicator, and writes claims to the ledger.
- **Q5 — Single-writer discipline.** `scheduler/__init__.py:4` — "One supervisor owns the SQLite
  queue (single-writer)." The run ledger follows the same discipline (SQLite/WAL, the scheduler is
  its writer in the trough job). The unit tests write to a tmp ledger directly; only the trough
  handler writes the live ledger.

- **Q6 — Where do the A/B's structural axes come from, and how are they keyed per run?**
  `dream_v2` step 10 (`dreamer.py:243-247`) writes a `StructuralSnapshot` to `self.snapshots` (β₀ via
  `n_holes`, `fiedler`, `frustration`, `mean_forman`, `frac_neg_curv`, `min_conductance`,
  `harmonic_persistence_total` — `core/complex/temporal.py:63-80`) **only when `snapshots is not
  None`** (E5(A2)/bp-045 wires that in `build_dreamer`; the ShadowRunner sets it on its own
  `Dreamer`). `StructuralSnapshot` carries **no config/run key** — only `taken_at` + an
  auto-`snapshot_id` (`temporal.py:64-67`). **The code does not settle per-run A2 keying — this plan
  settles it WITHOUT a schema change:** after each dream_v2 run the runner calls
  `SnapshotStore.latest_structural()` (`temporal.py` — returns a `dict[str,float]`) and writes each
  axis as a keyed `Reading(metric_name="structural_axes.<axis>", type_tag="Inv", key=<this run's
  §2.1 key>)` into the E1 eval store. The `structural.duckdb` store is unchanged (no new column);
  attribution lives in the eval store's key, where it belongs. phase7 (`dream()`) computes no
  snapshot, so `structural_axes.*` rows are dream_v2-only (catalog row 6 — "written only in dream_v2").

**Additional risks surfaced during reading:** (a) the σ-sweep-inside-shadow (annex §2) is an
*option*, not required for E2 — the first systematic σ sweep is E3a's `sweep.dreamer-sigma-ab`; this
plan records ONE run per pipeline per invocation (parked, §11). (b) `novel` is a per-`claim_id`
property across ALL prior runs — the insert must query the ledger, so `dream_claims` needs an index
on `claim_id`. (c) The registered guardrail metrics the runner evaluates (drift `D`, golden recall)
are the *built* instruments (`eval/drift.py`, `eval/golden.py`); the runner references them by their
E1 registry names, never re-implementing them.

## 4. Reconciliation

- **`scheduler/cron.py` — EXTENDED with a shadow trough job, announced as an extension
  (cross-reference-on-extension), NOT a correction.** The live `enqueue_dream` (`:61`) and its
  handler are **unchanged**; a new `enqueue_shadow` (background priority, trough-gated) is added
  beside it, with a one-line comment cross-referencing `core/dreaming/shadow.py`. The live nightly
  dream keeps writing the interpreted store exactly as today (the whole-plan falsifier guards this).
- **`live-adoption-and-longitudinal-harness.md` is `superseded` (immutable, A8).** This plan cites
  its §2 as the carried protocol annex; it edits it nowhere. `dn-evaluation-harness` frontmatter
  (`not-built`) becomes partially stale on build — batched to `owner-questions.md` on completion
  (the bp-039 pattern). Every change is additive.

## 5. Write scope

- `core/stores/runledger.py` — **NEW**: `dream_runs` + `dream_claims` (SQLite/WAL), `claim_id`
  derivation + `novel`-on-insert, writer/reader split, `open_run_ledger(config)`.
- `core/dreaming/shadow.py` — **NEW**: `ShadowRunner` (both pipelines, one snapshot, claim
  extraction → ledger, registered metric readings → the E1 eval store). Imports
  `eval.harness.{store,registry}` (bp-042) — hence `depends_on: [bp-042]`.
- `scheduler/cron.py` — Item 7 only: add `enqueue_shadow` + handler entry; **no edit to
  `enqueue_dream`** or the live handler.
- `tests/unit/test_runledger.py`, `tests/unit/test_shadow_runner.py`,
  `tests/integrity/test_shadow_isolation.py` — **NEW**.

**Deliberately OUT of scope:** the eval-results store (E1/bp-042 — a *different* DuckDB store; the
ledger never writes there); the verdict store (`core/stores/verdicts.py` — already built, E6's
surface); the review REPL (E6); any σ-sweep engine (E3); flipping `[dream_rnd] enabled` on disk
(bp-041's job, owner-gated); the interpreted/derived store (shadow never writes it — the falsifier);
`eval/golden/**`, `CONSTITUTION.md` (denylist); every design note (immutable, A8).

## 6. Interfaces pinned inline

```python
# core/stores/runledger.py — the run ledger. SQLite/WAL, scheduler single-writer. Append-only.

# dream_runs — one row per (pipeline, snapshot) execution. Columns VERBATIM from the L1 annex (§2):
#   run_id TEXT PK, started_at TIMESTAMP, pipeline TEXT ("phase7" | "dream_v2"),
#   config_fingerprint TEXT, corpus_digest TEXT, node_count INT, edge_count INT,
#   duration_s REAL, spectral_stats_json TEXT
# dream_claims — one row per claim; claim_id content-addressed (§2.2):
#   claim_id TEXT, run_id TEXT FK, kind TEXT, confidence REAL, support_json TEXT,
#   surface_text TEXT, novel BOOLEAN     -- INDEX(claim_id) for the novel check (§3 risk b)

import hashlib, json

def claim_id(kind: str, support: tuple[str, ...], polarity: str) -> str:
    """content-address EXCLUDING surface wording + confidence (§2.2). Canonical support = sorted set."""
    canon = json.dumps(sorted(set(support)), separators=(",", ":"))
    return hashlib.sha256(f"{kind}‖{canon}‖{polarity}".encode()).hexdigest()

# polarity map (§3 Q3): TENSION -> "-"; COMMUNITY/THEME/HOLE/THREAD -> "+"; unknown -> "+" (flagged)

class RunLedger:
    def start_run(self, *, pipeline: str, config_fingerprint: str, corpus_digest: str,
                  node_count: int, edge_count: int, duration_s: float,
                  spectral_stats: dict) -> str: ...          # returns run_id
    def add_claim(self, run_id: str, *, kind: str, confidence: float,
                  support: tuple[str, ...], surface_text: str, polarity: str) -> bool: ...
                  # computes claim_id + novel (unseen across all prior runs); returns `novel`
    def runs(self, *, pipeline: str | None = None) -> list[dict]: ...
    def claims(self, *, run_id: str | None = None, novel_only: bool = False) -> list[dict]: ...
    def close(self) -> None: ...

def open_run_ledger(config=None) -> RunLedger: ...
```

```python
# core/dreaming/shadow.py — drive BOTH pipelines over one MirrorView snapshot; write ledger only.

from dataclasses import dataclass

@dataclass
class ShadowRunner:
    ledger: "RunLedger"
    def run(self, *, config=None) -> tuple[str, str]:
        """One snapshot, two runs (returns both run_ids). Steps:
          1. project ONE MirrorView over the live VectorStore; compute corpus_digest (Merkle over
             the rows' `digest`s) + config_fingerprint (sha256 of resolved [dreaming] levers).
          2. phase7: run the community-interpreter claims (the dream() clustering, model-free —
             NO synthesis, NO derived-store write); start_run(pipeline="phase7"); add each claim.
          3. dream_v2: enable IN-PROCESS (replace(cfg.dream_rnd, enabled=True)); collect_claims +
             adjudicate (model-free); start_run(pipeline="dream_v2"); add each claim.
          4. per run: write claims → the ledger; write registered metric readings → the E1 eval
             store — guardrails (drift D, golden recall) + dream_v2 `structural_axes.*` (from
             SnapshotStore.latest_structural(), §3 Q6), each keyed by this run's §2.1 key.
        The interpreted/derived store is NEVER written; no [dream_rnd] disk flag is flipped."""
        ...

# The eval-store write (bp-042 surface, §3 Q6): reference metrics by their registry name; key each
# Reading by this run's (spec_hash, corpus_ref=corpus_digest, config_fingerprint, seed).
#   from eval.harness.store import EvalKey, Reading, open_eval_store
#   from eval.harness.registry import get as metric_spec
#   store.put(Reading(key=k, metric_name="drift_D", value=D, type_tag="Inv", ...))
#   for axis, v in snapshots.latest_structural().items():
#       store.put(Reading(key=k, metric_name=f"structural_axes.{axis}", value=v, type_tag="Inv"))
```

Pinned current forms (verified 2026-07-15):
```python
# core/dreaming/interpreters.py:67 — the Claim (no confidence; support = authored digests)
@dataclass(frozen=True)
class Claim:
    method: str
    statement: str
    support: tuple[str, ...]
    data: dict[str, Any] = field(default_factory=dict[str, Any])
# methods (:60-64): COMMUNITY="community"? THEME="theme" HOLE="hole" THREAD="thread" TENSION="tension"
# scheduler/cron.py:35 — DREAM_KIND = "dream"; enqueue_dream(:61) -> synthesis tier, background
```

## 7. Items

### Item 5 — `core/stores/runledger.py`: the two tables + `claim_id` + `novel`-on-insert
- **Objective:** the SQLite/WAL ledger with `dream_runs` + `dream_claims` (columns verbatim, §6),
  `claim_id(kind, support, polarity)` content-addressing (excludes surface/confidence), the
  polarity map, `add_claim` computing `novel` (unseen `claim_id` across all prior runs), and the
  writer/reader split + `open_run_ledger(config)`.
- **Files:** `core/stores/runledger.py`.
- **Acceptance test:** the module imports; `mypy` stays 0; a smoke `start_run` + `add_claim`
  round-trips; two `add_claim`s with the same (kind, support, polarity) and DIFFERENT surface_text
  yield the same `claim_id`; the second returns `novel=False`.
- **Falsifier:** two claims differing only in `surface_text` or `confidence` get DIFFERENT
  `claim_id`s (content-addressing leaked surface wording — novelty/duplication become ill-defined);
  OR `novel` is computed per-run instead of across all prior runs.
- **Invariant(s):** append-only (no update/delete); SQLite single-writer discipline; the ledger
  holds no model, no network.
- **Touches stored data?** Yes — a new ledger file. Tests use a tmp path; no live store touched.
  **Parallelizable?** No (Items 6–7 build on it).

### Item 6 — `core/dreaming/shadow.py`: the `ShadowRunner` (both pipelines, one snapshot; ledger + eval-store writes)
- **Objective:** `ShadowRunner.run` — one `MirrorView` snapshot, `corpus_digest` +
  `config_fingerprint` computed, both pipelines run model-free (phase7 community claims + dream_v2
  adjudicated claims); **claims → the run ledger** and **the registered metric readings → the E1
  eval store** per run: the built guardrails (drift `D` via `eval/drift.py`, golden recall via
  `eval/golden.py`+`eval/metrics.py`) and dream_v2's structural axes (read from the SnapshotStore via
  `latest_structural()` — §3 Q6). Both run_ids returned. `dream_v2` enabled in-process, never the
  disk flag; the interpreted/derived store is never written.
- **Files:** `core/dreaming/shadow.py`, `tests/unit/test_shadow_runner.py`.
- **Acceptance test:** a shadow run over a small fixture mirror writes exactly two `dream_runs`
  (one per pipeline) sharing one `corpus_digest`, ≥1 `dream_claims` row, and keyed `Reading`s in the
  eval store for the registered guardrails + `structural_axes.*` (dream_v2 only), each carrying the
  §2.1 key with this run's `corpus_digest`/`config_fingerprint`; **the live derived store is
  unmodified** (row count before == after) and **no `[dream_rnd]` disk flag changed**; a second run
  over the same mirror marks re-emitted claim_ids `novel=False` and (eval store append-only-by-key)
  skips already-present metric cells.
- **Falsifier:** the shadow run writes to the interpreted/derived store, OR flips the `[dream_rnd]`
  disk flag, OR the two runs get different `corpus_digest`s for one snapshot, OR a metric `Reading`
  lands with a key that does not match its run's `corpus_digest`/`config_fingerprint` (the A/B split
  would then be unattributable).
- **Invariant(s):** the whole-plan falsifier (live dream surface unchanged); shadow reads only a
  `MirrorView` (firewall — non-negotiable #11); model-free (the synthesis model is never called in
  shadow — claims and metrics are deterministic); every registered metric referenced by name (no
  ad-hoc metric — E1's registry is the namespace).
- **Touches stored data?** Yes — writes the ledger (Item 5) and the eval store (bp-042). Reads the
  live mirror READ-ONLY; writes no interpreted store. Requires the row-count-before/after dry check.
  **Depends on:** Item 5, bp-042 (the eval store + registry).

### Item 7 — the shadow trough job + the isolation integrity tooth
- **Objective:** `enqueue_shadow` in `scheduler/cron.py` (background priority, trough-gated, beside
  the untouched `enqueue_dream`) + its handler; and the non-skippable integrity test proving shadow
  writes ONLY the ledger and reads only a `MirrorView`.
- **Files:** `scheduler/cron.py`, `tests/integrity/test_shadow_isolation.py`.
- **Acceptance test:** the shadow job enqueues at background priority and is foreground-gated exactly
  like `dream`; the integrity test asserts (by construction) no write path from `shadow.py` to the
  interpreted/derived store and no read path outside `MirrorView`; runs in the `integrity/` profile.
- **Falsifier:** the shadow handler runs at foreground priority (would contend with the owner), OR
  the isolation test finds a shadow write reaching the derived store — either fails red, not relaxed.
- **Invariant(s):** trough-only, background priority (§13); mirror firewall; eval isolation (§2.10).
- **Touches stored data?** The job writes the ledger in production; the test does not touch live
  stores. **Depends on:** Items 5, 6.

## 8. Math carried explicitly

- **Content-addressed `claim_id = sha256(kind ‖ canonical(support) ‖ polarity)`** — *measures:*
  claim identity as a function of *what the claim is about* (kind + authored support + sign), not how
  it was worded — so "the same tension, found twice" is one id. *valid when:* `support` is the set
  of authored leaf digests (stable, content-addressed) and canonicalization is order-insensitive
  (`sorted(set(...))`). *fails its keep if:* two genuinely-distinct claims collide to one id (support
  canonicalization too coarse), or one claim re-worded yields two ids (surface leaked into the hash)
  — novelty/duplication/verdict-carryover all rest on this and break with it.
- **`corpus_digest` = Merkle root over the snapshot's chunk digests** — *measures:* the exact corpus
  state a run scored, so two pipelines on "one snapshot" are provably comparable and a longitudinal
  curve knows what grew. *valid when:* every mirror row carries a stable content digest and the
  Merkle fold is deterministic (sorted leaves). *fails its keep if:* the same snapshot yields two
  digests across the two pipeline runs (non-determinism) — the A/B comparison is then unfounded.

The **guardrail metrics (drift `D`, golden recall) and the structural axes (β₀, Fiedler, frustration,
Forman curvature, conductance, harmonic persistence)** are **carried, not implemented here** — built
in `eval/drift.py`, `eval/golden.py`+`eval/metrics.py`, and `core/complex/temporal.py`. This plan
*references them by their E1 registry name* and *stores their readings*; their three-clause
field-guide entries live with their own instruments (catalog rows 2, 1, 6).

## 9. Non-goals

- **No σ-sweep** — the annex's "σ-sweep inside shadow" option is NOT built here; the first systematic
  sweep is E3's `sweep.dreamer-sigma-ab` (parked, §11).
- **No verdict surfacing / review REPL** (E6) — claims land in the ledger; judging them is L2.
- **No flag flip** — `[dream_rnd] enabled` stays OFF on disk; the shadow run enables dream_v2
  in-process only. Wiring dream_v2 *live* is bp-041, owner-gated.
- **No eval-results-store write** (E1) — the ledger is a distinct SQLite store; it never writes the
  DuckDB eval table.
- **No per-claim polarity field on `Claim`** — polarity is derived from method (§3 Q3); a genuine
  per-claim polarity is a future `Claim` extension.

## 10. Stop-and-raise conditions

- The mirror rows carry no stable digest for the Merkle `corpus_digest` → **STOP, file a `codebase`
  finding** (§3 Q2): the digest is load-bearing for the whole comparison; do not invent an unstable one.
- The ShadowRunner cannot run a pipeline without writing the interpreted store → **STOP, file a
  `codebase` finding**: the off-loop/scratch premise is wrong and needs re-grounding (the falsifier).
- A claim kind appears with no polarity mapping and no sensible default → **file a `spec-defect`
  finding** (the polarity map is under-specified for that interpreter), park that kind, continue.
- The plan does not fit one session → **file a `spec-defect` finding and PARK**; the orchestrator
  re-graduates.
- Any blessing flip → **must not**.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| σ-sweep inside shadow (annex §2 option) | not built; one run per pipeline per invocation | build the σ-sweep here (rejected: it is E3's `sweep.dreamer-sigma-ab`; would duplicate the sweep engine) | E3 (bp-04x sweep engine) graduates |
| `config_fingerprint` scope | sha256 of the resolved `[dreaming]` levers only | fingerprint the full tuning manifest now (rejected: the manifest is E3's; premature) | E3's `config/tuning.toml` manifest lands → widen the fingerprint to the full resolved manifest |
| Per-claim polarity as a `Claim` field | derived from method (map in `runledger.py`) | add a `polarity` field to `Claim` (rejected: widens the interpreter contract for no current consumer) | an interpreter emits claims whose polarity is not a function of its method |
| Scratch derived-store persistence in shadow | none — shadow extracts claims, persists nothing but ledger rows | persist a scratch derived store per run (rejected: unnecessary I/O; claims are the unit) | a downstream consumer needs the full narrated dream, not just the claim |

## 12. Dependency & ordering summary

Blast-radius order: **Item 5** (new ledger store — lowest radius) → **Item 6** (the runner: reads
the live mirror read-only, writes the ledger + the E1 eval store) → **Item 7** (the trough job +
isolation tooth — touches `scheduler/cron.py` additively). One session, not parallel.
`depends_on: [bp-042]` — Item 6 imports `eval.harness.{store,registry}` to write metric readings, so
the eval store must exist first. The run ledger itself is a *distinct* SQLite store (not E1's DuckDB
table); the dependency is on E1's *surface*, not its storage.

**Cross-plan:** `parallelizable_with: [bp-044]` — disjoint write scopes (`core/stores` +
`core/dreaming` + `scheduler` here; `eval/harness/report.py` in E4). The first overnight dual-dreamer
A/B (the single-config comparison, §1 reconciliation) needs **E1 + E2 + E5(A2) + E4**: E1 the store,
**E2 (this plan)** the run producer — dream_runs/dream_claims + the keyed metric readings; **E5(A2)/
bp-045** wires `snapshots` so dream_v2 populates the structural axes this runner reads via
`latest_structural()`; **E4/bp-044** renders the A/B tables + drift study + cost appendix. So this
plan's Item 6 also depends, at RUNTIME, on E5(A2) being wired for `structural_axes.*` rows to be
non-empty — if bp-045 has not landed, the runner records the claims + guardrails and logs the A2 axes
as *not-captured* (no silent cap, §2.8), rather than failing. E6 (verdicts/review) judges the claims
this ledger accumulates; E3a generalizes this single-config run into the declarative σ-grid sweep.
Recorded in `docs/PARKING-LOT.md`.
