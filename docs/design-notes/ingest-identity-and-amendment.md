---
type: design-note
id: dn-ingest-identity-and-amendment
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Ingest Identity, Deduplication, and Amendment

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Inbound channel — ingestion (structural layer). Governed by the
sacred-boundary principle (`the-sacred-boundary.md`): the ingestion point is
sacred, and sanctity here is achieved by dissolving the mutate-the-core
privilege, not by granting it.
**Reconciles with:** `recursive-strata.md` (supersession edges), the provenance-
migration `--apply` work, the dual-scale / group-by-digest reframing.

> **Refinement (July 2026, post-builder-review):** §4's supersession-edge
> mechanics are specified and corrected in §4A below — the edge must be keyed on
> version identity (not content digest) and stored outside the balance-fed
> semantic edge projection. See §4A and open questions Q7–Q8.

---

## 1. The separation that dissolves the append-only/dedup tension

The apparent conflict between append-only provenance and deduplication is an
artifact of conflating two objects at different layers:

- the **log of ingest events** — where the append-only invariant belongs;
- the **derived index that instruments read** — where it does **not** belong.

Once separated, the "extremely privileged permission to modify the authored
layer" is unnecessary. That permission was the dangerous capability; the right
structure removes it.

## 2. Authored layer = append-only log of events

The authored layer is an append-only log of *events*, not a mutable store of
*current beliefs*.

**Re-ingesting an unchanged note** is a second event with the same content-hash.
It is never deleted — "ingested twice" is historical truth and provenance must
record it faithfully. But document **identity** is a canonical object keyed by
content-hash; the second event references the existing identity rather than
minting a new one. One document, two occurrences.

This answers "did I re-ingest?": yes — recognized by hash, logged as an
occurrence, no new identity.

## 3. Derived index = content-addressed projection

The embedding index is a **derived projection** of the log — the same discipline
as MirrorView, one level down. It holds **one point per canonical chunk, keyed by
chunk-content-hash**, not one point per ingest event.

Exact re-ingestion therefore **coalesces on the way in**: it resolves to the
existing point and adds nothing. The false-density pathology — duplicated points
inflating a region and manufacturing false importance — cannot arise, because the
index is content-addressed rather than occurrence-addressed. The problem is
dissolved at the key, not repaired after the fact by deletion.

## 4. Modified note = versioned amendment

The modified-note case is a **versioned amendment**:

- stable document identity (source path or a stable doc-id, **not**
  content-hash);
- new content as a new **version**;
- the log records **supersession**: version *v2*, hash *H₂*, supersedes *v1*.

Provenance is **enhanced**, not destroyed: a full version history plus a
supersession edge is strictly more provenance than before.

An amendment is a **chunk-level diff**, not a wholesale re-embed:

- unchanged chunks (same chunk-hash across versions) keep their existing points
  and fingerprints — no re-embed;
- changed and new chunks get new points;
- removed chunks are marked superseded.

The stable parts of a frequently-edited note therefore never accumulate
duplicates.

## 4A. Supersession edge realization — constraints (post-builder-review)

The running implementation records a version-supersession edge on amendment. The
following constraints correct how it must be keyed and where it must live. They
are the resolved design for these points, subject to the schema reality the
builder confirms in Q7. Constraints 2–3 are generalized into a principled edge
taxonomy in `the-edge-model.md` (E_geom ⊔ E_disp; note-version `supersedes` and
claim `supersede` are distinct dispositional edges, both excluded from the
balance Laplacian); the supersession *dynamics* live in `supersession-lifecycle.md`.

**Constraint 1 — key edge endpoints on version identity, not content digest.**
Supersession holds between *versions*, and version identity is not content.
Keying endpoints on raw-content digest collides on revert: editing v1 → v2 →
back to v1's exact bytes makes the third version's digest equal v1's, folding the
chain into a cycle and merging two distinct versions into one node. Key endpoints
on a version identity (stable doc-id + monotonic version-seq, or a per-version
surrogate). A revert is then v2 → v3 with v3 distinct from v1, the chain stays
linear, and **no cycle-guard is wanted** — a guard that rejected the revert edge
would refuse to record truthful history and violate the append-only property.
Content-hash stays the correct key for the vector projection (§3); version-id is
the correct key for the edge. Two layers, two identities; the implementation
correctly used content-hash for vectors and wrongly borrowed it for edges.

**Constraint 2 — version history lives in the provenance layer, not the
balance-fed edge projection.** Version-supersession is a primary provenance fact;
the signed-edge graph (support / contradiction) is a derived semantic projection
consumed by the balance math (signed Laplacian, frustration enumeration,
diffusion clustering). These are different layers (§1, §6), and co-locating them
leaks the separation at the storage layer. Do **not** rely on the balance
consumer filtering `supersedes` out by rel-type — that makes correctness a
discipline every current and future consumer must honor, and the placeholder
`sign=+1` becomes a live hazard the moment any consumer sums signs over all
edges. Put version history in a structure the balance math is structurally unable
to read. See Q8.

