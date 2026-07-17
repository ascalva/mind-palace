---
type: build-plan
id: bp-060
alias: conductance-profile
status: proposed
design_ref:
  - docs/design-notes/connectivity-instruments.md   # RATIFIED — CN-3 (the (σ,t) conductance profile + reconnection) + CN-4 (churn as change of measure)
contract: builder
write_scope:
  - eval/harness/conductance.py
  - tests/unit/test_conductance.py
  - tests/quality/test_conductance.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: [bp-059]
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/global-event-clock.md                       # GC-2 proper time / N_s (the depth budget)
  - docs/design-notes/velocity-instruments.md                     # churn/velocity magnitudes CN-4 consumes
  - docs/findings/finding-0090.md                                 # OPEN proper-time erratum — CN-4 uses N_s COUNTS, sidesteps it (see §3)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CN-3 + CN-4: the (σ,t) conductance profile, the churn change-of-measure, and reconnection events

## 0. Mode & provenance
Graduated from RATIFIED `dn-connectivity-instruments` CN-3 + CN-4. Investigation & planning produced
this; implementation proceeds item-by-item on owner approval; `proposed → ready` is owner-only. **Depends
on bp-059** — imports its `ConnIndex`/`ConnEvidence`/latest-cut acquisition from `eval/harness/connectivity.py`
(build bp-059 first; do not re-lay that scaffolding). The heart of this plan is a **law, not a knob**:
the churn signs are forced by circuit law (series impedes, parallel conducts); only the magnitudes are
sweepable, and they ship at 0.

## 1. Objective
`eval/harness/conductance.py`: report effective conductance **only as the (σ,t) profile** (never one
scalar) — finite-t diffusion/commute distances over the σ-graph Laplacian, each profile carrying its own
von-Luxburg **degeneracy self-diagnostic**; the **churn change-of-measure** edge weights
`w(u,v) = cos^α · exp(s_lat·a_lat − s_seq·a_seq)` (signs structural, α=1, magnitudes THRESH-dict at 0) with
the `χ_s` sequentiality statistic and the depth-budget tooth; and a **reconnection rider** — a verified
Δ-conductance spike across a cut pair with the bridging edge(s) named.

## 2. Context manifest (read in order)
1. `docs/design-notes/connectivity-instruments.md` — WHOLE, focus CN-3 (§2.3), CN-4 (§2.4), §3 item-2,
   §4 parked (conductance grain), §5 D1 (the sign is RETIRED — derived by circuit law, not chosen).
2. bp-059's merged `eval/harness/connectivity.py` — `ConnIndex`, `ConnEvidence`, `run_connectivity`,
   the latest-cut acquisition (`spine.cut_at`), the graph-at-cut convention. **The surface this imports.**
3. `core/dreaming/graph.py:22-59` — `MirrorGraph` (`sim`, `_adj`, `neighbors`, `degree`,
   `local_clustering`). The weighted adjacency the Laplacian is built from.
4. `core/temporal/spine.py:585-870` — `Spine.restrict`/`n_s(stratum)` (the N_s induced sub-poset),
   `events()`, `proper_time(a,b) -> (int, bool)`, `frontier`, `cut_at`/`downset`/`crossing_edges`.
   The depth-budget + χ_s source.
5. `eval/harness/gate.py:64-71` — `GATE_THRESH: dict[str, float]` (the THRESH-dict pattern to copy for
   `CONDUCTANCE_THRESH`) + the `NOISE_SETTLED_MAX` module-constant contrast (tolerances stay OUT of the dict).
6. `core/velocity.py` (or the module velocity-instruments landed in) — the churn magnitudes `a_lat`/`a_seq`
   read from; **consume magnitudes only, not the cross-edge-space angle** (finding-0091 — no dependency).
7. `eval/harness/store.py:47-100` — `EvalKey`/`Reading`/`EvalResultsStore.put` (the write target).

