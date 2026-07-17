# Conductivity and reasoning chains — the fable finalization pass (C1–C6)

> **Fable session capsule** (`claude-fable-5`/xhigh, tier owner-set in-session via /model+/effort;
> 2026-07-17). Durable *working material* (a brainstorm), **not** a design note — nothing here
> flips a status, edits a ratified note, or blesses a transition. This is the rigorous pass the
> owner chartered over `docs/brainstorms/conductivity-and-reasoning-chains.md` (and its companion
> `self-mapping-the-palace.md`): ground the four connectivity questions in proper math and weave
> them into the built system.
>
> **Scope discipline.** Design reasoning only. Ratified notes are cited, never edited. Owner-
> reserved calls are surfaced as explicit **OWNER DECISION** items. Every nontrivial claim is
> labeled `[ESTABLISHED: cite]` / `[GROUNDED: path]` / `[DERIVED: from X]` / `[INFERENCE]` /
> `[ANALOGY]`. Prior fable results are consumed, not re-derived — this pass must and does
> reconcile with `magnetic-laplacian-fable-pass.md` Q3/Q4/Q5/Q6.

---

## 0. Executive map (what this pass concludes)

- **C1.** Three *time-like* axes were conflated in the intuition and must be separated: **σ**
  (scale/abstraction), **t** (diffusion/walk time), and **cuts** (corpus history). Each is a
  different "time"; every instrument below is indexed by a point in `(σ, t, cut)`-space. "The
  graph at a moment" is well-defined **only at a certified cut** (bp-055) — the cut lattice is
  the snapshot index, and wall-clock indexes nothing (Law C4).
