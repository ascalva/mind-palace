---
type: design-note
id: dn-resolution-result-typing
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/capability-scope-algebra.md              # THE RATIFIED NOTE THIS AMENDS (§2.3) — never edited by an agent (A8)
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md  # the first customer (pers is the first Res inhabitant)
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md   # the warrant capsule (2026-07-16T17:32 — Inv-vs-Res(σ), Rule-SCALE-vs-meet/join)
  - docs/brainstorms/doc-code-entanglement.md                  # the multi-resolution family (π_grain, π_depth — the parameter-generic case)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/cross-strata-and-multiscale-dreamers.md
---

# Resolution-graded results: `Res(π)` and Rule SCALE — an amendment to `dn-capability-scope` §2.3

> Composed at **fable** (`claude-fable-5`, 2026-07-16, the sanctioned design pass). Filed as
> `draft`. **This note drafts an AMENDMENT to a ratified note** (`dn-capability-scope` §2.3,
> ratified 2026-07-15): the ratified text is agent-immutable (A8); nothing here edits it. On
> ratification of THIS note the owner (or the orchestrator immediately after, as a non-blessing
> edit if the owner so directs — the EH-a stamping pattern) adds a dated cross-reference in the
> ratified note pointing here. Until then the ratified dichotomy stands unmodified.
> **Design only; no build is authorized by this note.**

## 1. Purpose and scope

`dn-capability-scope` §2.3 grades query results by clock-dependence: `Inv` (depends only on the
window's event set) vs `Rate(κ)` (a difference quotient against a clock, Rule CLOCK at
`capability-scope-algebra.md:116`). The σ-fibers design (`dn-sigma-fibers`) produced the first
result that is neither: a value with **no clock in it** yet an **irreducible dependence on a
declared resolution ruler** (the σ-range and grid it was measured over). This note decides,
formally: (1) the result grammar gains a third class, `Res(π)`; (2) its carriage-and-comparability
law, **Rule SCALE**; (3) the negative half, proved — resolution does **not** enter the scope
object: no fifth coordinate, no lattice change, no admissibility change. Out of scope: any build
(`core/scope.py` additions follow ratification → `/graduate`); the fusion instruments over scale
families (per-feature, per `dn-sigma-fibers` §2.8); the smear/conversation-layer parks (unchanged).

## 2. Principles / decision

### 2.1 The amended result grammar

```
ResultGrade ::= Inv | Rate(κ) | Res(π)
```

where the **resolution descriptor** `π = (name, U, Γ)` declares: the parameter (`"sigma"`,
`"grain"`, `"depth"`), its unit and declared range U (e.g. cosine ∈ [0.55, 0.75] — the ruler),
and its sampling Γ (a grid, or an exact breakpoint partition). The two ratified classes are
unchanged — the amendment is strictly additive.

A `Res(π)` result is a measurement of **variation across a declared family of constructions
over one fixed event set** — where `Inv` sees one construction and `Rate(κ)` divides by an
event-clock's index, `Res(π)` spans a parameter family none of whose members changes what the
client may see. First inhabitant: `pers(χ) : Res(π_σ)` (`dn-sigma-fibers` §2.3).

### 2.2 Rule SCALE

Two halves, mirroring Rule CLOCK's shape but landing on the opposite side of the type system:

- **(i) Carriage.** A resolution-graded value carries π in its type and is never a bare number
  — exactly as a `Rate` carries its clock (`core/scope.py:596-601`: the `clock` field is
  required, so a clockless Rate is unconstructable). Build form (on graduation): a frozen
  `Res[T]` dataclass with a required `param` descriptor beside `Inv`/`Rate` at the bottom of
  `core/scope.py`, plus a checked constructor `res_under(value, *, param)` (the
  `rate_under` analog, `core/scope.py:610-619`). **Comparability law:** two `Res` values
  compare iff their π are identical (same name, same U, Γ compatible — a refinement of one
  grid by another is comparable up to the declared discretization bound; anything else is a
  new measurement). Cross-π comparison without a declared transport is refused — the CS-f
  conservatism ("Rate re-binning … always a new measurement",
  `capability-scope-algebra.md:171`), applied to rulers.
