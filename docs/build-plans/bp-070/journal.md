# Journal — bp-070 (Phase Α: scope tooling — D1 types · D2 declared-scope layer · D3 composed graph)

## 2026-07-18 (session-28, FABLE) — minted (proposed); GATE: dn-agent-taxonomy ratification
First plan of the amended game plan ("algebra leads" — agents born scoped). Three items: D1 additive
lattice extensions (DIALOGUE + refinements; fiber C) with the law suite extended; D2
`core/agent_scope.py` (role template constructors + meet-composition + `assert_conforms`, precedent
`test_view_scopes.py`); D3 `core/graph/composed.py` (explicit nodes × `E_sim ∪ E_proven` union with
per-class attribution, feeding the EXISTING σ*/conductance math unchanged — grounded: the harness's
`MirrorGraph` is mirror-similarity-only, so the union enters at assembly, in core). Vocabulary+guard
tier only — no read-path gating, no Views, no stores, ratchet stays 19. Est opus/140k, budget 2.
**Awaits: owner RATIFIES dn-agent-taxonomy, then blesses this proposed→ready.**

## 2026-07-18 (session-29, OPUS) — build START: gate satisfied, grounding complete
`dn-agent-taxonomy` **ratified** (owner) → gate passed. Status ready→in-progress; active-plan pointer
set. Read the full §2 manifest. Grounding notes that will not re-derive:

- **D1 (`core/scope.py`) is a clean additive extension.** Add `DIALOGUE` (base) +
  `DIALOGUE_TRANSCRIPT`/`DIALOGUE_ARTIFACT` (refinements) to `Stratum`; two edges into `_REFINES`;
  `_BASE_STRATA` derives automatically (excludes refinements + FOUNDATION). Add `"C"` to `Fiber`
  literal and to `EdgeScope.top()`. `⊤_Σ` grows by one base stratum, 𝔇 unaffected. **No fiber call
  site assumes exhaustive {F,D}** — the only enumerations are `EdgeScope.top()` (extend) and the
  `_population()` fixture in test_scope.py. `test_scope.py` extends additively (every existing test
  must pass verbatim + new DIALOGUE-closure / C-in-top / extended-law cases).

- **D2 (`core/agent_scope.py`, NEW) — role constructors return plain `Scope`** (§6 pins `-> Scope`).
  Scopes (T-shape = declared window ∗, per the View SCOPE pattern):
  · `sensor_scope(stratum)`: Σ={stratum↓}, E=⊥, T=(N_S,∗), A=(READ,W_Σ=1,NONE), STATIC_GUARD.
  · `query_scope(strata)`: Σ=downset, E=top (reads all classes), T=(COMMIT,∗ → no SLICE), A=(READ,0,NONE).
  · `integrator_scope(read_pairs, write_fibers)`: Σ=downset over ≥2 BASE strata (VALIDATE ≥2 or raise);
    write_fibers ⊆ {C,F} (VALIDATE or raise — the out-of-region falsifier); E=of(write_fibers),
    T=(COMMIT,∗), A=(READ,W_Σ=1,NONE). Layer labels are constructor args, documented, NOT lattice
    elements (Q3 parked default).
  · `dreamer_scope(strata,...)`: Σ up to ⊤_Σ, E=top, A=(READ,W_Σ=1,NONE) — constructor only, grants
    owner-declared.
  · `assert_conforms(declared, handles)`: guard-tier ⊑ — each `Handle` carries (stratum, writes_stratum,
    writes_fiber); reject a handle whose stratum ∉ declared.sigma, or W_Σ/fiber beyond declared. The
    "smuggled extra handle" falsifier. Composition is the EXISTING `Scope.meet` (no new lattice ops).