- **C2.** The owner's "path of least resistance" has an exact, cheap, buildable v1: **σ\*(A,B),
  the maximin-cosine merge threshold, is a single-linkage ultrametric** ("abstraction
  distance"), the **maximum-spanning-tree chain realizes it**, and one MST per cut yields all
  pairwise σ\* *and* the realizing chains in `O(E log V)`. Computable **today** — the σ-filtration
  and its language already exist in `eval/harness/fibers.py` ("the filtration sparse→dense").
- **C3.** "Conductivity" is effective conductance — but **raw resistance distance degenerates in
  exactly the dense regime the owner posits** [ESTABLISHED: von Luxburg et al.]. The honest
  instrument is the **(σ, t) conductance profile** with finite-time diffusion distance as the
  regularization; commute time gives it dreamer-native meaning; Rayleigh monotonicity matches
  the decay intuition exactly ("connected once, not anymore" = R_eff → ∞); and a **reconnection
  is an attributable event** — the spine names *which* new thought re-bridged two old ones.
- **C4.** "Change distorts distance and local clock" splits over the magnetic pass's Q5 axes:
  the *distance* half is **metric curvature** (activity-weighted edges; the sign of the effect —
  churn impedes vs conducts — is a genuinely open **empirical, sweepable** question: *is the
  corpus a metal or a semiconductor?*); the *clock* half is **already built** (bp-053's p_κ /
  N_s / proper time are the local clocks). The helix (C6) lives on the *gauge* side. The two
  slots are independent [DERIVED: magnetic pass Q5] — the intuition was two theorems, not one.
- **C5.** "A coherent argument" = a **well-formed path**: the unified algebra supplies the
  grammar as a *running scope-meet* — a path type-checks iff the meet of its edges' scopes stays
  non-empty and admissible, and **bp-056's atlas is precisely the cross-clock type-checker**
  (its conservatism — refuse when uncovered — is the anti-hallucination property for arguments).
  Report bridges on **two axes** (best well-formed chain; conductance) under the one-scalar
  prohibition inherited from bp-057. SETTLED/HUNCH philosophy extends from claims to bridges.
- **C7** (owner addendum, mid-pass — the arc). The lightning-in-wood analogy is **dielectric
  breakdown**, and it is exact where it matters: DBM growth is guided by the *same harmonic
  potential* that defines conductance (C3) — the field view and the growth view are one object.
  It contributes the missing **strategy layer**: bidirectional, field-guided, **budget-bounded**
  bridge search with principled refusal ("no arc at this voltage"), and an exploration knob (η)
  that interpolates deterministic search → dreamer-adjacent stochastic growth. §6b.
- **C6.** The helix, made rigorous via **gain graphs** [ESTABLISHED: Gross–Tucker; Zaslavsky]:
  put ℝ-gains on the idea-quotient's edges (spatial ≡ 0, temporal = +Δτ proper time). The naive
  "every cycle is a helix" **refines**: the pitch is a linear functional on the cycle space;
  purely-spatial cycles are flat (legal snapshot cycles); **every all-forward revisitation walk
  is FORCED helical by spine acyclicity** (`SpineCycleError` is the theorem's engine); mixed
  cycles can be time-balanced — and the pitch functional is exactly the **proper-time-valued
  refinement of the magnetic pass's Q3 arm-imbalance flux**. Combinatorial v1 detector:
  fundamental-cycle pitches off a spanning tree, `O(E)`. Blocked on **one** dependency:
  uuid-identity (which now has three consumers).

---

## 1. C1 — the connectivity object and its three times

**The two-layer corpus object** [GROUNDED]. A spatial layer — the σ-indexed smear graphs
`G_σ = (V, E_σ)`, `E_σ = {(u,v) : cos(u,v) ≥ σ}`, undirected, built by the dream pipeline
(`core/dreaming/graph.py`; σ = the cosine edge threshold, cf. `dream_rnd_sigma` in
`config/sweeps/dreamer-sigma-ab.toml`) — fibered over the temporal spine `N = (Ev, ≼)`
(`core/temporal/spine.py`: directed, causal, **acyclic by construction** — Kahn sort,
`SpineCycleError`). Acyclicity is a *temporal-layer* property only; the spatial layer is
undirected and cycles there are legal.

**The three time-like axes** [DERIVED]:
1. **σ** — abstraction scale. Nested: `σ ≤ σ' ⇒ E_{σ'} ⊆ E_σ` (a graph filtration; the fibers
   module already speaks this language — "its birth reading the filtration sparse→dense",
   `eval/harness/fibers.py` ClaimFiber docstring) [GROUNDED].
2. **t** — diffusion/walk time *inside* a fixed graph (the random-walk clock; §3).
3. **cuts** — corpus history. Down-sets of a finite poset form a distributive lattice
   [ESTABLISHED: Birkhoff]; certified cuts (bp-055: frontier + certificate, soundness =
   down-closedness via `crossing_edges == []`) are the *honestly computable* elements of it.
   Chains of cuts are histories. **Open (design content):** certified cuts are not obviously
   closed under lattice meet/join — can certificates compose cut-wise? Parked; not needed for
   the instruments below (sample cuts at session/handoff boundaries where certificates exist).

Every question the owner asked is a question about a point or a slice of `(σ, t, cut)`-space.
Conflating the axes is where the intuition wobbled; separating them is most of the answer.

## 2. C2 — connecting A and B: the σ\* ultrametric and its realizing chain

Fix a certified cut C. Define **σ\*(A,B) = sup{σ : A ∼ B in G_σ(C)}** — the strictest threshold
at which A and B still share a component.

- **σ\* is an ultrametric** (as `d = 1 − σ*`): threshold graphs nest, components merge
  monotonically, and merge heights of a nested filtration are single-linkage distances
  [ESTABLISHED: single-linkage / subdominant ultrametric]. Interpretation: *how coarse must the
  abstraction get before two thoughts are the same conversation.*
- **σ\* is a maximin path value**: `σ*(A,B) = max over paths P of (min edge-cosine along P)`
  [ESTABLISHED: minimax/bottleneck path duality]. The **widest path realizes it** — and all
  widest paths live on the **maximum spanning tree** of the cosine graph [ESTABLISHED:
  bottleneck property of MSTs]. So *one* MST per cut yields **all pairwise σ\* and the
  realizing chain for every pair** in `O(E log V)`. The owner's "path of least resistance" has
  a canonical v1: **the MST chain** — the strongest single chain of association between any two
  thoughts, extracted from a structure we compute once.
- **Cross-time connection** (the "maybe only at different points in time" case): when no finite
  σ connects A,B at cut C, temporal edges (supersession, reads-from) may connect them across
  cuts. This is temporal-graph reachability — *journeys*, order-dependent, asymmetric
  [ESTABLISHED: temporal networks literature]. Reachability-through-history ≠ reachability at
  any snapshot; the owner's intuition here is a known theorem shape, not a speculation.

**Computability today** [GROUNDED]: claim-grain σ-presence is already recorded (ClaimFiber:
`pers`, `sigma_min`, `sigma_max`, `n_cells` over the declared grid — `eval/harness/fibers.py`);
chunk-grain needs only the σ-graph builder the dreamer already runs. This is the cheapest
buildable item in the family.

## 3. C3 — conductivity made honest

Weighted Laplacian `L = D − W`; effective resistance `R_eff(A,B) = (e_A−e_B)ᵀ L⁺ (e_A−e_B)`;
conductance `C = 1/R_eff` [ESTABLISHED: Doyle–Snell].

- **What matches the intuition exactly** [ESTABLISHED]: parallel paths *add* conductance —
  path diversity is precisely what conductance measures and geodesics ignore (the owner's
  "reachable through different paths (?)" — the ? is answered: that is *the* distinguishing
  content of conductance). Rayleigh monotonicity: adding/strengthening edges never lowers any
  conductance; decay/pruning never raises it — so under pure edge decay, conductance only
  falls, and "connected once, not anymore" is `R_eff → ∞` at the component split. **Corollary
  [DERIVED]: only new content re-conducts old connections** — a conductance *jump* between
  consecutive cuts is attributable to specific new edges, hence to the specific spine events
  that minted them. *The system can name which new thought reconnected two old ones.* (This is
  the `self-mapping-the-palace` reconnection metric, sharpened: reconnection = attributable
  Δ-conductance spike across a large proper-time gap.)
- **Commute time** `κ(A,B) = 2m·R_eff(A,B)` [ESTABLISHED: Chandra et al.] gives the
  dreamer-native meaning: the expected wander time of a random walk A→B→A — and the dreamer IS
  a stochastic process on this graph, so conductance is its natural metric, not an imported one.
- **The protective result — where this breaks** [ESTABLISHED: von Luxburg–Radl–Hein]: in large
  *dense* graphs, `R_eff(A,B) → 1/d_A + 1/d_B` — resistance distance degenerates to local
  degrees and loses all global structure, in exactly the dense regime the owner's premise
  posits. Mitigations are known (amplified commute distance; p-resistances [ESTABLISHED:
  Alamgir–von Luxburg]; finite-time diffusion distance [ESTABLISHED: Coifman–Lafon], noting
  `R_eff` is the *integral over all t* of heat-kernel discrepancies — the degeneracy is the
  integral being dominated by trivial short-time behavior). **Ruling:** the instrument is the
  **(σ, t) profile** — conductance across the σ-filtration (sparse regimes are informative)
  plus finite-t diffusion distances at a small t-grid — *never* a single dense-graph `R_eff`.
  With a built-in diagnostic falsifier (§8): if `corr(R_eff, 1/d_A+1/d_B) ≈ 1` at the loosest
  σ, the report must say so and lean on the diffusion column. The instrument protects itself
  from becoming a vanity metric.

## 4. C4 — "change distorts distance and local clock": two slots, not one

The magnetic pass (Q5) already ruled that *gauge* curvature (flux/holonomy) and *metric*
curvature (Forman/Ollivier) are independent axes [DERIVED: magnetic-laplacian-fable-pass Q5,
"the Einstein–Maxwell slot"]. The owner's sentence contains one of each:

- **"distorts distance" — the metric slot.** Implementation: activity-weighted conductances,
  e.g. `w(u,v) = cos(u,v)^α · exp(s·a(u,v))` where `a` = local activity from the built
  instruments (proper-time density `N_s`, bp-053; velocity/churn, bp-052) and **`s` is a signed
  lever**. `s < 0`: churn impedes (stable regions conduct meaning reliably — "metal", resistance
  rises with temperature). `s > 0`: churn conducts (active regions are where connection happens
  — "semiconductor"). [ANALOGY made precise as a sign choice.] **OWNER DECISION (empirical,
  sweepable): is the corpus a metal or a semiconductor?** The sweep engine exists; the sign
  need not be decided by taste. Optional formalization if "activity curves the space" ever
  wants theorem status: Ollivier–Ricci on the weighted graph [ESTABLISHED, optional].
- **"distorts the local clock" — already built** [GROUNDED: bp-053]. Per-stratum proper time IS
  a local clock that runs fast where events are dense. Temporal path-length below (§6) routes
  through it; nothing new to build for this half. The intuition was retroactively load-bearing:
  the clock maps were built before the question that needs them was asked.

## 4b. C4b — owner refinement (2026-07-17, on the draft note): churn as measure; the depth budget

**The owner's bound, formalized** [DERIVED; the readings are GROUNDED: bp-053's N_s]. Events
partition by stratum, so over a global window W the budget is exactly additive:
`N(W) = Σ_s N_s(W)`. A ≼-chain visits distinct events, so any chain confined to stratum s
within W has ≤ `N_s(W)` events (≤ `N_s(W) − 1` supersession steps) — **proper time is the
sequential-depth budget**: a thread or argument chain through a region cannot be deeper than
the region's local clock ticked over the window it spans. Near-tautological as a theorem; its
value is the reframing it forces:

**The C4 sign question dissolves** [DERIVED]. Churn is a change of measure with two components
whose signs are forced by circuit law: **sequential churn** (supersession depth) acts in
*series* — through-window traversal walks the threads, step by step, drawing on the budget;
series impedes, by law. **Lateral churn** (new cross-links) acts in *parallel* — Rayleigh;
parallel conducts, by law. "Metal vs semiconductor" is therefore not a global empirical sign
but a **per-region, per-window measured ratio**. Canonical statistic [ESTABLISHED: Mirsky/
Dilworth]: restrict the region's events to the window; sequentiality
`χ_s(W) = longest-chain / N_s(W) ∈ (0,1]` (depth vs width of the event poset) — χ→1 fully
serial (revision grinding), χ small wide/parallel (lateral novelty). The C4 lever `s` is
REPLACED by two non-negative magnitudes `(s_seq, s_lat)` on the derived decomposition; only
magnitudes remain sweepable. Practical v1 approximation: edge-type counts (supersession vs
lateral events); the poset depth/width is the canonical target. OWNER DECISION D1 is thereby
**retired, not resolved** — the better outcome for a gate.

## 5. C5 — arguments as well-formed paths (the algebra earns its keep)

**The grammar, made operational** [DERIVED from the ratified scope algebra + bp-056]: give each
edge a scope `S(e)` (strata × time-window × resolution — note `Res[T]` typing is already in the
scope system, bp-054). A path `p = e₁…e_k` is **well-formed** iff the running meet
`S(e₁) ⊓ … ⊓ S(e_k)` stays non-empty and admissible — an `O(length)` check. Three properties:

1. **Cross-clock hops type-check exactly through the atlas** [GROUNDED: bp-056]. A chain whose
   steps live on different clocks composes iff the atlas covers them — and *refuses* otherwise.
   The T-meet completion, built for scope composition, is *literally* the type-checker for
   cross-strata reasoning chains; its conservatism is the anti-hallucination property: **an
   argument that cannot type-check refuses rather than silently guesses** — the same dishonesty
   the partial meet always refused, now refused at chain level.
2. **Association ≠ argument, and both are wanted.** Paths that fail the type-check are still
   conductance-bearing associations — exactly what the dreamer surfaces. bp-057's gate already
   grades this axis at claim level (SETTLED ≈ argument-grade persistence, HUNCH ≈
   association-grade); bridges inherit the same two-tier philosophy.
3. **Two-axis reporting, no scalar fusion** [GROUNDED: bp-057's one-scalar prohibition,
   extended]: a bridge `B(A,B)` = (best well-formed chain by weighted geodesic; conductance
   profile as confidence). *The argument you present* and *the confidence you have in the
   connection* are different quantities and are never multiplied.

[INFERENCE, noted for later] The well-formed-path structure is category-shaped (objects =
scoped smears; composition = meet-accumulation where defined); nothing below needs the label,
so it stays an observation, not a dependency.

## 6. C6 — the helix theorem, refined and reconciled

**Setup** [ESTABLISHED: gain/voltage graphs, Gross–Tucker; balance theory, Zaslavsky]. Let π
project versions/chunks onto idea identities (**uuid-identity — the one missing prerequisite**),
`Ḡ` = the idea quotient of the version graph (supersession within an idea becomes a self-loop;
temporal edges between ideas persist). Assign gains in (ℝ, +): **spatial edges ≡ 0**
(co-present at the cut under consideration — zero temporal displacement), **temporal edges
+Δτ** (proper-time lapse between the minted events, bp-053), traversal against orientation
contributing −Δτ. The gain of a cycle is a linear functional on the cycle space `Z₁(Ḡ)`.

- **The naive claim refines.** "Every cycle is a helix" is false as stated: purely-spatial
  cycles have zero gain and are legal snapshot cycles (the spatial layer is undirected;
  acyclicity never applied to it). Mixed cycles can be **time-balanced** (equal forward and
  backward temporal content). What survives — and it is the phenomenon the owner actually
  described — is:
- **The forced-helix theorem** [DERIVED]. *Every closed idea-walk that traverses ≥1 temporal
  edge and all of them forward has strictly positive gain; hence its lift to the version level
  cannot close; it is a helix — closed in idea-space, open in version-space, displacement
  purely temporal, pitch = the gain.* Proof: temporal edges advance ≥1 frontier coordinate, so
  forward proper-time increments are strictly positive; the walk's gain is a sum of zeros
  (spatial) and strictly positive terms with ≥1 of the latter; a closed lift would exhibit a
  ≼-cycle, refused by construction (`SpineCycleError`). ∎ The spine's acyclicity invariant *is*
  the theorem's engine: **revisitation is necessarily helical** — the only legal way back to
  the same thought is around and up.
- **Reconciliation with the magnetic pass** [DERIVED: magnetic-laplacian-fable-pass Q3, Q4].
  Q3 computed U(1) flux on supersession diamonds as `2πq × arm-length imbalance`; the ℝ-gain
  functional here is precisely the **proper-time-valued refinement** of that arm-imbalance flux
  (compactify by a period β — `θ = 2πΔτ/β` — and the gain graph becomes a magnetic Laplacian;
  its flux = pitch mod β; the pass's "spectrum depends only on flux" then gives spectral
  detection). Q4's ruling — two charges, never one connection over a mixed edge set — is
  respected: the temporal gain is *one* semantic (temporal displacement), total on the edge
  set, with spatial edges at a true zero (co-presence), not an unknown; no charge-mixing occurs.
  [INFERENCE, flagged as resonance only: β here and the wave-4 β* both parameterize an
  inverse-scale on temporal structure; whether they are the same lever is NOT claimed.]
- **Detection, combinatorial v1** [DERIVED; consistent with magnetic pass Q6's "earns a
  combinatorial v1" discipline]: spanning tree on `Ḡ`, fundamental-cycle gains from chords —
  `O(E)`. Report: cycles with pitch above threshold = **revisitation helices**, each with pitch
  (the owner's rabbit-hole *period*, measured) and winding (revisit count). The spectral/U(1)
  route waits for the magnetic lane's own build gate; nothing here forces it early.
- **Seed instance:** Ouroboros — the system named by its own founding note — is the corpus's
  first helix; the owner's every-few-years design rabbit holes are the pitch distribution of
  his personal ones. The self-map detecting its owner's helices closes the companion capsule's
  loop, now as a computable object rather than a metaphor.

## 6b. C7 — the arc: bidirectional field-guided search (owner addendum, rigorized)

**The analogy grounded** [ESTABLISHED: Niemeyer–Pietronero–Wiesmann, the dielectric breakdown
model]. Lichtenberg-figure growth (the lightning pattern burned into wood between two
electrodes) follows DBM: at each step, the discharge structure extends across a boundary bond
with probability `∝ |∇φ|^η`, where **φ solves the Laplace equation with the electrodes as
boundary conditions** — the same operator, the same potential, as C3's conductance and current
flow. The owner's two intuitions are one object seen twice: *conductance* is the field view;
*the arc* is the growth view. The channel that completes is the realized bridge; the streamer
trees explored before contact are the parallel-path ensemble — so the C5 duality survives
intact (channel = the argument; explored tree = the confidence).

**What it adds — the strategy layer** [DERIVED]. C2/C3 build *global, precomputable* objects
(one MST per cut; Laplacian profiles). The arc picture is the **query-time algorithm** for two
*named* endpoints:

- **Bidirectional growth**: frontiers from A and B expanded until they meet — meet-in-the-middle,
  the classical `O(b^d) → O(b^{d/2})` saving [ESTABLISHED: bidirectional Dijkstra/BFS]. Guiding
  expansion by the electrical potential is A\*-with-a-potential, which is exactly Dijkstra on
  reduced costs [ESTABLISHED: A\*/reduced-cost equivalence — the search-theory term "potential"
  is the same electrical analogy, already].
- **Type-checked growth** [DERIVED from C5]: each candidate extension is scope-meet-checked at
  expansion time (atlas consulted for cross-clock hops) — *the streamer can only grow through
  admissible bonds*. An argument arc is a breakdown channel through the composable subgraph;
  illegal edges are perfect insulation.
- **"Voltage" = budget = refusal semantics** [DERIVED]. Fix a work budget (or equivalently a
  minimum-conductance threshold). Frontiers exhaust it before meeting ⇒ the instrument reports
  **NO ARC AT THIS VOLTAGE** — a principled, quantified refusal (how much budget was spent, how
  far each frontier reached), not a timeout. This is the house discipline (honest refusal over
  silent guessing) arriving in the search layer, and the budget lever is meaningful: raising
  the voltage until an arc forms *measures* the pair's resistance from the query side.
- **η as the exploration knob** [INFERENCE, parked]. DBM's exponent interpolates uniform growth
  (η=0, Eden) → DLA-like branching (η=1) → increasingly directed (η→∞ ≈ greedy/deterministic).
  v1 is the deterministic high-η limit (bidirectional Dijkstra). A moderate-η *stochastic*
  field-guided grower is a dreamer-adjacent explorer — parked until v1 ships and the dreamer
  integration has its own gate.

## 7. The weave — where each object lives in the built system

**Zone discipline (all instruments):** read-side, derived-tier, model-free — the spine's own
posture (`core/temporal/spine.py` header invariants). No store writes beyond eval readings; no
wall-clock as an ordering key ever (Law C4); snapshots only at certified cuts (bp-055); grid +
fingerprint pinning copied from `FibersEvidence` (`eval/harness/fibers.py`) so every reading
stays independently recoverable.

**Consumer map:**

| Object | Home | Consumes | Status |
|---|---|---|---|
| σ\*/MST instrument (C2) | `eval/harness/` (new module) | σ-graph builder (`core/dreaming/graph.py`), certified cuts | buildable NOW; cheapest |
| (σ,t) conductance profile (C3) | `eval/harness/` (new module) | same graphs; Laplacian/heat-kernel (diffusion machinery precedent: `core/dreaming/cluster.py`) | buildable; needs weight pinning (C4 lever) |
| Bridge search v1 (C5+C7) | eval-side, report-layer | scope meets (`core/scope.py`), registered atlas (bp-056), typed edges | buildable; v1 = bidirectional Dijkstra over composable edges, budget-bounded (arc / no-arc-at-this-voltage) |
| Helix detector v1 (C6) | eval-side over the idea quotient | **uuid-identity (BLOCKER)**, spine proper time, spanning-tree cycles | blocked on π |
| Reconnection events (C3 corollary) | rider on the conductance profile | consecutive-cut deltas + spine event attribution | rides item 2 |

**Dependency spotlight — uuid-identity now has THREE consumers:** Track D (its original
wave-4 listing), the helix detector's π, and the SF-a claim-identity-flicker family (the same
identity problem at claim grain — one design should serve all three). Its wave-4 priority
strengthens accordingly.

**Falsifier battery** (executable, owner-ratifiable in his native mode):
1. Ultrametric inequality for σ\* on sampled real triples: `σ*(A,C) ≥ min(σ*(A,B), σ*(B,C))`.
2. MST-realization cross-check: σ\* via MST == σ\* via direct union-find sweep over the grid.
3. Rayleigh along the filtration: conductance non-decreasing as σ loosens, per real cut.
4. Dense-degeneracy self-diagnostic: `corr(R_eff, 1/d_A+1/d_B)` at loosest σ reported with
   every profile; ≈1 ⇒ the diffusion column is authoritative (the instrument says so itself).
5. Pitch soundness: gain ≡ 0 on every spatial-only cycle; gain > 0 on every all-forward
   revisitation walk (synthetic first; real once π lands).
6. Bridge refusal: a chain crossing atlas-uncovered clocks REFUSES (bp-056's conservatism
   observed at chain level) — never a silently-computed cross-clock argument.
7. Law-C4 tooth: no instrument reads a wall timestamp as an ordering key (AST/grep test, house
   style).
8. Arc correctness + refusal: the bidirectional meet-point chain equals the global weighted
   geodesic on the composable subgraph (meet-rule correctness); and with a budget set below the
   pair's requirement, the search REFUSES with the quantified no-arc report — never a partial
   path presented as a bridge.

**Levers (THRESH-style dicts first, `ops/levers.py` only by later owner-visible act, per
bp-057 precedent):** the t-grid; the activity exponent/sign `s` (C4 — the metal/semiconductor
question); the helix pitch threshold; β compactification (deferred with the magnetic lane).

**Non-goals:** no writes; no dreamer modification; no auto-surfacing of bridges into the
mirror (E6-style tenancy later); no Track-D correlator work; no claim-matching build (SF-a has
its own re-entry); no magnetic/spectral build ahead of its own lane's gate.

## 8. Graduation skeleton + owner decisions + open problems

**Recommended graduation path** — fold this pass + both companion capsules into the
`retrieval-and-temporal-scaling` design note when it is drafted (connectivity IS retrieval;
one gate, shared substrate), with the instrument family as its §3. Sketch of the plan tranche
that falls out post-ratification (estimates in the house unit):
1. σ\*/MST instrument + falsifiers 1–2, 7 (~150–180k, no new deps) — the keystone, computable now.
2. (σ,t) conductance profile + reconnection rider + falsifiers 3–4 (~200k; needs C4 sign lever
   pinned as a THRESH default, sweepable thereafter).
3. Bridge search v1 + falsifier 6 (~200k; same-stratum chains + atlas-checked cross-clock).
4. Helix detector v1 + falsifier 5 (~180k; **gated on uuid-identity landing first**).

**OWNER DECISIONS surfaced:**
- **D1 (empirical, sweepable):** the C4 sign — churn as resistance or conductance ("metal vs
  semiconductor"). Recommend: ship `s = 0` (neutral) as the THRESH default; let the first
  sweep move it; never decide by taste what a curve can decide.
- **D2 (chain-of-artifacts):** fold into `retrieval-and-temporal-scaling`'s design note (my
  recommendation) vs a standalone `dn-connectivity-instruments`. One gate is cheaper and the
  substrate is shared.
- **D3 (scheduling):** uuid-identity's priority, now three-consumer. It fronts the helix and
  Track D both.

**Open problems (honest gaps, parked with re-entry):**
- Certified-cut lattice closure: are meets/joins of certified cuts certifiable (certificate
  composition across cuts)? Re-entry: any instrument wanting cut *arithmetic* rather than cut
  *sampling*.
- Joint vs pairwise co-presence for snapshot-realizability of spatial cycles (the 1-D Helly
  argument does not lift to the cut lattice unmodified). Re-entry: the helix detector's
  treatment of spatial-cycle baselines.
- Grain: chunk-level vs claim-level conductance (the source-set relation supplies the
  group-by; which grain is owner-meaningful is likely query-dependent). Re-entry: instrument 2's
  design review.
- Journey semantics for arguments: temporal reachability is asymmetric; arguments may cite the
  past (backward traversal = citation — allowed?) while following supersession forward.
  Default: allow both, annotate direction per hop. Re-entry: bridge-search v1 design.

## 9. Pre-ratification errata (2026-07-17, adversarial pass over the draft note)

Eight wrinkles found and fixed in `dn-connectivity-instruments` before ratification; recorded
here so the derivation trail matches the decided text:
1. **Index signatures** — the blanket "(σ,t,cut) on every reading" law was over-strong (σ\* has
   no walk, hence no t); instruments now declare per-instrument signatures.
2. **σ\* grid-relativity** — the MST is built on the *loosest-grid* graph with the grid pinned
   in evidence (FibersEvidence pattern); off-grid pairs report "not connected within grid",
   never an extrapolated value (also removes any implicit O(V²) full-graph claim).
3. **Attribution phrasing** — "a jump is attributable to..." over-claimed; corrected to: a rise
   *requires* new edges (Rayleigh), contributors enumerable + leave-one-out *verified*.
4. **α and the edge convention were unpinned** — `α = 1` default joins the THRESH dict;
   `a_•(u,v)` = mean of endpoint strata's statistics (v1 convention, revisit at item-2 review).
5. **Cross-stratum gain was under-defined** — the primary gain is now the ℤ interval count
   (total, strictly positive per forward hop); per-stratum proper time is the refinement —
   which also insulates the detector from the OPEN finding-0090 proper-time erratum.
6. **Helix criterion clarified** — nonzero pitch, NOT snapshot-invisibility: a citation cycle
   can be co-present at one cut yet carry positive pitch (C6's falsifier updated accordingly —
   the earlier "visible at a cut ⇒ bug" clause would have flagged correct detections).
7. **"Composable subgraph" was ill-typed** — composability is a path property (running meet =
   state); C7's search is label-setting over (node, scope) states with sound dominance (scopes
   only narrow); the correctness falsifier now references an exhaustive small-instance oracle.
8. **Grain grounding** — the built `MirrorGraph` is note-centroid grain (not chunk); the parked
   grain default now says so.
