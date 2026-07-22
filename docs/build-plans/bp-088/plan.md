---
type: build-plan
id: bp-088
track: agentic-loop
status: complete
design_ref:
  - docs/design-notes/agentic-loop.md
contract: builder
write_scope:
  - core/scope.py
  - core/origin_view.py
  - tests/unit/test_scope.py
  - tests/unit/test_scope_laws.py
  - tests/unit/test_origin_view.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual:
    model: opus            # claude-opus-4-8[1m], tier verified via completion usage
    tokens: 163215
    tool_calls: 72
    duration_min: 22
    ratio: 0.54            # UNDER; F-AL6 + F-AL7 both hold; caught+resolved a plan §7(iv) imprecision (no finding — exclusion IS the safety property)
    session_delta: "weekly all-models pool; ran parallel with the S1 re-graduation; merged main first for AL-1's scope.py"
depends_on: [bp-086]
parallelizable_with: [bp-083, bp-085, bp-087]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/agentic-loop.md
  - docs/design-notes/capability-scope-algebra.md
  - docs/design-notes/agent-taxonomy.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AL-3: the exhaust⊂dialogue refinement + the origin(e) derived view

> Graduated from ratified `dn-agentic-loop` §2.4b (EX-1/EX-2) / §3 (AL-3). Two additive pieces,
> both structural-not-tuning: (a) the `exhaust ⊂ dialogue` refinement predicate WITH default-grant
> exclusion (the bp-081 HYPOTHETICAL precedent applied to a refinement — a read of agent-exhaust
> rows is constructible only under a grant naming `exhaust`); (b) `origin(e)` as a derived,
> regenerable view over C-witnesses + commit keys — **no store, no minted edge-of-edges rows**,
> E_disp discipline asserted. Independent of PD-1 (the trust class/weight stays owner-gated at the
> authorship-axis note).

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only. Additive lattice extension + a derived view — nothing amends
ratified `dn-capability-scope` (A8); the refinement follows the established named-extension pattern
(`mirror_authored ⊂ mirror`). **Depends on AL-1 (bp-086)** because both write `core/scope.py` and
its tests — AL-1 lands first (the zone law + `PRIVATE_STRATA`), AL-3 adds the refinement to the
same module (avoids a merge collision, not a logical dependency).

## 1. Objective

