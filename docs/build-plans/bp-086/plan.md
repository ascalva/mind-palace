---
type: build-plan
id: bp-086
track: agentic-loop
status: complete
design_ref:
  - docs/design-notes/agentic-loop.md
contract: builder
write_scope:
  - core/agent_scope.py
  - core/scope.py
  - tests/unit/test_agent_scope.py
  - tests/unit/test_scope.py
  - tests/unit/test_scope_laws.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual:
    model: opus            # claude-opus-4-8[1m], tier verified via completion usage
    tokens: 150640
    tool_calls: 69
    duration_min: 20
    ratio: 0.68            # UNDER estimate — well-pinned plan; F-AL3 crux passed, no stop-and-raise
    session_delta: "weekly all-models pool; ran parallel with bp-085/bp-083; ~10min lost to full-suite CPU contention (pivoted to blast-radius verify)"
depends_on: []
parallelizable_with: [bp-083, bp-085, bp-087]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/agentic-loop.md
  - docs/design-notes/capability-scope-algebra.md
  - docs/findings/finding-0011.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AL-1: the three actor profiles + the zone-boundary lattice test (G-D)

> Graduated from ratified `dn-agentic-loop` §2.3 / §3 (AL-1). Additive, zero behavior change: name
> `internal_actor` / `external_proposer` / `external_executor` profile constructors beside the
> existing role constructors, and turn the zone-boundary exclusion — held today only by Track G's
> *shape* — into a proved lattice law. The exclusion is currently *vacuously* true
> (`⊤_deployed.W_world = NONE`, finding-0011); this makes it a ratchet, not an accident.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only. Constructor-layer + test only — nothing here amends the
ratified `dn-capability-scope` algebra (A8); it is the profile layer *on top*, the same
relationship the existing role constructors have to the lattice. Grounds on finding-0011 (effector
dormancy), never reopens it.

## 1. Objective