## 3. Investigation & grounding
- **Q1 — Laplacian source.** `MirrorGraph.sim` (`core/dreaming/graph.py:24`) is the full cosine matrix;
  `_adj` the boolean σ-adjacency. The weighted Laplacian `L = D − W` uses `W = _adj * (churn-weighted sim)`
  per CN-4 (below). No networkx — NumPy `np.linalg` / `scipy.linalg` on the dense matrix (corpus is small;
  finding-0096 scale). R_eff via the pseudo-inverse `L⁺`; heat kernel `exp(−tL)` via eigendecomposition.
- **Q2 — the degeneracy self-diagnostic.** von Luxburg: R_eff → `1/d_A + 1/d_B` in dense/large regimes.
  The diagnostic is `corr(R_eff(A,B), 1/deg(A) + 1/deg(B))` over all pairs **at the loosest σ** (densest
  graph). High corr ⇒ R_eff is degenerate ⇒ the profile's authoritative reading is the **finite-t
  diffusion distance**, not R_eff. Every emitted profile carries this scalar (CN-3 falsifier: absent ⇒ malformed).
- **Q3 — the depth budget & χ_s (CN-4), grounded in the spine.** `N_s(W)` = the per-stratum event count
  over a window; from `len(spine.n_s(stratum).events())` restricted to W (`spine.py:788` `n_s`; `:686`
  `events`). The depth-budget tooth: no ≼-chain within `(s, W)` exceeds `N_s(W)` events — checkable via
  `spine.proper_time(a,b)` (`:793`, the max-chain length; `chain_complete` flags cross-stratum/concurrent).
  Sequentiality `χ_s(W) = longest-chain / N_s(W) ∈ (0,1]`, =1 iff the window-events are totally ordered.
  *Code settles this:* `proper_time` gives longest-chain; `n_s(...).events()` gives N_s. **finding-0090
  (proper-time-exactness erratum, OPEN) does NOT block this:** CN-4 uses N_s event *counts* (built objects),
  not the proper-time metric's exactness (note §Cross-references, verbatim). The v1 `a_•(u,v)` edge
  convention = mean of the endpoint strata's statistics (note §2.4; revisited at design review).
- **Q4 — the signs are LAW (D1 retired).** Sequential churn (supersession depth) acts in **series** ⇒
  impedes (the `−s_seq·a_seq` term); lateral churn (new cross-links) acts in **parallel** ⇒ conducts (the
  `+s_lat·a_lat` term) — Rayleigh monotonicity. The code must **never** assign lateral churn an impedance
  sign or sequential churn a conductance sign; the sign is structural, only `(s_seq, s_lat)` magnitudes are
  tunable, shipped at 0 in the THRESH dict. No `ops/levers.py` entry (promotion is a separate owner-visible act).
- **Q5 — reconnection across cuts, and the historical-graph gap (inherited from bp-059).** A reconnection
  event is a Δ-conductance spike between cuts with a large proper-time gap, **verified** by leave-one-out
  re-computation naming the bridging edge(s). *Code does not settle real-corpus historical graphs* — bp-059
  established `MirrorView` has no cut-restriction; v1 pins to the latest cut. So: the Δ-scan + leave-one-out
  attribution is **fully testable on SYNTHETIC cut-pairs** (G1, G2=G1+edges) for v1; the **real-corpus
  forward scan** reads the accumulated conductance reading series across ≥2 forward-*sampled* cuts (§4
  parked cut-sampling default) and is PARTIAL until the store holds ≥2 cuts with retained edge sets (§11).
- **Q6 — not a recall objective (finding-0096).** Conductance falsifiers are Rayleigh monotonicity + the
  self-diagnostic + a synthetic decay-only null — all structural, none a golden_recall signal.

**Additional risks:** (a) singular/near-singular L on a disconnected graph — operate per connected
component; R_eff across components is ∞ (report "not connected within grid", not a huge number). (b) t-grid
choice — declare a t-grid in evidence (like the σ-grid); the profile is `(σ, t)`-indexed, both pinned.

## 4. Reconciliation
- `dn-connectivity-instruments` §5 **D1 is RETIRED** by owner refinement (2026-07-17): the sign is not a
  decision. → **cross-reference-on-extension** in `conductance.py`'s module docstring: the churn term's
  signs are derived by circuit law, cite CN-4 §2.4; state that only `CONDUCTANCE_THRESH` magnitudes are
  sweepable and they ship at 0. No design-note edit (notes are owner-immutable).
