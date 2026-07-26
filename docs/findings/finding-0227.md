---
type: finding
id: finding-0227
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/dn-supervision-and-liveness.md   # §2.3 the capability reframing; §3 Consequences
  - docs/build-plans/bp-110/plan.md                    # §6 ReadOnlyRows; Item 5's tier-4 ratchet
  - scheduler/worker.py                                # the ratchet's subject
  - scripts/check_imports.py                           # the ratchet
  - docs/findings/finding-0225.md                      # the same species of wiring hand-off
ftype: discovery
origin_plan: bp-110
route: orchestrator
resolution: null
---

# Every lane module imports a store CLASS at module level, so no lane can move into the worker
# until it takes its stores by protocol — the refactor §2.3's capability claim requires but does
# not price

## What

bp-110 Item 5 landed the tier-4 ratchet: `scripts/check_imports.py` walks
`python -m scheduler.worker`'s transitive first-party import graph and fails if any node binds a
store-opening name, module-level or function-local. The worker is green today because it registers
no lane.

Surveying what happens when a lane *does* register — every lane module named in
`dn-supervision-and-liveness` §2.3's handler table imports a store **class** at module scope:

| lane module | module-level store imports |
|---|---|
| `core/ingest/sync.py:34-37` | `RawStore`, `VaultCatalog`, `VectorStore`, `VersionStore` |
| `core/ingest/index.py:23-24` | `SourceSet`, `VectorStore` |
| `core/ingest/code_corpus.py:50` | `core.stores.vectorstore` (grouped import) |
| `core/dreaming/dreamer.py:35-37` | `DerivedStore`, `EdgeStore`, `VectorStore` |
| `core/curator/curator.py:39-41` | `RawStore`, `DerivedStore`, `VectorStore` |
| `ops/chat_sensor.py:60-61` | `RawStore`, `ChatlogStore`, `open_chatlog_store` |
| `core/librarian/librarian.py:33,36` | `RawStore`, `VectorStore` |

**These are type annotations, not constructions** — every one of these modules already takes its
stores by *injection* (`Librarian(store=…, raw=…)`, `build_librarian` constructs at
`librarian.py:207-219`). The import exists so the parameter can be annotated. But the ratchet
cannot tell an annotation from a construction, and it must not try: a bound name is a reachable
constructor, and the whole point of tier 4 is that it re-derives the property from the AST rather
than trusting intent. `from core.stores.vectorstore import VectorStore` genuinely does put a store
constructor one call away from the worker's compute half.

So the mechanical consequence is uniform: **a lane migrates into the worker only after its module
stops naming a concrete store type and takes `ReadOnlyRows` (bp-110 §6) instead.** That is a real
refactor of the lane module's signatures — small per site, but touching every store-typed parameter
in the module — and it is a *precondition* of the migration, not a follow-up.

This is why bp-110's own proof lane is a worker-side bring-up handler rather than the production
`ambassador_task` compute half: `librarian.py`'s module-level `VectorStore`/`RawStore` would red the
ratchet, and `scheduler/interface.py` and `core/librarian/` are both outside bp-110's write_scope
(§5, "this plan owns the seam and NO lane"). Moving them would have been the finding-0191 failure
repeated inside the plan written to prevent it.

## Why it matters

**This does not trip bp-110 §10's STOP** ("a store-opening import proves *unavoidable* in the
worker's graph"), and the distinction is the whole content of this finding. The imports are
avoidable — `ReadOnlyRows` is exactly the seam that avoids them, and §2.3's claim that "the compute
half can be constructed without one" survives intact. Nothing built is wrong and no design line
needs revisiting.

What it changes is **cost, and therefore plan sizing** — which is why this routes to the
orchestrator rather than being silently absorbed:

1. **bp-113 and bp-114 are each larger than "register a compute handler".** Each carries a
   protocol-parameterization pass over its lane module first. `core/ingest/sync.py` alone names
   four store types; `dreamer.py` and `curator.py` three each. The note's §3 Consequences sizes the
   wave as "per-lane builder plans with disjoint scopes" without naming this pass.
2. **`ReadOnlyRows` may be too narrow for some lanes, and that is discoverable now rather than
   mid-build.** §6 pins three verbs (`all_rows`, `rows_for_source`, `search`). `sync.py` also
   reaches `VaultCatalog` and `VersionStore`; `dreamer.py` reaches `EdgeStore`. Those are separate
   read surfaces the pinned protocol does not cover, so a lane needing them needs either a second
   protocol or a wider one — a design question that belongs at the lane plan's graduation, where a
   §6 pin can be written, not to a builder discovering it against a red ratchet.
3. **The DRY risk finding-0225 names applies here too.** Three lanes independently inventing three
   read protocols is the duplication class the owner treats as a defect. One protocol per read
   surface, pinned once, is the reuse target — and `ReadOnlyRows` is where it starts.

## Re-entry condition

**Nothing is parked; bp-110 is unaffected and proceeded.** Re-enter when **bp-113 or bp-114 is
picked up** (whichever is first). That plan's §2 manifest must audit its lane module's store-typed
parameters against `scheduler/worker.py`'s `ReadOnlyRows`, and its §6 must pin either (a) that
`ReadOnlyRows` suffices for that lane, or (b) the additional read protocol the lane needs — named
and shaped in the plan, never inferred by the builder. If (b), the protocol lands in
`scheduler/worker.py` beside `ReadOnlyRows` so there is one home for read surfaces, not three.

A useful pre-check for whichever builder arrives: `uv run python scripts/check_imports.py` reports
the exact offending lines the moment a lane is registered, so the refactor's scope is machine-
readable rather than estimated.

## Routing

`codebase` in mechanism, **plan-sizing in consequence** → **orchestrator**, following
finding-0224's precedent (a codebase/spec-fidelity fact whose consequence is not a builder's to
decide). The technical resolution is entirely a builder's — the refactor is mechanical and needs no
owner input — but *how much work bp-113/bp-114 actually are*, and whether `ReadOnlyRows` needs
widening before either is graduated, is a graduation-time judgment. No `owner-questions.md` entry
is warranted: no ruling is required, only that the next graduation reads this before sizing.