Add three profile constructors to `core/agent_scope.py` (the IA/EA-p/EA-x points of §2.3) and one
lattice-law test asserting `s.Σ ⊓ (private strata) ≠ ⊥ ⇒ s.A.W_world = NONE` is unconstructable to
violate — so the zone boundary (broad private read ⊥ world reach) is a proved property, not a
structural coincidence.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/agentic-loop.md` §2.3 — the two profiles IA / EA (EA split into EA-p
   proposer + EA-x executor); the derivation (bright lines 1–2 as the lattice inversion); the
   exclusion law verbatim; gap G-D; falsifier F-AL3. Plus §3 AL-1's scope statement.
2. `core/scope.py` — whole; the lattice (`Scope`, `StratumScope`, `EdgeScope`, `TimeScope`,
   `Authority`), `WorldReach` (`:439-450`), the `Ideal` firewall-as-order-ideal machinery
   (`:598-620`), `DENYLIST_IDEAL` (`:613`), `admissible` (`:616`), `DEPLOYED_WORLD_CEILING`
   (`:643`), the base strata / `_BASE_STRATA` (`:99`).
3. `core/agent_scope.py` — whole; the four role constructors (`sensor_scope`, `query_scope`,
   `integrator_scope`, `dreamer_scope`) as the precedent shape; `assert_conforms`; the
   pure-core discipline (imports only `core.scope`).
4. `tests/unit/test_agent_scope.py`, `tests/unit/test_scope.py`, `tests/unit/test_scope_laws.py` —
   the existing lattice-law + role-region tests (the surface the new tests extend; the retrofit
   targets that assert the current constructor surface).

## 3. Investigation & grounding

Touches existing code; grounded at HEAD (`d08da37`):

- **Q1 — where do profile constructors live?** `core/agent_scope.py`, beside the role
  constructors (`sensor_scope`…`dreamer_scope`, `:72-158`) — the note's named precedent. They
  return template `Scope`s; composition against a parent stays the existing `Scope.meet`. Pure-core
  (imports only `core.scope`).
- **Q2 — what is `⊤_Σ = R ∖ 𝔇`, and how does IA's "broad Σ" express?** `StratumScope.top()`
  (`scope.py:135`) = the downset of `_BASE_STRATA`, already minus FOUNDATION and HYPOTHETICAL.
  IA = `top()` (optionally ∪ {HYPOTHETICAL} when the grant names it), `A = (READ_PROPOSE, W_Σ=1,
  W_world=NONE)`. `DerivedStore` has no provenance param, so interpreted-only write is structurally
  unforgeable (asserted in prose, not this plan's code).
- **Q3 — what are "private strata"?** The note says `s.Σ ⊓ (private strata) ≠ ⊥`. The code does
  NOT yet name a "private" subset — this plan must DEFINE it. Grounded proposal: private strata =
  every base stratum EXCEPT `WORLD` (mirror/curated/observed/ops/reference/interpreted/dialogue and
  their refinements are corpus/private; `world` is the only public/effector coordinate). The
  definition is pinned in `core/scope.py` as a named `frozenset[Stratum]` (`PRIVATE_STRATA`) with a
  one-line rationale, so the law reads off a declared set, not an inline guess. *The code does not
  settle whether `ops`/`reference` should count as "private" for this law* — the safe default is
  "all-but-world are private" (widest exclusion ⇒ strongest law); flagged for owner confirm at the
  proposed→ready gate.
- **Q4 — is the exclusion an `Ideal`?** Not directly: `Ideal.excludes` (`scope.py:607`) is a
  Σ-only order-ideal test. The zone law is a **cross-coordinate implication** (Σ × A), not a pure
  Σ-ideal. So AL-1 adds a predicate `zone_admissible(s) -> bool` (or `assert_zone(s)`) expressing
  the implication, tested — *stated as a firewall ideal in kind* (§2.3), not shoehorned into the
  existing `Ideal` dataclass. The note's phrasing "firewall ideal / lattice-law test" is honored as
  a law-test, since the implication crosses coordinates.
- **Q5 — EA-x's `Σ = ⊥`.** `StratumScope.bottom()` (`scope.py:140`); `A = (—, 0, W_world = ε)` with
  ε gated ops-side. EA-x never reads the vault (bright line 2) — `Σ = ⊥` makes that structural.

**Additional risks:** the law must not accidentally forbid EA-x (its Σ is ⊥ over corpus strata, so
the antecedent is false — the implication holds). And it must catch a *constructable* violation, or
F-AL3 fires and the derivation is decorative (then §2.3 must be reworked — a stop-and-raise).

## 4. Reconciliation

- `core/scope.py` — **EXTEND by cross-reference**: `DEPLOYED_WORLD_CEILING` (`:643`) and
  `WorldReach` gain a sibling `PRIVATE_STRATA` set + `zone_admissible` predicate; the module
  docstring cross-references §2.3 as the law's warrant. No existing symbol changes shape (no
  retrofit-surface break expected — additive names only).
- `core/agent_scope.py` — **EXTEND**: three new constructors appended beside the four roles;
  existing constructors untouched.
- **No banner-correction** — this plan corrects no committed behavior; it asserts a property the
  code already has (finding-0011's `⊤_deployed.W_world = NONE`).

## 5. Write scope

`core/agent_scope.py` (the three constructors), `core/scope.py` (`PRIVATE_STRATA` +
`zone_admissible`), and the three test files (`test_agent_scope.py`, `test_scope.py`,
`test_scope_laws.py`) — carried because they assert the current constructor/lattice surface and
the new profiles + law extend it. Deliberately OUT of scope: any read-path wiring (these stay
vocabulary + guard, no gate wired), the effector tier (finding-0011 unchanged), every store, the
ratified `dn-capability-scope` text.

## 6. Interfaces pinned inline

```python
# core/scope.py — existing, pinned:
class WorldReach(IntEnum): NONE=0; SENSING=1; REVERSIBLE=2; IRREVERSIBLE=3      # :439
DEPLOYED_WORLD_CEILING: WorldReach = WorldReach.NONE                            # :643
class Authority: privilege: Privilege; store_write: int; world: WorldReach      # :452
def StratumScope.top() / .bottom()                                             # :135 / :140
# core/scope.py — NEW (additive):
PRIVATE_STRATA: frozenset[Stratum]        # every base stratum except WORLD (the corpus/vault side)
def zone_admissible(s: Scope) -> bool     # s.sigma ∩ PRIVATE_STRATA == ∅  OR  s.authority.world == NONE
# core/agent_scope.py — NEW constructors (profile layer, §2.3):
def internal_actor(strata, *, hypothetical=False) -> Scope
    # Σ = top()(∪{HYPOTHETICAL}); E = ⊤; T = ledger/cut-bound; A = (READ_PROPOSE, 1, NONE); core
def external_proposer(...) -> Scope
    # Σ = mirror_authored (via MirrorView) or narrower; A = (READ_PROPOSE, 0, NONE)
def external_executor() -> Scope
    # Σ = ⊥; A = (READ, 0, W_world=ε) — never reads the vault (bright line 2)
