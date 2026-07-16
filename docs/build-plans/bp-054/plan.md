---
type: build-plan
id: bp-054
alias: res-typing-registry
status: complete
design_ref:
  - docs/design-notes/resolution-result-typing.md               # RATIFIED — §2.2 Rule SCALE; §3.2 the Res[T] build item; §2.4 zero-schema tags
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md   # RATIFIED — §2.4.4 the registry rows (FB-2)
contract: builder
write_scope:
  - core/scope.py
  - eval/harness/registry.py
  - tests/unit/test_scope_res.py
  - tests/unit/test_registry_res.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
  actual:
    model: opus
    tokens: 137494        # harness-measured
    tool_uses: 71
    ratio: 0.76           # actual/estimate — well-pinned, under estimate
    merged: 4ec4cdc       # 5-leg green on main: ruff · mypy(205) · argless 69 · type_gate · pytest 1349p/9s;
                          # additive proof: test_scope.py 28 passed UNCHANGED (2-hunk scope.py diff)
    sealed: 2026-07-16
    dollars: pending      # wave-level $ from owner end-of-session /usage relay
    findings: [finding-0086, finding-0093]   # 0086 RESOLVED (structural_axes registered); 0093 RESOLVED
                          # (plan's "import constants" pin ⇒ circular import; builder registered literals +
                          # test-enforced name agreement — the same no-drift guarantee, cycle-free)
depends_on: [bp-050]
parallelizable_with: [bp-053]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/findings/finding-0086.md   # the structural_axes.* registration rider — RESOLVED by this plan
  - docs/design-notes/capability-scope-algebra.md   # §2.3 — the amended-by-companion result grammar; the owner's cross-ref stamp is OWNER-SIDE, not this builder's
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — FB-2: `Res[T]`/`res_under` + the `sigma_persistence.*` and `structural_axes.*` registry rows

## 0. Mode & provenance
Graduated from RATIFIED `dn-resolution-result-typing` (the Res(π) amendment — owner-blessed) and
`dn-sigma-fibers` §2.4.4. Carries finding-0086's registration rider to resolution. **The owner's
dated cross-reference stamp in ratified `dn-capability-scope` §2.3 is an OWNER act (EH-a
pattern) — this builder never touches that file.**

## 1. Objective
(1) Add `Res[T]` + `res_under` beside `Inv`/`Rate` at the bottom of `core/scope.py` — additive,
zero behavior change to any View or existing type. (2) Register the `sigma_persistence.*` family
(type_tag `"Res(sigma)"`) and the `structural_axes.*` family (type_tag `"Inv"`; finding-0086) in
`eval/harness/registry.py`.