- `finding-0090` (proper-time erratum, OPEN) — the plan **records** that it consumes N_s counts not the
  metric's exactness, so the erratum does not gate it → a comment at the χ_s call site citing finding-0090
  + note §Cross-references. Not a correction; a documented non-dependency.

## 5. Write scope
`eval/harness/conductance.py` + its two test files. **OUT:** `eval/harness/connectivity.py` (bp-059's —
imported read-only), `core/**` (graph/spine/velocity are read-only substrate), `ops/levers.py` (the churn
magnitudes live in this module's `CONDUCTANCE_THRESH` dict — NEVER a lever here; promotion is a separate
owner act), `eval/harness/gate.py`/`fibers.py`/`store.py` (imported), the foundation denylist, the mirror
surfacing wiring.

## 6. Interfaces pinned inline
```python
# --- CONSUMED (verbatim) ---
# eval/harness/connectivity.py  (bp-059)
@dataclass(frozen=True)
class ConnIndex: grid: tuple[float, ...]; cut: CertifiedCut
@dataclass(frozen=True)
class ConnEvidence:
    grid: tuple[float, ...]; base_fingerprint: str; cut_fingerprint: str
    def as_ref(self) -> str: ...
# core/dreaming/graph.py
class MirrorGraph:
    sim: np.ndarray; _adj: np.ndarray
    def degree(self, i: int) -> int: ...
    def neighbors(self, i: int) -> list[int]: ...
# core/temporal/spine.py
class Spine:
    def n_s(self, stratum: str) -> Spine: ...          # the N_s induced sub-poset (alias of restrict)
    def events(self) -> list[SpineEvent]: ...
    def proper_time(self, a: str, b: str) -> tuple[int, bool]: ...   # (max-chain length, chain_complete)
# eval/harness/gate.py — the THRESH-dict pattern to copy
GATE_THRESH: dict[str, float] = {"theta_weak_cells": 2.0, "theta_strong": 0.5}

# --- TO BUILD in eval/harness/conductance.py ---
_INSTRUMENT = "conductance/v1"

# α default 1; magnitudes shipped at 0 (signs are LAW, not in the dict — the dict holds MAGNITUDES only)
CONDUCTANCE_THRESH: dict[str, float] = {
    "alpha": 1.0,     # cos(u,v)^α edge exponent
    "s_seq": 0.0,     # sequential-churn magnitude (series, impedes — the MINUS sign is structural)
    "s_lat": 0.0,     # lateral-churn magnitude (parallel, conducts — the PLUS sign is structural)
}

@dataclass(frozen=True)
class ConductanceProfile:
    a: str; b: str
    sigma_grid: tuple[float, ...]; t_grid: tuple[float, ...]
    commute: tuple[tuple[float, ...], ...]        # (σ × t) finite-t commute/diffusion distances
    r_eff_loosest: float                          # R_eff at loosest σ
    degeneracy_diag: float                        # corr(R_eff, 1/d_A + 1/d_B) at loosest σ — ALWAYS present
    chi_s: dict[str, float]                       # per-stratum sequentiality χ_s(W) ∈ (0,1]

@dataclass(frozen=True)
class ReconnectionEvent:
    a: str; b: str; delta_conductance: float
    proper_time_gap: int
    bridging_edges: tuple[tuple[str, str], ...]   # leave-one-out VERIFIED, never guessed

def churn_weight(sim_uv: float, a_lat: float, a_seq: float, thresh: Mapping[str, float]) -> float
def sigma_t_profile(graph: MirrorGraph, *, sigma_grid, t_grid, thresh) -> list[ConductanceProfile]
def reconnection_scan(before: MirrorGraph, after: MirrorGraph, *, proper_time_gap: int) -> list[ReconnectionEvent]
def run_conductance(*, view, spine, sigma_grid, t_grid, eval_store, base_fingerprint) -> ...
```

## 7. Items
### Item 4 — the (σ,t) profile + the degeneracy self-diagnostic  (blast: read-only)
- **Objective:** the weighted Laplacian per σ, finite-t commute/diffusion distances, and the von-Luxburg
  self-diagnostic on every profile.
