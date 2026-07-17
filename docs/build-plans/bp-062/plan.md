---
type: build-plan
id: bp-062
alias: helix-detector
status: ready
design_ref:
  - docs/design-notes/connectivity-instruments.md   # RATIFIED — CN-6 (the helix: revisitation is necessarily helical)
contract: builder
write_scope:
  - eval/harness/helix.py
  - tests/unit/test_helix.py
  - tests/quality/test_helix.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
  actual: null
depends_on: [bp-059]     # + GATED on uuid-identity landing (no plan id yet — see §0/§10/§12). Item 11 is the gated leg.
parallelizable_with: [bp-060, bp-061]   # independent of conductance/bridges (different graph); the shared surface is bp-059's scaffolding
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/global-event-clock.md                       # GC-2 proper time (the refinement gain) + the spine's acyclicity (the theorem's engine)
  - docs/brainstorms/magnetic-laplacian-fable-pass.md             # Q3/Q6 — the pitch is the proper-time refinement of the arm-imbalance flux; U(1) route stays gated
  - docs/findings/finding-0090.md                                 # OPEN proper-time erratum — the ℤ-primary gain SIDESTEPS it; the refinement waits on it
re_entry: null            # proposed, not parked; the uuid-identity gate is encoded in §0/§10/§12, not here
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CN-6: the helix detector — revisitation is necessarily helical

## 0. Mode & provenance — GATED
Graduated from RATIFIED `dn-connectivity-instruments` CN-6. **This plan is GATED on uuid-identity landing**
(owner-confirmed, 2026-07-17): the idea-quotient projection **π needs stable idea-identity along supersession
chains**, which is uuid-identity's own design/plan (not this tranche; the third registered consumer after
Track D and SF-a). Implementation proceeds item-by-item on owner approval; `proposed → ready` is owner-only.

**The gate is per-item, not all-or-nothing.** Item 10 (the combinatorial detector + pitch functional on a
**synthetic** gain graph) is buildable **now** — it needs no π. Item 11 (wiring π to the **real** corpus idea
quotient) is the leg that requires uuid-identity. **Owner's stated default (honored):** the whole plan waits
behind uuid-identity. The option surfaced for the owner's decision: bless item 10 forward independently (the
detector's correctness is fully provable on synthetic gain graphs — CN-6's "synthetic first, real once π
lands"), leaving item 11 parked behind the gate. The recommendation stands as the owner's — this note only
records that the split makes early value available if wanted.

## 1. Objective
`eval/harness/helix.py`: on the **gain graph over the idea quotient** (spatial edges gain 0; temporal edges
the ℤ-valued interval count as primary gain), compute the **pitch** (a linear functional on the cycle space)
of fundamental cycles off a spanning tree (O(E)), and detect **helices** — cycles of **nonzero pitch** (NOT
snapshot-invisibility) — reporting each with its pitch (period) and winding (revisit count); the forced-helix
theorem holds (every all-forward closed idea-walk has strictly positive pitch).

## 2. Context manifest (read in order)
1. `docs/design-notes/connectivity-instruments.md` — WHOLE, focus CN-6 (§2.6: the gain graph, the ℤ-primary
   gain, pitch = nonzero not snapshot-invisibility, the forced-helix theorem, π's requirement surface, the
   three falsifiers), §3 item-4 (the gate), §5 D3 (uuid-identity scheduling is the owner's).
2. bp-059's `eval/harness/connectivity.py` — `ConnIndex`, `ConnEvidence`, the cut acquisition (the shared
   CN-1 scaffolding this reuses).