- **(ii) Capability-invisibility (the negative half — the load-bearing ruling).** For every
  verb q in a Res-graded instrument family and all resolutions π, π′:

  ```
  req(q_π) = req(q_π′)
  ```

  Resolution never enters `s = (Σ, E, T, A)`, never affects admissibility
  (`req(verb) ⊑ s_granted`, §2.4 of the ratified note), and never composes under meet/join.

### 2.3 Why the negative half is right (the proof obligations, discharged for σ)

The warrant capsule asked: does the algebra need σ *in the scope type* ("Rule SCALE" as a
`s.T.clock = κ`-style premise), or is scale expressible via scope meet/join? **Answer: neither**
— and each half is shown, not asserted:

1. **Scale is not expressible via meet/join.** Meet/join act on the four coordinates
   (`core/scope.py:482-507`). A "tight" reading of G_{0.70} and a "loose" reading of G_{0.60}
   have *identical* coordinates: same Σ = {mirror_authored}, same E, same T, same A — both are
   `MirrorView.SCOPE` verbatim (`core/mirror.py:76-82`), because `MirrorGraph.build(view, sigma)`
   consumes an already-admitted view and σ only parameterizes the derived construction
   (`core/dreaming/graph.py:33-40`). Two scopes that are equal cannot be distinguished by any
   lattice expression. The founding capsule's "local vs macro scope IS the scope algebra's
   meet/join" is corrected accordingly: meet/join governs *strata extent*, not *resolution
   within a stratum*.
2. **Scale must not be added as a scope coordinate.** A Rule-CLOCK-style premise needs a scope
   slot to constrain (`s.T.clock = κ` works because T genuinely *has* a clock: a clock is a
   coarsening of the ledger's causal order, a property of the data's indexing that the View
   holds — `core/scope.py:171-184`). σ is a free parameter of an instrument-internal
   construction: for every σ the client reads **identical rows under an identical grant**, so a
   fifth coordinate would never affect admissibility — a fictional capability. The ratified
   note's own honesty precedents forbid exactly this (enforcement tier kept an annotation, not a
   lattice element; T-meets partial rather than guessed; the seed's conflated write rung
   repaired) — the algebra records only what changes what a client may do.
3. **Yet the value must carry σ (why bare `Inv` is a mis-typing).** `pers` is stable under grid
   *refinement* (the piecewise-constancy convergence, `dn-sigma-fibers` §2.1/§2.3) — the
   Inv-flavored half — but rescales under a change of declared range: measured on
   [0.55, 0.75] vs [0.50, 0.80], the same claim gets a different strength. A bare-`Inv` tag
   licenses type-directed dedup and cross-anchor comparison (`dn-evaluation-harness` §2.3) with
   no guard against comparing across rulers — precisely the failure class Rule CLOCK exists to
   foreclose one type earlier (the A7 apophenia class: "a drift *rate* read off an
   unacknowledged clock", ratified §2.3). Same disease, different parameter ⇒ same medicine:
   carry the ruler in the type. And it is not a `Rate`: nothing eventful divides into it — there
   is no σ-clock, because σ coarsens no event order.

**The resolution of the capsule's "typing subtlety," stated once:** grid-refinement-stability is
a **validity property** (a theorem about the estimator, reported with the reading);
range-dependence is a **type property** (carried as π). The dichotomy dissolves once the two
dependencies are separated.

### 2.4 The query-language consequence

A query sentence extends `(verb, s)` → `(verb, s, π?)` where π is optional and only selects
within a Res-graded instrument family. **π-erasure invariant:**
`admissible(verb, s, π) ⟺ admissible(verb, s)` — mode remains a corollary of scope (ratified
§2.4), untouched. Surface posture: separate opt-in entry points per family with the default path
byte-identical — the `grouped_semantic_search` precedent (`core/ingest/index.py:124-138`).
Result-store form at zero schema cost: `type_tag = "Res(<name>)"` in the existing VARCHAR
(`eval/harness/store.py:38`; the registry's tag field is likewise a string,
`eval/harness/registry.py:27`), with U and Γ pinned inside `spec_hash` as battery params
(`store.py:32`) and restated in the metric's `comparability` rule.

### 2.5 Parameter-generic instances (the multi-resolution family, typed once)

| π | family | status |
|---|---|---|
| `π_σ = ("sigma", [0.55,0.75], Γ_21)` | σ-fibers claim persistence | first inhabitant (`dn-sigma-fibers`) |
| `π_grain = ("grain", {chunk sizes}, …)` | chunk-smear retrieval | **parked, unchanged** — single-scale-at-chunk-grain stands; the offline grain experiment is the gate (`doc-code-entanglement` 2026-07-11) |
| `π_depth = ("depth", {L0,L1,L2}, exact)` | conversation-layer sensor | **parked, unchanged** — L2-first build ordering per its own capsule |

This table is the honest extent of the "scale as a first-class dimension" meta-pattern: **the
typing and comparability discipline is shared; the fusion instruments are not** (selection vs
retention-tiering vs privacy-ordering — three rules, three falsifiers, per `dn-sigma-fibers`
§2.8). Neither park's evidence bar is lowered by being named in this table.

## 3. Consequences — what this note licenses (on ratification)

1. The owner's dated cross-reference stamp in `dn-capability-scope` §2.3 (the EH-a pattern;
   owner-hand or explicitly-directed non-blessing edit — never an agent blessing).
