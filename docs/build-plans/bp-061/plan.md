---
type: build-plan
id: bp-061
alias: bridge-search
status: ready
design_ref:
  - docs/design-notes/connectivity-instruments.md   # RATIFIED — CN-5 (arguments are well-formed paths) + CN-7 (the arc: bidirectional field-guided search)
contract: builder
write_scope:
  - eval/harness/bridges.py
  - tests/unit/test_bridges.py
  - tests/quality/test_bridges.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: [bp-059, bp-060]
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/capability-scope-algebra.md                 # the scope meet / admissibility grammar CN-5 operationalizes
  - docs/design-notes/global-event-clock.md                       # GC-4 the ClockAtlas — the cross-clock type-checker
  - docs/design-notes/recursive-strata.md                         # I1 — bridges are surfacing-only, never a weight
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CN-5 + CN-7: type-checked bridges and bidirectional field-guided arc search

## 0. Mode & provenance
Graduated from RATIFIED `dn-connectivity-instruments` CN-5 + CN-7. Investigation & planning produced this;
implementation proceeds item-by-item on owner approval; `proposed → ready` is owner-only. **Depends on
bp-059 + bp-060** — imports the graph-at-cut surface, `ConnEvidence`, and the conductance profile (the
bridge's confidence axis and the search's guiding potential). I1 is absolute: a bridge is a **report**, never
a weight, a confidence input, or a promotion.

## 1. Objective
`eval/harness/bridges.py`: decide when a path between two thoughts is an **argument** (its running scope-meet
stays non-empty, admissible, and atlas-covered — else it *refuses*, the anti-hallucination property at chain
level), search for the best well-formed chain between two named endpoints by **bidirectional, field-guided,
budget-bounded** growth (deterministic v1 = the high-η bidirectional-Dijkstra limit), and report a bridge on
**two axes never fused** — the argument (best well-formed chain) and the confidence (conductance profile) —
or the principled refusal "no arc at this voltage."

## 2. Context manifest (read in order)
1. `docs/design-notes/connectivity-instruments.md` — WHOLE, focus CN-5 (§2.5), CN-7 (§2.7), §3 item-3,
   §4 parked (journey semantics), §6 non-goals (surfacing-only).
2. bp-059's `eval/harness/connectivity.py` — the graph-at-cut acquisition, `ConnIndex`, `ConnEvidence`.
3. bp-060's `eval/harness/conductance.py` — `ConductanceProfile` (the confidence axis) + the Laplacian
   potential (the field the search follows). **The two upstream surfaces this imports.**
4. `core/scope.py:311-609` — `Scope.meet` (raises `NoCommonClockError` on a cross-clock T-meet that the
   atlas cannot pull back), `Scope.__le__`, `admissible(s, ideals)`, `DENYLIST_IDEAL`, `NoCommonClockError`,
   `TimeScope.meet` (consults `_ATLAS`), `ClockAtlas` Protocol, `register_atlas`. **The type-check algebra.**
5. `core/temporal/atlas.py:46-87` — `SpineAtlas(spine)` + `has(clock)` (the "is this clock covered" check;
   `False` for exogenous WALL/NOW and un-materialized coarsenings). The registered cross-clock type-checker.
6. `core/mirror.py:66-105` — `MirrorView` (all rows `MIRROR_AUTHORED`; `SCOPE` ClassVar). Why the Σ-meet
   is trivial and the T-meet is the live axis (§3 Q1).
7. `eval/harness/store.py:47-100` — `EvalKey`/`Reading`/`EvalResultsStore.put`.

## 3. Investigation & grounding
- **Q1 — where does an idea-graph edge/node get its `Scope`? (the load-bearing gap).** The σ-graph
  (`MirrorGraph`) edges carry only cosine — **no scope**. The scope algebra is fully built
  (`core/scope.py`) but the mapping **node → Scope** for the eval-side idea graph is **not** built. *Code
  does not settle this.* What settles it: every MirrorView row is `MIRROR_AUTHORED` (`core/mirror.py:51,86-94`)
  — so the **Σ (stratum) meet is trivial** (one stratum; always non-empty). The **discriminating axis is TIME**:
  each node's `TimeScope` comes from its note's spine event (its clock + window); `Scope.meet` runs the
  `TimeScope.meet` which consults the registered `SpineAtlas` and **raises `NoCommonClockError` when a clock is
  atlas-uncovered** (`core/scope.py:367-390`). **v1 node→scope derivation (pinned):** each node's `Scope` =
  `MirrorView.SCOPE` refined with the node's spine-event `TimeScope` (clock + point/interval window); the running
  path meet is the composition; the atlas refusal IS CN-5's "steps on atlas-uncovered clocks refuse."
