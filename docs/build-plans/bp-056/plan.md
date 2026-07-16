---
type: build-plan
id: bp-056
alias: tmeet-completion
status: proposed
design_ref:
  - docs/design-notes/global-event-clock.md   # RATIFIED — §2.5 the T-meet totalization + the bit-identical falsifier (GC-4)
contract: builder
write_scope:
  - core/scope.py
  - core/temporal/atlas.py
  - tests/unit/test_tmeet_completion.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
depends_on: [bp-053]
parallelizable_with: [bp-055, bp-057]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/capability-scope-algebra.md   # §2.2 — "Until N exists, T is honestly a partial meet-semilattice"; this executes the anticipated completion
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — GC-4: the T-meet completion (pullback meets via an injectable clock atlas)

## 0. Mode & provenance
Graduated from RATIFIED `dn-global-event-clock` §2.5. **The highest-scrutiny plan of the wave:**
it changes behavior in `core/scope.py`, whose semantics are governed by the ratified algebra —
but ONLY on inputs that today RAISE (`NoCommonClockError`); the ratified note itself anticipated
exactly this completion ("Until N exists…", §2.2 there). The owner's ratification condition —
*a clock bridge without sacrificing structure* — is this plan's §7 falsifier verbatim.
**Orchestrator: scrutinize this diff line-by-line at merge (opus/xhigh), the bp-049 §8 pattern.**

## 1. Objective
(1) A `ClockAtlas` protocol in `core/scope.py` (pure-core: a typing seam, no store import) +
an optional module-level atlas registration consumed by `TimeScope.meet`/`common_refinement`.
(2) `core/temporal/atlas.py` — the concrete atlas backed by the spine's p_κ (bp-053), computing
pullback window intersections. (3) `NoCommonClockError` narrowed exactly per §2.5: raised for
unregistered/exogenous clocks or when no atlas is registered; computed otherwise.

