---
type: finding
id: finding-0094
status: resolved            # builder-resolved (spec-fidelity); annotated here + journal. (Renumbered from
                            # 0093 by the orchestrator: bp-053 and bp-054 both minted 0093 from the same
                            # 4b3ace7 baseline; bp-054's 0093 merged first, so bp-053's became 0094.)
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-053/plan.md                     # GC-2: the clock maps (this plan)
  - docs/design-notes/global-event-clock.md             # §2.3 (commit as a range), §2.10 (no socket)
  - core/temporal/spine.py                              # p/fiber COMMIT via injected coarsening map
  - core/scope.py                                       # Clock.COMMIT / _CUT_CLOCKS (read-only here)
ftype: spec-fidelity
origin_plan: bp-053
route: builder
resolution: >
  Resolved in-plan. The commit (and distinct_snapshot) clock consumes an INJECTED coarsening map
  (`Spine.derive(..., coarsening_ticks={Clock.COMMIT: {event_id: tick}})`); `p`/`fiber` operate over
  it, and `p(COMMIT, e)` raises a clear error when a tick is absent. Git stays OUT of core; the C2
  convexity LOGIC is unit-tested on injected fakes; the integrity test verifies it over real version
  shape with a version-respecting commit-ANALOGUE map. A TRUE git-history-sourced commit map (the
  live "commit fibers are ranges against the actual git history" check) needs an ops-side git helper
  — named below as the standing follow-up, NOT built here (out of write-scope; core never shells to
  git). No design change; the ratified note anticipated read-side injection.
---

# GC-2's commit clock: no store carries a commit SHA, and `core/` never shells to git — the `p_commit` tick is sourced by injection, not derived in-core

## What
Plan bp-053 §6 pins `Spine.p(Clock.COMMIT, event_id)` and §7 Item 2 requires "commit fibers are
ranges ON THE REAL STORES … verified against the actual git history + versions store." But the
disk audit (this build) shows **no store the spine enumerates carries a commit SHA**:

- `core/stores/versions.py` records `(doc_id, version_seq, digest, at)` — no commit column.
- `core/stores/catalog.py` records `(source_path, digest, title, provenance, active, updated_at,
  doc_id)` — no commit column.
- The only commit-SHA linkage in the system is `core/stores/reference_edges.py` (citation edges,
  `commit_sha` part of edge identity), which GC-1 does **not** enumerate; and `_resolve_default_commit`
  in `core/reference_view.py`.
- `git` subprocess usage is an **`ops/`-only** capability (`ops/code_snapshot.py`, `ops/self_sensor.py`,
  `ops/ci_witness.py`, …). `core/` never shells to git — consistent with dn-global-event-clock §2.10
  ("the spine is arithmetic over stores; no model, opens no socket") and non-negotiable #1/#2.

So `p_commit(e)` — "which git commit an event belongs to" — cannot be sourced from the spine's own
data, and sourcing it would require putting git subprocess into `core/`, which the architecture
forbids.

## Why it matters
Left unstated, a builder might either (a) shell git from `core/temporal/spine.py` (an architecture
violation), or (b) silently fake a commit grouping and call it "verified against git." Both are
wrong. The honest shape is: the commit tick is **externally sourced** and **injected**; the spine
holds the range LOGIC (Law C2 convexity) but not the git plumbing.

## Resolution (builder, spec-fidelity — implemented in this plan)
- `Spine` carries an additive, default-empty field `_coarsening_ticks: {Clock: {event_id: tick}}`
  for the repo-backed coarsenings (COMMIT, DISTINCT_SNAPSHOT), injectable via
  `Spine.derive(sources, coarsening_ticks=…)`. Additive — the pinned §6 method signatures are
  unchanged.
- `p(COMMIT, e)` returns the injected tick or RAISES a clear "sourced externally; inject via
  `coarsening_ticks`" error (p_commit is honestly PARTIAL over Ev — repo-backed events only).
  `fiber(COMMIT, tick)` ranges the injected map; `is_fiber_convex` is the Law C2 oracle.
- The REAL C2 falsifiers live in `tests/unit/test_clock_maps.py` (a gap-skipping map is caught; a
  monotone/range map is convex) — verifiable in a worktree. `tests/integrity/test_clock_laws.py`
  verifies convexity over real version shape with a `version_seq`-grouped commit-ANALOGUE map.

## Re-entry condition (the standing follow-up, NOT built here)
A TRUE git-history-sourced commit map — the live "commit fibers are ranges against the actual git
history" check — needs an **ops-side git helper** that maps each repo-backed event (a version's
digest) to the commit that introduced it, injected into the spine as `coarsening_ticks[Clock.COMMIT]`.
Re-entry: the first consumer that needs `Rate(commit)` or a commit-anchored cut over the live corpus
(GC-3 / a VI-a customer) — at which point the helper is an `ops/` concern (git lives there), wired
to the spine by injection. Recorded so it is never silently faked in-core.

## Routing
`spec-fidelity` → builder-resolved, annotated here + in the bp-053 journal; work continued. No
design-note change (the ratified note already mandates read-side derivation and no socket in core;
injection is the faithful realization).
