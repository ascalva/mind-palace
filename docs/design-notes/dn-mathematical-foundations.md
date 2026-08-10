---
type: design-note
id: dn-mathematical-foundations
track: mathematical-foundations  # NEW manifest, minted in this PR (docs/tracks/mathematical-foundations.md) — ⚑ the owner renames or rejects the coordinate at the merge
status: draft                    # provenance description, never a gate (merge-gated regime, 2026-07-28)
created: 2026-08-09
updated: 2026-08-09
links:
  - docs/brainstorms/mathematical-foundations.md        # THE WARRANT (PR #42, capture branch — lands first; see Sequencing) — owner seed 1 + the structure-instantiation bridge
  - docs/design-notes/dn-research-register.md           # THE SIBLING (§1.3) — same PR #47; the §2.3 claim ladder consumed here; its parked Lean row now points at §2.4 below
  - https://github.com/ascalva/mind-palace/issues/48    # the Lean investigation record — load-bearing external claims VERIFIED 2026-08-09 (its one [FROM MEMORY] row unleaned-on)
  - docs/design-notes/connectivity-instruments.md       # RATIFIED — CN-1..CN-7: σ*, the (σ,t) conductance profile, sign law, χ_s, forced helix
  - docs/design-notes/core-graph-instruments.md         # RATIFIED — P1 core self-containment, P3 one Laplacian, P4 no silent metric change
  - docs/design-notes/magnetic-laplacian.md             # RATIFIED (design-only) — the L^{(q)} fiber family; flux = abelianized holonomy
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED — A1–A8; π_active/σ_*, 𝔸 = d + τ, K(β), β*
  - docs/design-notes/core-query-protocol.md            # RATIFIED — §2.2 the query-mode algebra (tropical ↔ heat-kernel ↔ Gram via K(β))
  - docs/design-notes/vector-membership-store.md        # IN FORCE by owner merges (150a190…c62ea7c lineage; status field is provenance) — the §4 membership math
  - docs/design-notes/fiber-geometry.md                 # RATIFIED — FG-0 alphabet, FG-5 block-diagonal sheaf Laplacian
  - docs/NOTATION.md                                    # the symbol authority — staleness flagged in Cross-references, not fixed here
  - docs/WHITEPAPER-FORMAL-PROPERTIES.md                # the existing invariant tiering + property-test discharge scheme this note EXTENDS
supersedes: null
superseded_by: null
warrant: docs/brainstorms/mathematical-foundations.md   # owner seed 1, 2026-08-09 — quoted in the opening blockquote; reaches main via PR #42, sequenced first
---

# Mathematical foundations — structure-instantiation, the laws ledger, and the Lean ladder