Add the `EXHAUST` refinement (`exhaust ⊂ dialogue`, excluded from default grants — constructible
only when named) to `core/scope.py`, and expose `origin(e)` as a derived, regenerable traversal
over the C-edge witnesses + commit-keyed rows — so agent-exhaust rows are structurally excludable
and the exhaust→created-structure provenance spine is queryable, with zero new stores and zero
minted rows.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/agentic-loop.md` §2.4b — EX-1 (both axes; the stratum side as `exhaust ⊂
   dialogue` refinement, NOT a new base; the three structural cuts — mirror-opacity, default-grant
   exclusion, surfacing-only; "low priority = tuning, never protection"); EX-2 (the origin view;
   the four trust-propagation mechanisms; census acyclicity; PD-7 return-edge park); falsifiers
   F-AL6, F-AL7.
2. `core/scope.py:55-152` — the `Stratum` enum, `_REFINES`, `_BASE_STRATA`, `_refinements_below`,
   `_downward_close`, `StratumScope.of/top/bottom`. The HYPOTHETICAL precedent (`:74-102`): a
   stratum excluded from `_BASE_STRATA`, grantable only when named, `⊤_Σ` byte-identical.
3. `core/stores/causal_edges.py` — `CausalEdge` (its `edge_id`, witnesses: `transcript_digest`,
   `turn_index`, `tool_record`; the causal bracket) — the C-side of `origin`.
4. `core/stores/reference_edges.py` — the commit-keyed X_cite rows (the F-side; `origin(e)` for a
   citation edge is the C-edge whose witnessed commit minted it).
5. `docs/design-notes/agent-taxonomy.md` §2.4/§2.5 — the fiber-vs-edge criterion (why derivation
   tissue is NOT stored as graph edges); the witness law; C∘D as the sibling traversal shape.
6. `docs/design-notes/the-edge-model.md` — E_disp discipline (provenance-spine links are
   dispositional, never assembled into `A_geom`/L).

## 3. Investigation & grounding

Touches existing code; grounded at HEAD (`d08da37`):

- **Q1 — the refinement mechanism.** `_REFINES` (`scope.py:87`) maps child→parent;
  `_refinements_below(s)` (`:105`) returns children; `_downward_close` (`:111`) auto-adds all
  children of every named stratum; `_BASE_STRATA` (`:99`) excludes FOUNDATION and HYPOTHETICAL from
  `top()`. **The novel combination AL-3 needs:** `exhaust ⊂ dialogue` must be a refinement (so a
  grant naming `exhaust` is ⊑ a grant naming `dialogue`) YET excluded from the auto-downward-closure
  of a `dialogue`/`top()` grant (default-grant exclusion). The code does NOT yet support an
  *excluded refinement* — this plan adds a `_EXCLUDED_REFINEMENTS: frozenset[Stratum] = {EXHAUST}`
  set that `_downward_close` skips when closing a parent, adding it ONLY when `EXHAUST` is directly
  in the input strata. This keeps `⊤_Σ` byte-identical (exhaust never auto-added — the same
  additive property HYPOTHETICAL has, verified by the existing `top()` law tests staying green).
- **Q2 — which parent?** `exhaust ⊂ dialogue` (the note pins `dialogue`, not
  `dialogue_transcript`). The agent-side dialogue rows are the population it covers; dream/report
  exhaust needs no new home (already INTERPRETED / observed / dialogue). So `_REFINES[EXHAUST] =
  DIALOGUE`.
- **Q3 — where does `origin(e)` live?** A derived view reading stores ⇒ outer-ring, core-resident.
  Proposed `core/origin_view.py` (a View in the `MirrorView`/`ObservedView` family, read-only). It
  is NOT inner (it reads `causal_edges` + `reference_edges`) — no ring conflict with M0.
- **Q4 — is `origin(e)` derivable with no new store?** Per EX-2, yes: X_cite rows are commit-keyed;
  C-edges carry witnesses/commit. `origin(e) := the C-edge whose witnessed commit minted e` is a
  typed two-hop join (C ∘ commit-keying), the C∘D family. The code does not settle whether every
  durable edge carries a resolvable commit key at HEAD — **Item 17 verifies** `CausalEdge.edge_id`
  and the commit-keying on `reference_edges` exist; if a target edge kind lacks a commit key,
  record it (F-AL7's boundary) and scope `origin` to the kinds that do.

**Additional risks:** F-AL6 — post-landing, an agent-exhaust row reachable under a grant NOT naming
`exhaust` ⇒ the isolation is decorative. F-AL7 — an `origin(e)` result not re-derivable from
witnesses + commit keys alone ⇒ the view-not-store claim fails; reopen EX-2 by supersession.

## 4. Reconciliation

- `core/scope.py` — **EXTEND** (additive, cross-referenced): a new `EXHAUST` enum member + the
  `_EXCLUDED_REFINEMENTS` mechanism; the `Stratum` docstring gains an `exhaust ⊂ dialogue` line
  citing §2.4b. Existing `_REFINES`/`top()` semantics are preserved (byte-identical `⊤_Σ`); the
  existing lattice-law tests are the proof.
- `core/origin_view.py` — **NEW**: the derived view; its docstring states the E_disp discipline
  (origin links never enter `A_geom`/L) and that it mints no rows.
- **No banner-correction** — corrects no committed behavior; both pieces are additive.

## 5. Write scope

`core/scope.py` (the refinement + exclusion mechanism), `core/origin_view.py` (the derived view,
new), `tests/unit/test_scope.py` + `tests/unit/test_scope_laws.py` (the refinement lattice-law +
the default-grant exclusion F-AL6, carried because they pin the Σ surface AL-3 extends),
`tests/unit/test_origin_view.py` (F-AL7). Deliberately OUT of scope: `core/stores/**` (read-only;
the view reads causal_edges/reference_edges, never edits them), the ratified `dn-capability-scope`
text, `dn-authorship-distance-axis` (PD-1's class/weight stays owner-gated there — this plan adds
NO trust weight `w(a_self)`).

## 6. Interfaces pinned inline

```python
# core/scope.py — existing, pinned:
_REFINES: dict[Stratum, Stratum] = { MIRROR_AUTHORED: MIRROR, REFERENCE_REPO: REFERENCE,
                                     DIALOGUE_TRANSCRIPT: DIALOGUE, DIALOGUE_ARTIFACT: DIALOGUE }  # :87
def _downward_close(strata) -> frozenset[Stratum]                                                  # :111
# HYPOTHETICAL precedent: excluded from _BASE_STRATA ⇒ not in top(); grantable only when named.    # :81,99
# core/scope.py — NEW (additive):
class Stratum: ... EXHAUST = "exhaust"                 # ⊂ dialogue; excluded-by-default refinement
_REFINES[Stratum.EXHAUST] = Stratum.DIALOGUE
_EXCLUDED_REFINEMENTS: frozenset[Stratum] = frozenset({Stratum.EXHAUST})
# _downward_close: auto-add a parent's children EXCEPT those in _EXCLUDED_REFINEMENTS; add an
# excluded refinement only when it is directly among the input strata (default-grant exclusion).
# core/origin_view.py — NEW:
def origin(edge_id, *, causal_edges, reference_edges) -> CausalEdge | None
    # the C-edge whose witnessed commit minted `edge_id`; a derived two-hop join (C ∘ commit-keying);
    # regenerable, mints nothing, E_disp (never enters A_geom).
```
The invariant proved by the tests: `StratumScope.top()` and `StratumScope.of(Stratum.DIALOGUE)` do
NOT contain `EXHAUST`; only `StratumScope.of(..., Stratum.EXHAUST)` does (F-AL6).

## 7. Items

Ordered by blast radius (lattice vocabulary → derived read-view; nothing writes stored data).

### Item 16 — the `exhaust ⊂ dialogue` refinement with default-grant exclusion
- **Objective:** add `EXHAUST`, `_REFINES[EXHAUST]=DIALOGUE`, `_EXCLUDED_REFINEMENTS`, and the
  `_downward_close` skip; prove `⊤_Σ` byte-identical and the exclusion.
- **Files:** `core/scope.py`, `tests/unit/test_scope.py`, `tests/unit/test_scope_laws.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_scope.py tests/unit/test_scope_laws.py` green;
  new tests prove (i) `top()` unchanged (no `EXHAUST`), (ii) `of(DIALOGUE)` excludes `EXHAUST`,
  (iii) `of(DIALOGUE, EXHAUST)` includes it, (iv) `of(EXHAUST) ⊑ of(DIALOGUE)` (the refinement ⊑).
- **Falsifier (F-AL6):** a grant NOT naming `exhaust` (including `top()`) whose downset contains
  `EXHAUST` ⇒ the isolation is decorative; re-tier the stratum ruling.
- **Invariant(s):** additive — every existing lattice-law test stays green; `⊤_Σ` byte-identical;
  this is set-membership isolation (structure), not a weight (no `w(a_self)` added).
- **Touches stored data?** No. **Parallelizable?** No (Item 17 is independent but same module —
  keep one build). **Depends on:** bp-086.

### Item 17 — the `origin(e)` derived view
- **Objective:** `core/origin_view.py` — `origin(edge_id, ...)` as a regenerable two-hop join over
  C-witnesses + commit keys; mints no rows; E_disp asserted.
- **Files:** `core/origin_view.py` (new), `tests/unit/test_origin_view.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_origin_view.py` green; on a fixture,
  `origin(e)` returns the C-edge whose witnessed commit minted `e`, and the SAME result is
  reproduced from witnesses + commit keys alone (regenerability); the module mints no rows and
  exposes no `A_geom` assembly path.
- **Falsifier (F-AL7):** an `origin(e)` result that needs a fact no row carries (i.e. the view
  needs a store after all) ⇒ the composition claim fails; **stop**, reopen EX-2 by supersession,
  do not add a store silently.
- **Invariant(s):** read-only; no minted edge-of-edges (the fiber-vs-edge criterion); origin links
  never enter `A_geom`/L (E_disp, the-edge-model §3); acyclic by construction (exhaust→created
  only; no PD-7 return edge).
- **Touches stored data?** Reads only. **Parallelizable?** No (same build as Item 16).
  **Depends on:** none (independent of Item 16, but same plan).

## 8. Math carried explicitly

- **The excluded refinement `exhaust ⊂ dialogue`** — *measures:* nothing numeric; it is a downset
  element with a special closure rule. *valid when:* `_downward_close` adds it only on explicit
  naming, keeping `⊤_Σ` byte-identical. *fails its keep if:* it enters an unnamed grant (F-AL6) —
  then it is a base stratum in disguise and the ruling must be re-tiered.
- **`origin(e) = C ∘ commit-keying`** (a two-hop join, the C∘D family) — *measures:* which dialogue
  action minted a durable edge. *valid when:* the edge carries a resolvable commit key and a C-edge
  witnesses that commit. *fails its keep if:* a target edge kind carries no commit key (F-AL7) —
  then `origin` is scoped to the kinds that do, and the boundary is recorded, not papered over.

## 9. Non-goals

No trust class / weight `w(a_self)` (PD-1 — stays OBSERVED + speaker metadata, owner-gated at the
authorship-axis ratification). No new base stratum, no disk migration (EX-1 rejected re-homing
rows). No minted edge-of-edges rows / no `origin` store (EX-2). No "informed-by" return edges
(PD-7 — reading ≠ influence, the apophenia bar). No read-path gate wiring beyond the Σ-visibility
capability test. No φ_exhaust module (rejected three ways, §2.4).

## 10. Stop-and-raise conditions

- F-AL6: `EXHAUST` reachable under an unnamed grant ⇒ **stop**; the exclusion mechanism is wrong.
- F-AL7: `origin(e)` needs a fact no row carries ⇒ **stop**, reopen EX-2 by supersession (do not
  add a store).
- Any temptation to add a trust weight or a provenance-enum change ⇒ **stop**; that is PD-1,
  owner-gated at the authorship-axis note, a `design` finding to the orchestrator.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| PD-1 self-authored trust class/weight | stays OBSERVED + speaker metadata (fail-safe over-distrust) | add `w(a_self)` now (owner-gated, MIRROR_READABLE-adjacent) | `dn-authorship-distance-axis` ratification gate |
| PD-7 "informed-by" return edges | NOT minted (reading ≠ influence) | mint an edge per context-read (dense derivation stars, apophenia) | a consumer proves graph-grain loop reading is necessary AND a witnessed deterministic orientation record clears the bar |
| PD-8 edge-as-endpoint row-grain / per-producer exhaust predicate | expressible, uninhabited | build it now (no consumer) | first consumer needing row-grain origin, or a grant splitting exhaust by producing agent |

## 12. Dependency & ordering summary

Items 16 and 17 are independent in logic but land in ONE build (both are small, both live in the
scope/view layer). **Depends on bp-086 (AL-1)** — both write `core/scope.py` + `test_scope*.py`;
AL-1 first avoids a collision. Parallelizable with bp-083, bp-085, bp-087. Blast radius: additive
lattice vocabulary (Item 16) + a read-only derived view (Item 17); nothing writes stored data.
