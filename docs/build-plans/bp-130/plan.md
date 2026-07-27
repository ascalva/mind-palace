---
type: build-plan
id: bp-130
track: erratum-relation
status: proposed
design_ref:
  - docs/design-notes/erratum-relation.md
contract: builder
write_scope:
  - core/kernel/temporal/operators.py
  - core/kernel/temporal/__init__.py
  - tests/unit/test_temporal_operators.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on: []
parallelizable_with: [bp-129, bp-131]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/findings/finding-0257.md
  - docs/brainstorms/the-false-success-rule.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the `(I − Ε)` factor: `π_valid`, and transport-invariance made checkable

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on
owner approval**. It graduates `dn-erratum-relation` §4 — the one algebra factor the note
says is missing — which §5 lists as **panel-independent**.

⚑ **This plan builds a SURFACE, not a live query — and says so up front.** Grounding
(§3 Q1) established that `active_projection` (`π_active`) has **zero production callers**,
and that `TemporalView`, the one place the algebra meets a store, has **zero production
consumers**. Adding `(I − Ε)` here is mathematically real and observationally inert. The
note's §4 claim *"the extension is exactly the `(I − Ε)` factor — nothing else changes"* is
true **of the operator algebra** and must not be read as "the corpus now answers validity
queries." It does not, and this plan does not make it. That work is bp-131 (the chat lane's
default view) and, beyond it, a live read path that does not yet exist (finding-0257).

Authority-to-act is separate from the readiness blessing (`proposed → ready`), which is the
**owner's hand only**.

## 1. Objective

