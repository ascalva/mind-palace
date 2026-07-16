# bp-053 (clock-maps, GC-2) — builder journal

## Frame
- Extends `core/temporal/spine.py` (GC-1, already on main w/ the bp-051 fix) with the §6 clock-map
  surface: `p`, `fiber`, `n_s`, `proper_time`, `frontier_at`. Holds clock laws C1–C4 verbatim.
- Design ref (RATIFIED, CITE-never-edit): `docs/design-notes/global-event-clock.md` §2.3 (C1–C4 +
  GC-N6), §2.9-3/-6. finding-0090 = the proper-time discipline (per CHAIN, never per stratum).
- Write scope: `core/temporal/spine.py`, `tests/unit/test_clock_maps.py`,
  `tests/integrity/test_clock_laws.py` (+ this journal, findings).

## Worktree note (SEMANTIC BOUNDARY 0 — resolved)
- The worktree was created STALE at `4b3ace7` (before bp-051's spine landed) and lacked
  `core/temporal/spine.py`. Main HEAD `97239b8` carries the finalized spine (with bp-051 fix) and
  bp-053 `ready`. My branch had no commits of its own beyond `4b3ace7` (a strict ancestor of main),
  so I fast-forwarded the worktree branch to `97239b8` (`git merge --ff-only main`). Now extending
  the CORRECT base file. No divergence introduced; the orchestrator can merge my branch cleanly.
- ALL work happens in the worktree at `/Users/.../worktrees/agent-a18507b36396cedcf`.

## Key facts about the base (GC-1 spine)
- `Spine` is a mutable `@dataclass` with fields `_events, _succ, _chain_of, _gen_edges,
  _produced_by, _present, _refs_without_producer`. Constructed in `_Builder.finalize()` and
  `Spine.restrict()`.
- `SpineEvent(event_id, store, stratum, position, refs)`. `event_id = "<store>:<chain-key>:<pos>"`.
- `_succ` = DIRECT adjacency (g1∪g2∪g3), NOT the closure. `_reachable(e)` = BFS closure (strict).
- `order(a,b)` ∈ {BEFORE, AFTER, CONCURRENT}. `frontier()` = per-CHAIN latest positions keyed by
  `"<store>:<chain-key>"`. `restrict(stratum)` = induced sub-poset (N_s).
- Stores enumerated: versions (per-doc g1), runledger (g1 runs + g3 claims + g2 support), edges
  (g1 rowid), derived (g2 DAG only), attestations (g1 rowid + g2 derived_from_ids), eval
  (chain-less, position=None), catalog (chain-less). `_STRATUM` maps store→stratum.
- Acyclicity is a construction invariant (`SpineCycleError` on cycle).

## Clock vocabulary (READ-ONLY from `core/scope.py:171-217`, bp-056 owns changes)
`Clock` = {N, N_S, COMMIT, DISTINCT_SNAPSHOT, PROJECTION_EVENT, LAST_WRITE, WALL, NOW}. Hierarchy
`N ⪰ N_s ⪰ commit ⪰ distinct_snapshot`. N is `_PARKED` in scope.py — but the SPINE materializes N
(that is the whole point of dn-global-event-clock); I implement p_N in the spine WITHOUT touching
scope.py (the `_PARKED_CLOCKS`/T-meet completion is bp-056's seam, §4 reconciliation).

## Design decisions (my interpretation of the pinned §6 surface)
Each `Clock` member's `p_κ : Ev → I_κ` over the materialized spine:
- **WALL (C4):** `p`/`fiber` RAISE `ValueError`. Wall generates nothing (no p_wall exists).
- **N:** identity. `p(N, e) = e` (the event_id). Fiber(N, e) = [e] (singleton ⇒ C2 trivially).
  C1 trivial (identity preserves ≼).
- **N_S:** per-stratum event tick. `p(N_S, e) = (e.stratum, e.event_id)`. Singleton fibers ⇒ C2
  trivial; C1 holds within a stratum by identity. The RICH N_s object is `n_s(stratum)` (restrict).
- **PROJECTION_EVENT / LAST_WRITE / NOW (read-clocks, C3):** they mint no events; their tick is the
  BORROWED per-store write frontier. `p(read_clock, e) = frontier_at(e.store)`. This is the C3
  test: read-clock ticks == observed frontier. C1/C2 are NOT applied to read-clocks (design treats
  them under C3, a separate law — they are per-store samplers, not coarsenings of ≼); a cross-store
  comparable pair would trivially break a naive C1, which is exactly why C3 (not C1) governs them.
- **COMMIT / DISTINCT_SNAPSHOT (repo-backed coarsenings):** their tick is sourced EXTERNALLY (which
  git commit / content-snapshot an event belongs to). NO store the spine enumerates carries a
  commit SHA (verified on disk: versions/catalog have none), and git-subprocess is an `ops/`-only
  capability — `core/` never shells to git (arch: "the spine is arithmetic over stores; no model,
  opens no socket", §2.10). So the spine CANNOT source commit ticks from its own data. Resolution
  (spec-fidelity, see finding below): the spine consumes an INJECTED coarsening map
  `coarsening_ticks: {Clock: {event_id: tick}}` (additive Spine field, default empty). `p(COMMIT,e)`
  returns the injected tick or RAISES a clear "commit map not injected" error. This keeps git out of
  core, makes the C1/C2 LOGIC testable on synthetic fakes in-worktree, and lets the integrity test
  on main (which MAY shell git in the TEST — tests may) supply real data.

## proper_time (finding-0090 discipline) — `(int, bool)`
`(max-chain length, chain_complete)`. chain_complete=True ONLY when the causal interval [a,b] is a
TOTAL order (a chain) — then max-chain length == interval size == exact event count (the identity
holds only on a total chain). Rules:
- same stratum ⇒ compute on `restrict(stratum)` (N_s); cross stratum ⇒ chain_complete=False always.
- concurrent (neither reaches the other) ⇒ (0, False) — no chain connects them.
- comparable + interval total ⇒ (len, True). comparable + interval NOT total (concurrent events in
  between) ⇒ (longest-chain-len, False) — NEVER sell the bare count as proper time.

## VERIFICATION POSTURE (critical — this worktree has NO data/)
- `tests/integrity/test_clock_laws.py` runs on REAL stores → in THIS worktree it is TRIVIAL (empty
  spine), proves nothing. The REAL falsifiers live in `tests/unit/test_clock_maps.py` on INJECTED
  fakes: fiber order-convexity, C1 monotonicity (non-monotone commit map ⇒ fail), C4-raises,
  C3 frontier-borrow, and the proper_time chain_complete discipline. Those I CAN verify here.
- The LOGIC is grounded by REASONING about real git/versions structure, not by watching integrity
  go green. Assumptions to verify live are listed at the end.

## What landed (files)
- `core/temporal/spine.py` (+~180 lines): pinned §6 surface — `p`, `fiber`, `n_s`, `proper_time`,
  `frontier_at`, plus `is_fiber_convex` (the C2 oracle) and private `_chain_metric`/`_interval`/
  `_longest_chain_len`. Additive field `_coarsening_ticks` + `derive(..., coarsening_ticks=)` +
  `restrict()`/`finalize()` thread it. Imports `core.scope.Clock` (READ-ONLY) + `Hashable`.
- `tests/unit/test_clock_maps.py` (17 tests, the REAL falsifiers): C4-raises, N identity, N_S tick,
  C3 frontier-borrow, C1 monotone (+ inversion caught), C2 convex (+ gap-skipping caught),
  randomized monotone maps, COMMIT partial-domain, proper_time (exact-on-chain / cross-doc /
  cross-stratum / diamond-non-total / concurrent / unknown), n_s partition.
- `tests/integrity/test_clock_laws.py` (7 tests): commit-as-range (seeded + real), gap-skipping
  falsifier, N_s partition (seeded + real), proper_time discipline (seeded + real version chains).
- `docs/findings/finding-0093.md` (spec-fidelity, RESOLVED in-plan): the commit clock's tick is
  externally sourced (no store carries a commit SHA; core never shells to git) → consumed via an
  injected map; TRUE git-history commit map is a named ops-side follow-up, not built here.

## STATUS
- [x] Item 1 — p_κ per registered clock + C-law property tests (unit) — 17 pass
- [x] Item 2 — commit-as-range + N_s partition + proper_time (integrity) — 7 pass
- [x] Green gate (5 legs): ruff clean · mypy(core..) 205 OK · argless mypy tail=69 (baseline) ·
      type_gate OK · pytest 1360 passed / 10 skipped
- [x] finding-0093 filed (spec-fidelity, builder-resolved)
- [x] Boundary 0 — worktree corrected (FF to 97239b8), design fixed, journal seeded

## ASSUMPTIONS THE ORCHESTRATOR MUST VERIFY ON MAIN (live corpus)
1. `SpineSources.resolve()` on the live corpus DERIVES ACYCLICALLY (no SpineCycleError) — the
   integrity test's real-store legs are TRIVIAL in this worktree (no data/); the 1467-event-cycle
   class of defect only surfaces on real data. (This is GC-1's invariant, re-exercised by GC-2.)
2. The `n_s` partition holds over the live corpus: every real event lands in exactly one stratum's
   restriction and the union recovers Ev (real-store partition test).
3. proper_time on real version chains: any live doc with ≥2 versions gives chain_complete=True with
   length == version count; a cross-doc pair gives chain_complete=False.
4. The commit-as-range REAL check here uses a `version_seq`-grouped commit-ANALOGUE map (NOT git
   commits). A git-history-sourced commit map (finding-0093) is a separate ops-side follow-up; the
   live "against the actual git history" convexity claim is NOT yet mechanically verified — it is
   the finding-0093 re-entry, not a bp-053 deliverable.

## KEY REASONING (grounded, not test-observed — worktree has no data/)
- COMMIT fibers are convex against real git+versions BY STRUCTURE: within one doc a commit holds at
  most one version (you cannot commit v2 and v4 without v3); across docs a commit's versions are
  concurrent (different chains) ⇒ no betweenness ⇒ convex. The confound the "grain caveat" warns of
  (a commit skipping a version in one doc's chain) is the `is_fiber_convex` falsifier.
- restrict()'s `_succ` is the transitive CLOSURE (not direct adjacency); `_longest_chain_len` /
  `_interval` are correct on both the direct-adjacency full spine and a restricted closure spine.