- **Files:** `eval/harness/conductance.py`, `tests/unit/test_conductance.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_conductance.py -q` green — **Rayleigh monotonicity:**
  conductance is non-decreasing as σ loosens (removals never raise conductance) on real + synthetic graphs;
  every `ConductanceProfile` carries a `degeneracy_diag`; on a synthetic dense graph the diagnostic is high
  (R_eff ≈ 1/d_A+1/d_B) and the profile flags finite-t as authoritative; R_eff across disconnected
  components is ∞ → "not connected within grid".
- **Falsifier:** conductance *rising* as σ tightens (Rayleigh violated — the Laplacian/sign is wrong); a
  profile emitted without the self-diagnostic; a single dense-graph R_eff scalar reported as "the conductance".
- **Invariant(s):** never one scalar — always the (σ,t) profile; the self-diagnostic on every profile;
  model-free; certified-cut-only.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** bp-059.

### Item 5 — the churn change-of-measure + χ_s + the depth-budget tooth  (blast: read-only)
- **Objective:** `churn_weight` with structural signs (series −, parallel +), α from `CONDUCTANCE_THRESH`,
  magnitudes at 0; the per-stratum χ_s statistic; the depth-budget falsifier on the real spine.
- **Files:** `eval/harness/conductance.py`, `tests/unit/test_conductance.py`.
- **Acceptance test:** unit tests green — with `s_seq=s_lat=0` the weight reduces to `cos^α` (default 1 ⇒
  the raw cosine — a numerical no-op vs item 4, proving zero-magnitude ships inert); a **grep/AST test** asserts
  no code path pairs lateral churn with a minus or sequential churn with a plus (signs are law); a **grep
  test** asserts no hard-coded nonzero magnitude outside `CONDUCTANCE_THRESH` and no `ops.levers` import;
  **depth budget:** on the real spine, no ≼-chain within `(s, W)` exceeds `N_s(W)` events, and
  `χ_s ∈ (0,1]` with `χ_s = 1` iff the window-events are totally ordered (synthetic check).
- **Falsifier:** a lateral-churn impedance sign or a sequential-churn conductance sign anywhere; a nonzero
  magnitude hard-coded outside the dict; an `ops/levers.py` promotion done inside this plan; a ≼-chain
  exceeding `N_s(W)` (the budget law is violated — the spine or the counting is wrong); `χ_s > 1`.
- **Invariant(s):** signs structural (never tuned); magnitudes THRESH-first; the depth budget is additive
  (`N(W) = Σ_s N_s(W)`); CN-4 metric-curvature axis stays independent of §2.6 gauge holonomy.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** item 4.

### Item 6 — the reconnection rider (synthetic-verified) + entry point + readings  (blast: additive writes)
- **Objective:** `reconnection_scan` on a cut-pair: a Δ-conductance spike verified by leave-one-out edge
  attribution; the entry point + keyed readings with the ConnEvidence pin.
- **Files:** `eval/harness/conductance.py`, `tests/quality/test_conductance.py`.
- **Acceptance test:** `uv run pytest tests/quality/test_conductance.py -q` green — on a **synthetic
  cut-pair** `G2 = G1 + {e}` the scan reports a positive Δ-conductance and names `e` as the bridging edge
  (leave-one-out re-computation without `e` erases the rise); a **decay-only** synthetic interval
  (`G2 = G1 − edges`) shows **no** conductance increase (the null); every reading's `evidence_ref` decodes
  to a ConnEvidence carrying the σ-grid + t-grid + cut fingerprint; `put()` idempotent (re-run writes 0).
  The real-corpus forward scan runs with ≥2 sampled cuts if the store holds them, else reports "no cut pair
  yet" and notes it (a sanctioned partial outcome).
- **Falsifier:** a bridging edge named that leave-one-out does NOT confirm (a guessed reconnection — CN-3
  forbids); a decay-only interval showing a conductance rise (the monotonicity/attribution is broken); a
  reading missing the t-grid or cut fingerprint.
- **Invariant(s):** reconnection reports only edges it *verified* (leave-one-out), never a guess; the
  (σ,t) profile discipline; idempotent-by-key writes; certified-cut-only.
