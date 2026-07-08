---
type: design-note
id: dn-the-edge-model
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# The Edge Model — Knowledge Edges, Reasoning Paths, and Assertion Authority

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Cross-cutting. Refines how edges are typed and asserted across the
ingestion and reasoning layers; generalizes `ingest-identity-and-amendment.md`
§4A Constraints 2–3 and extends the sacred-boundary property "typed and
promotion-gated" (`the-sacred-boundary.md` §2.3) down onto edges.
**Reconciles with:** `ingest-identity-and-amendment.md` (§4A), `recursive-strata.md`
(edge budgets), `dialogue-ingest-and-recursion.md` (claim operations).
**Companion:** `supersession-lifecycle.md` — the dynamics (this note is the
statics). In the project's own terms: this note is *what a chair is* (the
taxonomy of relations); the lifecycle note is *how to build and use one*.

---

## 0. Why the edge model needed fixing

The graph's edges were specified only as "created, with a time property and a
support/contradiction property." That was a **complete** spec while every edge
was a two-place knowledge fact. It became **incomplete** the moment one edge type
— supersession — turned out to carry *intent* rather than state a *relation*. The
missing piece was never a property (sign, time, weight were always enough for
knowledge edges); it was the question of **who is entitled to assert an edge, and
against what authority**. This note supplies that.

## 1. Two edge classes, at two levels

### 1.1 Knowledge / fiber edges — the substrate
A two-place fact: `(u, v, rel ∈ {support, contradiction}, sign ∈ {+1, −1},
weight, time)`. Observer-independent — derived from **geometry**: embedding
proximity, co-occurrence, truth-functional relation. Computed identically on
every pass over the same content.

Budget categories (existing, `recursive-strata.md`):

- **grounding** — derived → authored anchor (K₀). Unbudgeted. Crosses layers by
  construction.
- **lateral** — derived → derived, same stratum. Bounded. Stratum-confined.
- **cross-stratum** — derived → derived across strata. Tightest budget.

### 1.2 Reasoning-path / supersession edges — built on the substrate
Irreducibly **three-place**: `(C, C′, warrant W)`, directed, carrying replacement
intent. Not a decorated edge — a small subgraph: the directed replacement
`s: C → C′` **plus** the fiber bundle `F(W) ⊆ {knowledge edges}` through which the
warrant reaches its context and scope. Formally a reasoning path is the pair
`(s, F(W))`. These necessarily **span strata** — a revise-and-ratify history
undulates across depth (see `supersession-lifecycle.md` §4.4).

### 1.3 The levels are not parallel
Fibers are the substrate; reasoning paths are **composed out of** fibers (`W` is
realized as `F(W)`). So the division of labor is **not** "agent A emits edge-type-1
and agent B emits edge-type-2 in parallel." It is: **substrate, then paths built
on it.**

## 2. Ownership is forced by failure mode

- **Geometry** (proximity / contradiction / co-occurrence) is observer-
  independent → a **deterministic ingest agent** computes it.
- **Intent** (C′ replaces C, warranted) is observer-**dependent**: geometry
  underdetermines it. Identical claims may **corroborate**, not supersede;
  contradictory claims may both be **held on purpose**. No deterministic pass can
  certify intent, because intent is not in the content.

Therefore:

- **Ingest lays fiber.** Deterministic, geometry-only. It asserts **no**
  supersession — it structurally cannot know intent, so it has **no supersession
  judgment to leak** into the Dreamer's later reasoning. This is why ingest must
  be the objective pass: not merely hygiene, but the *elimination of the bias
  vector*.
- **The Dreamer composes reasoning paths** on the fiber substrate. It does not
  refine an ingest supersession guess (there is none); it **constructs** the path
  the geometry made available. Knowledge → know-how, by different authorities.

## 3. The new field: assertion authority (a typing, not a property)

Every edge carries the authority entitled to assert it:

`authority ∈ { geometry, dreamer-proposed, verdict-certified }`

This is the sacred-boundary property *typed-and-promotion-gated* pushed down onto
edges: the graph types its **nodes** by stratum and its **edges** by who may draw
them.

- **geometry** — fiber / knowledge edges. Unconditional (geometry asserts them).
- **dreamer-proposed** — candidate supersession paths. Execute freely within the
  derived strata; **gated** when they would act on authored (depth-0) content
  (`supersession-lifecycle.md` §3).
- **verdict-certified** — a supersession ratified by an owner verdict. The
  transition `dreamer-proposed → verdict-certified` **is** the verdict event
  (`supersession-lifecycle.md` §2).

## 4. The algebra — which edges the balance math sees

Partition the edge set:

`E = E_geom ⊔ E_disp`

- **E_geom** — knowledge / fiber edges (`authority = geometry`). Signed. **Feeds**
  the balance math.
- **E_disp** — dispositional edges: note-version `supersedes` (Item 6, version
  store), claim-level `supersede` (reasoning paths, claim-op store), **and
  authored-historical `supersede`** (§4a). All **excluded** from the balance math.

