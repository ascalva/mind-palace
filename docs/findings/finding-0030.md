---
type: finding
id: finding-0030
status: open
created: 2026-07-11
updated: 2026-07-11
links:
  - tests/property/test_structural_interpreters.py
  - core/complex/topology.py
ftype: discovery
origin_plan: bp-007
route: orchestrator
resolution: null
---

# finding-0030 — persistence-stability property test has a float32-scale tolerance gap (pre-existing, unrelated to typing)

## What

Incidentally discovered while running the full ratchet during bp-007 (a mypy/typing
build plan — this is NOT a typing issue and NOT caused by any bp-007 edit; verified
against the unmodified file at `bfa19e1`, byte-identical, and reproduced with bp-007's
changes fully `git stash`ed).

`tests/property/test_structural_interpreters.py::test_persistence_is_stable_under_
perturbation` (Hypothesis property test, H5: bottleneck stability of `core/complex/
topology.py: long_lived_holes`) has a cached falsifying example:

```
n=4, seed=558, eps=1e-08
assert abs(h0.birth - h1.birth) <= tol
  where tol = eps + 1e-9 = 1.1e-08
  actual |h0.birth - h1.birth| = 2.9802322387695312e-08
  h0.birth = 0.30000001192092896   (the classic float32 rendering of 0.3)
  h1.birth = 0.29999998211860657
```

The tolerance `eps + 1e-9` assumes float64-level numerical precision, but the birth
values are exactly at float32 granularity (`0.300000011920928...` is `float32(0.3)` cast
up). The actual discrepancy (~3e-8) is consistent with float32 rounding error compounding
through whatever internal computation `long_lived_holes` (ripser-backed, per `core/
complex/topology.py`) performs — not a violation of the true bottleneck-stability
theorem, which holds over the reals/float64. At `eps` values this small (1e-8, near the
float32 machine-epsilon-adjacent regime), the fixed `+ 1e-9` slack in the test's own
tolerance formula is too tight relative to the actual numerical precision of the
computation being tested.

This is now a **permanently reproducible** Hypothesis-cached counterexample (stored in
the gitignored `.hypothesis/examples/` cache) — anyone who runs the full property suite
without a cleared cache will hit it. I cleared my own worktree's `.hypothesis/` cache
(untracked, gitignored, disposable session-local state — confirmed via `git check-ignore`
and `git status --porcelain --ignored`) so bp-007's own gate stays green and reflects a
fresh-CI state, but the underlying numerical edge case is unresolved and will resurface
whenever Hypothesis's search (seeded by wall-clock/environment, not fully deterministic
run-to-run without a persisted example DB) happens to explore this region again.

## Why it matters

If unaddressed, this is a latent, intermittent CI/gate flake: `test_persistence_is_
stable_under_perturbation` can fail nondeterministically depending on Hypothesis's
internal search order and whatever `.hypothesis/` cache state a given CI runner/session
happens to have. It is NOT evidence that `long_lived_holes` violates bottleneck
stability — it is evidence that either (a) `long_lived_holes` computes in float32
somewhere internally when float64 was assumed, or (b) the test's tolerance formula needs
a precision-aware floor (e.g. `max(eps, sqrt(eps32)) + slack` or similar), or (c) the
`eps` strategy's lower bound should exclude values this close to float32 noise if the
pipeline is float32 by design and that's acceptable.

## Re-entry condition

A build plan (or the owner, direct) with `core/complex/topology.py` and/or `tests/
property/test_structural_interpreters.py` in scope: (1) determines whether `long_lived_
holes`'s internal computation is float32 or float64 (trace the ripser call and any
intermediate casts); (2) if float32 by design, widens the test's tolerance formula to
account for float32 machine epsilon at small `eps`, or floors the `eps` strategy away
from that regime; if float64 is intended throughout, finds and fixes the stray float32
cast. Until then: this is PARKED, un-silenced (no test tolerance widened, no cast added,
no xfail applied) — the finding records the gap; the next full-ratchet run may
intermittently surface it again if Hypothesis's search revisits this input, and that
recurrence is expected, not a new regression.

## Routing

`discovery` → orchestrator (math-adjacent: a numerical-precision question about a
formal-properties test, `docs/WHITEPAPER-FORMAL-PROPERTIES.md`-linked per the test
file's own docstring — not a codebase/spec-fidelity question the builder can settle
against the code and spec, since settling it requires either a numerical-precision
design decision or tracing ripser's internal dtype, which bp-007's mypy-scoped write
scope and mandate do not license). Not filed as `spec-defect` (no design note is
contradicted) and not `blocker` (does not end this session — the local cache clear keeps
bp-007's own gate green; re-entry is for whoever next owns `core/complex/topology.py` or
this test file).
