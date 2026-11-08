---
type: experiment-report
experiment: utility-field
run: 1
status: complete; synthetic graphs only, no store read
started: 2026-11-08
links:
  - docs/design-notes/dn-utility-field.md                 # the design, UTL-1 to UTL-6, the build order
  - formal/Palace/Utility.lean                            # the theorems the measurements check
  - eval/utility_field.py                                 # the simulator that produced every table
  - docs/experiments/utility-field-2026-11-08/            # the tables: trajectory, localization, polya, loop, summary
  - papers/2026-11-08-utility-field/paper.tex             # the article
---

# The utility field, simulated: arcs form and fade, the bounded nudge, the exponent's threshold

**Question.** dn-utility-field proposes a field over the sites of a graph that records use and
the value use produced, decays toward a baseline, and nudges the structural weights within a
margin. Its laws say the field stays in a box (UTL-1), returns to the baseline on a declared
window (UTL-2), cannot collapse the walk onto hubs (UTL-3), moves the Laplacian's spectrum by at
most `2θ d_max` (UTL-5), and has one stationary state when the loop's gain is below the rate
(UTL-6); the controls say what happens without the decay, the cap and the margin. This run drives
the model under a query load on a synthetic graph and reports every bound against what was
measured, and every control against what it predicts. Nothing here reads a store.

## Setup

- Code: `eval/utility_field.py`, `uv run python -m eval.utility_field OUT_DIR`; seed `20261108`;
  the tables in `docs/experiments/utility-field-2026-11-08/`.
- Graph: two communities of 12 nodes, each a spanning path plus an edge between non-adjacent
  members with probability 0.5, joined by 2 bridges; weights uniform in `[0.5, 1]`; 24 nodes, 76
  edges, connected, spectral gap `γ = 0.18301`, largest degree `7.14`, largest ratio of two
  weights `1.97`.
- The field: baseline `b = 1`, rate `lam = 0.05`, cap `c = 0.02`, so the box is `[0.6, 1.4]`;
  nudge `η = 5/6`, so the margin is `θ = η c/lam = 1/3`, the effective weights lie in
  `[2/3, 4/3]` of the structural ones, and the bounds are `θ/(1 − θ) = 0.5` on total variation,
  `(1 + θ)/(1 − θ) = 2` on any node's stationary mass, `2θ d_max = 4.76` on any eigenvalue's
  move, `(1 − θ) γ = 0.122` on the gap. An arc is a site at or above `b + 0.3 = 1.3`.
- The load: three phases of 120 ticks. Phase 1 draws 10 anchors a tick from four nodes of the
  first community with rank-frequency weights `1/r` (the first anchor takes 48% of the queries);
  phase 2 moves the load to three nodes of the second community; phase 3 returns to the first.
  Each anchor has a planted answer: the neighbour the structural walk ranks second, so the first
  result is a different neighbour and the field has room to lift the answer within its tier.
- A query ranks the other nodes by the killed walk's first-passage score at `z = 1/2` (the
  shape of `diffuse`, RSP-1) on the nudged weights. If the first result is the answer, the query
  resolved with value: the edge to the answer is credited the full use `c`. Otherwise the edge
  to the first result is credited a tenth of `c` (a use that produced nothing), and with
  probability 0.5 the answer is reached anyway (a citation followed, a question resolved) and
  its edge is credited `c`. The field is updated once a tick with the summed credits, clamped to
  `[−c, c]`.
- Probes, every tick: the mean rank of the first load's four answers under the current ranking,
  how many of them are first, the total variation between the nudged and the structural
  stationary distributions, the largest move of a Laplacian eigenvalue, the gap, whether the
  field is in its box, and the field on the hot edge: the structural shortest path from the
  hottest anchor to its answer, which here is the one edge `(3, 6)`.

## Results: the field under the load

| quantity | measured | the law's bound or prediction |
|---|---|---|
| field in the box, every tick | yes, 360 of 360 | UTL-1: invariant |
| first arc | tick 31, on the hot edge | UTL-2's heat-spot form: `b + (c/lam)(1 − (1 − lam)^n) ≥ 1.3` at `n = 28` for a site at the cap every tick from the baseline; the hot edge took 32 ticks, so it was not at the cap on every one |
| hot edge's peak (phase 1) | 1.381 | the ceiling 1.4 |
| hot edge 74 ticks after the load moved | 1.0081 | UTL-2's window: within `ε = 0.01` of the baseline once `n ≥ log(c/(lam ε))/lam = 74` |
| arcs of the first load gone | tick 125, the sixth tick of phase 2 | `(1 − lam)^n (c/lam) < 0.3` at `n = 6` from anywhere in the box |
| arcs per phase (largest count) | 3, 3, 3 | each load's hot paths; the second load's own arcs form in phase 2 and fade in phase 3 |
| total variation, nudged against structural stationary distribution (largest) | 0.0120 | UTL-3: at most 0.5 |
| largest eigenvalue move (over all ticks and eigenvalues) | 0.367 | UTL-5: at most 4.76 |
| smallest gap | 0.18303 (structural 0.18301) | UTL-3: at least 0.122 |