- **Q2 — the type-check is O(length).** The running meet is state carried along the path (`core/scope.py:527`
  `meet`); each extension is one `meet` + one `admissible(...)` check (`:592`) against `DENYLIST_IDEAL`. A
  path type-checks iff the accumulated meet is never empty (no `NoCommonClockError`, no empty Σ/E) and stays
  admissible. Non-empty-but-non-argument paths remain conductance-bearing **associations** — graded by bp-060's
  profile, reported separately (never dropped).
- **Q3 — dominance pruning soundness.** Scopes only **narrow** along a path (meet is monotone-decreasing —
  `meet(a,b) ⊑ a`, `core/scope.py:527`), so label-setting over `(node, accumulated-scope)` states with dominance
  pruning is sound: a state dominated on both cost and scope-width can be discarded (CN-7). This is why the
  search is over `(node, scope)` states, not bare nodes.
- **Q4 — field guidance = the Laplacian potential.** CN-7's potential-guided priority is the A*/reduced-cost
  form of the **same** Laplacian object bp-060 computes for conductance; import it, do not recompute. v1
  deterministic = the high-η limit = bidirectional Dijkstra on the reduced cost; stochastic η-growth is parked.
- **Q5 — refusal is quantified, never partial.** Budget exhaustion yields `"no arc at this voltage"` carrying
  budget-spent + frontier-reach; a partial path is NEVER presented as a bridge (CN-7 falsifier).
- **Q6 — I1: surfacing-only.** The bridge writes only eval readings; it never writes a weight, a confidence,
  a DreamLogEntry, or a promotion. The two axes (chain, conductance) are reported side-by-side, never fused
  into one scalar (FB-3 one-scalar prohibition, inherited).

**Additional risks:** (a) the atlas must be **registered** (`register_atlas(SpineAtlas(spine))`) before any
T-meet, else every meet raises — the entry point registers it, tests assert the registration precondition.
(b) two endpoints on genuinely incompatible clocks → the search correctly refuses (not a bug); the quality
test includes such a pair. (c) exhaustive reference search is O(exponential) — bound the reference oracle to
small planted instances only.

## 4. Reconciliation
- `MirrorGraph` edges carry no scope → this plan **extends** the eval graph with a node→scope derivation
  (Q1), living entirely in `bridges.py`. → **cross-reference-on-extension**: `bridges.py` docstring states the
  v1 node→scope mapping (MirrorView.SCOPE + spine-event TimeScope), cites CN-5 §2.5 + `core/scope.py`. No
  `core/` edit; no `graph.py` change. If a future consumer needs richer per-edge scopes (e.g. EdgeScope
  fibers), that is its own warrant.

## 5. Write scope
`eval/harness/bridges.py` + its two test files. **OUT:** `eval/harness/connectivity.py` + `conductance.py`
(imported read-only), `core/scope.py`/`atlas.py`/`mirror.py`/`graph.py` (read-only substrate — the scope
algebra is consumed, never modified), `ops/**`, the foundation denylist, the mirror surfacing wiring (a later
E6 tenant plan — bridges are report-layer here, not auto-surfaced).

