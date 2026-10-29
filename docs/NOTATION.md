# The Mind Palace — Shared Notation

### The one glossary: symbol ↔ code name ↔ object ↔ family

**2026-07-01 · living document · referenced by every whitepaper and every boundary docstring**

This is the join between the mathematics and the code. Each load-bearing symbol is named **once**
here — the symbol, the code identifier that realizes it, the object it denotes, and which of the
**five families** (companion IV, `MATHEMATICAL-REFRAMING.md` §A) it belongs to. The point is that
"the whole codebase speaks one mathematical language" *without renaming anything*: the code keeps its
readable names (`MirrorView`, `PRE_DECLARED_MAX`, `decay_bound`), and this table is the dictionary.

The five families (companion IV §A.0):

| Family | The object | Substrate / engine |
|---|---|---|
| **1. Labelings & information-flow** | typed labels in a bounded lattice + monotone/erasure maps | substrate |
| **2. Regenerable derivation** | content-addressed base + pure-function derived + acyclic provenance-of-inference | substrate |
| **3. Guarded transition systems** | small finite automata with a checked guard before each side effect | substrate |
| **4. Metric geometry** | distances on a profile/graph, measured against frozen anchors | substrate |
| **5. The reasoning complex** | a multilayer typed temporal complex + a generalized Laplacian family | engine |

---

## The load-bearing symbols

### Family 1 — labelings & information-flow

