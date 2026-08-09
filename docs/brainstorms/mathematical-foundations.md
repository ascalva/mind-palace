# mathematical-foundations

## 2026-08-09T04:51:00Z

```capsule
topic: mathematical-foundations
date: 2026-08-09

seed (owner, paraphrase): the project's math is extensive — query algebras,
Laplacians, curvature, sets and memberships, type correctness. What axioms do
they rely on; can we "derive from first principles"? Would knowing that empower
us — is foundational math the bridge to other branches, a mini Langlands? When
we capture an idea it behaves like a theorem (or a proposed definition) — how
far does the rabbit hole of its implications propagate? Is this where a
proof-based language comes in?

decisions:
  - framing: the palace's math is finite in substance. The Laplacian is a
    concrete matrix; Ollivier-Ricci curvature on a finite graph is a finite
    linear program (W1 transport); memberships form a finite Boolean algebra;
    embeddings live in finite-dimensional inner-product spaces over R. The
    foundational reliance sits far below ZFC — classical logic + finite sets +
    real arithmetic. Axiomatic consistency is not where correctness risk lives.
  - framing: the working bridge to other mathematical machinery is
    structure-instantiation, not axiomatic descent. Name which structure each
    component is a model of (Boolean algebra, semiring, PSD operator,
    metric-measure space) and that structure's theorems transfer for free. The
    Langlands analogy lands as correspondences BETWEEN structures (graph <->
    operator, curvature <-> transport, membership <-> logic), not as shared
    axioms at the bottom.
  - framing: falsifiers before proofs. Algebraic laws land as property tests
    first — mechanized falsification matches the house epistemology (ratify
    falsifiers, not proofs). A proof assistant (Lean 4 + Mathlib) proves the
    math, never the Python; the translation gap means it belongs at
    design-note level, if anywhere.
  - the machine betrays the axioms: float addition is not associative, so the
    exact laws we rely on are the ones that must be tested with tolerance
    bounds. The epsilon-gap between R and float64 is the real foundational
    risk, not Russell's paradox.

parked:
  - decision: adopting a proof language (Lean 4) for design-note-level math
    default: no proof assistant; laws live as property tests in the suite
    re_entry: a design note whose central claim a property test cannot falsify
      (e.g. a convergence or spectral bound), or a wrong-math finding that a
      machine-checked proof would have caught

open_questions:
  - which structure does each component actually instantiate? query algebra —
    lattice, monoid, or semiring? memberships — finite Boolean algebra (finite
    Stone: every finite BA is a powerset algebra)? Laplacian — PSD operator,
    zero row sums? curvature — W1 on a finite metric-measure graph? Naming
    these precisely is the laws-ledger question.
  - how far does a captured definition's deductive closure propagate — should
    implication-tracking (what a ratified definition forces elsewhere) be an
    explicit artifact-chain mechanism, or is the gate discipline (findings
    re-enter only through the gate) already the control on propagation?
  - does semiring provenance (one algebra, many query semantics by swapping
    the semiring) fit the query algebra as prior art? [FROM MEMORY — verify
    before relying on it]
  - is mypy + type_gate already the Curry-Howard layer (types as propositions,
    the checker as a weak proof assistant), and how far can refinement-style
    newtypes push it before diminishing returns?

next_steps:
  - candidate: a laws-ledger sweep — per mathematical component, the claimed
    structure + its laws + one named falsifier (property test) per law;
    memberships (in flight) is the cheapest first target — Boolean-algebra
    laws are nearly free to test
  - if the ledger lands, fold the structure-claim into the build-plan §8 math
    field-guide so every new component names what it instantiates at mint time

references:
  - core/stores/memberships.py + tests/unit/test_memberships.py (staged, in
    flight — the first candidate surface)
  - dn-vector-membership-store, dn-core-graph-instruments (the structures
    under discussion)
  - Curry-Howard correspondence; Lean 4 + Mathlib [FROM MEMORY — verify
    Mathlib coverage before citing]
  - Green, Karvounarakis, Tannen — "Provenance Semirings" (PODS 2007) [FROM
    MEMORY — verify before any book-grade citation]
```
