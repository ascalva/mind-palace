---
type: build-plan
id: bp-070
alias: scope-tooling
status: proposed
design_ref:
  - docs/design-notes/agent-taxonomy.md            # dn-agent-taxonomy §3 Phase Α — REQUIRES RATIFICATION first
  - docs/design-notes/capability-scope-algebra.md  # RATIFIED — the lattice this extends additively
contract: builder
write_scope:
  - core/scope.py
  - core/agent_scope.py
  - core/graph/composed.py
  - tests/unit/test_scope.py
  - tests/unit/test_agent_scope.py
  - tests/unit/test_composed_graph.py
session_budget: 2
cost:
  estimate:
    model: opus
    tokens: 140k
  actual: null
depends_on: []
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/design-notes/agent-taxonomy.md
created: 2026-07-18
updated: 2026-07-18
re_entry: null
---

# Build Plan — Phase Α: the scope tooling (type extensions · declared-scope agent layer · composed graph)

## 0. Mode & provenance
Owner-sequenced (2026-07-18, the amended game plan: **"algebra leads"** — agents are born scoped, the
grant machinery debuts on deterministic clients before the model-priced dreamer). Graduates
`dn-agent-taxonomy` §3 Phase Α. **Gate: `dn-agent-taxonomy` must be RATIFIED before this builds** —
D1 encodes its decisions (fiber `C`, the `DIALOGUE` stratum) into the typed lattice.

## 1. Objective
Three deliverables, all additive, all deterministic, all fixture-tested:
- **D1 — type extensions:** `DIALOGUE` base stratum + refinements `dialogue_transcript` /
  `dialogue_artifact` into `Stratum`/`_REFINES`; fiber `C` (causal-witnessed) into `EdgeScope`.
  Lattice laws still hold (extended tests prove it).
- **D2 — the declared-scope agent layer** (`core/agent_scope.py`, NEW): per-role template scope
  constructors (sensor / query / integrator / dreamer regions, dn-agent-taxonomy §2.1),
  meet-composition against a parent grant (the ratified delegation law), and the **conformance
  pattern** — a guard-tier test helper asserting an agent's actual store handles ⊑ its declared
  scope. Precedent: `tests/unit/test_view_scopes.py`.
- **D3 — the composed-graph assembly** (`core/graph/composed.py`, NEW): a graph built from an
  EXPLICIT node set + an edge UNION (`E_sim ∪ E_proven`), pure and dependency-injected (no store
  reads), exposing the same surface the existing `core.graph` σ*/conductance math consumes. The
  harness's `MirrorGraph` stays untouched (mirror-similarity-only); cross-strata measurement enters
  at assembly, in core (math→core, the self-containment rule).

## 2. Context manifest (read in order)
1. `docs/design-notes/agent-taxonomy.md` (RATIFIED by then) — §2.1 role signatures, §2.2 laws,
   §2.3 DIALOGUE carving + reconciliations, §2.5 fiber C + witness/pair-cut language.
2. `core/scope.py` — the full lattice as types: `Stratum`/`_REFINES`/`_BASE_STRATA` +
   `StratumScope` (downward closure), `EdgeScope` (`Fiber = Literal["F","D"]` → extend), `Clock`/
   `Window`/SLICE, `Authority`. Pure-core; vocabulary, not a gate (bp-039 §0) — KEEP that posture.
3. `tests/unit/test_scope.py` — the lattice-law suite (meet/join idempotent/commutative/associative,
   absorption, delegation monotonicity, SLICE, denylist ideal). D1's acceptance extends these.
4. `tests/unit/test_view_scopes.py` — the existing View↔scope expectation tests: the conformance
   pattern D2 generalizes.
5. `core/graph/sigma_star.py` + `core/graph/conductance.py` — the math D3 must feed UNCHANGED; note
   what graph surface they consume (adjacency/Laplacian inputs) and mirror it exactly.
6. `core/dreaming/graph.py` (`MirrorGraph`) — the existing single-stratum assembly D3 parallels
   (NOT modifies).

