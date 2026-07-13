---
type: finding
id: finding-0070
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/design-notes/core-query-protocol.md
  - docs/design-notes/external-grounding.md
  - core/stores/reference_edges.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The read-only index-query slice is a thin façade; its SOLE blocker is the §2.4 boundary ruling

## What

Scoping the near-term "live self-index" query surface (resume-brief queue-item 2 — orch/
builders query the live v2 `reference_edges` graph instead of grepping) established, against
the code (Explore sweep 2026-07-13):

1. **The read query logic already exists.** `core/stores/reference_edges.py` exposes the
   full read surface, zero-model and deterministic: `all(source_ref=…)` ("what X cites"),
   `all(target_ref=…)` ("who cites X" — the finding-0059/0061 warrant), `all(direction=…)`,
   `for_commit(sha)`, `count()`. No schema/store/projection change is needed.
2. **The store is payload-free by schema.** Columns: `edge_id, commit_sha, ref_type,
   source/target_kind/ref/detail, source_line, created_at` — paths, citation-types, line
   numbers. **No note text, no mirror content.**
3. **The only gap is an agent-facing façade.** `reference_edges` is today *code-anchored +
   agent-unreachable* — nothing in the agent/tool layer imports the store; the Librarian
   (`core/librarian/librarian.py`) does not touch it. The build is a thin read-only façade
   over the three methods above + optionally a bounded `neighbors(ref, depth≤N)` traversal
   at the agent tier (the balance-isolation invariant forbids `core/complex` from building a
   Laplacian on these edges — `tests/integration/test_reference_edge_isolation.py`).
4. **The full `dn-core-query-protocol` note is NOT required for the conservative read.** Its
   fable-gated parts — the §2.2 kernel algebra, the §2.1 general capability-scope type
   system, the §2.4 *general* boundary formalism, the `w(d,a,c)` weight — are all for the
   *richer* surface, not the conservative read.
5. **The §2.4 plane-crossing concern is structurally defused for this subset:** the read is
   local (no network → Inv 1/2 untouched), read-only (no propose/write), over a payload-free
   store (nothing to leak → the mirror firewall cannot be crossed — there is no payload in
   the schema to cross it with). Safety is a property of the store's construction, not a
   policy the caller must remember.

**The sole remaining blocker is the §2.4 boundary ruling** — the *precedent* of a build-time
plane opening a core-owned store at all. It is `dn-core-query-protocol §1.3 item 1`'s
opus-provisional, fable-MUST-finalize call.

## Why it matters

The near-term context-cost win (context-economy: search-by-context-burn is O(context × turns
× tier); a live-index lookup is not) is buildable in a small sonnet plan the moment §2.4 is
settled — the substrate is ready and the façade is trivial. Recording this now means the
Jul-17 fable session inherits a sharp, pre-scoped question ("bless the conservative read-only
build-time→core-store boundary; the payload-free/read-only/no-network subset is safe by
construction — is that sufficient, or is the general scope type-system a prerequisite?")
instead of re-deriving the whole surface. It also prevents a future session from
over-estimating this as a large build.

## Re-entry condition

**The Jul-17 fable-vet of `dn-core-query-protocol` settles §2.4 (the sacred-boundary
ruling).** Owner decision (2026-07-13): park the read-only slice until then rather than
graduate it fast under `dn-external-grounding §3.1` — the boundary precedent warrants
fable + owner scrutiny. On that settlement: ratify `dn-core-query-protocol` (or graduate the
read slice under whichever note carries the ratified boundary ruling), then mint the small
façade plan (façade over `ReferenceEdgeStore.{all, for_commit, count}` + bounded neighbor
walk; checker = the §2.6 deterministic repo-grep-at-HEAD oracle, which also turns
finding-0059/0061 staleness into a monitored sensor-fidelity number).

## Routing

`design | direction` → orchestrator. No `owner-questions.md` entry needed — the owner has
already ruled (park to the fable-vet). This finding is the input to `dn-core-query-protocol
§2.4` for the Jul-17 fable session; feed it in alongside the §1.3 item list. Not promoted
(no design change yet — it sharpens an existing note's parked item); flips to `resolved` when
the façade plan is minted post-vet.