## 2. Context manifest (read in order)
1. `docs/design-notes/global-event-clock.md` §2.5 (WHOLE), §2.9-4 (the evaluation-regime
   generalization — NOT built here, but the meet's window result must be representable for it).
2. `core/scope.py:171-357` — `Clock`, `common_refinement`, `Window` (meet/join/⊑),
   `TimeScope.meet` (the raising branches this plan gives values to), `NoCommonClockError`.
3. `core/temporal/spine.py` as merged by bp-053 — `p`, `fiber`, `frontier` (the atlas substrate).
4. `docs/design-notes/capability-scope-algebra.md` §2.2 (ratified — the T-meet law; READ-ONLY).
5. `tests/unit/test_scope.py` (whole) — the lattice-law suite that must stay green UNCHANGED.

## 3. Investigation & grounding
- **The pure-core constraint is the load-bearing seam:** `core/scope.py` imports no store
  (:38-40 there). Resolution (pinned at graduation, from the note's ops-side-bridge precedent):
  scope.py gains ONLY a `ClockAtlas` Protocol + `register_atlas(atlas | None)`; the concrete
  atlas lives in `core/temporal/atlas.py` (a NEW file — disjoint from bp-055's spine.py edits)
  and is registered by consumers, never imported by scope.py. Default = None ⇒ every current
  behavior byte-identical.
- **The meet with an atlas:** same clock → unchanged window intersection (existing code path,
  untouched). Different registered clocks → `T₁ ⊓ T₂ = (N, atlas.pullback(κ₁,W₁) ∩
  atlas.pullback(κ₂,W₂))`, the result carried as an N-window (a frozen event-set token —
  CS-b's antichain window in its v1 form: an opaque, hashable frontier-pair). Wall/NOW or
  atlas-absent → raise, message updated to name the reason precisely.

## 4. Reconciliation
This plan executes the ratified algebra's OWN anticipated completion (its §2.2 sentence) under
the ratified clock note's §2.5 — no note is edited. If the pullback result proves
unrepresentable in the existing `Window` grammar without loosening its conservatism → STOP and
file a `design` finding (do not weaken `Window.meet`'s safe-conservative behavior).

## 5. Write scope
The three files in frontmatter. **OUT:** `core/temporal/spine.py` (bp-055 is editing it in
parallel — the atlas is a SEPARATE file for exactly this reason), every View, every store,
`tests/unit/test_scope.py` (additions go in the NEW test file; the old suite is the falsifier
and must not be touched), denylist.

## 6. Interfaces pinned inline
```python
# core/scope.py — the ONLY additions (a protocol + a registration point + the meet branch)
class ClockAtlas(Protocol):
    def has(self, clock: Clock) -> bool: ...
    def pullback(self, clock: Clock, window: Window) -> Hashable: ...   # an N-window token
    def intersect(self, a: Hashable, b: Hashable) -> Hashable | None: ...  # None ⇒ empty

_ATLAS: ClockAtlas | None = None
def register_atlas(atlas: ClockAtlas | None) -> None: ...

# TimeScope.meet — the new branch ONLY where it currently raises:
#   both clocks atlas-covered ⇒ TimeScope(Clock.N, <n-window token wrapped in Window>)
#   else ⇒ NoCommonClockError (message names: unregistered clock | no atlas | exogenous wall)

# core/temporal/atlas.py — the concrete impl over bp-053's spine (imports stores; scope.py never imports THIS)
class SpineAtlas:  # implements ClockAtlas
    def __init__(self, spine: Spine): ...
```

## 7. Items
### Item 1 — the protocol seam + the completed meet
- **Acceptance:** `uv run pytest tests/unit/test_tmeet_completion.py -q` green AND — the
  cardinal falsifier — `uv run pytest tests/unit/test_scope.py -q` green WITH ZERO EDITS to
  that file: every previously-legal meet returns bit-identical results with and without an
  atlas registered; with no atlas, every previously-raising input raises the same error type.
- **Falsifier (the owner's ratification condition, executable):** ANY previously-legal meet
  changing value = structure sacrificed = the plan has failed its charter — revert, STOP,
  finding. A cross-clock meet computing without an atlas-covered pair = a silent guess (the
  exact dishonesty the partial meet existed to prevent).
### Item 2 — the SpineAtlas + cross-clock property tests
- **Acceptance:** with a `SpineAtlas` over seeded fakes: `commit ⊓ N_s` computes the pullback
  intersection and the result's event set equals the hand-computed intersection; `wall ⊓
  anything` raises; `meet` is commutative and associative on atlas-covered triples
  (property test); empty intersections yield the EMPTY window, never an error.
- **Falsifier:** pullback disagreeing with a hand-enumerated fiber intersection; associativity
  failing on covered clocks.

## 8. Math carried explicitly
`T₁ ⊓ T₂ = (κ*, p₁⁻¹(W₁) ∩ p₂⁻¹(W₂))` with κ* = N (Theorem S2's condition now satisfied —
cq-scope-fable-pass S2, ratified via dn-global-event-clock §2.5). The completion is CONSERVATIVE:
its domain is exactly the former error path. Zone separation: scope.py stays pure-core (the
Protocol seam — no store import; assert via the existing isolation/import discipline).

## 9. Non-goals
No evaluation-regime work over N-windows (σ-transport products — a later consumer). No
`SliceError` change (bp-055 covers cuts). No CS-f re-binning helper. No edit to
`tests/unit/test_scope.py` (it IS the falsifier).

## 10. Stop-and-raise
The §7 Item-1 falsifier tripping → revert + `design` finding, never patch around. `Window`
grammar insufficient → finding (see §4). Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| N-window in the Window grammar proper | opaque hashable token wrapped in existing Window | a consumer needs N-window arithmetic (CS-b's full antichain machinery) |
| auto-registration of the atlas at daemon start | manual registration by consumers | a second consumer duplicates registration |

## 12. Dependency & ordering
Depends bp-053 (p_κ). Parallel with bp-055/bp-057 (disjoint files — atlas.py is new). Highest
blast radius of the wave (core/scope.py behavior on former-error paths) — merge LAST in wave 3,
orchestrator-scrutinized.
