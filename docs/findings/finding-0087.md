---
type: finding
id: finding-0087
status: open
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - docs/build-plans/bp-046/plan.md
  - core/dreaming/shadow.py
  - ops/levers.py
  - config/loader.py
  - docs/inbox/owner-questions.md
ftype: design
origin_plan: E3a-graduation (bp-046 reserved)
route: orchestrator
resolution: owner-decision-owed (folds into oq-0024)
---

# The sweep can't sweep the runner: registered levers are `[dreaming]`, but `ShadowRunner` computes from `[dream_rnd]`

## What
Discovered during the E3a graduation grounding pass (2026-07-16). `dn-evaluation-harness` §2.6/§2.9
pins the first sweep instance as `sweep.dreamer-sigma-ab` with `levers = { dream_similarity_threshold
= "full" }` — a sweep over a **registered lever**. But the BUILT `ShadowRunner` (bp-043) that a sweep
drives once per lever-cell:

- computes its graph + claims from **`[dream_rnd]`** — `MirrorGraph.build(view, sigma=rnd.sigma)`,
  `community_interpreter(graph, rnd)`, `collect_claims(graph, ctx, rnd)` (`shadow.py:139,146,164`);
- only **fingerprints `[dreaming]`** — `_config_fingerprint` hashes the 4 `[dreaming]` levers
  (`shadow.py:94-105`), and its own docstring flags this as a placeholder *"E3 widens this to the full
  tuning manifest (parked, §11)"*.

`[dreaming]` and `[dream_rnd]` are **separate config sections** parsed independently
(`config/loader.py:363-370`). All 4 registered levers (`ops/levers.py:75-112`) live in `[dreaming]`.
So varying any current lever changes the eval-store **key** (distinct fingerprint → resumable cells)
but **not the runner's output** → a sweep produces **flat curves by construction**. The engine cannot
do its job against the built runner with today's levers.

The σ collision makes it concrete: oq-0024's σ is `dreaming.similarity_threshold` = 0.62 (a lever),
but the runner's actual bandwidth knob is `dream_rnd.sigma` (**not** a registered lever). oq-0024's
envisioned `[0.55, 0.75]` sweep would move the lever, not the dream_v2 output.

## Why it matters
It **blocks a clean graduation of E3a-1** (the sweep engine, bp-046 reserved). E3a-1's core design —
what its `config_fingerprint` covers (the bp-043-parked widening), what grammar the sweep spec targets,
and whether it touches `ops/levers.py` — all depend on this fork. Graduating E3a-1 now would mean
inferring a design decision the owner deliberately owns (the lever registry is *"the ENTIRE
self-modifiable surface … a deliberate, reviewable diff, never a guess"* — `ops/levers.py:11-13`).
Per the graduate discipline (never infer design to make a plan look finished), E3a-1 is **parked**;
E3a-2 (bp-047, the manifest/CLI) and E6 (bp-048) graduated this session (both fork-independent).

## The fork (owner-decision owed — options, with the orchestrator's lean)
1. **Register the `[dream_rnd]` knobs as levers** (recommended). Make `dream_rnd.sigma` (and the peers
   a sweep would vary) first-class bounded levers, so the sweep varies what the runner actually reads,
   AND every swept knob stays inside the tuning gate's "must resolve to a registered lever" invariant
   (note §2.6). Cost: a deliberate, reviewable widening of the self-mod surface the owner bounded —
   exactly the kind of change `ops/levers.py` says must be explicit. Most faithful to oq-0024.
2. **Fix `ShadowRunner` to honor `[dreaming]` levers** — make the runner's clustering read
   `dreaming.similarity_threshold` etc. A bp-043 correction; keeps the registry unchanged, but forces
   the question of whether `[dreaming]` or `[dream_rnd]` is the true dream_v2 surface (they overlap).
3. **Widen the sweep grammar to target `[dream_rnd]` directly** (weakest). Violates note §2.6's
   "must resolve to a registered lever" + the §14 gate's registry requirement; rejected unless 1 & 2
   are both undesirable.

Either way, E3a-1 must also widen `_config_fingerprint` to cover the swept knob (the widening bp-043
explicitly parked to E3), so cells are honestly distinguishable.

## Routing
`design`, route → orchestrator → owner. **Folds into oq-0024** (which already asks "re-tune σ + build
a σ-sweep harness"): this finding is the concrete grounding that the harness must resolve the
which-knob fork first. Non-blocking for the rest of the harness (E3a-2, E6, E7 unaffected). Re-entry:
owner picks a fork → E3a-1 (bp-046) graduates against it.
