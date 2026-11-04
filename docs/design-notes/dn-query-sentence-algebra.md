---
type: design-note
id: dn-query-sentence-algebra
track: query-language          # NEW manifest, minted with this note (docs/tracks/query-language.md) — ⚑ the owner renames or rejects the coordinate at the merge
status: draft                  # provenance description, never a gate (merge-gated regime, 2026-07-28)
implementation: building       # QL-1 and QL-2 begun 2026-11-04 on the branch by the owner's order ("start implementing the code itself (core), no pr yet"); core/sentence/
created: 2026-11-04
updated: 2026-11-04
links:
  - docs/brainstorms/query-sentence-algebra.md          # THE WARRANT — the owner's three seeds of 2026-11-04, near-verbatim
  - docs/design-notes/core-query-protocol.md            # RATIFIED — §2.1 scope; §2.2 the one algebra, SEARCH as the cone's generic point
  - docs/design-notes/capability-scope-algebra.md       # RATIFIED — §2.4 a query is (verb, s); mode a corollary of scope; §2.3 Inv/Rate
  - docs/design-notes/fiber-geometry.md                 # RATIFIED — §2.0 Σ_move; §2.3 the chain language; FG-d's named consumer
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED — §2.1 K(β); §2.2 π_active/σ_*/σ^*; §2.6 β*
  - docs/design-notes/magnetic-laplacian.md             # RATIFIED — the sign and phase fibers a contradiction lives in
  - docs/design-notes/dn-mathematical-foundations.md    # the ladder the proofs climb; the ledger the laws enter when code relies on them
  - docs/brainstorms/fiber-chain-grammar.md             # the chain as a sentence; the verb-licensing table
  - docs/brainstorms/scoped-context-queries.md          # a question compiles to bounds; loud failure; the lessons loop
  - formal/Palace/Sentence.lean                         # the composition laws, machine-checked (formal/Palace/Sentence/Defs.lean the model)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/query-sentence-algebra.md
---

# The query sentence algebra — verbs with nouns, adjectives and hypotheses, and the compiler that plans them

> Composed on the Lean-ladder session (Fable 5.1, 2026-11-04) from the owner's three seeds of the
> same day (the warrant), on the owner's direction that the design and its proofs proceed together
> and the build follow a proven design. Agent-drafted, filed `draft` on a branch; under the
> merge-gated regime nobody flips a status and the owner's merge is ratification. Nothing is built:
> `core/` is untouched, and every change this note proposes to it is a proposal for the owner.
> Every nontrivial claim carries a grade: `[THEOREM]` is machine-checked in `formal/` and names its
> declaration; `[ESTABLISHED]` is Mathlib's or a ratified note's; `[DERIVED]` is argued here from
> those; `[INFERENCE]` is a design call with a named falsifier. Code claims were read on this
> branch (`build/lean-design-theorems` at `31ecabf`).

## 1. Purpose and scope

### 1.1 What this note decides

`core/query.py` asks the core a question in one word. A query is `(verb, s)`: one of eight verbs,
one required scope, admitted iff `req(verb) ⊑ grant`, its mode a corollary of the scope
(dn-capability-scope §2.4). SEARCH is the embedding Gram kernel's column at the query text — the
generic point of the PSD cone (dn-core-query-protocol §2.2, the Moore–Aronszajn inversion) — and in
this language it is the *base case*: a noun phrase with no connective, no adjective and no walk.
The machinery the ratified notes built — the cone's `+`, `⊙` and congruences, the path semiring, the
β-curve, the transports, the chain language — is reachable only by composition, and today nothing
composes. This note decides:

1. **The sentence (§2.1).** A query is a typed term: nouns are sorts, adjectives are masks and
   indices, verbs are operators between sorts, connectives are the operations each sort's structure
   gives, and one modality, `assume`, evaluates a sentence under a hypothesis.
2. **The sorts and their algebras (§2.2),** with the bridges between them and exactly where a bridge
   is partial or lossy.
3. **The grammar (§2.3):** productions, operator precedence, the adjectives' meanings.
4. **The typing (§2.4):** sort rules; the scope check, clause by clause; the mode per clause; the
   rule that the noun, not the verb's name, carries the edge letter; the result typing `Hyp(Δ)`
   beside `Inv` and `Rate(κ)`.
5. **The composition laws (§2.5),** machine-checked before any code parses a sentence: each is the
   licence for one rule of the grammar or one rewrite of the planner.
6. **Hypotheticals (§2.6):** what an assumption is, where it lives, what a result under it is, and
   how the graph's response is read — including the owner's correction that an assumption can
   raise resistance.
7. **The compiler (§2.7):** six stages, precedence and precedents, the ambiguity policy, the plan
   as an artifact.
8. **The falsifier battery (§2.8):** the real questions on which a composed sentence must beat
   flat search, measured at build time.

### 1.2 Out of scope

Any `core/` change (the two defects §2.4 finds are reported, not fixed); the Librarian's and the
Ambassador's RAG machinery, which become clients of the sentence; the build itself (§3 licenses it;
`/graduate` follows the owner's merge); learned grammars (fiber-geometry FG-e stands); non-regular
path languages (FG-c stands); a second dial `z` on the curve (temporal-retrieval TA-b stands); the
diachronic reader (dn-core-query-protocol §2.7). The retrieval mathematics is cited, never
re-derived: this note adds composition laws and response laws, nothing about kernels at rest.

### 1.3 What is proved, what is cited, what is open

Proved on this branch, in `formal/Palace/Sentence.lean` over `formal/Palace/Sentence/Defs.lean`,
attacked in `formal/PalaceTest/Sentence.lean` (seeds 219–244, each law with a negative control):
the nine law families of §2.5. They are design theorems in the sense of `formal/README.md`: no code
relies on them yet, so the ledger has no rows and `lake comparator` does not judge them; the six
kernel checkers replay them. When QL-1 lands (§3), each becomes a ledger row with a `Spec/`
statement and a Python property test, the two-sided bridge of dn-mathematical-foundations §2.4.

Cited: the Schur product theorem (Mathlib, `Matrix.PosSemidef.hadamard`); Rayleigh's law (CND-2,
`Palace/Rayleigh.lean`); balance (LAP-5, LAP-6, `Palace/Balance.lean`); the retrieval curve (RSP-1
to RSP-4, `Palace/Retrieval.lean`); negative type (`Palace/NegativeType.lean`); the scope algebra
(SCO-1 to SCO-8, `Palace/Scope.lean`).

Open, stated where it bites: Schoenberg's direction (negative type ⇒ `e^{−sd}` PSD) is not
machine-checked, so the metric-to-kernel bridge is a hypothesis off the canonical curve (§2.2); the
exact response of the RSP kernel to one assumed edge is derived, not proved (§2.6); the move class of
RELATED's relation edges is the owner's (§2.4).