**Constraint 3 — version-supersession and claim-supersession are distinct
relations.** `dialogue-ingest-and-recursion.md` §4 defines a claim-level
`supersede(C, C′, W)` that carries a warrant and is a reasoning act. Amendment
`supersedes(v1, v2)` is note-version-level: no warrant, a file edit. They are
orthogonal — a note can be amended without superseding any claim (a typo fix),
and a claim can be superseded without editing any note (a dialogue concludes a
claim is wrong). They must be distinct rel-types in distinct structures.
Separating version history per Constraint 2 is therefore a **prerequisite** for
the dialogue operation vocabulary, not independent of it.

**Constraint 4 — "removed chunks are marked superseded" (§4) means excluded from
the active projection, not lingering.** This is an active-view-correctness
requirement, independent of edges: a removed chunk's vector must not remain live
in the active projection, or it inflates density for content that no longer
exists — the exact pathology §3 and §7 prevent. Per-chunk supersession *edges*
are a separate, deferrable provenance-granularity feature: raw blobs of every
version are kept, so chunk-level removal history is reconstructible by diffing
raw without per-chunk edges. Confirm the active-view exclusion; defer the edges.

**Ordering authority.** The current version is determined by the version sequence
(monotonic version-seq / append-log position), never by walking edge direction.
Edges are provenance annotations over an already-ordered sequence; consumers
order by version-seq. This is the deeper reason no cycle-guard is needed: order
never depends on edge topology, and Constraint 1 keeps cycles from arising in the
first place.

## 5. No mutate-the-immutable operation exists

Corrections are **appends** (a supersession edge) **plus re-materialization** of
the derived view. The privilege required is the ordinary append privilege plus
view-rebuild — **not** a special capability to reach into and alter the authored
layer. The scary permission was never needed; this is the capability-dissolution
test passing for the ingestion boundary.

## 6. Two views over one log

- The reasoning complex reads the **active projection**: current versions,
  deduplicated by chunk-identity, so diffusion, SBM, and curvature see clean
  density and never the double-ingested log.
- Provenance queries read the **full historical log**.
- The Dreamer's MirrorView is content-deduplicated and version-current by
  construction; the auditor sees complete history.

The math is protected without lying about history.

## 7. The dedup boundary rule (it inverts — get this right)

Coalesce by **content identity** (same bytes = one fact = one point). **Do not**
coalesce by **semantic proximity.**

Two distinct authored artifacts that happen to agree are **corroboration** —
independent provenance asserting the same claim is evidentiary weight the system
*should* feel. Collapsing them by embedding-distance would erase it. The "false
sense of importance" worry is correct for *occurrences of a single artifact* and
wrong for *agreement between distinct artifacts*.

> **Rule: dedup exactly at authored-artifact identity, never by proximity.**
> Two occurrences of one note inflate density spuriously → coalesce.
> Two notes that agree inflate it correctly → keep both.

## 8. Open question (requires reading the code)

- **Q1.** Does the librarian key the derived embedding index by
  **chunk-content-hash** or by **ingest occurrence**? Cite the schema and the
  write path (`path:line`). State plainly whether the §3 content-addressed-
  projection model is already satisfied, partially satisfied, or absent. This is
  the single place the current code either already gives this model or quietly
  does not, and it touches stored data, so it must be resolved before any corpus
  work and coordinated with provenance migration `--apply`.
- **Q7 (version identity).** Is there a version identity independent of content
  digest? Are supersession edges currently keyed on content digest or on version
  identity? Cite (`path:line`). If versions are distinguished only by content
  digest, the revert case is unrepresentable (v1 and a later identical version
  are the same object) and a version-identity key must be added — a foundational
  change to coordinate with provenance migration `--apply`.
- **Q8 (store separation).** Does the balance-math consumer (signed Laplacian /
  frustration / diffusion) read the same store that holds `supersedes` edges, and
  if so does it exclude them structurally or only by rel-type filter? Cite the
  consumer's rel-type selection. Confirm `supersedes` and its placeholder sign
  never enter the signed-graph computation. Target: version history in a separate
  structure the balance math cannot read.

## 9. Reconciliation

Consistent with the append-only-log / derived-index separation and the
versioned-amendment direction already in the project's learnings, and with the
supersession edges in `recursive-strata.md`. The builder should locate the
existing passages this extends and propose a cross-reference (or a partially-
superseded banner if any existing text conflicts), per repository discipline.