| symbol | code name | object | where | tier |
|---|---|---|---|---|
| **ρ** | `Provenance` (StrEnum) | the provenance labeling `ρ: V → P` into an *unordered* set (G8 retired the order); only `MR`-membership is load-bearing | `core/provenance.py` | structural |
| **π_MR** | `MirrorView.project` / `MIRROR_READABLE` | the mirror projection onto the mirror-readable layers `MR = {authored-solo, authored-dialogue}` | `core/mirror.py`, `core/provenance.py` | structural (I6) |
| **𝒜** | `MintedAgent.scope`, `dispatcher_for` | authority = the *set* of tool handles an agent holds, ordered by inclusion (a bounded meet-semilattice); mint is the meet `𝒜(mint) = scope ∩ MAX` | `core/factory/factory.py`, `core/factory/tools.py` | structural (I13) |
| **MAX** | `PRE_DECLARED_MAX` | the top of the capability semilattice — the only handles any minted agent may *ever* hold (no shell/cred/net handle exists in it) | `core/factory/roles.py` | structural |
| **π_public** | `ResearchCriteria` / `deidentify` | the airlock erasure map onto a label with no field that can carry note content | `core/research/criteria.py` | structural (I11) |
| **C** | `Clearance[L]`, `MIRROR_READ` … `MAINTENANCE_READ` | a read capability `C ⊆ P`: the provenance classes a read may return; minted only by authorities (the mirror, an admitted query's scope, the named grants); `meet` is ∩ (delegation only narrows) | `core/kernel/clearance.py` | structural + static (A3) |
| **L** | the label parameter of `Row[L]`, `Occupancy[L]`, `PlaneHit[L]` | a set of classes at the TYPE level — a union of `Literal[Provenance.X]`; covariant, so the subset lattice of classes is mypy's subtype lattice | `core/kernel/clearance.py` | static (A3.4) |
| **M_c, M_C** | the `occ_<class>` relations of the shared plane | the occupancy relation partitioned by class, `M = ⊔_c M_c`; a read under `C` reads `M_C = ⊔_{c∈C} M_c` and nothing else | `core/stores/plane.py` | structural (A3.2) |
| **NI** | noninterference (Goguen–Meseguer 1982) | every read under `C` is a function of `M_C` and the atoms it references; mutating `M_c` for `c ∉ C` changes no `C`-read | `tests/property/test_plane_noninterference.py` | property-tested (A3.5) |

### Family 2 — regenerable derivation

| symbol | code name | object | where | tier |
|---|---|---|---|---|
| **H** | `hashlib.sha256(…).hexdigest()` in `RawStore.add` | the content-address hash `H: 𝓑* → Σ` (write-once; identity = content) | `core/stores/rawstore.py` | structural |
| **Σ** | the digest space (hex SHA-256 strings) | the codomain of `H` — the space of content addresses that name raw objects and authored leaves | `core/stores/rawstore.py` | structural |
| **c** | `decay_bound(…)`, `DreamLogEntry.confidence` | confidence of an interpreted claim; `c ≤ γ^d · g`, corroboration-lifted `c₀ = g·(1 + λ(|Agr|−1))` | `core/recursion.py`, `core/dreaming/adjudicator.py` | property-tested (I10) |
| **g** | `grounding_score`, `Source` | the authored-grounding score `g(κ) ∈ [0,1]`; `Cit(A) ⊆ Ret` decided by digest | `core/selfcheck.py`, `core/dreaming/adjudicator.py` | property-tested (I9) |
| **d** | `DerivedStore.depth`, the `depth` arg of `decay_bound` | derivation depth `d(κ)` — 0 for an authored leaf, `1 + max` over interpreted parents (well-defined because the DAG is acyclic) | `core/stores/derived.py`, `core/recursion.py` | structural acyclicity (I10) |
| **γ** | `DEFAULT_GAMMA` (= 0.5) | the per-depth confidence decay base, `γ ∈ (0,1)` — depth-3 is capped at `0.125·g`, so recursion contracts | `core/recursion.py` | declared bound (G7) |
| **λ** | `DEFAULT_LAMBDA` (= 0.1) | the corroboration bonus, `λ ≥ 0` (≤ 0.25) — agreement is a *multiplier, not a vote* (g = 0 keeps c = 0) | `core/recursion.py`, `core/dreaming/adjudicator.py` | declared bound (G7) |

### Family 4 — metric geometry

| symbol | code name | object | where | tier |
|---|---|---|---|---|
| **D(t)** | `drift()` / `DriftReport.drift` | the drift gauge `D(t) = d(μ(s_t), B)` — a one-sided L2 deterioration (pseudo)metric; a Constitution breach hard-trips `D = ∞` | `eval/drift.py` | property-tested (G4) |
| **B** | `metrics` in `eval/golden/baseline.json`, `load_baseline` | the **frozen anchor** — the blessed golden-set capability rates ⊕ the Constitution fingerprint; the boiling-frog inequality forces it to be frozen | `eval/golden/baseline.json`, `eval/golden.py` | owner-blessed, frozen (I9/§15) |
| **Θ** | `DriftConfig.theta` / `drift.drift_tolerance` | the tolerance band — `D ≤ Θ` is the gate's drift conjunct; a **frozen fixed point excluded from the lever set** | `eval/drift.py`, `eval/golden/baseline.json` | owner-blessed, frozen |

### Family 5 — the reasoning complex (companions III · **NOT YET BUILT**)

> **Honest status.** Family 5 is the one genuinely-new code family (companion IV §A.5). `core/complex/`
> **does not exist yet**; it is fully specified in `REASONING-COMPLEX-{MATHEMATICS,BUILD}.md` and will
> ship behind the `DreamerAdapter` seam with the dream-R&D flag OFF (Track H). The symbols below are
> notation for that spec, not for running code — recorded here so the account is complete and the
> future code has a name to bind to. `ℋ` is *seeded* today only by the `derived_from` edge set in
> `core/stores/derived.py` (family 2); the hypergraph proper is future work.

| symbol | code name (planned) | object | where | tier |
|---|---|---|---|---|
| **𝔎** | `core/complex/` (planned) | the multilayer, typed, temporal knowledge complex (layers = provenance strata) | *(not built)* | — |
| **K_σ** | `core/complex/` (planned) | the similarity flag complex (edges where cosine ≥ σ) | *(not built)* | — |
| **ℋ** | `core/complex/` (planned); seeded by `derived_from` | the derivation hypergraph (B-hypergraph); its junctions are today's `derived_from` edges | `core/stores/derived.py` (seed only) | — |
| **δ\*δ** | `core/complex/` (planned) | the generalized Laplacian family (ordinary / signed / sheaf / hypergraph) — the complex's central operator | *(not built)* | — |

---

## Supporting notation (appears in the boundary docstrings & companion II)

These are not in the headline set but are load-bearing in the derived formulas above and in the
invariant catalog, so they are pinned here too:

| symbol | code / meaning | family |
|---|---|---|
| **MR** | `MIRROR_READABLE = {authored-solo, authored-dialogue}` — the mirror-readable subset of `P` | 1 |
| **μ(s_t)** | `Profile` — the behavioral profile at state `s_t`: capability rates ⊕ Constitution conformance | 4 |
| **Δ, s, s′** | a proposed self-mod change `Δ`, the state `s`, and `s′ = Δ·s iff G(Δ,s) else s` | 3 |
| **G, G_now** | the gate admission predicate; `G_now = approved ∧ golden ≥ B ∧ D ≤ Θ` (`conforms` deferred, G5) | 3 |
| **\|Agr(κ)\|** | `agreement` — the number of *distinct* interpreters that corroborate a claim | 2 |
| **Cit(A), Ret** | the citation set of an answer / the retrieved set; grounding is `Cit(A) ⊆ Ret` | 2 |

---

## How this is used

- **Boundary docstrings** (companion IV §B.4) at each family 1–4 boundary carry a three-line
  `OBJECT / INVARIANT / ENFORCED` header. The symbols in those headers resolve here.
- **The whitepapers** (companions I–IV + the technical companion) each reference this file from the top.
- **The assurance tier** column mirrors the companion II hierarchy (structural > static > runtime >
  property > assumption). Where a symbol's invariant is *not* structurally enforced, the honest
  residual is recorded in companion II as a gap (the G9–G11 pattern) — notation never outruns
  enforcement.

*Companion glossary. One name per symbol; the code keeps its readable identifiers; this table is the
join. If a symbol is added to the model, add it here first.*