## 2. Principles / decision

### 2.1 A query is a sentence; SEARCH is one word of it

**Decision.** A query is a term of a small typed algebra. Its denotation is a value of its sort,
computed against the stores at a cut; its *plan* is the term in a normal form the proved identities
justify; its *answer* is the value rendered — ranked, each hit carrying provenance and status,
never bare text (scoped-context-queries). The parts of speech:

| part | what it is | examples |
|---|---|---|
| **noun** | a value of a sort (§2.2) | an atom; a region of atoms; the field `near "…"`; the kernel `K_sem`; the relation `F`; a chain |
| **verb** | an operator between sorts, the eight of `core/query.py` among them | `near` (SEARCH), `reach`, `diffuse`, `history`, `related`, `origin`, `capture` |
| **adjective** | a restriction or an index on a noun | `within ⟨region⟩`, `as of ⟨cut⟩`, `via ⟨path⟩`, `over ⟨strata⟩`, `with β=…`/`k=…`/`depth=…` |
| **connective** | an operation the sort's structure gives | `and` (`⊙` on kernels and fields, `∩` on regions), `or` (`+`, `∪`), `then` (the first's region masks the second) |
| **modality** | a hypothesis the sentence is evaluated under | `assume ⟨edge⟩ in ⟨sentence⟩` |

SEARCH is `near t`: the column of `K_sem` at the embedding of `t`, a **field**. It composes with
everything and is the generic point of the cone, so it is where every retrieval that names no
structure lands — the base case, not the point. The point is what the connectives and adjectives
reach: `near t and cited-by X`, `diffuse from X within (ratified notes) as of c`, `chains from A to
B via S*·(C|D)`, `assume F A B in resistance C D`. `[DERIVED — from dn-core-query-protocol §2.2 and
dn-capability-scope §2.4]`