The signed adjacency and Laplacian are assembled from **E_geom only**:

```
A_geom[u,v] = Σ_{e ∈ E_geom : e=(u,v)} sign(e)·weight(e)          (0 if none)
L          = D − A_geom          D = diag(Σ_v |A_geom[u,v]|)
```

Frustrated-triangle enumeration, diffusion clustering, and curvature all read
`L`. **E_disp never enters `L`.** This is the general form of §4A Constraint 2
(store separation) and Constraint 3 (version-`supersedes` vs claim-`supersede`
must not share a type or store): dispositional edges live in stores the balance
math has **no handle to**, so exclusion is **structural**, not a per-consumer
filter discipline. Any placeholder sign on a dispositional edge is inert — it is
never assembled into `A_geom`.

**Field-guide clause.** *Measures:* the semantic-tension structure of the
**current** claims. *Valid when:* `E_geom` contains only observer-independent
relations. *Falsifier:* adding or removing a dispositional edge changes any
clustering, frustration, or curvature result → `E_disp` has leaked into `A_geom`
→ the partition is not structural and must be fixed at the store boundary.

## 4a. A third dispositional edge: authored-historical `supersede` (PD11)

The founding corpus records "a later musing supersedes an earlier one." Apply the
**one-line test** — *does the edge connect two versions of one document, or two
documents?* A founding `supersede(A, B)` has `A`, `B` at **different `source_paths`**
(distinct authored notes), so it connects **two documents**. That rules out both
existing dispositional types:

- **not note-version `supersedes`** — that relation is *within one `doc_id`*, keyed
  `(doc_id, version_seq)` and derived from consecutive versions of the **same**
  document; it structurally cannot key a cross-document relation;
- **not claim `supersede`** — it carries **no warrant**, is **no reasoning act**, and
  **mints no derived alternative**; both endpoints stay authored (K₀).

So it is a **third E_disp member: authored-historical `supersede`** — both endpoints
K₀, both persist in the log, dispositional (never in `A_geom`). It gets its **own
store** keyed on the two authored digests — **not** the version store, and emphatically
**not** a synthesized shared `doc_id` (a fabricated identity is the
content-digest-as-version-key failure family, `ingest-identity-and-amendment.md` §4A C1).

**Ungated *only* when owner-declared — the write-path invariant.** The "no verdict
gate" property rests entirely on the assertion being **the owner's hand**. That holds
of the founding manifest / an owner CLI (`FoundingItem.supersedes` is an owner-authored
field, `scripts/ingest_founding.py`) — but it is **not intrinsic to the edge type**. A
supersession between two authored notes **can be machine-derived**: the unasserted-
supersession scorer `s(C, D)` (`supersession-lifecycle.md` §6) runs over authored
`E_geom`, and the curator's near-duplicate finder (`core/curator/curator.py`) pairs
authored notes — both propose "B revises A" with **no owner in the loop**. A
machine-derived edge that demoted an *active, retrievable* K₀ note would be derived
material silently hiding blessed content — exactly the demotion the blessing gate (I1a,
`supersession-lifecycle.md` §3) exists to stop. So ungated-ness is a property of the
**authority, not the edge type**. Resolution (PD11): the authored-historical store is
**owner-declared only** — its write-path admits no model / scheduler / dreamer source
(fail-closed), so its ungated-ness holds *by construction* (the capability-dissolution
move, `the-sacred-boundary.md` §3). A machine-inferred authored↔authored supersession is
a **dreamer-proposed candidate** routed through the proposed→certified blessing gate
(Item 8); it demotes an active note **only after an owner verdict**. Build:
`edge-and-supersession-build-plan.md` Item 8 / 8f + PD11.

## 5. The model at a glance

| Class | Arity | Authority | Feeds `L`? | Store |
| --- | --- | --- | --- | --- |
| knowledge / fiber (support, contradiction) | 2-place | geometry | **yes** | balance-edge store |
| note-version `supersedes` | 2-place, directed | geometry (file edit) | no | version store |
| claim `supersede` (reasoning path) | 3-place `(C,C′,W)`, directed | dreamer-proposed → verdict-certified | no | claim-op store |
| authored-historical `supersede` (§4a) | 2-place, directed | authored-ingest (owner's hand at authoring) | no | authored-supersession store |

Four edge classes across four stores; the balance math holds a handle only to the
first (`E_geom`). The three dispositional stores are structurally unreachable from `L`.

## 6. Reconciliation

Generalizes `ingest-identity-and-amendment.md` §4A (add a pointer there).
Extends `the-sacred-boundary.md` §2.3. The claim-`supersede` row is the vocabulary
of `dialogue-ingest-and-recursion.md` §4. Dynamics — states, gate, grounding
maintenance, decay math — are in `supersession-lifecycle.md`. Open questions live
in the accompanying builder prompt.
