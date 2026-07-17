# bp-056 journal — GC-4: the T-meet completion (pullback meets via an injectable clock atlas)

Builder session, worktree `worktree-agent-ad4eec91c9992bfd1`, off main tip `61fdedb`.

## State: COMPLETE — both items built, 5-leg gate green, ready to merge (LAST in wave 3).

## What was built (write_scope only)
- `core/scope.py` — **purely additive** (diff: 46 insertions, 1 deletion; the 1 deletion is the
  `import` line gaining `Protocol`). Three additions, nothing relocated:
  1. `ClockAtlas(Protocol)` — the pure-core typing seam (`has` / `pullback` / `intersect`),
     signatures verbatim per plan §6. Inserted between `NoCommonClockError` and `class TimeScope`.
  2. `_ATLAS: ClockAtlas | None = None` + `register_atlas(atlas | None)` — the process-wide
     registration point. Default `None` ⇒ the T-meet is the partial semilattice it ships as.
  3. A new branch in `TimeScope.meet`, inserted ONLY between the same-clock return and the two
     existing `raise NoCommonClockError` branches (both left byte-identical). Captures `atlas =
     _ATLAS` locally (mypy-clean narrowing); when both clocks are atlas-covered, pulls each window
     back and intersects → `TimeScope(Clock.N, Window.interval(token, token))` (or `Window.empty()`
     when `intersect` returns `None`). With `_ATLAS is None` the branch is skipped entirely →
     control flows to the untouched raises → byte-identical.
- `core/temporal/atlas.py` (NEW) — `SpineAtlas(spine)` implementing `ClockAtlas`, imports stores via
  the spine; `core/scope.py` never imports it (the pure-core seam holds). Token = the pulled-back
  **event set** as `frozenset[str]` (v1 opaque hashable form of CS-b's antichain window, plan §11);
  `intersect` = set ∩ (empty → `None`). `has()` excludes wall/now (exogenous, no p_κ) and returns
  False for un-materialized COMMIT/DISTINCT_SNAPSHOT (probes `spine.fiber` — public API, no private
  field access) so an un-materialized clock RAISES rather than silently returning empty. `pullback`
  enumerates `spine.events()` and coarsens each via `spine.p(κ, e)`, skipping events outside
  `dom(p_κ)` (honest partiality). `_in_window` handles ALL/EMPTY/POINT/int-interval and the
  frozenset-bounded N-window (set membership) — the last is what makes a re-meet against N recover
  its set (associativity).
- `tests/unit/test_tmeet_completion.py` (NEW) — 13 tests, all green. Covers Item 1 (seam off by
  default; same-clock bit-identical with/without atlas; clearing restores partiality) and Item 2
  (coverage; `pullback == hand-enumerated spine.fiber`; `commit ⊓ N_s` == hand-computed set;
  wall/now raise even with an atlas; empty → EMPTY window; commutativity + associativity over
  covered triples; `_in_window` unit). An **autouse fixture resets `register_atlas(None)` around
  every test** so no atlas leaks into test_scope.py (whose cross-clock-raises falsifier depends on
  `_ATLAS is None`).

## Cardinal disciplines — verified
- **test_scope.py passes with ZERO edits.** `git diff --stat` shows ONLY `core/scope.py`;
  test_scope.py is absent. `pytest tests/unit/test_tmeet_completion.py tests/unit/test_scope.py`
  = 41 passed. The 24 lattice-law tests are green unchanged.
- **scope.py diff is purely additive** (see above). Both existing raise branches and the same-clock
  branch are byte-identical; the join/Scope/Window/admissibility code is untouched.
- **scope.py stays pure-core** — imports no store; only `Protocol` was added to the typing import.
  The concrete atlas (which imports stores) is the separate `core/temporal/atlas.py`.
- **Conservative completion** — the new branch's domain is EXACTLY the former cross-clock error
  path. No-atlas ⇒ every previously-raising input raises the same `NoCommonClockError`; wall/now ⇒
  raise; both-covered ⇒ compute; empty ⇒ EMPTY window (never an error).

## §7 acceptances / falsifiers verified
- Item 1: test_tmeet_completion green AND test_scope green with zero edits; same-clock meets
  bit-identical with/without atlas (`test_same_clock_meet_is_bit_identical_with_and_without_atlas`);
  no-atlas cross-clock raises same type (`test_default_atlas_is_none_so_cross_clock_still_raises`).
- Item 2: `commit ⊓ N_s` == hand-computed set (`test_commit_meet_ns_is_the_pullback_intersection`);
  pullback == hand-enumerated `spine.fiber` (`test_pullback_equals_hand_enumerated_fiber`); wall ⊓
  anything raises (`test_wall_and_now_meets_raise_even_with_an_atlas`); commutative + associative on
  covered triples; empty intersection → EMPTY (`test_empty_intersection_is_the_empty_window...`).

## Gate (each leg run separately)
1. `ruff check .` — All checks passed.
2. `mypy core agents eval ops scheduler scripts` — Success, 0 issues in 206 files.
3. `mypy` (argless) — Found 69 errors in 20 files (unchanged; the new test file's one `set(Hashable)`
   overload error was removed by comparing the pullback to a `frozenset` directly).
4. `python -m ops.type_gate` — OK.
5. `pytest -q -m 'not live'` — 1408 passed, 10 skipped, 9 deselected.

## Design decisions taken (grounded, no finding needed)
- **N-window representation.** Wrapped the opaque event-set token as `Window.interval(token, token)`
  (a degenerate cut-pair `[S, S]` over Clock.N) rather than `Window.point(token)`. Reasons:
  (a) note §2.5/§2.9-4 frame N-windows as intervals (down-set cut-pairs); (b) POINT would trip the
  SLICE rule for any downstream multi-stratum Scope on clock N (not in `_CUT_CLOCKS`), an accidental
  behavior interaction — INTERVAL avoids it. The Window grammar was NOT loosened (opaque frozenset
  bounds ride the existing conservative meet/join/⊑ paths), so plan §4/§10's "unrepresentable ⇒
  finding" trigger did NOT fire. Matches plan §11's parked default (opaque token in the existing
  Window; full antichain machinery deferred to a consumer needing N-window arithmetic).
- **has() excludes now as well as wall** (plan §3 / cardinal discipline: "Wall/NOW → raise"). now is
  the live-present exogenous anchor with no fixed event set; wall has no p_κ (Law C4).
- **Existing raise messages left byte-identical** rather than rewritten to name "exogenous wall".
  The hard requirement (byte-identical no-atlas behavior, cardinal discipline 1) outranks the
  message-polish note; the first raise's "N is parked" message is honest for wall (no common
  materialized clock). With an atlas registered, an uncovered clock (wall/now) simply falls through
  to the same untouched raise — still `NoCommonClockError`, verified by test.

## Findings filed
None. No `design`/`math`/`direction` question arose — the pullback was representable in the existing
Window grammar without loosening conservatism, so finding **0096** (reserved) was NOT needed.

## Next
Commit on the worktree branch (done at seal). Do NOT merge to main — orchestrator merges LAST in
wave 3 after a line-by-line review of the `core/scope.py` diff.