- **D3 (`core/graph/composed.py`, NEW) — the consumed surface is MirrorGraph's duck-type**:
  `.n` (property), `.digest(i)->str`, `.neighbors(i)->list[int]`, `.sim` (np.ndarray `[i,j]`).
  `build_max_spanning_tree`/`sigma_star` use n/digest/neighbors/sim; `sigma_t_profile`/
  `effective_conductance` use n/digest/sim (re-threshold `sim[i,j]>=σ`); `reconnection_scan` uses
  n/digest/neighbors/sim. **Design:** `compose(nodes, sim_edges, proven_edges)` builds a flattened
  symmetric `sim` matrix = **max(weight)** per pair over the union (a proven edge weight 1.0 ≥ any
  cosine grid σ, so proven edges are present at every threshold — "a bridge C-edge joins two
  σ-components"); `_adj = sim>0`; per-class attribution retained in `edge_classes: dict[(i<j),
  frozenset]` with a `classes_of(a,b)` query. sim-only compose reproduces single-class behavior.
  **The math is UNCHANGED** — the test bridges ComposedGraph→MirrorGraph with a localized
  `cast(MirrorGraph, g)` (mypy checks tests/; cast is a static bridge, NOT a math change → NOT the
  §10 stop condition). Edge-weight-for-C = 1.0 (§11 parked default).

Item order 1 → {2, 3}. Building Item 1 next.

## 2026-07-18 (session-29, OPUS) — Item 1 COMPLETE (D1 type extensions)
`core/scope.py`: added `DIALOGUE` + `DIALOGUE_TRANSCRIPT`/`DIALOGUE_ARTIFACT` to `Stratum`, two
`_REFINES` edges, `"C"` to `Fiber` literal + `EdgeScope.top()`. `_BASE_STRATA` derives automatically.
`test_scope.py` extended additively (4 new tests; the 28 existing pass verbatim): dialogue downward
closure, ⊤_Σ ⊇ dialogue ∧ ∌ FOUNDATION, C in edge-top (orthogonal axis: meets F/D to ⊥), lattice
laws over a dialogue+C population. **Acceptance MET:** `test_scope.py` 32→ green (34 passed incl.
new), ruff+mypy clean, **ratchet 19** (scope.py imports only core — no new violation). **Falsifier
checked:** grepped every `EdgeScope.top()`/`.fibers` production site — none assumes exhaustive {F,D}
(the eval `ClaimFiber`/`FibersResult` hits are an unrelated fiber concept). Next: Items 2 + 3.

## 2026-07-18 (session-29, OPUS) — Item 2 COMPLETE (D2 declared-scope agent layer)
`core/agent_scope.py` (NEW, pure-core, imports only `core.scope`): five constructors returning plain
`Scope` (§6 pin) + `Handle`/`HandleInventory`/`ConformanceError`/`assert_conforms`.
· `sensor_scope`: Σ={stratum}↓, E=⊥, T=(N_S,∗), A=(READ,1,NONE). · `query_scope`: Σ=downset, E=⊤,
T=ledger(N,∗), A=(READ,0,NONE). · `integrator_scope(read_pairs, write_fibers)`: **validates** ≥2
distinct BASE strata (via `_base_of` mapping refinements→parent) AND fibers ⊆ {C,F}, else ValueError;
Σ=downset, E=of(fibers), T=(COMMIT,∗), A=(READ,1,NONE). Layer labels are documented args, not lattice
elements (Q3 parked). · `dreamer_scope`: Σ=downset(grant), E=⊤, T=ledger, A=(READ,1,NONE), constructor
only. · `assert_conforms`: per-`Handle` (stratum/writes_stratum/writes_fiber) ⊑ declared Σ/W_Σ/E, else
ConformanceError. **Composition is the EXISTING `Scope.meet`** — no new lattice op. **Acceptance MET:**
11 tests green (each role in-region; delegation meet ⊑ parent over query+integrator; conforms accepts
match, rejects out-of-Σ handle / W_Σ-violation / out-of-E fiber). **Falsifiers:** integrator rejects
single-base-stratum + rejects D write fiber; conformance rejects smuggled handle. ruff+mypy clean,
**ratchet 19**. Note: `from core.scope import _REFINES` (intra-core private import; scope.py stays
enum/literal-only per §4). Next: Item 3 (D3 composed graph).

## 2026-07-18 (session-29, OPUS) — Item 3 COMPLETE (D3 composed graph) + SEAL
`core/graph/composed.py` (NEW, pure-core, imports only numpy): `ComposedGraph` frozen dataclass +
`compose(nodes, sim_edges, proven_edges)`. Presents MirrorGraph's EXACT runtime surface (`.n`,
`.digest`, `.neighbors`, `.sim`) so the σ*/conductance math runs UNCHANGED. Union = flattened
weighted multigraph via **max** weight per pair; `_adj = sim>0`; per-class attribution in
`edge_classes[(i<j)]→frozenset` with `classes_of(a,b)`. Proven weight 1.0 (§11) dominates any cosine
⇒ present at every grid σ ⇒ bridges components. **Acceptance MET (8 tests):** sim-only reproduces
single-class (two σ-components); proven bridge flips σ*(a,d) None→0.9 with chain a-b-c-d + raises
effective conductance 0→positive (Rayleigh direction); both class tags survive a sim∧proven pair
(max weight kept); `pairwise_sigma_star` + `sigma_t_profile` + `effective_conductance` all called on
the composed graph DIRECTLY. **Falsifiers:** math needed ZERO change (real functions run via a
localized `cast(MirrorGraph,·)` static bridge — mypy clean on module AND test, NOT the §10 stop
condition); class tags not lost; compose fails closed on unknown node / self-loop. ruff+mypy clean.

═══ SEAL — bp-070 COMPLETE (Phase Α, the diamond's root) ═══
All 3 items landed. **Whole-plan verification:** full deterministic suite (gate command, ratchet
deselected) = **1567 passed, 4 skipped, 0 failures** — the existing View/scope/graph suites pass
UNMODIFIED (the whole-plan falsifier). **Ratchet held 19** every phase (all three modules import only
core substrate; agent_scope→core.scope, composed→numpy). No Views/stores/harness touched (§9 honored).
- **Delivered:** D1 DIALOGUE stratum (+2 refinements) + fiber C — additive lattice extension, law
  suite extended not modified. D2 `core/agent_scope.py` — 4 role constructors + conformance, born
  scoped, composition = existing meet. D3 `core/graph/composed.py` — E_sim ∪ E_proven assembly
  feeding the existing math unchanged, per-class attribution retained.
- **Enables:** Β (bp-069) consumes D2's `sensor_scope(DIALOGUE)` + `assert_conforms`; Γ (bp-071)
  consumes D1's C/DIALOGUE + D2's `integrator_scope`; Δ consumes D3's composed graph.
- **Parked (unchanged from §11):** layer-refinement lattice inside Σ (v1 = (stratum,layer) args);
  dialogue_artifact vs reference_repo overlap; C-class edge weights (1.0, Δ calibrates).
- **cost.actual (owner relay, session-29):** opus, **$15.29** (shared w/ the ops-leg fix), **105.2k
  output tokens** vs 140k estimate → **ratio 0.75×** (tight §6 pinning + full manifest up front →
  near-first-try landings, only ruff line-length fixups). session_delta **+8%** (62%→70%), week_delta
  **~0%** (11%→11%). Single session (budget was 2). ⚠️ 94% of 24h usage at >150k context — bp-069
  gets a FRESH small-context session, not a continuation.
Status flipped in-progress→complete; active-plan pointer cleared.