## 3. Investigation & grounding
- **Q1 — DIALOGUE placement.** Base stratum + two refinements (per the ratified §2.3), i.e. entries in
  `Stratum`, edges in `_REFINES`; `_BASE_STRATA` derives automatically. `⊤_Σ` grows; 𝔇 unaffected.
  The `dialogue_artifact`/`reference_repo` overlap stands as v1 (both may name the same stores — R is
  grant vocabulary, not a disk partition; ratified §2.3 reconciliation).
- **Q2 — fiber C.** `Fiber = Literal["F","D","C"]`; `EdgeScope.top()` gains C. Check every
  `EdgeScope.top()`/fiber-enumerating call site for hidden exhaustiveness assumptions (grep at build).
- **Q3 — D2 shape.** Constructors return `Scope` values (e.g. `sensor_scope(stratum)`,
  `integrator_scope(pairs, fibers)`); NO new lattice machinery — compose with the existing
  meet/join/⊑. Layer-granularity: v1 carries (stratum, layer) pairs as the constructor's arguments
  and documents them on the returned scope; a layer-refinement lattice INSIDE Σ is out (parked —
  refinements-of-refinements are recursion-ready when needed). Conformance = a helper that takes an
  agent's declared scope + its actual handle inventory and asserts ⊑ (guard tier, honestly labeled).
- **Q4 — D3 shape.** Inputs: `nodes: Sequence[NodeId]`, `sim_edges`, `proven_edges` (weighted pairs;
  provenance-tagged per class), → the adjacency/Laplacian surface `sigma_star`/`conductance` consume.
  Edge-class tag kept per edge so Δ-phase readings can attribute structure to `E_sim` vs `E_proven`
  (the falsifier oq-0031 needs). Pure functions; fixtures in tests.