UTL-5's order law is not exercised by this graph: no two of its weights are more than the factor
`(1 + θ)/(1 − θ) = 2` apart (the largest ratio is 1.97), so every pair lies within the margin and
the law constrains none. `tests/unit/test_utility_field.py::test_order_is_kept_beyond_the_margin`
checks it at `θ = 1/4`, on the pairs of a smaller graph's edges that are beyond the margin.

The learning cycle, read on the first load's answers (mean rank among all nodes; the share
ranked first):

| when | mean rank | share first | hit rate on the live load |
|---|---|---|---|
| tick 0 | 2.00 | 0.00 | 0.00 (first 10 ticks) |
| end of phase 1 (last 20 ticks) | 1.75 | 0.25 | 0.26 |
| end of phase 2, the load elsewhere | 2.00 | 0.00 | (the probe only) |
| end of phase 3, the load back | 1.50 | 0.50 | |

One of the four answers was ranked first at the end of the first phase and two at the end of the
third; the others stayed second. The lift was gone at the end of the second phase, with the load
elsewhere, and came back with the load. The laws bound how far each weight can move, by the
factor `(1 + θ)/(1 − θ) = 2` at most, and say nothing about which of two walk sums is the larger,
so they do not say which answers rise; this run does not separate why the other two stayed
second.

## Results: the controls

**The exponent.** An edge-reinforced walk with no decay and no cap, each edge's weight its
structural weight plus its traversal count to the power `α`, 20,000 steps from node 0, against
the design's bounded field under the same walk:

| scheme | `α` | total variation from the structural stationary distribution | share of steps on the most used edge | nodes visited |
|---|---|---|---|---|
| reinforced | 0.5 | 0.060 | 0.020 | 24 |
| reinforced | 1.0 | 0.483 | 0.133 | 24 |
| reinforced | 2.0 | 0.910 | 0.999 | 8 |
| bounded field | | 0.028 | 0.020 | 24 |

Superlinear reinforcement localizes: after a transient of eight nodes the walk crosses one edge
back and forth, which is the attracting edge of strongly reinforced walks. Linear reinforcement
visits every node, concentrates on no edge, and sits far from the structural law, which is the
random environment the cited theorems describe: a mixture of reversible chains, whose stationary
law is drawn once per run and is not the structural one. Sublinear reinforcement stays near the
structural walk. The walk on the bounded field sits nearer still, and its stationary law is
within the bound 0.5 of the structural one at every time (UTL-3).

**The two-site mean field.** The leader's share `x/(x + y)` from `(1.2, 1)` after `n` steps of
the mean field `x ↦ x + x^α/(x^α + y^α)`:

| `n` | `α = 0.5` | `α = 1` | `α = 2` |
|---|---|---|---|
| 1 | 0.538 | 0.545 | 0.559 |
| 100 | 0.507 | 0.545 | 0.926 |
| 2000 | 0.502 | 0.545 | 0.996 |

At `α = 1` the share is `6/11` at every step, the ratio `1.2` held exactly
(`Palace.Utility.polya_ratio_eq`); above it the leader takes everything, below it the sites
equalize.

**The closed loop.** The use as a linear function of the field, `use = K (u − b)`, iterated
fifty ticks from two random fields in the box on 16 sites; the contraction of their sup distance
per tick against UTL-6's `1 − lam + K`, and the fixed points found among the baseline, the
ceiling and the floor:

| `K / lam` | bound `1 − lam + K` | measured rate | fixed points |
|---|---|---|---|
| 0.25 | 0.9625 | 0.9625 | 1 |
| 0.5 | 0.975 | 0.975 | 1 |
| 0.9 | 0.995 | 0.995 | 1 |
| 1.5 | 1.025 | 1.007 | 3 |

Below the rate the measured contraction is the bound, since a linear feedback attains it; at
`1.5` times the rate the distance grows and the baseline, the ceiling and the floor are all
fixed: the self-reinforcing state of the control `Palace.Utility.Witness.bistable`.

## Reading

Every bound held with room: the field's effect on the walk's stationary law and on the spectrum
was one to two orders of magnitude inside UTL-3 and UTL-5 at a margin of a third, because the
load heats a few paths while the bounds are stated for the worst field in the box. The arcs did
what UTL-2 says: formed on the hot paths in about thirty ticks, came within 0.02 of the ceiling,
and were gone by the sixth tick after the load left, the hot edge back within a hundredth of the
baseline on the declared window. The learning is visible and bounded: the field lifted some
answers to the first result while their load stayed and let them go on the window when it left;
the laws bound how far it can move the weights, not which answers it lifts. The controls behaved
as the theorems and the cited results predict: no decay and no cap exceed every box, a
superlinear exponent localizes, a gain above the rate holds a self-reinforcing state. The run is synthetic; what it cannot say is where a real load sits
between the worst field and this one, which is the corpus instance's first measurement when the
build is licensed (dn-utility-field §7).