## 6. Interfaces pinned inline
```python
# --- CONSUMED (verbatim) ---
# core/scope.py
class NoCommonClockError(ValueError): ...
@dataclass(frozen=True)
class Scope:
    def meet(self, other: Scope) -> Scope: ...     # componentwise; raises NoCommonClockError on cross-clock T-meet; meet ⊑ self
    def __le__(self, other: Scope) -> bool: ...     # ⊑ on the four coordinates (tier excluded)
def admissible(s: Scope, ideals: Iterable[Ideal]) -> bool: ...
DENYLIST_IDEAL: Ideal   # foundation denylist as an order-ideal
def register_atlas(atlas: ClockAtlas | None) -> None: ...
class ClockAtlas(Protocol):
    def has(self, clock: Clock) -> bool: ...
    def pullback(self, clock: Clock, window: Window) -> Hashable: ...
    def intersect(self, a: Hashable, b: Hashable) -> Hashable | None: ...
# core/temporal/atlas.py
class SpineAtlas:                                   # a structural ClockAtlas
    def __init__(self, spine: Spine) -> None: ...
    def has(self, clock: Clock) -> bool: ...        # False for WALL/NOW + un-materialized coarsenings
# eval/harness/conductance.py  (bp-060)
@dataclass(frozen=True)
class ConductanceProfile: ...                       # the confidence axis (never fused with the chain)

# --- TO BUILD in eval/harness/bridges.py ---
_INSTRUMENT = "bridges/v1"

@dataclass(frozen=True)
class SearchState:                                  # label-setting node; dominance pruning sound (scopes only narrow)
    node: str; accumulated_scope: Scope; cost: float; path: tuple[str, ...]

@dataclass(frozen=True)
class Bridge:                                        # TWO AXES, NEVER FUSED
    a: str; b: str
    chain: tuple[str, ...] | None                   # the best WELL-FORMED (type-checked) chain; None ⇒ refused
    conductance: ConductanceProfile                 # the confidence axis, reported separately
    refusal: str | None                             # "no arc at this voltage" + budget-spent/frontier-reach; None ⇒ found

def type_checks(path_scopes: Sequence[Scope]) -> bool               # running meet non-empty + admissible + atlas-covered
def node_scope(digest: str, *, spine: Spine) -> Scope                # v1: MirrorView.SCOPE ⊓ spine-event TimeScope
def search_arc(graph, a: str, b: str, *, budget: int, potential) -> Bridge   # bidirectional, field-guided, label-setting
def run_bridges(*, view, spine, conductance, pairs, budget, eval_store, base_fingerprint) -> ...
```

## 7. Items
### Item 7 — the type-check: node→scope, the running meet, atlas refusal  (blast: read-only)
- **Objective:** `node_scope` + `type_checks` — a path is an argument iff its running scope-meet is
  non-empty, admissible, and atlas-covered; an atlas-uncovered step **refuses** (raises → not-an-argument).
- **Files:** `eval/harness/bridges.py`, `tests/unit/test_bridges.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_bridges.py -q` green (the type-check half) — a path all
  on covered clocks type-checks; a path with a step on an **atlas-uncovered clock** (WALL/NOW, or an
  un-materialized coarsening) **refuses** (returns not-an-argument via the caught `NoCommonClockError`), it
  does **not** compute a bridge; a path violating `DENYLIST_IDEAL` admissibility fails; the running meet is
  monotone (`meet ⊑ self`) — asserted. The entry-path asserts `register_atlas(SpineAtlas(spine))` ran first.
- **Falsifier:** a chain crossing an atlas-uncovered clock that **computes** a bridge instead of refusing (the
  anti-hallucination property is broken); a type-check that mutates the graph or a store.
- **Invariant(s):** the anti-hallucination property (uncovered-clock chains refuse); admissibility against the
  denylist; the meet monotonicity; model-free; no writes.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** bp-059, bp-060.

### Item 8 — bidirectional field-guided budget-bounded search + the refusal  (blast: read-only)
- **Objective:** `search_arc` — label-setting over `(node, accumulated-scope)` states with dominance pruning,
  frontiers from A and B expanding by potential-guided priority, each extension scope-meet-checked at
  expansion; budget exhaustion → the quantified refusal.
- **Files:** `eval/harness/bridges.py`, `tests/unit/test_bridges.py`.
- **Acceptance test:** unit tests green — on small planted instances the meet-point chain **equals** the
  optimal well-formed chain from an exhaustive reference search (label-dominance correctness); a
  below-requirement budget yields the refusal `"no arc at this voltage"` carrying budget-spent + frontier-reach
  (never a partial path); the search only extends through scope-meet-admissible bonds (a step that would break
  the running meet is never added to the frontier).
- **Falsifier:** the meet-point chain ≠ the exhaustive optimum on a small instance (dominance pruning is
  unsound — it pruned a reachable optimum); a below-budget run returning a partial path presented as a bridge.
- **Invariant(s):** dominance pruning sound (scopes only narrow); deterministic v1 (high-η limit); refusal
  quantified, never partial; no writes.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** item 7.

### Item 9 — the two-axis bridge report + entry point + readings  (blast: additive writes)
- **Objective:** `Bridge` reported on two axes never fused (chain + conductance), the entry point, keyed
  readings with the ConnEvidence pin; I1 re-asserted (surfacing-only).