- **Q5 — enforcement tier.** Everything here is vocabulary + guard (static+guard), matching the
  ratified annotation ladder. NO read-path gating is wired (that stays the Views' job).

## 4. Reconciliation
`core/scope.py` — additive enum/literal extensions only; every existing law test must pass unmodified
PLUS extended cases. `core/agent_scope.py`, `core/graph/composed.py` — NEW, core-internal, stdlib+numpy
only ⇒ **the self-containment ratchet stays 19**. No View, store, or scheduler changes in this plan.

## 5. Write scope
As front-matter. **OUT:** the Views (no enforcement wiring); `core/dreaming/graph.py`; the eval
harness (Δ-phase); every store; the dreamer grant machinery (its own gated program).

## 6. Interfaces pinned inline
```python
# core/scope.py — D1 (additive):
class Stratum(StrEnum):
    ...existing...
    DIALOGUE = "dialogue"
    DIALOGUE_TRANSCRIPT = "dialogue_transcript"   # ⊂ dialogue (chat stores: raw, chatlog, chat_events)
    DIALOGUE_ARTIFACT = "dialogue_artifact"       # ⊂ dialogue (brainstorms/design notes/docs)
_REFINES += {DIALOGUE_TRANSCRIPT: DIALOGUE, DIALOGUE_ARTIFACT: DIALOGUE}
Fiber = Literal["F", "D", "C"]                    # C = causal-witnessed (dn-agent-taxonomy §2.5)

# core/agent_scope.py — D2 (NEW):
def sensor_scope(stratum: Stratum) -> Scope: ...          # Σ={stratum↓}, E=⊥, A=(READ, WΣ=1, NONE)
def query_scope(strata: Iterable[Stratum]) -> Scope: ...  # read-only, WΣ=0
def integrator_scope(read: Iterable[tuple[Stratum, str]],   # (stratum, layer-label) pairs, ≥2 strata
                     write_fibers: Iterable[Fiber]) -> Scope: ...
def dreamer_scope(strata: Iterable[Stratum], ...) -> Scope: ...   # constructor only; grants stay owner-declared
def assert_conforms(declared: Scope, handles: HandleInventory) -> None: ...  # guard-tier ⊑ check

# core/graph/composed.py — D3 (NEW):
@dataclass(frozen=True)
class ComposedGraph:                      # explicit nodes × tagged edge union; pure
    nodes: tuple[str, ...]
    # per-class weighted edges; the surface sigma_star/conductance consume is derived from these
def compose(nodes, sim_edges, proven_edges) -> ComposedGraph: ...
```

## 7. Items
### Item 1 — D1 type extensions  (blast: core typing + its law suite)
- **Acceptance:** `uv run pytest tests/unit/test_scope.py -q` green with NEW cases: DIALOGUE downward
  closure (a `dialogue` grant includes both refinements); `⊤_Σ` includes dialogue, still excludes 𝔇;
  C ∈ `EdgeScope.top()`; meets/joins over the extended sets keep every lattice law. ruff+mypy clean;
  ratchet 19.
- **Falsifier:** an existing law test breaks (the extension was NOT additive); a fiber call site
  assumed exhaustive {F,D}.
- **Invariant:** vocabulary-not-gate posture unchanged. **Stored data?** No. **Parallelizable?** No.

### Item 2 — D2 declared-scope layer  (blast: new module + conformance pattern)
- **Acceptance:** `uv run pytest tests/unit/test_agent_scope.py -q` green — each role constructor
  yields a scope INSIDE its §2.1 region (sensor: own-stratum/E=⊥; integrator: ≥2 strata + write
  fibers ⊆ {C,F}; query: WΣ=0); meet with a narrower parent never widens (delegation law reused);
  `assert_conforms` accepts a matching inventory and REJECTS a handle outside the declared Σ.
- **Falsifier:** a constructor can express an out-of-region scope (e.g. a sensor scope naming two
  strata); conformance passes on a smuggled extra handle.
- **Invariant:** no new lattice ops; composition is the existing meet. **Stored data?** No.
  **Parallelizable?** After Item 1.

### Item 3 — D3 composed graph  (blast: new pure-math module)
- **Acceptance:** `uv run pytest tests/unit/test_composed_graph.py -q` green — on fixtures: a
  sim-only composition reproduces the single-class behavior; adding proven edges changes
  connectivity/conductance readings in the DIRECTION the fixtures encode (a bridge C-edge joins two
  σ-components); per-class attribution is queryable; the output surface is consumed by
  `core.graph.sigma_star` + `core.graph.conductance` functions directly (called in the tests).
- **Falsifier:** the math modules need ANY change to consume it (wrong surface — stop and re-ground);
  class tags lost in composition.
- **Invariant:** pure/injected; no store imports. **Stored data?** No. **Parallelizable?** After Item 1.

## 8. Math carried explicitly
The lattice laws (meet/join/⊑, downward closure, delegation monotonicity) — extended, not altered;
the composed graph's union is a weighted multigraph flattened to the existing Laplacian surface with
per-class attribution retained. No new mathematical objects beyond the union.

## 9. Non-goals
NO enforcement wiring into read paths (vocabulary + guard only). NO dreamer grant runtime (its own
gated program). NO harness/instrument changes (Δ). NO store or View changes. NO ratchet regression.

## 10. Stop-and-raise conditions
- `dn-agent-taxonomy` not ratified → STOP (the gate).
- An existing lattice-law test must be MODIFIED to pass → STOP: the extension is not additive
  (`spec-fidelity` finding).
- D3 cannot feed the existing math unchanged → STOP, re-ground the surface (`codebase` finding).
- Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| layer-refinement lattice inside Σ | (stratum, layer) pairs as constructor args, documented | an agent needs layer-granular MEETS |
| dialogue_artifact vs reference_repo | both may name the same stores | the enum-change review |
| edge weights for C-class | weight 1.0 per witnessed edge | Δ-phase calibration |

## 12. Dependency & ordering summary
First plan of the diamond (nothing depends on unbuilt work; the ratification is the only gate).
Items: 1 → {2, 3} (2 and 3 independent after 1). **Downstream:** bp-069 (Β) consumes D2's sensor
scope + conformance; bp-071 (Γ) consumes D1's C/DIALOGUE + D2's integrator scope; Δ consumes D3.