- **Touches stored data?** Yes — eval Readings; dry-run in-memory `EvalResultsStore` in the test first;
  no core-store writes.
- **Parallelizable?** No.  **Depends on:** items 4–5.

## 8. Math carried explicitly
- **Effective conductance / R_eff** — *measures:* the electrical conductance of the σ-graph between two
  thoughts (commute-time proportional). *valid when:* reported as the (σ,t) profile with the degeneracy
  self-diagnostic; per connected component. *fails its keep if:* it degenerates to `1/d_A+1/d_B` (the
  diagnostic fires) and is still reported as the authoritative distance instead of finite-t diffusion.
- **Finite-t diffusion / commute distance** — *measures:* expected wander time of a dreamer-like walk.
  *valid when:* `t` is finite and declared in the t-grid; the graph is connected in-component. *fails its
  keep if:* it disagrees with R_eff in the sparse regime where R_eff is NOT degenerate (both should agree there).
- **χ_s — window sequentiality** — *measures:* how totally-ordered a stratum's window-events are
  (`longest-chain / N_s(W)`). *valid when:* `N_s(W) > 0`; longest-chain from `spine.proper_time`. *fails its
  keep if:* `χ_s ∉ (0,1]`, or `χ_s ≠ 1` on a synthetically total order.
- **The churn change-of-measure weight** — *measures:* how sequential vs lateral churn reweights an edge's
  conductance. *valid when:* signs are structural (series −, parallel +), α and magnitudes from
  `CONDUCTANCE_THRESH`. *fails its keep if:* a sign is assigned by tuning, or a magnitude lives outside the dict.

## 9. Non-goals
No bridges / arc search (bp-061). No helix (bp-062). No σ* re-implementation (import bp-059). No
`MirrorView` cut-restriction / historical-graph reconstruction (parked in bp-059). No `ops/levers.py`
promotion. No golden_recall coupling (finding-0096). No magnetic/spectral route (its own lane's gate). No
mirror surfacing wiring. No claim matching (SF-a). No proper-time-exactness fix (finding-0090 — sidestepped, not touched).

## 10. Stop-and-raise conditions
- The real-corpus reconnection scan needs a historical graph (not just the sampled series) for acceptance →
  STOP; that is bp-059's parked `core/` prerequisite (a re-graduation trigger), not a mid-build core edit.
- Any temptation to pick a churn sign by data-fit → STOP; the sign is circuit law (D1 retired), only
  magnitudes tune.
- Any pressure to hard-code a nonzero magnitude "to see an effect" → STOP; magnitudes ship at 0, sweeps are
  a separate act; a promotion to `ops/levers.py` is owner-visible and not this plan.
- The spine has no certified mirror cut / N_s is empty → file a `codebase` finding, journal, complete the
  buildable structural items, park the spine-dependent ones with the re-entry.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| real-corpus reconnection over history | synthetic cut-pairs verified; real scan reads the sampled reading series (partial until ≥2 cuts) | reconstruct historical graphs now | bp-059's `MirrorView` downset `core/` plan lands + ≥2 forward-sampled cuts with retained edge sets |
| `a_•(u,v)` edge convention | mean of endpoint strata's statistics | canonical poset depth/width (Mirsky/Dilworth) now — heavier | item-2 design review shows the mean convention distorts a real region |
| churn magnitudes as registered levers | `CONDUCTANCE_THRESH` dict (shipped 0) | `ops/levers.py` entries now | owner wants sweep-driven `(s_seq,s_lat)` tuning → a separate owner-visible lever plan |
| conductance grain (chunk vs note) | note-centroid grain | chunk-grain now | design review shows chunk/claim-grain queries dominate |

## 12. Dependency & ordering summary
**Depends on bp-059** (imports `ConnIndex`/`ConnEvidence`/latest-cut acquisition + the graph-at-cut
convention). Items serial by blast radius: 4 (read-only: profile + self-diagnostic) → 5 (read-only: churn
signs/χ_s/depth-budget) → 6 (additive writes: reconnection rider + entry point). Not parallelizable with any
sibling. **Downstream:** bp-061 (bridges) uses the conductance profile as the confidence axis of a two-axis
bridge report.