- **Files:** `eval/harness/bridges.py`, `tests/quality/test_bridges.py`.
- **Acceptance test:** `uv run pytest tests/quality/test_bridges.py -q` green — a well-formed pair yields a
  `Bridge` with a non-None chain AND a `ConductanceProfile`, and a **grep/AST test** asserts no code path fuses
  chain-quality and conductance into one scalar (the one-scalar prohibition); a genuinely incompatible-clock
  pair yields a refusal with the chain None but the conductance profile still reported (association without
  argument); the module writes to **no store beyond eval readings** (grep-test: no ledger/DreamLog/promotion
  import); `put()` idempotent; every reading's evidence_ref decodes to a ConnEvidence.
- **Falsifier:** any pers/conductance/chain-quality scalar fusion; a bridge writing to any store beyond eval
  readings (I1 broken); a refusal that drops the conductance association instead of reporting it separately.
- **Invariant(s):** I1 (surfacing/report-layer only — never a weight/confidence/promotion); two axes never
  fused; idempotent-by-key writes; certified-cut-only.
- **Touches stored data?** Yes — eval Readings; dry-run in-memory store first; no core-store writes.
- **Parallelizable?** No.  **Depends on:** items 7–8.

## 8. Math carried explicitly
- **The path type-check (running scope-meet)** — *measures:* whether a chain of associations is a
  well-formed argument (composable capability scope, admissible, atlas-covered). *valid when:* the meet is
  computed left-to-right as state (O(length)); node scopes come from MirrorView.SCOPE ⊓ the spine-event
  TimeScope; the atlas is registered. *fails its keep if:* an atlas-uncovered chain computes instead of refusing.
- **Label-setting bidirectional search over (node, scope) states** — *measures:* the best well-formed chain
  between two named endpoints under a budget. *valid when:* scopes only narrow along a path (dominance sound);
  the priority is the reduced-cost/A* form of the Laplacian potential; deterministic (high-η limit). *fails its
  keep if:* the meet-point chain disagrees with an exhaustive reference optimum on a small instance.
- **The refusal "no arc at this voltage"** — *measures:* that no well-formed chain exists within budget.
  *valid when:* it carries budget-spent + frontier-reach. *fails its keep if:* a below-budget run yields a
  partial path presented as a bridge.

## 9. Non-goals
No helix (bp-062). No σ*/conductance re-implementation (import bp-059/bp-060). No `core/scope.py` change (the
algebra is consumed). No richer per-edge EdgeScope fibers (parked). No stochastic η-growth (parked — the
dreamer-integration gate). No auto-surfacing of bridges into the mirror (a later E6 tenant plan). No weight /
confidence / promotion writes (I1). No golden_recall coupling (finding-0096). No claim matching (SF-a).

## 10. Stop-and-raise conditions
- The v1 node→scope derivation (Q1) proves insufficient for a real pair (e.g. the TimeScope is absent on a
  note's spine event) → STOP, file a `codebase` finding naming the gap, park the affected pairs with a
  re-entry; do NOT invent a scope to force a type-check to pass.
- A pair's clocks are genuinely incompatible → that is a **refusal**, a correct outcome, not a stop condition.
- Any pressure to fuse the two axes into one score "for ranking" → STOP (the one-scalar prohibition, I1/FB-3).
- Any temptation to auto-surface a bridge into the mirror / write a weight → STOP (I1 — surfacing-only, a
  future E6 tenant plan owns wiring).
- Any blessing: never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| node→scope richness | MirrorView.SCOPE ⊓ spine-event TimeScope (Σ trivial, T live) | derive per-edge EdgeScope fibers now (unneeded — single-stratum authored graph) | a consumer needs edge-fiber-typed arguments → its own warrant |
| stochastic η-growth | deterministic v1 (high-η = bidirectional Dijkstra) | probabilistic dielectric-breakdown growth now | bridge-search v1 shipped + a dreamer-integration gate |
| journey semantics (citing the past) | both directions allowed, direction annotated per hop | forbid backward hops now | bridge-search v1 design review |
| the conductance grain | note-centroid (bp-059/060 grain) | chunk/claim grain now | design review shows finer-grain arguments dominate |

## 12. Dependency & ordering summary
**Depends on bp-059 + bp-060** (graph-at-cut + ConnEvidence from bp-059; ConductanceProfile + the Laplacian
potential from bp-060). Items serial by blast radius: 7 (read-only: type-check + node→scope + atlas refusal) →
8 (read-only: bidirectional search + refusal) → 9 (additive writes: two-axis report + entry point). Not
parallelizable with any sibling. **Downstream:** none in this tranche (bp-062 helix is independent of bridges).