3. `core/temporal/spine.py:108-148, 585-870` — `SpineEvent`, `SpineEdge` (`src`,`dst`,`gen`), `generators()`,
   `order(a,b) -> Order`, `proper_time(a,b) -> (int, bool)`, the **constructed acyclicity** (`SpineCycleError`,
   the theorem's engine). The temporal edges + the interval-count source.
4. `docs/brainstorms/magnetic-laplacian-fable-pass.md` — Q3 (pitch = proper-time refinement of arm-imbalance
   flux) + Q6 (the U(1)/spectral route stays behind the magnetic lane's gate — v1 is combinatorial only).
5. `docs/findings/finding-0090.md` — the OPEN proper-time erratum; why the ℤ-primary gain sidesteps it (the
   per-stratum proper-time refinement waits on its resolution).
6. `eval/harness/store.py:47-100` — `EvalKey`/`Reading`/`EvalResultsStore.put`.
7. **(item 11 only, gated)** the uuid-identity design/module once it lands — π's surface: total on versioned
   chunks, constant along supersession chains, never merging distinct ideas.

## 3. Investigation & grounding
- **Q1 — the primary gain: the ℤ interval count.** A spatial edge (co-presence) carries gain 0; a **forward
  temporal edge** carries the ℤ-valued **interval count**, strictly positive per forward hop, well-defined even
  across strata. Source: the spine's forward temporal structure — `SpineEdge`/`generators()` + `order(a,b)`
  (`core/temporal/spine.py:691,639`). *Code does not settle the exact interval-count definition for a
  cross-stratum hop;* what would: a spine method returning the interval count per forward hop. **v1 default
  (pinned):** the interval count = the number of forward temporal generators traversed along the hop (1 per
  primitive forward edge); the per-stratum **proper-time refinement** (`proper_time`, `spine.py:793`) applies
  only where a hop stays within one stratum, and **waits on finding-0090** (the ℤ-primary choice is exactly the
  insulation — CN-6 §2.6 verbatim).
- **Q2 — pitch is a linear functional on the cycle space; the criterion is NONZERO pitch.** Not
  snapshot-invisibility: a citation cycle fully co-present at one cut can carry positive pitch (a legitimate,
  separately-reported subclass — "closed by time while visible in one snapshot"). v1 detector = fundamental-cycle
  pitches off a spanning tree, O(E) (each non-tree edge closes one fundamental cycle; its pitch = the gain sum
  around it).
- **Q3 — the forced-helix theorem + its engine.** Every closed idea-walk traversing ≥1 temporal edge
  **all-forward** has strictly positive pitch — its lift cannot close; the engine is the spine's **constructed
  acyclicity** (`SpineCycleError` fail-closed, `spine.py:151`). Purely-spatial cycles are legal and **flat**
  (pitch 0); time-balanced mixed cycles exist (forward + backward temporal hops cancelling).
- **Q4 — π needs uuid-identity (the gate).** The idea quotient collapses a versioned chunk's supersession chain
  to one idea-node; π must be **total on versioned chunks, constant along supersession chains, and never merge
  distinct ideas** — **false merges manufacture phantom cycles**, so the detector's integrity depends on π's
  **precision** more than its recall. π is uuid-identity's deliverable; **item 11 cannot be built until it
  lands** (the gate). Item 10 needs no π — it operates on a hand-constructed synthetic gain graph.
- **Q5 — not a recall objective (finding-0096).** The falsifiers are structural (spatial-only ⇒ pitch 0;
  all-forward revisitation ⇒ pitch > 0; a zero-pitch cycle reported as a helix is a bug), none a recall signal.

**Additional risks:** (a) a **false merge** in π (item 11) manufactures a phantom helix — item 11's acceptance
must include a π-precision guard (a known distinct-idea pair must NOT collapse). (b) the U(1)/spectral pitch
route is OUT (magnetic lane's gate, Q6) — v1 is combinatorial only.

## 4. Reconciliation
- `finding-0090` (proper-time erratum, OPEN) — CN-6's ℤ-primary gain is chosen precisely so the detector does
  not depend on proper-time exactness. → **cross-reference-on-extension**: a comment at the gain-assignment
  site citing finding-0090 + CN-6 §2.6, stating the per-stratum refinement is deferred until the erratum
  resolves. Not a correction; a documented deferral.
- No code is corrected; the idea quotient is a NEW eval-side construction (no existing quotient to reconcile).

## 5. Write scope
`eval/harness/helix.py` + its two test files. **OUT:** `eval/harness/connectivity.py` (bp-059's — imported),
`core/temporal/spine.py` (read-only substrate — the acyclicity is consumed, never modified), the uuid-identity
module (item 11 imports π read-only once it lands; it does not author it), `ops/**`, the foundation denylist,
the mirror surfacing wiring.

## 6. Interfaces pinned inline
```python
# --- CONSUMED (verbatim) ---
# core/temporal/spine.py
@dataclass(frozen=True)
class SpineEdge: src: str; dst: str; gen: str        # "g1"|"g2"|"g3"
class Order(Enum): BEFORE; AFTER; CONCURRENT
class SpineCycleError(RuntimeError): ...              # the constructed-acyclicity engine
class Spine:
    def generators(self) -> tuple[SpineEdge, ...]: ...
    def order(self, a: str, b: str) -> Order: ...
    def proper_time(self, a: str, b: str) -> tuple[int, bool]: ...   # the refinement gain (within-stratum only)
# eval/harness/connectivity.py (bp-059)
@dataclass(frozen=True)
class ConnEvidence: ...
    def as_ref(self) -> str: ...

# --- TO BUILD in eval/harness/helix.py ---
_INSTRUMENT = "helix/v1"

@dataclass(frozen=True)
class GainEdge:                                       # the gain graph over the idea quotient
    u: str; v: str; gain: int                         # 0 for spatial (co-presence); ℤ interval count for forward temporal

@dataclass(frozen=True)
class Helix:
    cycle: tuple[str, ...]                            # the idea-node cycle
    pitch: int                                        # nonzero ⇒ helix (the period); NEVER snapshot-visibility
    winding: int                                      # the revisit count
    co_present: bool                                  # True ⇒ the "closed by time while visible in one snapshot" subclass

def fundamental_cycle_pitches(edges: Sequence[GainEdge]) -> list[Helix]   # off a spanning tree, O(E)
def detect_helices(edges: Sequence[GainEdge]) -> list[Helix]              # the nonzero-pitch cycles
# item 11 (GATED on uuid-identity):
def idea_quotient_gain_graph(*, spine: Spine, pi) -> list[GainEdge]       # π = uuid-identity projection (imported)
def run_helix(*, spine, pi, eval_store, base_fingerprint) -> ...          # real-corpus entry (GATED)
```

## 7. Items
### Item 10 — the gain graph + pitch functional + fundamental-cycle detector (SYNTHETIC; UNGATED)
- **Objective:** the pitch of fundamental cycles off a spanning tree, the nonzero-pitch helix criterion, and
  the forced-helix theorem — all provable on synthetic gain graphs, **no π required**.
- **Files:** `eval/harness/helix.py`, `tests/unit/test_helix.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_helix.py -q` green — **spatial-only ⇒ flat:** every
  spatial-only (all-gain-0) cycle has pitch 0 and is NOT reported as a helix; **forced-helix:** every synthetic
  all-forward temporal closed walk has strictly positive pitch; a **time-balanced** mixed cycle (forward +
  backward hops summing to 0) has pitch 0 (legal, flat); a **co-present positive-pitch** cycle is reported as a
  helix with `co_present=True` (the criterion is nonzero pitch, not snapshot-visibility); pitch is computed as
  the gain sum around each fundamental cycle (O(E) off a spanning tree).
- **Falsifier (CN-6, verbatim):** a nonzero pitch on any spatial-only cycle; a zero pitch on any all-forward
  revisitation walk; a **zero-pitch cycle reported as a helix** (the detector used snapshot-visibility as the
  criterion — the explicit bug CN-6 names).
- **Invariant(s):** the helix criterion is nonzero pitch (never snapshot-visibility); pitch is linear on the
  cycle space; the combinatorial v1 only (no U(1)/spectral); model-free; no writes.
- **Touches stored data?** No.
- **Parallelizable?** No (item 11 builds on it).  **Depends on:** none (synthetic; bp-059 only for later readings).

### Item 11 — the real-corpus idea quotient via π + readings  (GATED on uuid-identity)
- **Objective:** `idea_quotient_gain_graph` wiring the real spine's temporal edges + π (uuid-identity) into the
  gain graph; the entry point + keyed readings with the ConnEvidence pin.
- **Files:** `eval/harness/helix.py`, `tests/quality/test_helix.py`.
- **GATE:** requires uuid-identity's π to exist. **If π is absent, the builder STOPS at this item, parks it**
  with re-entry `uuid-identity lands` (a sanctioned partial completion — item 10 ships, item 11 waits), and
  completes the plan. Do NOT stub π or fabricate an idea quotient.
- **Acceptance test (once π lands):** `uv run pytest tests/quality/test_helix.py -q` green — on the real
  corpus, spatial-only citation cycles are flat and all-forward revisitations are helical (the falsifiers, now
  real); a **π-precision guard**: a known pair of **distinct** ideas is NOT collapsed by π (a false merge would
  manufacture a phantom helix); every reading's evidence_ref decodes to a ConnEvidence; `put()` idempotent.
- **Falsifier:** a phantom helix traced to a π false-merge (π's precision failed — the detector's integrity
  clause); a real all-forward revisitation reported flat; a reading missing the cut/grid pin.
- **Invariant(s):** π total/constant-along-supersession/precision-first; certified-cut-only; idempotent writes;
  surfacing-only (no weight/promotion).
- **Touches stored data?** Yes — eval Readings; dry-run in-memory store first.
- **Parallelizable?** No.  **Depends on:** item 10 + **uuid-identity (the gate)**.

## 8. Math carried explicitly
- **The gain graph over the idea quotient** — *measures:* the winding of idea-walks through time. *valid when:*
  spatial edges carry gain 0, forward temporal edges the ℤ interval count (strictly positive); π is
  precision-first (no false merges). *fails its keep if:* a false merge manufactures a phantom cycle.
- **Pitch (linear functional on the cycle space)** — *measures:* how far a closed idea-walk fails to close in
  the lift (the helix period). *valid when:* computed as the gain sum around a fundamental cycle; the criterion
  is nonzero (not snapshot-visibility). *fails its keep if:* a spatial-only cycle has nonzero pitch, or a
  zero-pitch cycle is called a helix.
- **The forced-helix theorem** — *measures:* that revisitation is necessarily helical (all-forward closed walks
  have positive pitch). *valid when:* the spine's constructed acyclicity holds (the engine). *fails its keep
  if:* an all-forward revisitation walk shows pitch 0.

## 9. Non-goals
No σ*/conductance/bridges (bp-059/060/061). No U(1)/spectral pitch route (the magnetic lane's own gate, Q6).
No proper-time-exactness fix (finding-0090 — the ℤ-primary gain sidesteps it; the refinement waits). No
uuid-identity design (its own act — this plan is a **consumer**, item 11 imports π read-only). No mirror
surfacing wiring. No golden_recall coupling (finding-0096). No weight/promotion writes (surfacing-only).

## 10. Stop-and-raise conditions
- **The gate:** item 11 requires uuid-identity's π. π absent → STOP at item 11, park it with re-entry
  `uuid-identity lands`, ship item 10, complete the plan (a sanctioned partial outcome). Never stub π.
- A π false-merge is detected (item 11) → STOP, file a finding routed to uuid-identity's owner (π's precision
  clause failed); do not loosen the helix criterion to absorb phantom cycles.
- Any temptation to use snapshot-invisibility as the helix criterion → STOP (the explicit CN-6 bug).
- Any pressure to build the U(1)/spectral route → STOP (the magnetic lane's gate holds).
- Any blessing: never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| item 11 (real-corpus π wiring) | GATED — parked until uuid-identity lands | build now with a stub π (fabricates the quotient — the detector's integrity depends on π's precision) | uuid-identity's π lands (total, constant-along-supersession, precision-first) |
| the interval-count for a cross-stratum hop | ℤ count = forward generators traversed | per-stratum proper time now | finding-0090 resolves ⇒ the proper-time refinement applies within-stratum |
| the U(1)/spectral pitch route (β compactification) | combinatorial v1 only | build the spectral route now | the magnetic lane's own build gate opens (Q6) |
| snapshot-realizability (the Helly gap) | not needed by v1 | treat co-presence realizability now | the spatial-cycle baseline needs it |

## 12. Dependency & ordering summary
**Depends on bp-059** (the shared CN-1 scaffolding — ConnEvidence, cut acquisition — for item 11's readings)
**and, critically, on uuid-identity for item 11 (the gate — no plan id yet; owner schedules it, D3).**
Independent of bp-060/061 (a different graph — the idea-quotient gain graph, not the σ-MST); parallelizable
with them once ready. Items: **10 (synthetic, UNGATED — buildable now)** → **11 (real-corpus π, GATED)**. The
per-item gate means item 10 can ship while item 11 waits (the owner's call at the bless gate; default: the
whole plan waits behind uuid-identity).