## 2. Context manifest (read in order)
1. `docs/design-notes/resolution-result-typing.md` (WHOLE — Rule SCALE, the π descriptor, the
   comparability law, §2.5's inhabitant table).
2. `core/scope.py:577-619` — `Inv`/`Rate`/`rate_under` (the exact pattern `Res`/`res_under`
   mirrors; note `Rate.clock` is REQUIRED — π is required the same way).
3. `eval/harness/registry.py` (whole) — `MetricSpec`, `register` (duplicate-name refusal), the
   `_BUILT` tuple this extends.
4. `core/dreaming/shadow.py:232-243` — the `structural_axes.<axis>` names actually written
   (register EXACTLY those; enumerate from `compute_snapshot`'s output keys).
5. `docs/findings/finding-0086.md` — the rider being resolved.
6. bp-050's merged `eval/harness/fibers.py` — the aggregate names registered here MUST match
   what FB-1 writes (`sigma_persistence.mean/.p50/.max/.frac_ge_strong/.n_claims`).

## 3. Investigation & grounding
- **π as a frozen dataclass:** `ResParam(name: str, lo: float, hi: float, grid: str)` — the
  descriptor is REQUIRED on `Res` (a π-less Res unconstructable — the §2.2(i) carriage law);
  `res_under(value, *, param)` mirrors `rate_under`'s checked-constructor shape. Comparability
  helper: `res_comparable(a, b) -> bool` (π-identical), refusing cross-π (RT-a: transport is
  parked — always a new measurement).
- **Zero-schema tags:** the store's type_tag is VARCHAR; the registry's `type_tag` is a str —
  `"Res(sigma)"` needs no schema or validator change (§2.4 of the amendment).
- **structural_axes registration:** `guardrail_eligible=False`, comparability "same fixture /
  same pipeline; A2 axes over the scratch snapshot", `assertion_shape="regression"`,
  `source_instrument="row6-structural-axes"`.

## 4. Reconciliation
`registry.py`'s docstring says type_tag is `"Inv" | "Rate(<clock>)"` — this plan widens the
comment to include `"Res(<param>)"` (a comment inside write_scope, citing the ratified
amendment). No other committed surface moves. finding-0086 → status resolved (this plan's
completion note is the resolution record; the orchestrator flips the finding at merge).

## 5. Write scope
The four files in frontmatter. **OUT:** `docs/design-notes/capability-scope-algebra.md`
(ratified — the stamp is the owner's), `eval/harness/store.py`, `fibers.py` (bp-050's),
`shadow.py`, denylist.

## 6. Interfaces pinned inline
```python
# core/scope.py — mirror the built pattern EXACTLY (:586-619)
@dataclass(frozen=True)
class ResParam:
    name: str; lo: float; hi: float; grid: str    # "Γ_21" | "exact-partition" | ...

@dataclass(frozen=True)
class Res[T]:
    value: T
    param: ResParam                                # REQUIRED — a π-less Res is unconstructable

def res_under[T](value: T, *, param: ResParam) -> Res[T]: ...
def res_comparable(a: Res[Any], b: Res[Any]) -> bool: ...   # π-identical only (RT-a)

# eval/harness/registry.py — the new rows (names EXACT)
MetricSpec("sigma_persistence.mean", "Res(sigma)", "row15-sigma-fibers",
           "same corpus_ref, identical resolution descriptor π; never across grids/ranges "
           "without a declared transport", "regression", False)
# … .p50 / .max / .frac_ge_strong / .n_claims identically; structural_axes.* as Inv rows.
```

## 7. Items
### Item 1 — Res[T] + res_under + comparability (core/scope.py)
- **Acceptance:** `uv run pytest tests/unit/test_scope_res.py -q` green: π-less construction is
  a TypeError; `res_under` round-trips; `res_comparable` is True iff π equal, False across
  distinct ranges/grids; AND the whole existing scope suite green unchanged
  (`uv run pytest tests/unit/test_scope.py -q`) — the additive guarantee.
- **Falsifier:** ANY behavior change to `Inv`/`Rate`/`rate_under`/meet/join (bit-identical is
  the bar — the bp-039 discipline); a constructable π-less Res.
### Item 2 — the registry rows
- **Acceptance:** `uv run pytest tests/unit/test_registry_res.py -q` green: all five
  `sigma_persistence.*` + every written `structural_axes.<axis>` resolve via `registry.get`;
  duplicate registration refused; names match FB-1's writes exactly (import the name constants,
  don't restring them); `guardrail_eligible` False for all new rows.
- **Falsifier:** a name mismatch with what shadow/fibers actually write (the finding-0086
  failure class recurring); any new row marked guardrail-eligible.

## 8. Math carried explicitly
Rule SCALE (ratified §2.2, hold verbatim): (i) carriage — π in the type, never a bare number;
(ii) capability-invisibility — nothing here touches `Scope`, meet/join, or admissibility (the
proof obligation is discharged by NOT writing that code).

## 9. Non-goals
No transport between π (RT-a parked). No structured π in the store (RT-b: strings + spec_hash).
No Res guardrails (RT-c). No edit to any ratified note. No fibers/gate logic.

## 10. Stop-and-raise
The additive falsifier failing (any existing scope test changes) → STOP, the change is not
additive. Any blessing: never.

## 11. Parked decisions
RT-a/RT-b/RT-c inherited verbatim from the ratified amendment — none re-opened.

## 12. Dependency & ordering
Depends bp-050 (name agreement). Parallel with bp-053 (disjoint files). Feeds bp-057 (the gate
reads registered tiers' metric names). Resolves finding-0086. Blast radius: additive typed shim
+ metadata rows.