```
The law: **`zone_admissible(s)` is True iff `s.sigma.strata ∩ PRIVATE_STRATA == ∅` OR
`s.authority.world == WorldReach.NONE`** — i.e. non-⊥ private Σ forces `W_world = NONE`.

## 7. Items

### Item 12 — `PRIVATE_STRATA` + `zone_admissible` (the law)
- **Objective:** declare the private-stratum set and the cross-coordinate predicate in
  `core/scope.py`.
- **Files:** `core/scope.py`.
- **Acceptance test:** `zone_admissible` returns False for a hand-built `Scope` with non-⊥ private
  Σ and `W_world = SENSING`, True for that Σ with `W_world = NONE` and for `Σ=⊥`/`Σ={world}` at any
  reach.
- **Falsifier (F-AL3):** a constructable deployed grant with non-⊥ private Σ and `W_world > NONE`
  that `zone_admissible` *passes* ⇒ the law is decorative; **stop** and rework §2.3.
- **Invariant(s):** additive only; no existing symbol reshaped; no read path wired.
- **Touches stored data?** No. **Parallelizable?** Yes. **Depends on:** none.

### Item 13 — the three profile constructors
- **Objective:** `internal_actor`, `external_proposer`, `external_executor` in `core/agent_scope.py`.
- **Files:** `core/agent_scope.py`.
- **Acceptance test:** each constructor returns a `Scope` in its §2.3 region: IA has broad Σ +
  `W_world=NONE` + interpreted-tier write; EA-p is propose-only, mirror_authored; EA-x has `Σ=⊥`.
- **Falsifier:** any constructor produces a scope that `zone_admissible` rejects (IA/EA-p) — they
  must be zone-admissible by construction (IA/EA-p have `W_world=NONE`; EA-x has `Σ=⊥`).
- **Invariant(s):** pure-core (imports only `core.scope`); monotone delegation preserved
  (`meet(parent, template) ⊑ parent`).
- **Touches stored data?** No. **Parallelizable?** Yes. **Depends on:** Item 12.

### Item 14 — the lattice-law tests + profile-region tests
- **Objective:** prove the law over the constructors and over adversarial hand-built scopes; prove
  each profile lands in its region (the role-region test pattern).
- **Files:** `tests/unit/test_scope.py` / `test_scope_laws.py` (the law), `test_agent_scope.py`
  (the profile regions).
- **Acceptance test:** `uv run pytest tests/unit/test_scope.py tests/unit/test_scope_laws.py
  tests/unit/test_agent_scope.py` green; the law test includes the F-AL3 adversarial case (a
  non-⊥-private + `W_world>NONE` scope is refused/flagged).
- **Falsifier (F-AL3):** the adversarial scope is constructable AND passes the law.
- **Invariant(s):** the existing role-constructor tests still pass unchanged.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 12–13.

## 8. Math carried explicitly

- **The zone-exclusion lattice law** `Σ ⊓ private ≠ ⊥ ⇒ W_world = NONE` — *measures:* whether a
  capability that reads private strata can also reach the world. *valid when:* `PRIVATE_STRATA` is
  the correct corpus/vault side (all-but-world). *fails its keep if:* a deployed grant violating it
  is constructable and the test cannot refuse it structurally (F-AL3) — then it asserts nothing and
  §2.3 must be reworked.

## 9. Non-goals

No read-path gate wiring (vocabulary + guard only). No effector-tier change (finding-0011 stands;
today the law is vacuously true). No amendment to `dn-capability-scope`. No new stratum (that is
AL-3's `exhaust` refinement). No `Ideal`-dataclass change (the cross-coordinate law is a law-test,
not a Σ-only ideal).

## 10. Stop-and-raise conditions

- F-AL3: a violating deployed grant is constructable and the test can't refuse it ⇒ **stop**, file
  a `design` finding, route to the orchestrator (§2.3 rework is owner-level).
- Ambiguity on whether `ops`/`reference` count as "private" ⇒ park that edge with the safe default
  (all-but-world private) and name it for the owner at proposed→ready; do not block.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Exact membership of `PRIVATE_STRATA` (ops/reference in or out) | all base strata except `world` | enumerate a narrower "vault-only" set (weaker law; risks a real leak passing) | owner confirm at proposed→ready, or a consumer needs a finer split |
| Wire the law into a read path | vocabulary + guard only (test asserts it) | a runtime gate (no consumer; structural-enforcement says a test suffices while `⊤_deployed.W_world=NONE`) | an EffectView is ever wired (finding-0011 re-entry — owner act) |

## 12. Dependency & ordering summary

Items 12 → 13 → 14 sequential. No dependency on other plans. Parallelizable with bp-083, bp-085,
bp-087. **NOT parallelizable with bp-088 (AL-3)** — both write `core/scope.py` and its tests;
sequence AL-1 before AL-3 (AL-1 lands the law + `PRIVATE_STRATA`; AL-3 adds the `exhaust`
refinement to the same module). Blast radius: additive vocabulary + guard tests.