2. **One small build item** (graduates with, or as a rider on, `dn-sigma-fibers` FB-2): `Res[T]`
   + `res_under` in `core/scope.py` beside `Inv`/`Rate` — additive, zero behavior change to any
   View or existing instrument (bit-identical reads is the falsifier, as bp-039 held); property
   tests: a π-less Res unconstructable; comparability refused across distinct π.
3. Registry vocabulary: `type_tag = "Res(<name>)"` admissible for new metric families
   (`sigma_persistence.*` first). Existing tags untouched.
4. Future Res customers (π_grain, π_depth) inherit the discipline with no further algebra work —
   if and only if their own parks re-enter on their own evidence.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| RT-a | transport between distinct π (re-binning strengths across rulers) | refused — always a new measurement (the CS-f conservatism) | a consumer genuinely needs cross-ruler comparison (e.g. a lever-bounds change mid-longitudinal-series) |
| RT-b | π as a structured runtime object vs registry/spec_hash metadata only | typed dataclass on `Res[T]`; store/registry carry it as strings + spec_hash params (zero schema change) | a consumer needs machine-checked π equality across stores |
| RT-c | Res-graded *guardrails* | none — Res metrics are `guardrail_eligible = False` descriptive instruments | a Res metric's distribution stabilizes AND a bright line over it is owner-argued |

## Cross-references

- `docs/design-notes/capability-scope-algebra.md` — the ratified note amended: §2.3 (the
  dichotomy, Rule CLOCK at :116), §2.2 (the honesty precedents cited in §2.3-2 above), §2.4
  (mode-as-corollary — preserved by π-erasure). Agent-immutable; stamped only per §3-1.
- `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` — the first customer; its FB-2
  gates on this note (fallback recorded there if the owner rejects the amendment).
- code: `core/scope.py` (:171-184 clocks; :482-507 meet/join; :586-619 Inv/Rate/rate_under —
  the pattern `Res`/`res_under` mirrors), `core/mirror.py` (:76-82), `core/dreaming/graph.py`
  (:33-40), `eval/harness/store.py` (:32,:38), `eval/harness/registry.py` (:27),
  `core/ingest/index.py` (:124-138).
- `docs/brainstorms/cross-strata-and-multiscale-dreamers.md` (2026-07-16T17:32 capsule — the
  parked decision this note is the re-entry of: "the pass shows scale is NOT faithfully
  expressible via meet/join … → draft the algebra extension as its own note").