> Composed at **fable** (`claude-fable-5`, xhigh, 2026-08-09). Per the
> banner-unreliability lesson (finding-0147, frozen history: a composed-at banner is a
> claim, not a proof), the owner cross-checks usage at review. Agent-drafted, filed as
> `draft` on a branch. Under the merge-gated regime (owner ruling 2026-07-28) nobody
> flips a status — **the owner's merge of this PR is ratification**, and the `status:`
> line above is provenance description, never a gate. If this text is on `main`, the
> owner put it there.
>
> **Sequencing:** this note rides **PR #47 beside its sibling,
> dn-research-register** (the research-register design — the claim ladder this note
> consumes), per owner seed 3 (2026-08-09: *"draft the foundations note, the laws
> ledger AND the Lean ladder, the full treatment … PR #47 can contain all the design
> notes, it's an overhaul"*). The warrant capsule lives only on the capture branch of
> PR #42 and is not at HEAD (`68d8d39`); that PR lands first — or this branch stacks
> on it — so both notes' warrant paths resolve in the tree the reviewer reads. **A
> third dependency:** the memberships store (the bp-152 lineage — the
> vector-membership-store build) is *staged in the owner's checkout, on no branch*;
> the MEM family reads it, so MF-1 is entry-gated on that store landing by its own
> PR.

> *"the project's math is extensive — query algebras, Laplacians, curvature, sets and
> memberships, type correctness. What axioms do they rely on; can we derive from first
> principles; would that empower us; what stable foundation proves correctness? A
> captured idea is like a theorem/proposed definition — how far does the rabbit hole of
> implications propagate? Is foundational math the bridge to other branches — 'our mini
> Langlands'? Is this where a proof-based language comes in?"* — owner, 2026-08-09
> (seed 1).
>
> The answer, in one sentence: **the palace's correctness does not rest on axiomatic
> descent — it rests on structure-instantiation: every component names the known
> structure it is a model of and imports that structure's theorems under stated
> hypotheses; the laws ledger makes those namings auditable law by law, and the Lean
> ladder makes the finite algebraic core machine-checkable, one priced rung at a
> time.**

## 1. Purpose and scope

### 1.1 What this note decides

Five decisions, presented as one note because they are one move — the palace saying
exactly what mathematics it stands on, and building the two artifacts that keep the
saying honest:

1. **The frame** (§2.1) — correctness by structure-instantiation, not first-principles
   derivation. The palace's mathematics is finite in substance; "what axioms do we
   rely on" resolves into "which structure is each component a model of, under which
   hypotheses" — and the implemented correspondences between structures are tabled as
   the working bridges.
2. **The laws ledger** (§2.2) — a single authored index, `docs/LAWS.md`, one row per
   law: statement with arithmetic domain, claimed structure, code anchor, ladder
   label, named falsifier test, formal status. The ledger *indexes* — it restates no
   proof, no test, no Lean statement. A law without its falsifier test is at most
   Conjecture, and the ledger makes that visible. That visibility is the point.
3. **Structure honesty** (§2.3) — the true structure of each component, named as
   implemented; the known Boolean-algebra tension over memberships resolved on the
   record's side; the temporal/query algebra's pinned-vs-conjectural line reported.
4. **The Lean ladder** (§2.4) — the L0–L4 adoption ladder from the Lean investigation
   (issue #48, the Lean-adoption investigation; load-bearing external claims verified 2026-08-09)
   adopted as design: `formal/` as a zero-coupling sibling package, L1
   statements-as-specs with a sorry-count ratchet, L2 agent-proved discharge, L3/L4
   parked with re-entry.
5. **Float-epsilon as substance** (§2.5) — the arithmetic-domain column is mandatory
   ledger schema; the three arithmetic tiers the codebase already practices are named
   and bound. This consumes the register's rule R7 and §2.3.3 (dn-research-register —
   the sibling); the rule lives there, the substance lives here.

How far the rabbit hole of implications propagates — capture-as-conjecture, deductive
closure through labeled steps — is the sibling's territory: a captured idea enters as
**Conjecture** and its implications propagate only through falsifier-carrying labeled
claims (dn-research-register §2.2, the capture → conjecture mapping; §2.3, the
ladder). Cited here, never repeated.

The track is `mathematical-foundations` — a new lane, minted with this note (manifest
in this PR; the scored-beliefs/erratum-relation precedent: an agent mints the
coordinate alongside its founding note and the owner adjudicates it at the merge). No
existing lane honestly fits: `workflow` owns how work is framed and recorded — exactly
why the sibling lives there, and why its §1.3 carves this arc *out*; the foundations
substance (Laplacians, curvature, memberships, query algebras, the formal layer)
spans core-wide mathematics no manifest owns.

### 1.2 Non-goals (load-bearing — read at ratification)

1. **No Lean in `core/` — ever, in either direction.** `formal/` is a sibling package
   like `eval/`: never imported by `core/`, importing nothing from it. The spec layer
   is documentation-with-a-kernel-check, zero runtime coupling. [ESTABLISHED — core
   self-containment (dn-core-graph-instruments P1) + issue #48 Axis D.]
2. **L3 and L4 are not licensed.** Float-ε formal bridges (FloatSpec-style) enter
   per-claim only, and verified kernels stay parked; both carry recorded re-entry
   conditions (Parked decisions). [ESTABLISHED — the ladder's own pricing, issue #48.]
3. **Ollivier–Ricci and Cheeger formalization are not licensed.** Both are absent from
   Mathlib (issue #48, verified 2026-08-09; the W₁/KR layer of arXiv:2607.08986 is
   the recorded on-ramp for the *Ollivier* side specifically); the house curvature
   floor is Forman (§2.3.3), and L1
   formalizes definitions and stated laws only. [ESTABLISHED.]
4. **No golden-set or eval-fixed-point touch.** `CONSTITUTION.md`, `eval/golden/**`,
   `eval/golden.py` are denylist surfaces; nothing here proposes them.
   [ESTABLISHED — the fixed points.]
5. **The ladder labels are consumed, never redefined.** The rungs, the agent ceiling
   (Proposition-with-checkable-inline-proof / Claim-with-named-falsifier), the two
   Proposition guards, the reserved words, and the arithmetic-domain rule are the
   sibling's (dn-research-register §2.3, frozen there); this note and the ledger use
   them as given. [ESTABLISHED — the §1.3 boundary, both notes.]
6. **`docs/NOTATION.md` stays the symbol authority.** Its Family-5 staleness (it still
   says `core/complex/` "does not exist yet") is flagged in Cross-references, not
   silently fixed; new ratified symbols (σ*, L^{(q)}, [d,τ], K(β), χ_s, M ⊆ V×O)
   enter the table in their own surgical PR. [INFERENCE — a notation refresh is its
   own change; folding it in here would smuggle scope.]
7. **No external submission.** The register's venue park stands (dn-research-register,
   Parked decisions). [ESTABLISHED.]
8. **The research Question stays owner-only.** This note names structures; it does not
   author the study's Question. [ESTABLISHED — standing rule.]
9. **Nothing is restated that lives elsewhere.** Proofs live in the ratified notes and
   their fable-pass capsules; enforcement lives in tests; formal statements will live
   in `formal/`; the ledger and this note index and cite. [ESTABLISHED — DRY is a
   defect, not a nit.]
10. **No `core/` code changes are licensed.** MF-2/MF-3 write tests only; a defect a
    new falsifier exposes lands as a `type:defect` issue, never a drive-by fix.
    [INFERENCE — a falsifier batch and a behavior change never share a plan.]

### 1.3 The sibling boundary — pointing back

The warrant capsule carries two arcs; the sibling (dn-research-register) is the
register arc and this note is the foundations arc. The shared boundary, honored from
this side: the claim-ladder labels of its §2.3 are *consumed* here — every ledger row
lands as a labeled claim with a falsifier, in the sibling's vocabulary, and neither
note redefines the labels without the other. The float-epsilon caveat appears in both
homes as designed: there as a register rule (its §2.3.3/R7), here as substance
(§2.5). And the sibling's parked Lean row is re-pointed at this note's ladder by the
surgical edits riding this same PR: default **L0 — ladder specified here (§2.4)**;
re-entry for L1, **the laws ledger's first laws exist to state** (issue #48's own
proposed wording, applied under owner seed 3's direction).

## 2. Principles / decision

### 2.1 The frame — correctness is structure-instantiation, not axiomatic descent

**Decision.** The palace's foundation is the discipline that each mathematical
component (a) **names the known structure it is a model of**, (b) **states the
hypotheses** under which it instantiates that structure, and (c) **imports that
structure's theorems** only under those hypotheses. "Model of a known structure" is
the sibling's own lexicon row for structure-instantiation; the register note carries
the term, this note makes it the load-bearing frame.

Why this and not first principles: the mathematics is **finite in substance**. The
Laplacian family is finite real symmetric matrices (`core/kernel/complex/laplacian.py`
— L, L_sym under w ≥ 0, L̄ via its signed identity: PSD quadratic forms on finite
weighted graphs, each under its stated hypothesis); the built
curvature is integer combinatorics on finite supports (`core/kernel/complex/curvature.py`
— Forman, exact over ℤ; the finite-LP object is the *deferred* Ollivier enrichment,
not the floor, §2.3.3); memberships are a finite coordinate-keyed relation
(`core/stores/memberships.py`, §2.3.1); embeddings are finite-dimensional
inner-product spaces; the temporal operators are finite-matrix operator algebra
(dn-temporal-retrieval-algebra). Reliance sits far below ZFC — finite sets, finite
linear algebra, elementary order theory and probability. Deriving these "from first
principles" would add no power the finite structures do not already give; what *does*
add power is the transfer of theorems: when the hypotheses hold, the structure's
results hold for free — and the hypotheses do real work. Mathlib's
components-equal-nullity theorem (a `SimpleGraph.lapMatrix` result — **unweighted**)
is the proof *substrate* for `spectral.py`'s per-component contract (issue #48);
binding it to the palace's **weighted** L takes one short house step (w ≥ 0; the
kernel reduces to the unweighted support graph's), stated on the LAP rows and priced
into MF-4.

**The bridges — the working correspondences.** Owner seed 1 asks whether foundational
math is "the bridge to other branches — our mini Langlands". The honest answer: the
Langlands analogy lands not as a program but as the correspondences the palace has
already implemented *between* its structures. (The metaphor stays internal per the
sibling's R5 — never in external register.) The implemented bridges, each cited to
its home and restated nowhere:

| bridge | the correspondence, one clause | home |
|---|---|---|
| graph ↔ operator | weighted σ-graph ↔ L = D − A, the two-point L⁺ form R_eff, the heat kernel e^{−tL} | core/kernel/complex/laplacian.py; core/graph/conductance.py (CN-3/CN-4; P3/P4) |
| direction ↔ gauge | direction/sign data ↔ the magnetic fibers L^{(q)}; flux = abelianized holonomy; L̄ = the q=1/2 fiber | dn-magnetic-laplacian (design-only; q=0 built) |
| curvature ↔ transport | support combinatorics ↔ the Forman floor (built, exact ℤ); the OT side (Ollivier over W₁) deferred, PD-c | core/kernel/complex/curvature.py (§2.3.3) |
| membership ↔ keyed relation | occupancy ↔ keyed partial function; multiset atom projection; Boolean support image | memberships.py; dn-vector-membership-store §4 (§2.3.1) |
| time ↔ operator algebra | supersession ↔ π_active/σ_* transport, 𝔸 = d + τ, the dilation of T_active | dn-temporal-retrieval-algebra A1–A8 (§2.3.2) |
| query ↔ semiring / kernel cone | retrieval modes ↔ one K(β) deformation: tropical (min,+) ↔ heat kernel ↔ Gram | dn-core-query-protocol §2.2 (§2.3.2) |

Each row is a correspondence between two named structures, already load-bearing in
ratified text or shipped code. The frame's obligation is that every future
mathematical component adds its row — or says honestly that it has no structure to
name yet, which is a **Conjecture**-labeled row, not an absent one.

### 2.2 The laws ledger — one index that makes honesty visible

**Home and form.** `docs/LAWS.md` — a single authored artifact (verified absent at
HEAD; minted by MF-1). Not derived, not a skill, not per-module scatter: one file the
owner can read top to bottom, the `docs/lexicon.md` precedent from the sibling. Every
module docstring that carries an OBJECT/INVARIANT/ENFORCED header keeps it — the
ledger indexes those headers, it does not replace them.

**The row schema — seven columns, all mandatory.**

| column | carries |
|---|---|
| law id | family-prefixed: MEM-, LAP-, SPC-, CUT-, CND-, CRV- + number |
| statement | the law, one clause, **with its arithmetic domain** (exact ℤ/ℚ, or ε = <stated> over float64) — the §2.5 discipline |
| claimed structure | the known structure the law instantiates (§2.3's namings; standard names per the sibling's R5) |
| code anchor | file + defining symbol (`module.py::name`), resolved at HEAD; line numbers are gloss, never the key |
| ladder label | the sibling's §2.3.1 rung — consumed, never redefined |
| falsifier | the pytest node id (`file::test_name`) that would catch the law false — or `GAP`, which caps the label |
| formal status | the `formal/` statement/proof ref (§2.4) — or `—`; at seeding, uniformly `—` (no `.lean` exists at HEAD) |

**The single-sourcing discipline, stated as law.** The ledger *indexes*: proofs live
in the ratified notes and their capsules (cited by id), enforcement lives in the named
tests, formal statements live in `formal/`. The ledger never restates any of them — a
ledger row that carries a derivation is a defect. This is what keeps thirty rows
honest instead of thirty opportunities to drift.

**Resolution and repair, stated once.** Anchors resolve **at HEAD**: the MF-2 checker
asserts each anchored symbol exists and each falsifier node id is collected by
pytest. When a refactor moves a law's ground, the checker reds and **the refactoring
PR carries the row repair** — detection is mechanical, repair rides the PR that moved
the code. No standing sweep, no per-PR read-through duty; what the minimal checker
cannot see (statement drift against unmoved symbols) stays honestly parked (Parked
decisions).

**The label discipline, inherited.** Per the sibling's §2.3.2 item 3, each law lands
as a labeled claim — typically Claim, or Proposition with its paired falsifier — one
falsifier per law. The consequences this note adds as ledger policy: **a law whose
falsifier column reads `GAP` is at most Conjecture** — the falsifier described, not
yet run — matching the register's ceiling (a Claim requires its *named* falsifier;
seed cells write the target, e.g. `Conjecture → Prop at MF-2`). Two ledger-side
**annotations** qualify a rung without minting one: *(cited)* — a documented-only
theorem citation, never more than the rung it decorates; *(structural)* — a law
enforced by a structural scan rather than a numeric assertion. A **Proposition** row
bears its label at the law's home artifact: the checkable inline proof lives in the
home note, docstring, or test derivation, the statement cell cites that home, and
the ledger mirrors — never houses — the proof (single-sourcing). The ledger exists
precisely to make those caps visible instead of buried in docstrings.

**The seed inventory.** MF-1 seeds the ledger from the tables below — real laws, real
anchors, grounded at HEAD `68d8d39` plus the staged memberships store (the bp-152 lineage —
the vector-membership-store build plan; staged == worktree, verified). These tables are the graduation spec, terse
by design (anchors here are draft start-lines — **MF-1 composes them into symbol
anchors and pytest node ids per the schema**, lines demoted to gloss; statements
compressed; the ledger's structure and formal-status columns are composed at MF-1
from §2.3 and `—`): once MF-1 merges, the
ledger is authoritative and these tables are provenance. `GAP → MF-n` marks the
enforcement gaps §2.6 prices. Memberships first — the one family whose laws hold
exactly over ℤ, end to end.

**I. Memberships** (`core/stores/memberships.py`, staged; tests
`tests/unit/test_memberships.py`, staged — the house falsifier discipline at its most
developed):

| id | law (arithmetic domain) | anchor | label | falsifier |
|---|---|---|---|---|
| MEM-1 | keyed finite relation; atom projection a multiset; n_doc ≤ n_occ (exact, ℤ) | memberships.py:148 | Definition + Proposition | test_memberships.py:204 (two-rows witness) |
| MEM-2 | version fibers partition M: Σ\|fiber\| = \|M\| (exact, ℤ) | memberships.py:264 | Proposition | test_memberships.py:633 (seeded violating subclass) |
| MEM-3 | slot runs = adjacent-collapse RLE; \|edges\| = \|runs\|−1; a revert stays visible (exact, ℤ) | memberships.py:381 | Proposition + Claim | test_memberships.py:588 |
| MEM-4 | re-land is idempotent BY reconciliation, never by short-circuit — the C1 law (exact, ℤ) | memberships.py:243 | Claim | test_memberships.py:286 (exhibited wrong lander) |
| MEM-5 | currency selects one fiber per path; current_any(v) ⇔ n_doc(v,t) > 0 (exact, ℤ/Bool) | memberships.py:294 | Claim | test_memberships.py:653 (seeded drift flip) |
| MEM-6 | \|V\| monotone up; purge the one logged decrement — tombstones M, never deletes (exact, ℤ) | memberships.py:511 | Claim | test_memberships.py:671; :440 (the hole exists) |
| MEM-7 | chain fibers ⊆ version fibers, ⊊ iff an off-chain fiber exists (witnessed); side-branch atoms on no run (exact, ℤ) | memberships.py:392 | Claim | test_memberships.py:614 |
| MEM-8 | presence is typed by geometry: keyed (content_id) × (model, dim) (exact, strings) | memberships.py:191 | Claim | test_memberships.py:310 (same-embedder control) |
| MEM-9 | coverage(atom) ⊆ span(slot); strict for nested symbols; shell span = whole file (exact, ℤ) | memberships.py:94 | Proposition + Claim | test_memberships.py:147 (leaf control) |
| MEM-10 | crash orphans observable, invisible to default search; re-land adopts at zero embeds (exact, ℤ/Bool) | memberships.py:432 | Claim | test_memberships.py:479 (injection asserted) |
| MEM-11 | the kernel never imports the store; memberships enter as data (RowSource) | memberships.py:9 | Claim (structural) | test_memberships.py:228 (negative control) |

**II. Laplacian & balance** (`core/kernel/complex/laplacian.py`, `balance.py`) **and
spectral** (`core/complex/spectral.py`):

| id | law (arithmetic domain) | anchor | label | falsifier |
|---|---|---|---|---|
| LAP-1 | L·1 = 0 for L = D − A (exact weights: exact; f64: allclose 1e-8; route agreement ≤ 4·eps·max) | laplacian.py:26 | Proposition | test_complex.py:100; test_graph_boundary.py:69 |
| LAP-2 | xᵀLx = Σ w(x_u−x_v)² ≥ 0 (symmetric A, w ≥ 0); L̄ PSD via its signed identity (laplacian.py:52) | laplacian.py:1 | Conjecture → Prop at MF-2 | GAP — direct PSD untested |
| LAP-3 | dim ker L = #components (w > 0 on edges; SimpleGraph thm in Mathlib, weighted via support) | laplacian.py:27 | Conjecture (cited) | GAP — nullity never counted → MF-2 |
| LAP-4 | Spec(L_sym) ⊆ [0,2] (A ≥ 0); D^{−1/2} := 0 at degree 0 (ε = 1e-9, float64) | laplacian.py:33 | Proposition + Definition | test_complex.py:104; convention pointwise → MF-2 |
| LAP-5 | λ_min(L̄) = 0 ⇔ balanced (Hou/Kunegis); house reading: max over components (ε = 1e-6) | balance.py:28 | Claim (cited) | test_complex_properties.py:93 (converse: one instance) |
| LAP-6 | a triangle is frustrated ⇔ it carries an odd count of negative edges (exact, ℤ/2 parity) | balance.py:9 | Proposition | test_complex_properties.py:96 |
| SPC-1 | clustering is deterministic (fixed ramp v0, seed 0); ≥90% stable at 1e-3 noise (float64, platform-scoped) | spectral.py:32 | Hypothesis | test_complex_properties.py:35, :66 |
| SPC-2 | components are clustered independently, never merged (labels disjoint — exact, sets) | spectral.py:119 | Conjecture → Claim at MF-2 | GAP — behavioral only (test_complex.py:108) |

**III. Cut & conductance** (`core/complex/cut.py`; `core/graph/conductance.py`):

| id | law (arithmetic domain) | anchor | label | falsifier |
|---|---|---|---|---|
| CUT-1 | Φ(S) = w(∂S)/min(vol S, vol S̄) ∈ [0,1]; degenerate S → 0.0, no community → 1.0 — OPPOSITE alarms (float64) | cut.py:35 | Definition + Conjecture → Prop at MF-3 | GAP — untested |
| CUT-2 | Cheeger ½λ₂ ≤ h ≤ √(2λ₂), λ₂ of L_sym; h = min over ALL cuts (partition min bounds it above); computed nowhere | cut.py:7 | Remark | none owed — nothing depends on it |
| CUT-3 | grounding_cut = integer max-flow; monotone in capacities; chain bottleneck (dyadic ℚ, ×2¹⁰) | cut.py:70 | Prop. (cites max-flow min-cut) | test_structural_interpreters.py:88 |
| CND-1 | R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ per component; ∞ across components (rtol 1e-10; ∞ exact) | conductance.py:226 | Definition + Claim | test_conductance.py:206; graph_boundary:125 |
| CND-2 | a rise requires a weight-increased edge (Rayleigh, cited; ε = 1e-9); attribution = leave-one-out | conductance.py:441 | Claim (cited) | test_conductance.py:124; quality suite |
| CND-3 | every profile carries degeneracy diag corr(R_eff, 1/d_A + 1/d_B); ≥ 0.9 flips authority to finite-t (float64) | conductance.py:256 | Claim | test_conductance.py:150 |
| CND-4 | d_t² = Σ e^{−2tλ_k}(φ_k[i] − φ_k[j])² over the COMBINATORIAL L; a reading = the (σ×t) grid (f64) | conductance.py:239 | Proposition + Definition | test_conductance.py:163 |
| CND-5 | w = cos^α·exp(s_lat·a_lat − s_seq·a_seq); signs are law; magnitudes ship 0 ⇒ w = cos (IEEE-exact) | conductance.py:106 | Definition + Claim | test_conductance.py:260 (AST scan) |
| CND-6 | χ_s = chain/N_s ∈ (0,1] for window=None (the only wired call); None at N_s=0 (ℚ-valued, 1 f64 div) | conductance.py:375 | Proposition | test_conductance.py:314; windowed → MF-3 |

**IV. Curvature** (`core/kernel/complex/curvature.py` — Forman, not Ollivier; §2.3.3):

| id | law (arithmetic domain) | anchor | label | falsifier |
|---|---|---|---|---|
| CRV-1 | Ric_F = 4 − deg(u) − deg(v) + 3·\|△(u,v)\| on binarized support (exact, ℤ); the declared augmented-Forman variant | curvature.py:25 | Definition | exactness exercised by CRV-2 |
| CRV-2 | two m-cliques + one bridge: Ric_F(bridge) = 4 − 2m, the strict unique minimum (exact, ℤ) | test_structural_interpreters.py:26 | Proposition | its own paired property test |
| CRV-3 | most_negative_edges: κ ≤ 0 else argmin; (κ,i,j) tie-break; top_k cap (κ int-valued f64, == exact) | curvature.py:46 | Definition | GAP — untested (consumer: dreaming) → MF-3 |
| CRV-4 | Ollivier–Ricci over W₁ deliberately absent — Forman is the floor (issue #48: Mathlib lacks OT) | curvature.py:15 | Observation | the absence is stated in-code |

The property-test substrate is existing house practice, not a proposal: `hypothesis`
is already a dev dependency with a `tests/property/` tier, and
`docs/WHITEPAPER-FORMAL-PROPERTIES.md` already defines a per-invariant discharge
scheme. **The catalog boundary, stated once:** the whitepaper's I-rows are
architecture invariants and stay its own; `docs/LAWS.md` owns algebraic laws; the
§A.5 family-5 obligations the whitepaper delegates to the REASONING-COMPLEX
companions are absorbed here as rows, and the H-N ids those companions and test
docstrings already carry (H4/H5/H6 …) are cross-referenced in the row statements —
MEM-/LAP-/SPC-/CUT-/CND-/CRV- become the per-law coordinates going forward. §A.5's
own staleness (it still says `core/complex/` "does not exist yet") is flagged here
exactly as NOTATION.md's is, into the same parked refresh lane. The ledger extends
the tiering; it does not invent a parallel one.

### 2.3 Structure honesty — naming what is actually instantiated

#### 2.3.1 Memberships — the true structure, settled

The capture capsule (PR #42) says "memberships form a finite Boolean algebra." The
implemented store says otherwise, in its own header: `core/stores/memberships.py:5` —
*"INVARIANT: MULTISET, never a set."* This note resolves the tension on the record's
side, and sharpens it, because "a multiset" is itself lossy about what is built:

**Definition (the structure as coded).** The membership relation M is a **finite
partial function on coordinate space** — the SQLite primary key
`(path, blob_sha, layer, chunk_index)` makes each row unique by *occupancy
coordinates*, with `content_id` outside the key. Three derived layers, each real:

- **Version fibers are finite sequences.** Each fiber M(path, blob_sha) is totally
  ordered by `chunk_index` and read back in that order — a *word* over the atom
  alphabet, not a bare bag (`memberships.py:264`; order asserted by
  `test_memberships.py:133`). Held-by-whom, said plainly: the PK enforces uniqueness
  per (path, blob_sha, *layer*, chunk_index); fiber-wide total order and
  one-current-fiber-per-path are the **writer's** invariants (the pure derivation;
  `reconcile_currency`'s postcondition) — stated hypotheses for any L1 statement,
  not schema constraints.
- **The atom projection is a multiset.** Pushing rows along π: row ↦ content_id gives
  the free-commutative-monoid reading: n_occ(v) = multiplicity (row count), and the
  coarser path pushforward gives n_doc(v) = document frequency; n_doc ≤ n_occ, strict
  on the enforced duplicate-window witness (MEM-1). Two byte-identical windows are two
  rows — the schema-enforced counterexample to any set reading.
- **Boolean structure appears exactly once: the support image.** The current-view
  predicate current_any(v) ⇔ n_doc(v,t) > 0 maps into 𝒫(atoms), and the query-visible
  read `currently_held` returns exactly that support set — **Observation:** the
  *image* of the support map lives in a finite Boolean algebra of subsets.
  (`known_atoms` is a different surface: the embedder-typed atoms-ledger read —
  MEM-8's relation — which includes zero-occupancy crash orphans, so it is *not*
  the support image.) That is a fact
  about the image, not about the store: no store operation is claimed to respect
  Boolean structure (land/purge are not ∨/∧-homomorphisms on views). Any stronger
  reading — Boolean-algebra laws holding for the view under the store's dynamics — is
  **Conjecture**, unheld and untested; its falsifier, named at birth per the ladder:
  a view-level ∨-homomorphism check across a land/purge pair (nothing claims it
  commutes). The capsule's sentence, per the ladder, is
  refuted as a statement about occupancies and demoted to that Conjecture about the
  current-view image.

The laws the structure carries are the MEM rows of §2.2 — fiber idempotence held *by
reconciliation* rather than by skipping (MEM-4, the C1 law, with the wrong lander
exhibited in a mutation test), purge-tombstone monotonicity (MEM-6), and
currency-as-cache coherence (MEM-5) chief among them. The domain claim worth its own
sentence: **the memberships family is pure ℤ/Boolean/string — zero floats — so every
one of its ledger rows may claim "holds exactly," with no ε anywhere.** It is the one
component where exactness is fully real, which is why it seeds first.

#### 2.3.2 The temporal and query algebras — pinned vs. conjectural

What is **pinned**, by ratified text (cited, never restated here):
dn-temporal-retrieval-algebra (the temporal-retrieval algebra) pins the two mode-3
operators and their non-interchangeability (π_active a contraction and not a chain
map; σ_* a chain map), Theorem A1's K(β) family with its two endpoints and the
convergence identity, the six A3 results (the [d,τ] severed-citation support formula,
𝔸² = [d,τ] + τ², the dilation reading, the owner-as-only-energy-source contraction),
A7's apophenia discriminator, and A8's β* finiteness criterion.
dn-core-query-protocol §2.2 pins the query-mode algebra: modes 1a/1b/2/3, the
tropical-to-heat-kernel deformation via Maslov dequantization, the PSD-kernel cone
operations, Moore–Aronszajn (not Mercer) as the mode-2 warrant.

What remains **conjectural or open**, honestly: the diamond/τ²-coherence closure
(TA-c) is a *sketch* by the ratified note's own grading — and dn-magnetic-laplacian
refuted its abelian-closure form three ways; the TA-a..e and PD-a/b/c parks (their notes' own parked-decision ledgers) stand,
re-entered only through their own named gates. This note reopens none of them.

The register-honesty caveat this note adds: those ratified results are
prose-proof-warranted (the fable-pass capsules, cited by their notes) and their
labels are merged provenance — this note relabels nothing. What the ledger records is
the *formal* column: uniformly `—` today, honestly. The L1/L2 rungs (§2.4) target the
finite/algebraic core first (memberships, Laplacian PSD/nullity, L⁺ symmetry); the
temporal algebra's analytic results are not first-batch material and are not promised.

#### 2.3.3 Curvature — Forman is the floor

**Observation.** The implemented curvature is the *augmented Forman–Ricci* variant on
the binarized support — pure degree-and-triangle combinatorics, integer-valued, no
optimization anywhere (`core/kernel/complex/curvature.py:25`, CRV-1). Ollivier–Ricci
over W₁ is *deliberately not implemented* (`curvature.py:15`) — it is the parked PD-c
enrichment, and the finite Kantorovich LP enters the palace only when that park
re-enters. Two corrections ride this naming, neither weakening a verified status:
the capsule's "curvature = finite LP" describes the deferred enrichment, not the
shipped floor; and the Lean report's Axis-A gloss of `curvature.py` as
"Ollivier-Ricci over W₁" is a loose *target description* — its Mathlib-absence
verdicts for Ollivier and Cheeger stand exactly as verified (issue #48). The ledger
anchors house curvature on Forman (CRV-1/2/3) and carries the OT side as the honest
absence (CRV-4).

### 2.4 The Lean ladder — L0–L4 adopted as design

**Decision.** The four-rung adoption ladder proposed by the Lean investigation
(issue #48 — Mathlib coverage, Plausible, FloatSpec, lean-action, and the agent-era
cost premise all verified there 2026-08-09; this note cites and does not re-verify)
is adopted as design. The investigation's own boundary holds: the ladder is
foundations-arc substance, so it lands here, and the sibling's parked row now points
at this section (§1.3).

- **L0 — today.** Nothing. No `.lean` exists in the repo (verified at HEAD). The
  ladder's default resting state, and where it retracts to if L1 fails its falsifier.
- **L1 — statements as specs** (licensed: MF-4). `formal/` — a sibling lake package
  with **zero import coupling with `core/` in either direction** (non-goal 1):
  `lakefile` + pinned `lean-toolchain`, Mathlib as the dependency, cache via
  `lake exe cache get`. Lean *statements* of the first ledgered laws — the memberships
  relation/multiset laws (MEM-1/2/3/5), L PSD and **L·1 = 0 for the combinatorial L**
  (the report's bundling corrected: zero row sums is a law of L, not of L_sym, whose
  kernel vector is D^{1/2}·1), L_sym PSD, L⁺ symmetry/PSD — each carrying a
  **Plausible counterexample attack** (the falsifiers-before-proofs epistemology as a
  Lean tactic). Proofs taken where Mathlib gives them directly: the named `SimpleGraph.lapMatrix`
  lemmas (`isPosSemidef_lapMatrix`, components-equal-nullity — issue #48) discharge
  the **binarized-support** statements in one line, and the weighted forms take the
  small house reduction lemma (w ≥ 0 — priced here, not free); `sorry` elsewhere. **The sorry-count ratchet — review-enforced in the advisory era, machine-enforced
  at the flip:** `formal/sorry-budget` records one integer; the CI job (MF-5) counts
  `sorry` occurrences after `lake build`, fails when count > budget, and **asserts
  the axiom escape shut** (`axiom`/`admit` grepped to zero outside Mathlib — every
  declaration rests on Lean's three standard axioms alone); a diff that raises the
  budget, lowers the count by deleting or weakening statements, or swaps `sorry` for
  an axiom is the defect MFF-3 names. Every formal statement carries
  its ledger law id in a comment, and the ledger's formal column points back — the
  two-sided cross-reference MFF-4 patrols.
- **L2 — proofs of the finite/algebraic core** (licensed with entry condition: MF-6).
  Discharge L1 obligations over exact arithmetic, agent-authored under supervision —
  the mathematician-directs-AI workflow the investigation verified at
  research scale (arXiv:2607.08986: headline theorems in about a week, the full
  299-declaration development in about a month), applied at palace scale. This
  unlocks the sibling's Theorem rung honestly: **Theorem (machine-checked,
  `formal/...`)** — reachable without lowering its price.
- **L3 — the numerical bridge.** FloatSpec-style float-ε models, entered **per-claim
  only**, where a design claim demands a machine-checked ε-bound. Parked with
  re-entry (Parked decisions); not licensed (non-goal 2).
- **L4 — verified kernels.** Parked. No palace claim needs it (issue #48).

**The bridge stays two-sided.** Lean never proves the NumPy (issue #48 Axis B): Lean
states and proves laws over exact arithmetic; Hypothesis property-tests the Python
against the same laws with tolerance bounds; the artifacts cross-reference by law id.
One law, two independent attack surfaces — the ledger is the join.

**CI, advisory before required.** MF-5 wires `lean-action` (elan install,
`lake build`, Mathlib cache) as an **advisory** job. The flip to required is the
owner's hand alone, after a stated stability window: the advisory job green on every
merge for four consecutive weeks with no fix-forward commit targeting `formal/`
breakage. Until then a red lean job blocks nothing — it informs.

**The rung falsifier, carried verbatim in force** (issue #48): if the statement layer
never catches a mis-stated law that Hypothesis alone missed, by the third law batch,
L1 is decoration and retracts to L0 — MFF-5, and the un-minted rungs above it die
with it.

### 2.5 Float-epsilon as substance — the three arithmetic tiers

The sibling's rule (its §2.3.3 and R7): every algebraic or equality claim states its
arithmetic domain, because float addition is non-associative and exact-equality claims
over floats are precision theater. Consumed here as **mandatory ledger schema** — the
statement column carries the domain or the row is malformed. The substance this note
adds is that the codebase already practices three separable tiers, which the ledger
names per row:

1. **Exact domains — where equality is real.** Memberships (pure ℤ/Bool/string, zero
   floats); Forman curvature (integer closed forms asserted with `==` — sound
   *because* integer-valued); grounding_cut (integer capacities
   fixed-point ×2¹⁰ = 1024, so flow values are dyadic rationals exactly representable
   in float64 — the one deliberate escape from float arithmetic). Exact-equality
   claims are licensed here and only here.
2. **Ulp-classed reassociation — where float error is bounded by construction.** The
   `test_graph_boundary.py` doctrine, adopted as the ledger's model entry (LAP-1):
   Laplacian off-diagonals exact, degree sums within 4·eps·max — with the written
   rule that reassociation is not a metric change and O(1) divergence is a P4 stop;
   R_eff route-invariance at rtol 1e-10, "generous over ulp noise, catastrophically
   failed by any real metric change."
3. **Named tolerance constants — where ε is doctrine.** 1e-6 (balance zero —
   test-enforced in the property suite; `is_balanced` itself ships `tol=1e-8`), 1e-9
   (Rayleigh slack, spectrum bounds), 1e-12 (zero tests), 0.9 (degeneracy authority)
   — deliberately segregated from tunable magnitudes (`conductance.py:159-160`: *"a
   tolerance (module constant), not a tunable magnitude — it stays OUT of
   `CONDUCTANCE_THRESH`"*; the :96 header comment states the same law). Ledger rows
   cite the constant they are enforced at, naming the enforcing site when it differs
   from the shipped default.

χ_s sits deliberately *between* tiers, and its row says so: ℚ-valued in substance (a
ratio of small integers) but computed as one float64 true division
(`conductance.py:390`) — `= 1.0` and the `≤ 1` bound are exact comparisons (n/n = 1.0
exactly; (n−1)/n rounds strictly below 1.0 for realistic N_s), general equality is
not, and its own falsifier asserts `pytest.approx` (test_conductance.py:329), never
`==`. (And the (0,1] range law is stated **for `window=None`** — the only wired call;
a windowed numerator counts full-stratum chains, so the bound there is a stated
hypothesis, recorded on CND-6 and closed at MF-3.)

Hypothesis falsifiers are tolerance-bounded accordingly; a falsifier asserting exact
equality over a tier-2/3 quantity is itself a defect the ledger review catches.

### 2.6 What the ledger surfaces first — the enforced-vs-documented gap

The seeding's immediate yield is the gap list, priced into MF-2/MF-3: **PSD of L and
L̄** as direct assertions and **dim ker L = #components** (documented-only in Python
while machine-checked in Mathlib by name — simultaneously the weakest local
enforcement and the cheapest honest L1 statement, issue #48); **Φ(S)** and
`min_conductance` (no direct unit test — only downstream range assertions — while
carrying two *opposite-direction* degenerate conventions: degenerate S → 0.0
"maximally sealed" vs. no qualifying community → 1.0 "healthy", both definitional,
neither tested); **most_negative_edges'** emission rule (consumed by dreaming, zero
direct tests); the **isolated-node convention** pointwise; **never-merge-components**
directly. Where Mathlib has the theorem and the local suite does not even count the
nullity, the honest order of work is: state the law in the ledger (MF-1), test it in
Python (MF-2/3), state it in Lean (MF-4), prove it (MF-6).

## 3. Consequences

**On the owner's merge of this note, and not before** — six graduation licenses,
session-sized, dependency-ordered, split at graduation, named **MF-N** (mathematical
foundations) per the sibling's unit-naming precedent (WF-N → RR-N → MF-N). All plans
land `proposed`; the owner's merge or instruction is the readiness signal. Dispatch
is serialized (the budget rule).

- **MF-1 — the ledger seeded** (docs-only; entry: the bp-152 store merged — see
  Sequencing). Deliverable: `docs/LAWS.md` minted with
  the §2.2 schema and the full seed inventory (~30 rows, memberships family first,
  riding the staged bp-152 store), every row complete — statement with domain,
  structure from §2.3, anchor, label, falsifier-or-GAP, formal `—`; plus the track
  manifest's DoD row check-off. Zero proofs, zero tests — seeding is naming and
  labeling. Falsifier: a row missing its arithmetic domain or claiming a structure
  §2.3 does not warrant; acceptance: file parses, reserved-words grep clean
  (the sibling's §2.3.3 table).
- **MF-2 — the Laplacian/spectral falsifier batch.** Deliverable: named tests closing
  the family's GAP rows (direct PSD of L and L̄; nullity = component count; the
  isolated-node convention pointwise; never-merge directly), Hypothesis-generated
  where a planted family exists; **plus the minimal ledger checker** —
  `tests/unit/test_laws_ledger.py`, parsing `docs/LAWS.md` and asserting every
  anchored symbol exists at HEAD and every falsifier node id is collected by pytest
  (the structural-enforcement rule: the index is only real once a test proves its
  pointers); the checker and the falsifier batch are separable surfaces — split at
  graduation if one session cannot carry both. Green, or a counterexample recorded
  and filed as a `type:defect` issue — a result, not a failure (non-goal 10: no
  drive-by fixes). Ledger labels upgrade only as tests land. Unit falsifier: a
  planted stale pointer the checker passes; or a new falsifier that cannot fail
  (checked against a deliberately mutated implementation at review).
- **MF-3 — the cut/conductance/curvature falsifier batch.** Deliverable: direct Φ(S)
  known-value tests plus both degenerate conventions and the singleton-skip; the
  most_negative_edges emission rule (κ≤0-else-argmin, tie-break, cap); the CND-6
  windowed-law falsifier (the χ_s hypothesis, §2.5). Same acceptance shape and unit
  falsifier as MF-2 (a test that cannot fail is the defect). Serialized after MF-2
  (both write the shared ledger).
- **MF-4 — `formal/` L1.** Deliverable per §2.4: the sibling lake package (lakefile,
  pinned `lean-toolchain`, Mathlib dep), statements of the first ledgered laws with
  Plausible attacks, one-line Mathlib proofs where free, `sorry` elsewhere,
  `formal/sorry-budget` recorded as the ratchet baseline. Acceptance is local:
  `lake build` green, attacks run. Depends on MF-1 (statements mirror stated laws).
  The plan budgets the first Mathlib cache fetch (multi-GB wall clock) as a
  stop-and-raise if unavailable. **The toolchain install is an owner hand-act before
  dispatch** (verified absent on this machine): `elan` via its official installer or
  `brew install elan-init`; the pinned `lean-toolchain` self-resolves on first
  `lake build`. A machine mutation belongs to the owner, not a plan. **The natural
  split line, pre-named:** (a) package skeleton + toolchain + cache + one
  pipeline-proving law; (b) the memberships model (coordinate-keyed relation,
  fibers-as-words, the RLE run structure — definitions, not transcription) + the
  statement batch. Split there rather than mid-session. Unit falsifier: a merged
  statement whose Plausible attack never ran, or one that fails `lake build`.
- **MF-5 — the advisory CI job.** Deliverable: `.github/workflows/` lean job via
  `lean-action` with the Mathlib cache, the sorry-budget assertion, the axiom-escape
  guard, and the ledger⇄formal law-id cross-reference grep (MFF-4's mechanical half),
  **path-scoped to `formal/**`** plus a weekly cron for drift, advisory; acceptance:
  green on a real PR touching `formal/` with the cache hitting. Unit falsifier: a
  "green week" in which no run built a `formal/` change counts toward nothing — the
  flip window's weeks are qualified by at least one `formal/`-building run. A deliberate split from
  MF-4 (different zone, different failure surface — runner cache/minutes vs. local
  build); folding them is legal only if one plan's write_scope honestly carries both
  zones.
- **MF-6 — the first L2 discharge batch** (entry-gated, not mintable before its
  condition). Entry: MF-4 landed and its statements have survived their Plausible
  attacks. Deliverable: proof discharge of the memberships/Laplacian statement set
  over exact arithmetic; the sorry budget strictly decreases **by named-law
  discharge** (law ids are the acceptance; the count is only the trace); the first honest
  *Theorem (machine-checked, `formal/...`)* citations become available to future
  artifacts. Falsifier: MFF-3 (a gamed ratchet).

**Priced, so the owner ratifies with the bill visible.** MF-1 is one docs session
(the RR-1 shape). MF-2/MF-3 are one test-writing session each — the falsifier
batches are the expensive honesty, and they may *file defects* rather than fix them.
MF-4 is the investigation's own sizing: one build-plan-sized unit, plus the one-time
Mathlib cache cost. MF-5 is small. MF-6 is the first genuinely new-currency spend
(agent proof sessions under supervision) and is entry-gated so it cannot start on an
unproven statement layer. Ladder rungs above it cost nothing until entered.

**Explicitly NOT licensed:** L3 (per-claim entry only, parked) and L4 (parked);
Ollivier–Ricci or Cheeger formalization (non-goal 3); the required-in-CI flip (owner
act, after the stated window); any `core/` code change (non-goal 10); the NOTATION.md
refresh (non-goal 6); authoring the Question (non-goal 8); relicensing anything of
the sibling's (RR-1/2/3 are its own).

## 4. Wiring & enablement

**How it wires:** `docs/LAWS.md` (new, authored — the §2.2 schema; the one ledger
artifact); `tests/unit/test_laws_ledger.py` (MF-2 — the symbol/node-id checker that makes
*pointer* rot machine-visible at HEAD; statement drift stays parked, named); the family falsifier tests in `tests/unit/`
and `tests/property/` (MF-2/3 — running under the normal pytest gate, no new
runner); `formal/` (MF-4 — sibling lake package: `lakefile`, pinned
`lean-toolchain`, `formal/Palace/*.lean` statement modules carrying ledger law ids,
`formal/sorry-budget`; imported by nothing in `core/`, importing nothing from it);
`.github/workflows/` lean job (MF-5 — `lean-action`, Mathlib cache, sorry-budget
assertion, advisory); `docs/tracks/mathematical-foundations.md` (this PR — the MF
DoD rows). `scripts/board.py`: zero lines. `CLAUDE.md`: zero lines. No daemon
surface anywhere in this arc — `mind-palace deploy` is not involved.

**What it takes to flip it on:** (a) MF-1 merges → the ledger is live on read;
(b) MF-2/MF-3 merge → the falsifiers and the ledger checker run on every CI pass —
live on first run, no switch; (c) MF-4 merges → `lake build` is runnable locally
(owner prerequisite: `elan` installed by hand — official installer or
`brew install elan-init`; first build fetches the Mathlib cache);
(d) MF-5 merges → the advisory job runs per PR — live on the next PR, no switch;
(e) the owner's only hand-acts: adjudicate the track coordinate at this note's
merge, install `elan` before MF-4 dispatch, merge each MF plan's PR, and — after
the four-green-weeks window (qualified weeks, MF-5) — flip the lean job from
advisory to required, by hand, if he chooses.

## Parked decisions

| decision | default recorded | re-entry condition |
|---|---|---|
| L3 — float-ε formal bridge | not entered; rung specified §2.4 | a design claim demands a machine-checked ε-bound (per-claim entry, one claim at a time) |
| L4 — verified kernels | parked | a palace claim needs a verified kernel; none does (issue #48) |
| Ollivier–Ricci formalization | not licensed; Forman is the floor (§2.3.3) | a design claim needs curvature *theorems*, or Mathlib gains OT/W₁ (the KR layer is the on-ramp) |
| Cheeger-in-Mathlib recheck | absent, verified 2026-08-09 (issue #48) | cheap periodic recheck at each MF-4+ session; or a claim comes to depend on the inequality (CUT-2 leaves Remark) |
| ledger checker beyond minimal | MF-2's anchor/test-id checker only | a stale row the checker passed (statement drift) — then statement-hash or deeper checking becomes a unit |
| required-in-CI flip for `formal/` | advisory | four consecutive green weeks, then the owner's hand — never an agent act |
| NOTATION.md + whitepaper §A.5 refresh | both stale texts flagged (Family-5; "does not exist yet"), not fixed | one surgical de-stale PR; new symbols enter NOTATION there |
| toolchain / Mathlib pin bump | pinned `lean-toolchain`; bumped only in MF-track sessions, never drive-by | an MF session needs a newer lemma, or the advisory job reds on cache drift |

## Falsifiers — what would prove this design wrong

The owner ratifies falsifiers, not proofs.

- **MFF-1 (ledger-rot):** a merged ledger row's anchor or falsifier name goes stale
  and both review and the MF-2 checker miss it. The index then misleads — worse than
  no index. Two occurrences reopen the checker park at the deeper tier.
- **MFF-2 (structure-mislabel):** a ledger row names a structure the code demonstrably
  does not instantiate — the Boolean-algebra case is the template — and it merges
  without a Conjecture cap. The §2.3 honesty discipline then failed at review, and
  the row's whole column is suspect until re-audited.
- **MFF-3 (the ratchet gamed):** the sorry count drops by deleting or weakening
  statements or by `axiom`/`admit` substitution rather than proof; or the budget file
  is raised without a warranted note in the PR body; or padding statements are added
  only to be "discharged." The ratchet then measures nothing; MF-6 cannot claim
  discharge on it — its acceptance is named-law discharge, never raw count decrease.
- **MFF-4 (formal/ divergence):** a `formal/` statement and its ledger row drift —
  the law id cross-reference broken or the statements semantically different — and
  merge that way. The two-sided bridge (§2.4) is then one-sided decoration.
- **MFF-5 (the L1 value falsifier, issue #48's own):** by the third law batch the
  statement layer has caught no mis-stated law that Hypothesis alone missed. L1 is
  then decoration: it retracts to L0, MF-6 is never minted, and the parked rungs stay
  parked — the ladder dies at its first rung, honestly.

## Cross-references

Code, at `68d8d39` plus the staged store (paths current at HEAD — several ratified
notes pin pre-migration `core/complex/` paths for what now lives under
`core/kernel/complex/`; content stands, cite by object and current path):
`core/kernel/complex/laplacian.py` (L, L_sym, L̄ — LAP rows),
`core/kernel/complex/balance.py` (signed spectrum, masking fix),
`core/kernel/complex/curvature.py` (Forman floor; Ollivier deferred — CRV rows),
`core/complex/spectral.py` (SPC rows), `core/complex/cut.py` (CUT rows),
`core/graph/conductance.py` (CND rows; the OBJECT/INVARIANT/ENFORCED header and
cite-don't-restate docstring pattern the ledger indexes),
`core/stores/memberships.py` + `tests/unit/test_memberships.py` (staged — MEM rows;
the precondition-first falsifier discipline), `tests/unit/test_graph_boundary.py`
(the float-ε model entry), `tests/property/` + `docs/WHITEPAPER-FORMAL-PROPERTIES.md`
(the existing discharge tier this note extends), `pyproject.toml` (hypothesis already
a dev dependency).

Artifacts, glossed: `docs/brainstorms/mathematical-foundations.md` (the warrant
capsule, PR #42, sequenced first — owner seed 1, structure-instantiation,
falsifiers-before-proofs, the float-ε risk; its "finite Boolean algebra" and
"curvature = finite LP" phrasings are corrected by §2.3.1/§2.3.3 on the record's
side); `docs/design-notes/dn-research-register.md` (the sibling, same PR — the claim
ladder §2.3, reserved words, R5/R7, the §1.3 boundary; its parked Lean row re-pointed
at §2.4 here by this PR's surgical edits); GitHub issue #48 (the Lean investigation —
Mathlib coverage table, Plausible/FloatSpec/lean-action, the agent-era cost premise,
the L0–L4 proposal; external claims verified there 2026-08-09 *unless marked
otherwise in the report* — every claim this note leans on is a VERIFIED row, the one
[FROM MEMORY] row (semiring/inner-product bedrock) is not load-bearing here — cited,
never re-verified); `docs/design-notes/connectivity-instruments.md`
(dn-connectivity-instruments, ratified — CN-1..CN-7);
`docs/design-notes/core-graph-instruments.md` (dn-core-graph-instruments, ratified —
P1/P3/P4, the import-walk tooth); `docs/design-notes/magnetic-laplacian.md`
(dn-magnetic-laplacian, ratified, design-only — the L^{(q)} family, F1–F5);
`docs/design-notes/temporal-retrieval-algebra.md` (dn-temporal-retrieval-algebra,
ratified — A1–A8; its banner predates the merge-gated regime and is not quoted as
live mechanics); `docs/design-notes/core-query-protocol.md` (dn-core-query-protocol,
ratified — §2.2 the query-mode algebra); `docs/design-notes/vector-membership-store.md`
(dn-vector-membership-store — in force by owner merges; its frontmatter `status:
draft` is provenance, never edited); `docs/design-notes/fiber-geometry.md`
(dn-fiber-geometry, ratified — FG-0/FG-5); `docs/NOTATION.md` (the symbol authority —
**staleness flagged, not fixed:** its Family-5 header still says `core/complex/`
"does not exist yet", false at HEAD; the refresh is parked, non-goal 6);
`docs/tracks/mathematical-foundations.md` (this note's manifest, minted in this PR —
⚑ owner adjudicates the coordinate at the merge).