**The verbs, restructured (owner's direction, 2026-11-04).** The eight one-word verbs become typed
operators named for the sort they return, and the *relation noun* a verb walks carries the edge
letter (Rule NOUN, §2.4). HYBRID stops being a verb: it was a composition all along. CAPTURE is a
write and has no sentence (a sentence is a reading). The map, which `core/sentence/legacy.py`
implements so the old surface is a fragment of the new:

| old verb | sentence | sort |
|---|---|---|
| SEARCH `text` | `near "<text>"` | field |
| DIFFUSE `target` | `diffuse S from <note> [beta β]` | field |
| HYBRID `text, target` | `near "<text>" and diffuse S from <note>` | field |
| REACH `target` | `reach F from <note> [depth n] [back\|forward\|both]` | region |
| RELATED `target` | `relate <note>` | region (signed detail) |
| HISTORY `target` | `trace <note> [forward\|back]` | chain |
| ORIGIN `edge` | `witness "<edge id>"` | witness |
| — | `walk from <note> [to <note>] via <path>` | chain (new: the product automaton) |
| — | `far`, `top k`, `atleast t`, `not`, `minus` | the bridges and the region operations |
| CAPTURE | — | a write, outside the grammar |

**The owner's questions, as sentences.** What each returns today, and what the sentence returns:

| question (owner's words, paraphrased) | sentence | flat search | the sentence |
|---|---|---|---|
| notes near ⟨the magnetic Laplacian⟩ that the fiber-geometry note cites | `near "magnetic Laplacian" and reach F⁻¹ from dn-fiber-geometry depth 1, top 8` | the nearest texts, cited or not | the nearest *cited* texts: the column of `K_sem` masked by the citation region (QSA-2, QSA-3) |
| what superseded X since the September cut, and who cited the old version | `history D forward from X as of c_sep then reach F⁻¹ depth 1` | nothing: no verb walks two fibers | the successors, then every citer of the version chain (`then` feeds a region to a mask) |
| near ⟨t₁⟩ but unlike ⟨t₂⟩ | `near t₁ and far t₂` | cannot negate | the product with the reversed field `1 − near t₂` (fields are bounded; §2.2) |
| far in text, close by citation: the cross-domain imports | `diffuse over F from X with β=1 and far X` | cannot | the S↔F mismatch adjective of fiber-geometry §2.2, as a sentence |
| how A and B connect through witnessed steps, resembling at most twice | `chains from A to B via S{0,2}·C+` | cannot | the explainable-retrieval direction of fiber-geometry §2.3-5: witnessed paths, verb-licensed |
| what was near X before the refactor | `near X as of c₀` | the present | the past cut, an index, never a letter (fiber-geometry §2.3-8) |
| where is the project headed (the onboarding question) | `near "direction" over {design-notes, findings, brainstorms} within status ∈ {ratified, open} with window 14d, then top 12 by recency × centrality grouped by source` | a nearest-neighbour list with no bounds | the three bounds of scoped-context-queries, as adjectives; loud and empty when the bounds exclude the answer |
| assume dn-A cites dn-B: does the resistance between C and D fall, and does the citation coherence change? | `assume F A B in (resistance C D; coherence)` | cannot | a `Hyp` result beside the actual: the response (§2.6) |

### 2.2 The sorts and their algebras

Each sort is a known structure and has exactly the operations that structure gives
(dn-mathematical-foundations §2.1, structure-instantiation). The type checker refuses the rest,
with the reason.

| sort | carrier | closed under | not closed under | structure | where it already lives |
|---|---|---|---|---|---|
| **Region** | a finite set of atoms (or of strata, for `over`) | `∪`, `∩`, `∖`, complement | — | Boolean algebra | `Finset`; a scope's `Σ` is a region of strata |
| **Field** | a bounded score per atom, `V → [0, 1]` | pointwise `⊙`, `+` (renormalized), `c·`, `within`, `far` = `1 − f` | — | the cone's columns: every field here is a kernel's column at an anchor (QSA-3) | `Hit.score`; `k_sem`, `k_struct` in `_hybrid` |
| **Kernel** | a positive semidefinite `V × V` matrix | `+`, `⊙`, `c·` for `c ≥ 0`, `within` (congruence), submatrix | `max`, `1 − K`, complement of a mask | the PSD cone (Schur; sum; congruence) `[ESTABLISHED]` | `K_sem`, `K_struct`, `e^{−tL}` (CND-4), `L⁺` (CND-1), `G_β` (RSP-2) |
| **Metric** | a quasi- or pseudo-metric on atoms | min-plus composition (shortest path), restriction | the cone, except through negative type | the path semiring's tropical boundary (dn-core-query-protocol §2.2) | `free_energy_distances` (RSP-4), `d_t` (CND-4), σ* (SIG-3) |
| **Relation** | one move class of `Σ_move = {S, F, D, C}` as a weighted Boolean matrix | `∪`, `∘`, `*` (the path semiring); restriction by an automaton; symmetrization | — | the typed graph of fiber-geometry §2.0 | `X_cite`, the version chains, `E_proven`, the σ-backbone |
| **Chain** | a list of moves with the vertices reached | concatenation; the product walk | — | words over `Σ_move` (fiber-geometry §2.3) | `connected_set`'s paths, implicit |
| **Transport** | `σ_*`, `σ^*`, `π_active` | composition | — | the operator algebra of dn-temporal-retrieval-algebra §2.2 | `_history`'s forward and back |
| **Witness** | a record: the commit that minted an edge | — | — | the C fiber's two-hop join | `origin()` |

**The bridges, and where each is partial.** A sentence moves between sorts only through these:

| from → to | the bridge | total? | law |
|---|---|---|---|
| Kernel → Field | the column at an anchor, `K e_a` | total | QSA-3 |
| Field → Region | a threshold `≥ t`, or the top-`k` | total, **lossy**: the winner-take-all step | QSA-4: a threshold commutes with `within`; the top-`k` does not — ranking is last |
| Region → mask | the indicator | total | QSA-2 |
| Metric → Kernel | `e^{−βd}` | **total on the canonical curve**: `e^{−βd}` is positive definite for every `β` there (RSP-3) `[THEOREM]`; **off it, only under negative type**, a decidable quadratic-form check (`NegType`), and Schoenberg's direction is cited, not machine-checked `[ESTABLISHED, FROM Schoenberg 1938]` | RSP-2, RSP-3; `NegativeType.lean` |
| Relation → Kernel | symmetrize, take `L`, apply `f(L)` | total for `f` the heat kernel, the pseudo-inverse, the resolvent | CND-4, CND-1; the magnetic fibers for direction (BRG-7) |
| Relation → Region | the reachability closure of the path semiring | total | REACH; QSA-7 (monotone) |
| Relation → Chain | the product walk against a path language | total | QSA-7 |
| Chain → Transport | a `D`-chain along one identity's version chain | total where the chain is well-typed (one identity) | dn-temporal-retrieval-algebra A6 |

The compiler inserts a bridge only where the grammar names it (`top k`, `≥ t`, `via`, `as of`),
never silently: a sentence that needs a bridge the grammar did not write is a type error with the
missing word named. `[INFERENCE — falsifier QSF-3]`

### 2.3 The grammar

The grammar as implemented in `core/sentence/grammar.py` (a recursive-descent parser by
precedence; every parse error names the production that failed and the token it saw):

```
sentence  := or-expr ("then" or-expr)*                      -- `then` binds loosest
or-expr   := and-expr ("or" and-expr)*
and-expr  := unary (("and" | "minus") unary)*               -- `and` binds tighter than `or`
unary     := operand adjunct*                               -- adjectives bind tightest
adjunct   := "within" operand | "over" WORD+ | "as" "of" STRING
operand   := "far" operand | "top" NUMBER operand | "atleast" NUMBER operand | "not" operand
           | "(" sentence ")" | "assume" hypothesis "in" sentence | clause
clause    := "near" STRING
           | "diffuse" [rel] "from" atom ["beta" NUMBER]
           | "reach" [rel] "from" atom ["depth" NUMBER] [direction]
           | "relate" atom
           | "trace" atom [direction]
           | "walk" "from" atom ["to" atom] "via" path ["depth" NUMBER]
           | "witness" STRING
hypothesis:= rel atom atom [("+" | "-") NUMBER] | "sever" rel atom atom | "contradict" atom atom
rel       := "S" | "F" | "D" | "C"
direction := "forward" | "back" | "both"
path      := a regular expression over S, F, D, C: letters, ( ) | * + ? {m} {m,n}
atom      := STRING | WORD                                   -- a path, a digest or a title
```

Kernels never appear as nouns in a sentence: every kernel the sentence needs is read as its column
at an anchor (QSA-3), which is what `near` and `diffuse` return; metrics appear only through
`diffuse`'s `e^{−βd}`. `supersede` as a hypothesis is parked (QSA-g): `D` at the note grain is not
in the universe yet.

**Precedence, tightest first:** adjectives; `and` (`⊙`, `∩`); `or` (`+`, `∪`); `then`. `not` and
`minus` apply to regions only: the cone has no complement, so `not` on a field or a kernel is a type
error that says so; `far f` is the bounded field's reversal, which the cone *does* allow at the
field level (a field is a column, not a kernel). `[DERIVED — §2.2]` Associativity and commutativity
of `and` and `or` (`Matrix.hadamard_comm`, `hadamard_assoc`; `add_comm`) justify the planner's
canonical order; `then` is not commutative and is not reordered. `assume` extends as far right as it
can and is parenthesized to continue a sentence.

**The adjectives' meanings.** `within R` is the mask: congruence by the projection onto `R` on a
kernel (QSA-2), zero outside `R` on a field, `∩ R` on a region. `as of c` is the **index** of the
reading (connectivity-instruments CN-1): it sets the cut every clause reads at and the `π_active`
the point window applies, and it is never a letter — a sentence that traverses lineage writes
`D`-moves (fiber-geometry §2.3-8's normal form). `via L` restricts a chain noun to the words of a
regular language over `Σ_move`, evaluated as the product walk with dead-state pruning (QSA-7).
`over Σ` names the strata; `with` sets the dials (`β`, `k`, `depth`, `direction`), whose defaults
come from the resolution ledger (§2.7).

**The connectives.** `and` is the Schur product on kernels and fields, intersection on regions;
`or` is the sum (renormalized on fields) and union; `then` evaluates its first clause to a region
and masks the second with it (`s then t ≡ t within region(s)`), the sequencing that lets a walk's
result bound a search. `[DERIVED]`

### 2.4 The typing

A sentence is typed before it is planned; an ill-typed sentence is unrepresentable, the MirrorView
move dn-capability-scope §2.4 made uniform, now for sorts as well as scopes.

**Sort rules** (the licences in §2.5): `and : Kernel × Kernel → Kernel` (QSA-1), `or` likewise;
`within : Region × Kernel → Kernel` (QSA-2); `at : Kernel × Atom → Field` (QSA-3); `top k`, `≥ t :
Field → Region` (QSA-4); `via : Path × Chain → Chain` (QSA-7); `e^{−β·} : Metric → Kernel` total on
the curve, hypothesis-guarded off it (§2.2); `then : Sentence × Clause → Clause` through the
region of the first.

**Scope rules.** Each clause requires the scope `required(verb)` of `core/query.py`, with the
noun's letter (below). A sentence's requirement is the **list** of its clauses' scopes — one per
clock plane, as a grant is a set of scopes, one per plane — and it is admissible iff every clause's
scope lies under some granted plane: **QSA-5**, the type checker is local
(`Sentence.admissible_and`, `admissible_or`, `admissible_seq`, `admissible_iff_clauses`
`[THEOREM]`). Nothing is joined across clocks, so a sentence that walks the commit plane and the
`N_s` plane needs a grant on both, exactly as the Ambassador's three planes give it. Mode is per
clause, `mode_of` of the clause's scope; **QSA-8** transcribes the table verb by verb
(`modeOf_required` `[THEOREM]`): SEARCH semantic, temporal with history; DIFFUSE, HYBRID, RELATED
and REACH structural; HISTORY temporal; ORIGIN causal; CAPTURE semantic.

**Rule NOUN: the letter in `E` is the relation walked, not the verb's name.** The table
QSA-8 proves reads two defects off the code, both the owner's to rule on (no `core/` change here):

- `required(DIFFUSE)` and `required(HYBRID)` are `E = {F}`, citation-structural, while `_diffuse`
  and `_hybrid` walk the **similarity backbone** `S` (`_note_graph`: cosine weights at the σ
  threshold). `S` is not an `E` letter; S-moves are licensed by kernel-carrying `Σ`
  (fiber-geometry §2.0). Typed by the noun, both clauses are `E = ∅` over `mirror_authored` —
  which `mode_of` calls **semantic**, and rightly: diffusion on the similarity graph is the thin
  graph-spectral locus *inside* the semantic cone (dn-core-query-protocol §2.2, the fable
  inversion). The verb table hides a type error the noun exposes. `[DERIVED — from QSA-8 and
  `core/query.py::_note_graph`]`
- `required(RELATED)` is `E = {F}` while `_related` walks the **signed relation edges**
  (`core/stores/edges.py`: supports, contradicts, contextualizes), which are in no class of
  `Σ_move`. Whether they are a fifth letter, an overlay class like `E_STAGED`, or a signed reading
  of `S` is the owner's (Parked, QSA-b).

**Rule HYP: a result under `assume` carries its assumptions in its type.** Beside `Inv` and
`Rate(κ)` (dn-capability-scope §2.3) the result typing gains **`Hyp(Δ)`**: the value of a sentence
evaluated under the hypotheses `Δ` in force. It is never `Inv` (`Sentence.not_isInv_assume`
`[THEOREM]`); the hypotheses of a connective are both halves' (`hyps_and`), so assumptions
accumulate and a bare number never comes out of a hypothetical. A clause under `assume` requires
the overlay stratum `hypothetical` in its `Σ` (`withOverlay`), so **a grant must name the overlay**
(`admissible_assume_overlay` `[THEOREM]`); the Ambassador's three planes do not, so it admits no
hypothetical today (`ambassador_no_assume` `[THEOREM]`), and `top()` omits the overlay (SCO-1),
so hypotheticals are opt-in for every client. The overlay does not change a clause's mode
(`modeOf_withOverlay`).

### 2.5 The composition laws — machine-checked

Each law is the licence for a rule of §2.3–§2.4 or a rewrite of §2.7. Declarations are in
`formal/Palace/Sentence.lean` (namespace `Palace.Query`), attacks in `formal/PalaceTest/Sentence.lean`
with the seed given; every attack has a negative control, a nearby false law that is refuted.

| id | law | Lean | attack · control | licenses |
|---|---|---|---|---|
| QSA-1 | `and` and `or` keep the cone: the Schur product and the sum of PSD kernels are PSD | `and_posSemidef` (Mathlib's `PosSemidef.hadamard`), `or_posSemidef` | 219 · 220 (symmetric factors of either sign) | the connectives' sort rules |
| QSA-2 | `within S` is the congruence by the projection onto `S`, so keeps the cone; it distributes over `and` and `or`; adjectives stack by intersection; `within univ` is the identity | `mask_eq_diagonal_mul_mul`, `posSemidef_mask`, `mask_hadamard`, `mask_add`, `mask_mask`, `mask_univ`, `mask_smul` | 221 · 222; 223 · 224 (no distribution over the matrix product) | the adjective's sort rule; the planner's pushdown and adjective merging |
| QSA-3 | the field of `and` at an anchor is the pointwise product of the fields, of `or` the sum, of `within` the masked field; a field is `K e_a` | `fieldAt_hadamard`, `fieldAt_add`, `fieldAt_mask`, `fieldAt_eq_mulVec` | 225 · 226 | columns instead of kernels at an anchor: HYBRID's score as `k_sem * k_struct`, `O(n)` not `O(n²)` |
| QSA-4 | a positive threshold commutes with `within`; the top-`k` does not (witness on `(3, 2, 1)`, `{1, 2}`, `k = 1`) | `thresh_maskF`, `topk_maskF_ne` | 227 · 228 (the non-rewrite, refuted) | masks pass thresholds; ranking is the last step of every plan |
| QSA-5 | admissibility is clause-wise; `assume` needs a granted plane naming the overlay; the Ambassador's grant admits no hypothetical; a result under `assume` is never `Inv` | `Sentence.admissible_and/or/seq/within`, `admissible_iff_clauses`, `admissible_assume_overlay`, `ambassador_no_overlay`, `ambassador_no_assume`, `isInv_and`, `not_isInv_assume`, `hyps_and`, `modeOf_withOverlay` | by `decide` and by structure | the local scope check; Rule HYP |
| QSA-6 | noninterference composes: when every clause evaluator reads only its declared strata (and the overlay only under the modality) and a hypothesis writes only the overlay, two stores agreeing on a sentence's reads evaluate it alike; a store's overlay is invisible to an `Inv` sentence | `Model.eval_noninterference`, `Model.hypothetical_notMem_reads`, `Model.eval_perturb_of_isInv` | over an abstract store | composition cannot widen reach; the firewall on the overlay |
| QSA-7 | a chain is admissible under a language iff the product walk from `(u, start)` reaches an accepting state; pruning at a dead state loses no admissible chain; more edges, more admissible chains, so a hypothetical edge only adds; the set `E` is the one-state automaton accepting `E*`, order-blind; the grounding production `S*·(C\|D)` is live off its dead state and accepts `SSC`, not `CS`, which `{S, C}` accepts | `admissible_iff_prodOk`, `prune_sound`, `admissible_mono`, `admissible_assume`, `TGraph.le_assume`, `ofSet_accepts`, `grounding_live_iff`, `grounding_words` | 229 · 230 (the set in place of the grammar); 231 · 232; 233 · 234; 235 · 236 | `via`; the product-automaton walker (fiber-geometry FG-1's design directive, FG-3's `[FROM MEMORY]` RPQ claim now checked on the finite model) |
| QSA-8 | the mode table, `mode_of ∘ required`, verb by verb | `modeOf_required` | by `decide` | the mode per clause; Rule NOUN's finding |
| QSA-9 | the response to a hypothetical edge: a rank-one update of `L` along `e_u − e_v`, of `L̄` along `e_u − σ e_v`; the energy never falls under a positive edge; adding weight lowers every effective resistance and removing it raises every one (CND-2 forward and backward); a new signed edge keeps the camps' balance iff its sign agrees with them; a contradiction closing a supported path is frustrated and lifts the zero mode (LAP-5, LAP-6); Sherman–Morrison for the inverse | `lap_assumeEdge`, `signedLap_assumeEdge`, `dotProduct_lap_le_assumeEdge`, `rEff_assumeEdge_le`, `rEff_le_assumeEdge`, `balanced_assumeEdge`, `contradiction_frustrates`, `pos_energy_of_not_balanced`, `inv_add_vecMulVec` | 237 · 238 (one arc alone); 239 · 240 (a present edge of the other sign); 241 · 242 (the wrong sign); 243 · 244 (the correction added) | §2.6's response classes; the compiler's symbolic answers |

The pattern is the ladder's (dn-mathematical-foundations §2.4): statement, attack, control, proof,
on exact arithmetic — ℚ and ℤ in the attacks, ℝ in the cone laws. What a Python build transcribes
from these laws is property-tested against the same statements (QL-1), and the laws enter
`docs/LAWS.md` as rows when code relies on them, under a prefix the owner rules (Parked, QSA-a).

### 2.6 Hypotheticals — `assume Δ in s`, the overlay, and the response

**The construct.** `assume Δ in s` evaluates `s` on the store perturbed by `Δ`, where `Δ` is one
of: `edge m a b ± w` (add or strengthen, or weaken, an edge of class `m`), `sever m a b`,
`contradict a b` (a negative signed edge), `supersede a by b` (a hypothetical `D`-arrow). The
perturbation is written to the **`hypothetical` overlay stratum** the scope algebra already has
(`Stratum.hypothetical`; `internal_actor`'s staging inserts it into `Σ`; `composed.py`'s `E_STAGED`
is its edge overlay), never to a base stratum; clauses under the modality read the overlay merged
with the base, clauses outside it do not (QSA-6). The result is **`Hyp(Δ)`**, and the **response**
is the pair, or the difference, of the two evaluations: `⟦s⟧(G ⊕ Δ)` beside `⟦s⟧(G)` — a difference
of fields or kernels, a symmetric difference of regions, the new words of a chain language. "Does
the meaning change?" is the response read on the right sort: a kernel's columns move continuously;
a region gains or loses members; a chain language gains words (never loses them, for an added edge:
QSA-7); and a sign structure flips or holds (below). `[DERIVED]`

**The response laws, by the class of the assumption** — the owner's correction made precise. CND-2
is a statement about *adding conductance of the sign the quadratic form already has*; the other
classes behave differently, and the compiler must know which class it holds:

| assumption | the update | what is forced | what is not | law |
|---|---|---|---|---|
| **add or strengthen** an edge, `+w` | `L ↦ L + w (e_u − e_v)(e_u − e_v)ᵀ`, rank one, PSD | the energy never falls; **every** effective resistance falls or holds; reachability and the admissible chains grow | the kernel columns move with no uniform sign | `lap_assumeEdge`, `dotProduct_lap_le_assumeEdge`, `rEff_assumeEdge_le`, `admissible_assume` `[THEOREM]` |
| **remove or weaken** an edge, `−w` | the same rank-one term, subtracted | **every** effective resistance rises or holds along paths through it — an assumption can raise resistance | — | `rEff_le_assumeEdge` `[THEOREM]` |
| **contradict**, a negative edge where there was none | `L̄ ↦ L̄ + w (e_u + e_v)(e_u + e_v)ᵀ`: rank one along the **sum**, the anti-alignment mode | the signed energy never falls; the cost of `u` and `v` *disagreeing* falls; if the sign agrees with the camps the graph stays balanced by them; if it closes a supported path the graph is frustrated and the zero mode is lifted: `L̄` is positive definite on a connected support — the meaning changes | aligned-mode quantities move with no uniform sign | `signedLap_assumeEdge`, `balanced_assumeEdge`, `contradiction_frustrates`, `pos_energy_of_not_balanced` `[THEOREM]`; LAP-5, LAP-6 |
| **mixed or phased** (several edges of both signs; a magnetic phase `θ`) | a sum of rank-one terms, each PSD in its own fiber | nothing uniform across pairs | — | the explicit response: Sherman–Morrison per rank-one term, `inv_add_vecMulVec` `[THEOREM]`; the phase fibers BRG-7 |
| **supersede** `a` by `b` | `π_active` drops `a`; a `D`-arrow in the overlay | the active view loses `a`; `history` gains a step | kernels change by removing a row and column: a submatrix, still PSD | `Matrix.PosSemidef.submatrix` `[ESTABLISHED]`; dn-temporal-retrieval-algebra §2.2 |

Two sharpenings. (i) "Does the meaning change" under a contradiction is **holonomy**: in the sign
fiber (`θ = π`, BRG-7) a negative edge is a transport `−1`, and the assumption changes the sign
structure exactly when the cycles it closes carry an odd number of negative edges (LAP-6; the
magnetic kernel theorem for general phases). The compiler answers it by a sign test, not by a
spectrum. (ii) The canonical curve's kernel `G_β = (D − z·w∘w^β)⁻¹` responds to one new edge at
`β = 1` by a rank-**two** update, `α (e_u − e_v)(e_u − e_v)ᵀ + α' (e_u + e_v)(e_u + e_v)ᵀ` with
`α = (δ + zδ²)/2`, `α' = (δ − zδ²)/2`, both nonnegative for `zδ ≤ 1`; so `G_β` falls in the Loewner
order and its exact response is two Sherman–Morrison steps. `[DERIVED — not machine-checked; a
QL-1 item]`

**The compiler's duty.** It classifies the assumption syntactically (one signed edge: which class;
several: mixed) and answers a sign question symbolically when a law of the table applies ("every
resistance falls", "the camps hold"), numerically otherwise, and says which it did. A symbolic
answer outside its class is a defect (QSF-6). `[INFERENCE]`

**Why this is the right home.** A hypothetical is the counterfactual overlay dn-fiber-geometry §5
anticipated (`E_STAGED` entering chains), the staging `internal_actor` already carries, and the
firewall the plane's noninterference (PLN-2) states for strata: QSA-6 is that firewall one floor
up, and QSA-5 is the capability discipline applied to it. An assumption can never launder into
belief: its result is `Hyp`, its writes are in the overlay, and the overlay is outside `top()`.
`[DERIVED]`

### 2.7 The compiler — a language with a grammar, precedents, a planner, and a refusal

The language is a language: its grammar is followed, its ambiguities are resolved by rule, and its
sentences are compiled into a plan. The six stages, each with its contract and the falsifier that
would catch it wrong:

| stage | contract | falsifier |
|---|---|---|
| **parse** | the grammar of §2.3 with its precedence; a parse error names the production that failed | a sentence parsed two ways |
| **elaborate** | fill the dials from the **resolution ledger** (below); resolve names to atoms; mark every reading of an ambiguous name | a default applied with no ledger entry |
| **check** | sorts (§2.4); scope, clause by clause (QSA-5); mode per clause (QSA-8); the bridges' hypotheses (§2.2); the hypothesis class (§2.6) | an ill-typed sentence that runs; an admissible one refused |
| **plan** | rewrite to normal form by the proved identities: push `within` to the leaves and merge adjectives (QSA-2); flatten and canonically order `and` and `or` (commutativity, associativity); take columns instead of kernels wherever the sentence has an anchor (QSA-3); keep `top k` and `≥ t` last, letting only thresholds pass masks (QSA-4); compile `via` to the product walk with dead-state pruning (QSA-7); hoist `as of` to one cut per sentence (the SLICE rule); choose the symbolic or numeric response for `assume` (§2.6) | a plan whose answer differs from the unoptimized evaluation (QSF-1) |
| **execute** | the clause evaluators of `core/query.py` over the stores, deterministic: same sentence, same corpus state, same answer | a run-to-run difference |
| **explain** | the plan rides with the answer (today's `operator` string becomes the plan tree); every hit carries provenance and status; an empty answer is loud and says which bound emptied it | an answer with no plan, or a silent empty |

**The optimizer is correct because each rule is a theorem.** The planner is an evaluator of a term
rewriting system whose rules are exactly the identities of §2.5; a plan denotes what its sentence
denotes by construction, and the one place a rewrite is *refused* — the top-`k` through a mask — is
refused by a proved counterexample. The rulebook is `formal/Palace/Sentence.lean`; the build
transcribes it (QL-1), and the transcription is property-tested against the same statements.
`[DERIVED]`

**Types, and the intermediate form.** Yes to both, and they are the same object read twice. The
*types* are the sorts of §2.2 (field, region, chain, witness inhabited; kernel and metric as the
columns and curves they are read through), the clause scopes `(Σ, E, T, A)` of the scope algebra,
and the result grades `Inv`, `Rate(κ)` and now `Hyp(Δ)` in `core/kernel/scope.py`. The
*intermediate form* is the typed term in normal form: `core/sentence/grammar.py` parses the
concrete syntax to the frozen dataclasses of `core/sentence/ast.py`; `core/sentence/types.py` sorts
the term and computes its clauses' scopes, modes and assumptions; `core/sentence/plan.py` rewrites
it to normal form and packages it with those as a `Plan`, a value — two sentences with the same
plan mean the same thing, and `Plan.explain()` is the artifact that rides with the answer;
`core/sentence/execute.py` evaluates the plan to values of its sort against a `Universe`
(`FieldV`, `RegionV`, `ChainsV`, `WitnessV`, `HypV`) and renders hits. No stage below the plan
reads the sentence's text, and no stage above the plan touches a store. `[DERIVED]`

**Precedents, two senses.** *Precedence* is the operator order of §2.3, fixed by the grammar.
*Precedents* are resolutions: when a sentence is ambiguous and the owner resolves it ("`recent`
means the projection-event clock, 14 days"; "`near` with no `over` means `mirror_authored`"), the
resolution is recorded in the **resolution ledger** with a default and a re-entry condition — the
parked-decision discipline applied to the language — and the elaborator applies it next time. A
precedent is a versioned artifact, so a change in it is visible and a query re-run under a new
precedent is a measured answer-drift (scoped-context-queries). `[INFERENCE]`

**The ambiguity policy.** Enumerate the readings; keep the well-typed ones; keep the ones the
client's grant admits (a sentence that is admissible one way only is not ambiguous for that
client); apply the precedents; if one reading remains, plan it; otherwise **refuse**, listing the
readings and the word that would pick one. Never a silent nearest-neighbour mush that looks like an
answer. At the surface, the refusal is a question back to the asker. `[INFERENCE — falsifier
QSF-3]`

**The natural-language front end is a client, not the compiler.** A model may *propose* a sentence
for a question; the compiler checks and plans it; the model never executes (the model advises, code
acts — scoped-context-queries). Whether that front end lives in the Ambassador or in a `/context`
skill agents call is Parked (QSA-f).

### 2.8 The falsifier battery — where a sentence must beat a word

The design is wrong if composition does not pay. At QL-4 the questions of §2.1's table, and others
the owner adds, are run three ways — flat `near`, the composed sentence, and the composed sentence
with its plan explained — and scored against **owner-endorsed answer sets** (a held-out arm, the
apophenia discipline of fiber-geometry §2.3-6). Each row's win condition:

| question | wins when |
|---|---|
| near *and* cited by | the endorsed cited notes rank above uncited near ones; flat search interleaves them |
| superseded since a cut, then the old version's citers | the sentence returns the set; flat search cannot |
| near `t₁` and far `t₂` | the endorsed set excludes the `t₂`-near notes flat search keeps |
| far in text, close by citation | the endorsed cross-domain imports appear; flat search returns none |
| chains via `S{0,2}·C+` | every returned chain exists with the claimed moves (the records certify it) and the endorsed explanation is among the top ranked |
| as of a past cut | the answer matches the snapshot's; the present differs |
| the onboarding question with bounds | the endorsed direction notes appear and the unbounded list's noise does not |
| a hypothetical's response | the symbolic sign agrees with the numeric response on every pair; the frustration test agrees with the spectrum |

A majority of ties or losses for the sentence retires the layer to a planning aid for the model
(QSF-5, the MFF-5 shape). `[INFERENCE]`

## 3. Consequences — what this note licenses, on the owner's merge

Five units, session-sized, dependency-ordered, split at graduation, named **QL-N** (query language)
per the unit-naming precedent. All land `proposed`; the owner's merge or instruction is the
readiness signal.

> **Owner's order, 2026-11-04:** *"continue with work aka feel free to start implementing the code
> itself (core), no pr yet"*, with *"feel free to also restructure the verbs"*. QL-1 and the core
> of QL-2 therefore began on the branch before ratification, as `core/sentence/` (grammar, ast,
> types, plan, algebra, automaton, execute, legacy, precedents), `Hyp` in `core/kernel/scope.py`,
> `docs/query/precedents.md`, and the tests named below. What is built reads the authored notes
> through `QueryEngine`'s note graph and the reference edges among them; `D` and `C` moves at the
> note grain are empty and the answer says so; `over` beyond the mirror and a past `as of` are
> refused, never emptied. The legacy `core/query.py` table is untouched: the Ambassador's MCP tool
> still speaks the eight words, and the two Rule NOUN defects stay there until QL-3 flips the
> surface.
>
> **QL-3 followed the same day, on the branch.** `palace query "<sentence>"` (`scripts/palace.py`;
> the logged ask, the rendering and the sensor in `core/sentence/surface.py`) runs a sentence
> read-only under the Ambassador's grant — the one grant in code; `--as <role>` labels the asker
> for the sensor and grants nothing. The Ambassador's MCP server gained the `query` tool with its
> `sentence` argument, listed and served only under `[query] sentences` (default `false`); the
> web bridge's static manifest follows the switch and is regenerated by `mind-palace mcp
> --manifest > edge/palace_tools.json`. The `/context` skill (`.claude/skills/context/SKILL.md`)
> owns the translation. The query log `data/query_log.jsonl` records every sentence either
> surface asks — role, strata, modes, outcome, the refusal's class — and `palace query --log`
> reads it as the sensor; an empty answer is its own outcome, the mechanical proxy for a failed
> translation (the brainstorm's open question on the sufficiency verdict, answered by default).
> Not built: a client holding the overlay (an owner act, §4 d); the legacy table's Rule NOUN fix
> (the owner's order); the battery (QL-4).

- **QL-0 — the design proved.** This note and `formal/Palace/Sentence.lean` (on this branch, green
  through `formal/check.sh`). Acceptance: the owner's merge, with the ⚑ track coordinate
  adjudicated. Nothing further to build.
- **QL-1 — the compiler as pure functions.** `core/query/` (TA-d's parked home, pinned here for the
  *sentence* layer; `X_cite` keeps its own ruling): the grammar and parser, the sort checker, the
  scope checker over the existing `Scope`/`Grant` (clause-wise, QSA-5), the mode per clause, the
  planner whose every rewrite is one of §2.5's laws, and the resolution ledger's reader. **Zero
  stores, zero behaviour change:** `core/query.py`'s eight verbs keep their answers bit for bit.
  Each transcribed law gets a property test against its Lean statement, and the laws enter
  `docs/LAWS.md` as rows with `Spec/` statements and the comparator's judgement (dn-mathematical-
  foundations §2.2 and §2.4). The two Rule NOUN defects land here **only by the owner's order**,
  as `type:defect` issues otherwise. Falsifier: QSF-1, QSF-2.
- **QL-2 — the executor.** Clause evaluators over the existing stores (the eight verbs reused as
  clause bodies), the mask/column/product/threshold operators, the product-automaton walker (the
  CN-7 generalization fiber-geometry §2.1 directed: the composability state typed as the automaton
  state from day one), the overlay for `assume` with its response classes. Falsifier: a plan's
  answer differing from the unoptimized evaluation on the battery's sentences.
- **QL-3 — the surface.** `palace query "<sentence>"`, read-only; a `/context <question>` skill that
  proposes a sentence and shows the plan; the resolution ledger as an authored file; the query log
  as a sensor (which strata serve which roles, which translations failed — the lessons loop of
  scoped-context-queries); the Ambassador's MCP tool gaining a `sentence` parameter behind a flag.
  Falsifier: QSF-3, QSF-4.
- **QL-4 — the battery run.** §2.8 against owner-endorsed answers, a finding either way.
  Falsifier: QSF-5.

**Explicitly NOT licensed:** any `core/` change before the owner's merge; the learned grammar
(FG-e); non-regular paths (FG-c); the `z` dial (TA-b); granting the overlay to any client (an owner
act, §4); the natural-language front end's home (Parked QSA-f).

## 4. Wiring & enablement

**How it wires:** `core/sentence/` (built 2026-11-04: `grammar.py`, `ast.py`, `types.py`,
`plan.py`, `algebra.py`, `automaton.py`, `execute.py`, `legacy.py`, `precedents.py`; `core/query/`
was taken by the legacy module's name), reading `core/kernel/scope.py` (which gains `Hyp`) and the
stores `core/query.py` already opens, through `Universe.from_engine`; `docs/query/precedents.md`
(the resolution ledger, authored, versioned with the corpus, pinned to its mirror by a test);
`palace query` in `scripts/palace.py` over `core/sentence/surface.py` (built 2026-11-04, QL-3:
`ask_logged`, `render_text`, the `QueryLog` and `summarize`); the `/context` skill under
`.claude/skills/context/` (built); the Ambassador's MCP server (`agents/ambassador/mcp.py`) with
the `query` tool and its `sentence` argument, gated by `Server.sentences`; `QueryConfig` in
`core/kernel/config/loader.py` — `[query] sentences`, default `false`; the web manifest
(`agents/ambassador/handoff.py::web_manifest`) following the switch, regenerated by `scripts/
palace_mcp.py --manifest`; the query log at `data/query_log.jsonl`; `docs/LAWS.md` rows and
`formal/Spec/` statements as the laws are relied on; `docs/tracks/query-language.md`. Tests:
`tests/unit/test_sentence_{grammar,types,plan,automaton,execute,surface}.py`,
`tests/property/test_sentence_laws.py` (each law against the Lean statement; each falsifier
checked against a mutated `core/sentence/`). `scripts/board.py`: zero lines. No daemon surface;
`mind-palace deploy` is not involved.

**What it takes to flip it on:** (a) QL-1 merges → the compiler is importable and property-tested;
no behaviour changes. (b) QL-2 merges → `palace query` runs read-only on the next merge, no switch.
(c) QL-3 merges → `palace query` is the owner's hand at once; the owner sets `[query]
sentences = true` in `config/ouroboros.toml`, regenerates the web bridge's manifest
(`mind-palace mcp --manifest > edge/palace_tools.json`) and restarts the stack to expose sentences
through the Ambassador on both transports; until then the eight one-word verbs are what it has. (d) Hypotheticals: the owner
grants a client a plane that names `hypothetical` — a `Grant` the Ambassador does not hold today
(`ambassador_no_assume`) — by hand, per client. (e) The owner adjudicates the ⚑ track coordinate
at this note's merge.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| QSA-a | the law-family prefix for the ledger rows | `QSA` in this note and the Lean docstrings, unbolded, no rows yet | the owner rules the prefix when QL-1's first row lands (the RSP precedent) |
| QSA-b | the move class of RELATED's signed relation edges | none; RELATED typed as the code types it | the owner rules: a fifth letter, an overlay class like `E_STAGED`, or a signed reading of `S` |
| QSA-c | `far f = 1 − f` on fields | allowed on bounded fields, refused on kernels | a field that is not a kernel column appears, or a consumer needs a kernel-level negation (none can exist in the cone) |
| QSA-d | the metric-to-kernel bridge off the canonical curve | refused unless `NegType` holds, with the violating vector shown; Schoenberg's direction cited | Schoenberg's "if" machine-checked, or a consumer needs `e^{−βd}` off the curve |
| QSA-e | the exact RSP-kernel response to an assumed edge | recompute `G_β`; symbolic sign only when §2.6's table applies | the rank-two decomposition is machine-checked (a QL-1 item) and the two-step update is cheaper on the live graph |
| QSA-f | the natural-language front end's home | a `/context` skill proposing sentences; the compiler checks | the Ambassador's tool gains `sentence` (QL-3) and the owner wants proposals there too |
| QSA-g | the encoding of a hypothetical supersession | the frame it sets is the index (`as of`); the lineage it adds is a `D`-move in the overlay (fiber-geometry §2.3-8's normal form) | a consumer needs the two to differ |
| QSA-h | `then`'s place in the precedence | loosest, not commutative, never reordered | a sentence where `then` inside `or` is the natural reading |
| QSA-i | non-regular `via` languages | regular only (FG-c stands) | a genuine soundness rule proven non-regular |
| QSA-j | which clock temporal adjectives default to | the clause's verb fixes it (`required(verb)`'s clock); `recent` needs a precedent | a precedent is recorded (QL-3) |

## Falsifiers — what would prove this design wrong

- **QSF-1 (a rewrite lies):** a planned sentence's answer differs from its unoptimized evaluation.
  Since every rewrite is a theorem, this is a transcription defect; two occurrences retire the
  planner to the identity until the transcription is re-tested law by law.
- **QSF-2 (the scope check is not local):** a sentence admitted though a clause's required scope
  lies under no granted plane, or refused though every clause's does. QSA-5 says this cannot
  happen in the model; in the code it is a defect against `Grant.admits`.
- **QSF-3 (a silent resolution):** an ambiguity resolved with no precedent recorded, or a bridge
  inserted the grammar did not name. The language then stopped being a language.
- **QSF-4 (laundering):** a `Hyp` result rendered as `Inv`, or an overlay write visible to a
  sentence outside `assume`. QSA-5 and QSA-6 say the model forbids both; in the code it is the
  plane's noninterference defect one floor up.
- **QSF-5 (composition does not pay):** the battery's majority is ties or losses for the sentence.
  The layer retires to a planning aid for the model; the proofs stay, as laws of the cone.
- **QSF-6 (a sign law outside its class):** the compiler answers "every resistance falls" for an
  assumption that removes weight or carries a sign. The owner's correction, as a test.

## Open questions

- Is a citation into authored ground an admissible terminal of the grounding production — does
  `S*·(C|D)` extend to `S*·(C|D|F)`? (fiber-geometry §5; the `via` adjective inherits the answer.)
- Should a chain crossing a node superseded at the read's cut be *hard*-required to carry its
  `D`-context in the sentence, or is that a narration rule? (fiber-geometry §5.)
- What are the two-point responses of the signed pseudo-inverse to a contradiction, pair by pair:
  the difference mode `(e_u − e_v)ᵀ L̄⁺ (e_u − e_v)` is unchanged on the symmetric path of three
  vertices (worked by hand); is there a general law, or only Sherman–Morrison?
- Which sentences does the Librarian's retrieval already approximate, so that it can become a
  client without a second machinery?

## Cross-references

**Formal (this branch):** `formal/Palace/Sentence/Defs.lean` (the model: nouns and masks, the
sentence syntax with `reqs`, `hyps`, `reads`, the evaluation model, `Move`, `TGraph`, `Auto`,
`ofSet`, `grounding`, `chainOk`, `prodOk`, `assumeEdge`, `dvec`, `modeOf`);
`formal/Palace/Sentence.lean` (QSA-1 to QSA-9, the declarations named in §2.5);
`formal/PalaceTest/Sentence.lean` (seeds 219–244); `formal/Palace/Scope.lean` (SCO-1 to SCO-8,
`build_ok`, `ambassador`); `formal/Palace/Rayleigh.lean::rEff_anti` (CND-2);
`formal/Palace/Balance.lean` (`Balanced`, `not_balanced_triangle_iff`, `zero_energy_iff_balanced`);
`formal/Palace/Retrieval.lean` (RSP-1 to RSP-4); `formal/Palace/NegativeType.lean` (`NegType`,
`bddAbove_negType`); Mathlib `Matrix.PosSemidef.hadamard`, `PosSemidef.add`,
`PosSemidef.conjTranspose_mul_mul_same`, `PosSemidef.submatrix`, `Matrix.add_mul_mul_inv_eq_sub`
(Woodbury, the general form of QSA-9's Sherman–Morrison).

**Code (read at `31ecabf`):** `core/query.py` (`Verb`, `required`, `mode_of`, `Grant`, `Query`,
`QueryEngine._search/_diffuse/_hybrid/_reach/_history/_related/_origin`, `_note_graph`,
`free_energy_distances`); `core/kernel/scope.py` (`Scope`, `Inv`, `Rate`, `req_admissible`);
`core/kernel/clearance.py`; `core/stores/edges.py` (the signed relation edges, QSA-b);
`core/graph/composed.py` (`E_STAGED`); `core/stores/reference_edges.py` (`X_cite`);
`core/reference_view.py` (`connected_set`).

**Design:** dn-core-query-protocol §2.1, §2.2, §2.5; dn-capability-scope §2.1–§2.4; dn-fiber-
geometry §2.0, §2.1 (the CN-5/CN-7 directive), §2.3 (FG-3, the chain language; FG-c, FG-d, FG-e),
§5; dn-temporal-retrieval-algebra §2.1 (A1), §2.2 (A2), §2.6 (A8), TA-b, TA-d; dn-magnetic-laplacian
(the sign and phase fibers; BRG-7); dn-mathematical-foundations §2.1, §2.2, §2.4; dn-connectivity-
instruments CN-1, CN-5, CN-7; dn-synchronic-diachronic-dreamer §2.9 (records, not causes);
docs/brainstorms/fiber-chain-grammar.md (the chain as a sentence; verb licensing);
docs/brainstorms/scoped-context-queries.md (bounds, loud failure, the lessons loop, the model
advises); docs/brainstorms/query-sentence-algebra.md (the warrant).