Add the erratum projection `Ε` and the validity projection `π_valid = π_active ∘ (I − Ε)` to
the temporal operator algebra, with **transport-invariance (`Ε σ_* = σ_* Ε`) asserted as an
executable property on a non-empty erratum set** — the formal content of "never true".

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/erratum-relation.md` §4 — the algebra claim, `π_valid`, and the two
   forensic queries. §7 — the resurrection test, which is this plan's falsifier.
2. `core/kernel/temporal/operators.py` (whole, 130 lines) — the module being extended;
   `active_projection` at `:55` is the operator `Ε` sits beside and `π_valid` composes.
3. `core/kernel/temporal/complex.py` — `CitationComplex`, `.nodes`, `.node_index`, `.n_nodes`;
   the shapes every operator here is typed over.
4. `tests/unit/test_temporal_operators.py` (9 tests) — the existing property style to extend.
5. `core/kernel/temporal/__init__.py:30-38` — the re-export block Item 2 extends.
6. `docs/brainstorms/the-false-success-rule.md` — the degenerate input for *this* plan is
   unusually easy to hit (§7 Item 3); read it before writing the tests.

**DRY audit — does `core/` already implement this? (required — this plan introduces a
mathematical object).** Audited before authoring:

- **A diagonal projection onto a named node subset** — **YES, and `Ε` must be built in its
  image.** `core/kernel/temporal/operators.py:55-60` `active_projection(cx, superseded)` is
  precisely "diagonal projection selecting nodes by set membership". `Ε` is the **same
  construction with the complementary polarity** (1.0 *on* the named set instead of 0.0). It
  must be written to match — same dtype (`np.float64`), same dense-`np.diag` return, same
  idempotence/contraction guarantees — not re-derived in a different style.
- **`(I − P)` for a diagonal `P`** — no helper exists and none is warranted: for a diagonal
  projection it is `np.eye(n) - P`, one line. Adding a general complement helper would be
  ceremony over a primitive.
- **A validity/erratum projection** — **NO. Nothing exists.** Verified: `erratum` appears in
  `core/` only at `core/graph/conductance.py:60,362,378`, an unrelated finding erratum.
- ⚑ **Name-collision hazard, recorded so it is not re-derived:** `core/graph/sigma_star.py` is
  a **different `σ*`** — the abstraction ultrametric over a max spanning tree. It has nothing to
  do with correspondence transport. Do not import it, do not "unify" them.

## 3. Investigation & grounding

- **Q1 — Is the algebra real code, and does anything call it?**
  **Real, and almost nothing calls it.** `active_projection` is `operators.py:55`;
  `pushforward_0` `:63`; `pushforward_1` `:75`; `pullback_0` `:112`; `t_active` `:121`. A
  repo-wide search excluding `tests/` and `.claude/worktrees/` finds **zero production callers**
  for `active_projection`, `pushforward_*`, `pullback_0`, `t_active` — only the re-exports at
  `core/kernel/temporal/__init__.py:31,37` and `tests/unit/test_temporal_operators.py:21`.
  `sigma_node_map` (`:32`) is the sole algebra symbol with a live caller
  (`core/temporal_view.py:223`). `TemporalView` itself has no production consumer: the only
  non-test mention outside its own file is a docstring at `core/temporal/acquire.py:53`.
  ⇒ Filed as **finding-0257**, and it is why §0 states the inertness plainly rather than
  letting a seal imply live effect.

- **Q2 — Where does the *effective* active projection live on the real retrieval path?**
  Not in this module. `core/stores/vectorstore.py:321` appends a literal `current = true` SQL
  clause inside `search(..., include_superseded: bool = False)` (`:303`), and
  `core/verdict/dispositions.py:101` `retracted()` is applied by `core/dreams_view.py:70`.
  ⇒ **A future user-visible `π_valid` is a second SQL predicate, not a matrix product.** This
  plan does not build that; recording it here stops the next builder assuming the operator
  change propagates.

- **Q3 — What exactly does `Ε σ_* = σ_* Ε` mean, given the shapes?**
  Non-trivially, and this is the item's substance. `Ε_n` is `(n_n, n_n)`; `σ_*` (`pushforward_0`)
  is `(n_np1, n_n)`. So the two sides are `Ε_{n+1} σ_*` and `σ_* Ε_n`, both `(n_np1, n_n)`. They
  are equal **iff σ carries the erratum set consistently** — every erratum-target node maps to an
  erratum-target node and every clean node maps to a clean node. The identity is therefore a
  **real, falsifiable condition on the target set's transport**, not an automatic consequence of
  diagonality. Same for `σ^*`: `Ε_n σ^* = σ^* Ε_{n+1}`.

- **Q4 — Do `π_active` and `Ε` commute with each other?**
  Yes, trivially — both are diagonal, and diagonal matrices commute. So
  `π_active ∘ (I − Ε) = (I − Ε) ∘ π_active`, and `π_valid` is well-defined without an ordering
  convention. Worth an assertion, but it is the *cheap* property; **Q3 is the load-bearing one**
  and the tests must not let the easy one stand in for it.

- **Q5 — Does `π_valid` remain a projection and a contraction?**
  It should: the product of two commuting diagonal orthogonal projections is a diagonal
  orthogonal projection. `π_valid² = π_valid` and `‖π_valid‖ ≤ 1` must both be asserted — they
  are what make it a legitimate member of the same operator family, and `active_projection`'s
  docstring (`:57-58`) claims exactly these for its own case.

- **Q6 — Does the note's `π_valid(anchor) = π_active(anchor) ∘ (I − Ε)` type-check against the
  code's signatures?** Yes. `active_projection(cx, superseded) -> np.ndarray` is dense diagonal;
  `(I − Ε)` is dense diagonal of the same shape `(cx.n_nodes, cx.n_nodes)`. The composite is a
  plain `@`. **The code does not settle** what supplies the erratum target *set* — that is
  bp-129's `ErrataStore.targets_for(surface)`. This plan takes a `set[str]` parameter and stays
  store-free (core self-containment: `core/kernel/**` opens no store).

**Additional risks or questions surfaced during reading:**

- ⚑ The degenerate input here is unusually easy to hit: with an **empty** erratum set,
  `Ε = 0`, `(I − Ε) = I`, and `π_valid ≡ π_active` — so **every property in this plan passes
  vacuously**, including the commutation identity. Item 3 exists specifically to make that
  impossible to ship.
- `core/kernel/**` is the inner ring (`core/kernel/rings.py:92-96`). No store import, no config
  import, stdlib + numpy/scipy only. This plan extends an existing module rather than adding one,
  so no ring registration changes.

## 4. Reconciliation

- `docs/design-notes/temporal-retrieval-algebra.md:5` — front matter reads
  `implementation: design-only`, which is **stale**: bp-032/bp-033 shipped the operators this
  plan extends. → **[banner: correction]**, carried by **finding-0257**, not by an edit — the
  note is **ratified and agent-immutable**. No diff proposed against the file.

- `docs/design-notes/erratum-relation.md:188` — *"The extension is exactly the `(I − Ε)` factor
  — nothing else changes."* → **[cross-ref: extension]**, carried by **finding-0257** and by
  §0 of this plan. The sentence is true of the operator algebra and false as a statement about
  observable retrieval behavior, because `π_active` has no production caller. Recorded, not
  edited.

- `core/kernel/temporal/operators.py` — **[cross-ref: extension]**. The new operators must carry
  a comment tying them to `active_projection` and naming the distinction, so a later reader
  cannot mistake `Ε` for a second supersession filter:
  ```
  # π_active is ANCHOR-RELATIVE and deliberately does NOT commute with the transports — that is
  # its function. Ε is the opposite: a NODE PROPERTY that rides through σ_*/σ^* unchanged (E3).
  # That commutation IS the formal content of "never true" — supersession is transport-relative,
  # erratum is transport-invariant (dn-erratum-relation §4).
  ```

- `core/kernel/temporal/__init__.py:30-38` — **[cross-ref: extension]**: the re-export list gains
  the new names, alphabetically, matching the existing ordering.

## 5. Write scope

- `core/kernel/temporal/operators.py` — **the deliverable**: `erratum_projection`,
  `valid_projection`, `commutes_with_pushforward`, `commutes_with_pullback`.
- `core/kernel/temporal/__init__.py` — **carried because the module's public surface is its
  re-export block** (`:30-38`); a new operator absent from it is not reachable the way every
  sibling operator is.
- `tests/unit/test_temporal_operators.py` — **carried because it is the existing home of this
  module's property tests** (9 today). Extending it keeps one test module per operator module;
  a second file would fragment the surface.

**Deliberately OUT of scope:** `core/stores/**` (this plan opens no store — inner-ring
self-containment); `core/temporal_view.py` (wiring `π_valid` into a View is **not** in this
plan — see §9 and finding-0257); `core/stores/vectorstore.py` (the real retrieval path — §3 Q2);
every design note; the foundation denylist. ⚑ **No live store is opened or written.**

## 6. Interfaces pinned inline

**Existing, copied verbatim** (`core/kernel/temporal/operators.py:55-60`):

```python
def active_projection(cx: CitationComplex, superseded: set[str]) -> np.ndarray:
    """`π_active` on 0-cochains: the diagonal orthogonal projection onto the not-yet-superseded
    node subspace (`T = now`). Idempotent (`Π² = Π`) and a contraction (`‖Π‖ ≤ 1`) by
    construction, and deliberately NOT a chain map — it destroys superseded content rather than
    transporting it."""
    diag = np.array([0.0 if name in superseded else 1.0 for name in cx.nodes], dtype=np.float64)
    return np.diag(diag)
```

`pushforward_0(cx_n, cx_np1, index_map) -> sp.csr_matrix` — shape `(n_np1_nodes, n_n_nodes)` (`:63`).
`pullback_0(cx_n, cx_np1, index_map) -> sp.csr_matrix` — shape `(n_n_nodes, n_np1_nodes)` (`:112`).
`sigma_node_map(cx_n, cx_np1, sigma) -> dict[int, int]` — raises `DiamondError` on a merge (`:32`).

**The operators this plan adds** — note the **polarity inversion** against `active_projection`:

```python
def erratum_projection(cx: CitationComplex, erratum_targets: set[str]) -> np.ndarray:
    """`Ε` on 0-cochains: the diagonal orthogonal projection ONTO the span of erratum-targeted
    nodes — the complement polarity of `active_projection`, which projects onto the nodes NOT in
    its set. Idempotent and a contraction by construction. A NODE property (E3): it takes no
    anchor and no cut, because erratum status acts at EVERY cut, including cuts before the
    erratum was asserted."""
    diag = np.array([1.0 if name in erratum_targets else 0.0 for name in cx.nodes],
                    dtype=np.float64)
    return np.diag(diag)


def valid_projection(cx: CitationComplex, superseded: set[str],
                     erratum_targets: set[str]) -> np.ndarray:
    """`π_valid = π_active ∘ (I − Ε)` (dn-erratum-relation §4): what was TRUE at the anchor, as
    opposed to what the store BELIEVED. Excludes erratum targets at every cut, including cuts
    inside a row's apparent lifetime — which `π_active ∘ σ^*` alone cannot do, since it
    resurrects any past-active row as legitimate. Both factors are diagonal, hence commuting, so
    the composition order is immaterial (asserted, not assumed)."""
    e = erratum_projection(cx, erratum_targets)
    identity = np.eye(cx.n_nodes, dtype=np.float64)
    out: np.ndarray = active_projection(cx, superseded) @ (identity - e)
    return out


def commutes_with_pushforward(cx_n: CitationComplex, cx_np1: CitationComplex,
                              index_map: dict[int, int],
                              targets_n: set[str], targets_np1: set[str]) -> bool:
    """The E3 transport-invariance check on 0-chains: `Ε_{n+1} σ_* == σ_* Ε_n`. TRUE iff σ carries
    the erratum set consistently (every targeted node maps to a targeted node, every clean node to
    a clean one). This is a REAL condition on the target set's transport, not a consequence of
    diagonality — the honest negative the falsifier needs."""


def commutes_with_pullback(cx_n: CitationComplex, cx_np1: CitationComplex,
                           index_map: dict[int, int],
                           targets_n: set[str], targets_np1: set[str]) -> bool:
    """The E3 check on 0-cochains: `Ε_n σ^* == σ^* Ε_{n+1}`."""
```

**The invariant being encoded** (`dn-erratum-relation` §4, verbatim): *"`Ε` commutes with the
transports: `Ε σ_* = σ_* Ε` and `Ε σ^* = σ^* Ε` — erratum status rides through temporal transport
unchanged. `π_active` deliberately does NOT commute with them (it is anchor-relative; that is its
whole function). **This commutation property IS the formal content of "never true"**."*

## 7. Items

### Item 1 — `Ε` and `π_valid`

- **Objective:** `erratum_projection` and `valid_projection` exist in `operators.py`, matching
  `active_projection`'s construction, dtype, and return shape.
- **Files:** `core/kernel/temporal/operators.py`.
- **Acceptance test:** `uv run mypy core agents eval ops scheduler scripts` reports
  **Success: no issues** (floor stays 0); `uv run python scripts/check_imports.py` exits 0;
  `uv run ruff check .` passes. On a fixture complex with a **non-empty** erratum set:
  `Ε² == Ε`; `‖Ε‖ ≤ 1`; `π_valid² == π_valid`; `‖π_valid‖ ≤ 1`;
  `π_valid == (I − Ε) @ π_active` (order-independence, §3 Q4).
- **Falsifier:** `Ε` is built with the **same** polarity as `active_projection` (0.0 on the named
  set) rather than the inverted one. The symptom is subtle and would pass a careless test:
  `π_valid` would then exclude everything *except* the errata — the exact inverse of the intent,
  and a corpus that serves **only** the rows it asserts were never true. Assert directly that for
  a target node `v`, `Ε[v,v] == 1.0` and `π_valid[v,v] == 0.0`.
- **Invariant(s) it must not violate:** E3 (no cut/anchor parameter on `Ε` — a signature check,
  not a comment); inner-ring self-containment (`core/kernel/**` imports no store, no config).
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** none.

### Item 2 — transport-invariance as an executable property

- **Objective:** `Ε σ_* = σ_* Ε` and `Ε σ^* = σ^* Ε` are checkable functions, and the check is
  demonstrated to distinguish a consistent transport from an inconsistent one.
- **Files:** `core/kernel/temporal/operators.py`, `core/kernel/temporal/__init__.py`.
- **Acceptance test:** on a two-complex fixture with an injective σ and a **non-empty** target set:
  - `commutes_with_pushforward(...)` is **True** when σ carries targets to targets;
  - it is **False** when one target node maps to a node absent from `targets_np1` — ⚑ **the
    honest negative; an implementation that returns True unconditionally is the failure this
    item exists to catch**;
  - both hold identically for `commutes_with_pullback`;
  - `from core.kernel.temporal import erratum_projection, valid_projection,
    commutes_with_pushforward, commutes_with_pullback` succeeds (the re-export).
- **Falsifier:** the negative case cannot be constructed — i.e. the identity holds for *every*
  target set. That would mean the check is vacuous and transport-invariance is not a property of
  the erratum set at all but an artifact of diagonality, which would **falsify the note's §4
  claim that the commutation carries formal content**. Report it as a finding rather than
  weakening the test.
- **Invariant(s) it must not violate:** `π_active` must **not** be made to commute — its
  non-commutation is its function (§4 of the note); if a change makes `active_projection` commute
  with the transports, something is wrong.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Item 1.

### Item 3 — the degenerate input must redden (the false-success rule)

- **Objective:** prove the suite cannot pass vacuously.
- **Files:** `tests/unit/test_temporal_operators.py`.
- **Acceptance test:** ⚑ **The named degenerate input:** an **empty** erratum target set, on which
  `Ε = 0`, `(I − Ε) = I`, `π_valid ≡ π_active`, and **every property in Items 1–2 passes without
  testing its claim**. The suite must redden on it. Concretely:
  - a test asserts `Ε` is **non-zero** and `π_valid ≠ π_active` on the fixture — so a fixture
    that silently loses its targets fails loudly rather than passing green;
  - **the resurrection test** (`dn-erratum-relation` §7 falsifier (i)), the note's own named
    falsifier of the central claim: build a node erratum-targeted at cut `n+1`, transport a
    0-cochain **backward** via `pullback_0` (`σ^*`) to cut `n`, apply `π_valid` there, and assert
    the corrected node's component is **0.0**. Under `π_active` alone it is **non-zero** — the
    row is resurrected as legitimate. **Both halves must be asserted**, because the second is
    what proves the new factor did the work.
  - **the mutation campaign** (finding-0249: both surviving mutants last wave were found by
    mutating and running, neither by reading). Apply, run, record, revert:
    1. `erratum_projection` returns `np.zeros(...)` — the degenerate mutant;
    2. `valid_projection` returns `active_projection(...)` unchanged — the "factor forgotten" mutant;
    3. `Ε`'s polarity inverted (Item 1's falsifier);
    4. `commutes_with_pushforward` returns `True` unconditionally (Item 2's falsifier).
    **Every mutant must be CAUGHT.** A survivor is a vacuous test; strengthen it before closing.
- **Falsifier:** mutant 1 or 2 **survives** — that is the false-success signature: the suite is
  green, `π_valid` is in the codebase, and it demonstrably does nothing.
- **Invariant(s) it must not violate:** the 9 existing tests in the file stay green; the argless
  `uv run mypy` tail still equals the pinned tests/ baseline (**69**).
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Items 1, 2.

## 8. Math carried explicitly

- **`Ε` (the erratum projection)** — *measures:* the subspace of records asserted to have had
  **empty validity** — never true at any cut. *valid when:* the target set is a fixed, enumerated
  node set (PD-1) and carries no cut parameter, so the operator is a node property (E3); and the
  underlying σ is injective (no diamond — `sigma_node_map` raises `DiamondError` otherwise, so
  the precondition is enforced upstream rather than assumed). *fails its keep if:* the commutation
  `Ε σ_* = σ_* Ε` cannot be violated by any target set — then it carries no information about
  transport and the note's §4 claim is empty (Item 2's falsifier).

- **`π_valid = π_active ∘ (I − Ε)` (the validity projection)** — *measures:* what was **true** at
  the anchor, as opposed to what the store **believed** — the valid-time axis of the bitemporal
  split, against `π_active`'s transaction-time axis. *valid when:* both factors are diagonal
  orthogonal projections over the same node ordering (so they commute and the product is again a
  projection), and the anchor is a legitimate cut. *fails its keep if:* a `σ^*`-mediated validity
  query at a pre-correction cut returns a corrected row as **valid** — the note's §7 falsifier
  (i), the resurrection test, asserted directly in Item 3.

- **The composition law `correction(r) = supersession(r → r′) ∧ erratum(r)`** — *measures:* that
  a correction is not a primitive but a conjunction, so the default read path sees only a
  supersession (the owner's "no need to wipe" clause) while the temporal paths see the falsity.
  *valid when:* `Ε` is transport-invariant and `π_active` is not — the asymmetry is what makes
  the two distinguishable at all. *fails its keep if:* a correction is exhibited whose target has
  a **non-empty** validity interval (§7 falsifier (ii)) — then erroneousness is cut-relative, the
  marker-on-edge model was right, and `Ε` should have been an edge attribute, not a node one.

## 9. Non-goals

- **No wiring into any View.** `core/temporal_view.py` is out of scope. `π_valid` will have no
  production consumer when this plan closes, exactly as `π_active` has none today — stated in §0
  and filed as finding-0257 rather than quietly fixed here.
- **No change to the real retrieval path** (`core/stores/vectorstore.py`'s `current = true`
  prefilter, §3 Q2). A user-visible validity query is a second SQL predicate and a different plan.
- **No store access.** This plan supplies the operator; bp-129 supplies the target set. They are
  joined by a caller that does not yet exist.
- **No change to `π_active`'s semantics.** Its non-commutation with the transports is deliberate.
- **No new module, no ring re-registration** — `operators.py` is extended in place.

## 10. Stop-and-raise conditions

- **The negative case in Item 2 cannot be constructed** → the note's §4 claim may be empty. File a
  **`math`-typed finding** (routes to the orchestrator) and park Item 2 with a re-entry condition.
  Do **not** delete the test or weaken it to the trivially-true form.
- **A mutant survives after strengthening** → record it in `journal.md` as an **equivalent mutant
  with an explicit argument**, or file a finding. Never silently accept a survivor.
- **`(I − Ε)` is found to require an anchor or cut to be useful** → that contradicts E3 and the
  note's central claim. **Stop and file a `spec-defect` finding**; this is a design-level
  contradiction a builder must not resolve by inventing a cut parameter.
- **Any instinct to make this plan "actually do something"** by wiring `π_valid` into
  `TemporalView` or `VectorStore.search` → **stop.** That is out of scope (§9), it is where the
  real blast radius lives, and it needs its own plan with its own acceptance.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **PD-E — wiring `π_valid` to a live read path** | **Parked entirely.** The operator lands unwired, matching `π_active`'s existing state. | *Wire it into `TemporalView` now* — rejected: `TemporalView` has zero production consumers (§3 Q1), so it moves the inertness one layer out rather than removing it. *Wire it into `VectorStore.search`* — rejected: that is the real retrieval path and a genuine blast radius, and it is a SQL predicate rather than an operator (§3 Q2) — a different design, not this factor. | A plan exists that gives `TemporalView` (or the vector search path) a real consumer. **finding-0257** carries the gap. |
| **PD-F — where the erratum target set comes from at call time** | A `set[str]` parameter, supplied by the caller. `core/kernel/**` is the inner ring and opens no store. | *Read `ErrataStore` directly from the operator* — rejected: it would make the inner ring store-dependent and break `core/kernel/rings.py`'s registration, for no gain. | Never, unless the ring boundary itself is redesigned. |
| **PD-G — 1-chain / edge transport for `Ε`** | **0-chains only**, matching the note, which defines `Ε` on the node space. | *Also define `Ε` on 1-chains* (as `pushforward_1` exists) — rejected: the note's §3 arity argument is that erratum is a **node** property precisely because a retraction has no successor edge. A 1-chain `Ε` would smuggle back the edge-anchored model the note rejects. | A concrete need for edge-level erratum transport, named in a finding. |

## 12. Dependency & ordering summary

**Within this plan** — strictly serial; all three items are read-only in blast-radius terms (pure
functions in the inner ring, no store, no I/O), so the ordering is logical rather than risk-based:

```
Item 1 (Ε, π_valid)  ─>  Item 2 (transport-invariance + re-export)  ─>  Item 3 (degenerate input + mutation)
```

Item 3 last on purpose: it is the item that proves the other two are not vacuous, and it can only
be written once their surfaces exist.

**Across plans:**
- `parallelizable_with: [bp-129, bp-131]` — **disjointness verified mechanically, not assumed.**
  bp-129 writes `core/stores/errata.py`, `tests/unit/test_errata.py`, `ops/lifecycle/launcher.py`,
  `tests/integration/test_lifecycle.py`; bp-131 writes `core/chat_validity_view.py`,
  `tests/unit/test_chat_validity_view.py`, and (fallback only) `core/kernel/rings.py`,
  `tests/unit/test_inner_ring.py`. Neither set intersects this plan's three globs.
  The plans meet only conceptually: bp-129 produces the target *set*, this plan the *operator*
  over it, bp-131 the row-set realization. None imports another.
  ⚑ Note the one live hazard in the pair with bp-131: if bp-131 takes its **fallback** and edits
  `core/kernel/rings.py`, that is still disjoint from this plan's files — but it changes the inner
  ring, and this plan's module (`core.kernel.temporal.operators`) is **already declared inner**.
  Adding functions to it does not change its import closure so long as no new outer import appears
  (this plan adds numpy usage only). If `tests/unit/test_inner_ring.py` reddens during this plan's
  run, the cause is bp-131's concurrent edit, not this one.
- **No `depends_on`.** This plan is buildable with an empty erratum set as a fixture parameter and
  needs nothing from bp-129 at build time.
- bp-131 depends on bp-129, not on this plan — the chat lane's default view is a SQL/read-path
  concern, not an operator one (§3 Q2).
