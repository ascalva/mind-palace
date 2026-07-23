---
type: finding
id: finding-0168
status: routed
created: 2026-07-23
updated: 2026-07-23
links:
  - docs/findings/finding-0167.md                      # the mechanical reuse port this SUBSUMES
  - docs/design-notes/temporal-code-corpus.md          # amends D1/D2's row model (via the design gate)
  - core/stores/sourceset.py                           # "a source object IS the set of its idea-vectors" — completed by overlap
  - core/stores/vectorstore.py                         # the row model that changes
ftype: direction         # owner-ruled store model — the terminal form of the temporal corpus
origin_plan: orchestrator
route: orchestrator      # → the next Fable design pass (with the expert panel per the new gate)
resolution: null
---

# Owner ruling: vectors are the versioned entities — content-addressed chunk store + version membership, never duplicated rows

## What (owner, 2026-07-23, verbatim reasoning)

"The vectors themselves can be seen as versioned … a document can hold 5 vectors and maybe only
one changes — the current graph cut would reveal the document was superseded, with 4 original
vectors and one updated vector with a history — but that doesn't mean you keep storing those
unchanged vectors over and over; that would be a waste of storage and not an efficient retrieval
method."

The terminal store model this rules in:
- **Chunk-vector = content-addressed entity** (`layer + content_hash`), stored ONCE ever — deduped
  across versions, across reverts, across files with identical text.
- **Document version = a MEMBERSHIP record** `(path, blob_sha) → {chunk ids}` (relational, sqlite
  beside the lance table — lance does no joins). The graph cut at v resolves membership: shared
  ids = carried; new ids = the change.
- **Supersession at TWO grains:** the doc chain (blob→blob — bp-099, built) and the CHUNK-SLOT
  chain (L0a qualname / L1 symbol slots are stable across versions → per-slot vector history;
  L0b windows have no stable slot — their chunks enter/leave membership, honestly chainless).
- `current` + `digest` move to the membership relation; a denormalized `current`
  ("member of any HEAD projection") stays on rows for the cheap default filter.
- This COMPLETES the sourceset axiom: source object = set of its idea-vectors, where the sets
  OVERLAP and shared elements are stored once — group-by-digest becomes a membership join.

## Why it matters

1. **Storage:** the bp-099 row model duplicates every unchanged chunk per version (~4–5×
   redundant vector bytes at ~6 versions/file, growing with velocity).
2. **Retrieval (the stronger argument):** duplicated near-identical rows pollute the ANN space —
   historical neighborhoods fill with copies of one meaning. Deduped, each distinct idea is ONE
   point, and a hit natively answers "this idea lives in versions v3–v7 of X" — the chunk's
   LIFESPAN becomes first-class. Dissolves the near-duplicate-crowding risk recorded at the
   PD-B reversal.
3. **Subsumes finding-0167:** embed-reuse falls out of the model (landing a version inserts only
   MISSING chunks — embed cost ≈ distinct new chunks, automatically).

## Sequencing (recommendation recorded; owner may re-order)

**Deploy bp-099 as planned** — keep-and-link stops the delete-bleed NOW; the duplicated backfill
is regenerable waste, not debt (vectors are derived; reset+re-embed is doctrine). Design the
membership store at the next Fable pass (this finding + finding-0167 + dn-temporal-code-corpus
D1/D2 amendment, through the NEW expert-panel gate — core + systems + math auditors at minimum).
Then ONE rebuild — which under dedup embeds only distinct chunks, i.e. CHEAPER than the backfill
it replaces. Nothing done now is lost.

## Owner ruling addendum (2026-07-23, same thread): cross-file sharing + FORK semantics — ruled IN

Two documents sharing a chunk = ONE vector, TWO memberships. If the chunk changes in one file,
**the lineage forks**: only that file's membership swaps to the new vector, minting a supersession
edge to the new item scoped to ITS slot; the other file keeps pointing at the original. The formal
pin that makes this coherent: **supersession edges live on the SLOT-LINEAGE `(path, slot)`, never
on the vector** — a vector is immutable/eternal with no successor of its own; succession is a
property of occupancy chains. Edge identity = `(path, slot, old_hash → new_hash, at blob
transition)`. Consequences, all free: the shared past is a GRAPH FACT (two lineages intersecting
at a node — "historically once the same" is readable, not stored); parallel same-edits mint
parallel edges through the same nodes with distinct provenance; CONVERGENCE (later copy-paste
re-shares the node) joins as naturally as forks. The store is git's own model one level down:
content-addressed immutable nodes, memberships as trees, lineage per-path — self-similar with the
file grain (`digest` = blob sha; `content_hash` = chunk sha).

## Open for the design pass

- Membership store shape (sqlite table beside the catalog? its own db?), the denormalized-flag
  update discipline (flip on supersession), and crash consistency between lance + membership.
- Slot identity across layers: L0a/L1 slots = qualname/symbol (stable); L0b windows are slotless
  (membership-only, no chains) — confirm the slot vocabulary the edge schema carries.
- Whether the NOTE corpus adopts the same model when its keep-and-link lands (finding-0164 — one
  membership machinery for all lanes, or code-first).
- Chunk-slot supersession chains (L0a/L1) as first-class edges for the integrator's composed
  graph (a finer D-fiber than blob→blob).

## Routing

`direction`, owner-ruled → the next Fable design pass with the expert panel. Amends
dn-temporal-code-corpus D1/D2 through the proper gate (ratified note — owner banners at the
amendment's ratification).
