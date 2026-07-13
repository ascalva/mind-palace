---
type: build-plan
id: bp-013
status: complete
design_ref:
  - docs/design-notes/code-observation-projection.md
contract: builder
write_scope:
  - "core/stores/reference_edges.py"
  - "ops/code_sensor.py"
  - "tests/**"
  - "docs/findings/**"
  - "docs/build-plans/bp-013/**"
session_budget: 1
cost:
  estimate: { model: fable, tokens: 250k }    # first fiber writer + isolation proof
  # Two builders across two sessions. Items 6-7 (store + extraction): prior session,
  # token usage NOT captured (delegated builder, no completion-notification recorded).
  # Item 8 (isolation proof) + finding renumber: resume builder, opus, 54k tokens,
  # 44 tool calls, ~350s. Whole-plan actual under estimate on the captured half.
  actual: { model: opus, tokens: 54048, tool_calls: null, duration_min: null } # PARTIAL — Item 8 + finding-renumber session only; the Items 6-7 session was never captured (journal :263-265, the recorded ledger gap). Late seal-fill, 2026-07-12.
depends_on: [bp-011, bp-012]
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/findings/finding-0021.md # code-as-corroboration — what these edges structuralize
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-c: Lane-1 reference edges — the first fiber writer, cross-stratum and balance-isolated

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from the ratified `code-observation-projection.md` — its **B-c**, Lane 1 only:
deterministic doc↔code references become typed edges in a dedicated store the balance
math cannot reach. This is the first edge writer in the system's history; the isolation
proof carries the plan. Lane 2 (semantic proposals) is NOT here. Readiness blessing is
the owner's hand.

## 1. Objective

Deterministic cross-references (validated patterns from bp-011's V4 inventory) are
extracted at projection time into a dedicated reference-edge store — geometry-class
authority, cross-stratum endpoints, provably invisible to every balance instrument.

## 2. Context manifest

1. `docs/design-notes/code-observation-projection.md` — §2.5 Lane 1 (the decision this
   implements, incl. the dedicated-store reasoning), B-c falsifier (verbatim §6).
2. `docs/build-plans/bp-011/inventory.json` + journal — the validated patterns + precision.
3. `core/stores/edges.py` + `core/complex/build.py:106-162` — the E_geom ⊔ E_disp
   partition and WHY these edges must NOT enter `A_signed` (`build_complex` holds no
   handle; keep it that way).
4. `tests/integration/test_edge_partition.py` — the bit-identical instruments test this
   plan's isolation proof mirrors.
5. `core/stores/code_observations.py` (bp-012) — the code-side endpoints.

## 3. Investigation & grounding

- **Q1 — why a new store rather than EdgeStore?** Pinned from the ratified note §2.5:
  the endpoints are CROSS-STRATUM (observed ↔ authored/curated); 𝔎|\_MR is authored-only;
  EdgeStore feeds `A_signed`. The separation pattern is `versions.py`'s: a store
  `build_complex` has no parameter for. _The code confirms:_ `build_complex(view, *,
edges=None, derived=None, sim_floor=...)` — no path for a second edge store; adding
  none preserves the isolation by construction.
- **Q2 — edge identity?** (source, target, ref_type, source_line) where source/target are
  typed endpoints: code side = (commit_sha, path, qualname); corpus side = note path or
  content digest. _The code does not settle digest-vs-path for corpus endpoints_ — the
  catalog keys docs by absolute source_path; design notes are not IN the catalog (not
  vault content). Default: repo-relative path for design-note targets, digest for
  vault-note targets when resolvable; builder confirms and journals.
- **Q3 — symmetry?** (note's open question) Default: store the direction as extracted
  (doc→code and code→doc are different assertions by different authors); consumers may
  symmetrize on read. Recorded, not silently chosen.
- **Q4 — reset semantics?** Corpus-layer (like bp-012's store): reset target.

**Additional risks or questions surfaced during reading:** extraction precision below
bp-011's measured bar on any pattern → drop that pattern, journal it — precision beats
recall for Lane 1 (a wrong deterministic edge is worse than a missing one; Lane 2 exists
for fuzzy).

## 4. Reconciliation

- The 2026-07-10 survey's standing fact ("nothing mints E_geom fibers; the balance math
  runs on recomputed cosine") → **cross-ref: extension** — remains TRUE for E_geom/
  A_signed after this plan (the new edges live outside it); the store docstring says so
  explicitly to prevent the finding-0013 wording class.

## 5. Write scope

Prose mirror: the new store, the sensor's extraction pass, tests (new files), findings,
own dir, plus the same one-line `reset_targets()` amendment mechanism as bp-012 Item 4
(`ops/lifecycle/launcher.py`, subject to the same blessing-time scope concurrence).
**Out of scope:** `core/stores/edges.py`, `core/complex/**` (NOTHING changes on the
balance side — that is the point), MirrorView/provenance, Lane 2 anything.

## 6. Interfaces pinned inline

Lane 1 (note §2.5, verbatim-condensed): _deterministic references … geometry-class
authority … BUT cross-stratum — they live in a dedicated reference-edge store the
balance math holds no handle to; `build_complex`'s signature stays untouched._

B-c falsifier (note §3.3, verbatim): _"any instrument result changes when reference
edges are added or removed."_

references_out element shape (note §2.3): `{type: note-citation | path-mention |
symbol-mention | design-ref, target: str, source_line: int}`.

## 7. Items

### Item 6 — the reference-edge store

- **Objective:** `core/stores/reference_edges.py` — typed directed edges, identity-keyed,
  append-only, open\_\* helper; docstring carries the Q1 isolation rationale.
- **Files:** store + new unit tests.
- **Acceptance test:** unit tests (idempotency, typed endpoints); core mypy-green;
  ratchet green.
- **Falsifier:** any import path from `core/complex/**` to this store (grep-asserted in
  the test).
- **Invariant(s):** `build_complex` signature untouched; import-firewall green.
- **Touches stored data?** new store only. **Parallelizable?** no **Depends on:** bp-012

### Item 7 — extraction at projection time

- **Objective:** the sensor's projection pass populates `references_out` (bp-011's
  validated patterns only) and mints the corresponding edges; attested within
  `project_observations`.
- **Files:** `ops/code_sensor.py`, tests (new).
- **Acceptance test:** fixture repo with planted references of each validated type →
  edges present with correct endpoints/lines; unvalidated patterns absent; idempotent.
- **Falsifier:** an edge minted from a pattern bp-011 marked below the precision bar.
- **Invariant(s):** Lane-1/Lane-2 separation — no model call anywhere in the path.
- **Touches stored data?** yes (new store; fixture-first).
- **Parallelizable?** no **Depends on:** Item 6

### Item 8 — the isolation proof

- **Objective:** the bit-identical instruments test: run the full instrument stack
  (balance, Laplacian, curvature, clustering) over a fixture corpus WITH and WITHOUT a
  populated reference-edge store — results identical to the bit.
- **Files:** new integration test mirroring `test_edge_partition.py`.
- **Acceptance test:** the test itself; it IS the B-c falsifier, automated forever.
- **Falsifier:** B-c's, verbatim (pinned §6) — any drift fails the build.
- **Invariant(s):** the E_geom ⊔ E_disp partition doctrine extends to the new store.
- **Touches stored data?** no (fixtures). **Parallelizable?** with Item 7
  **Depends on:** Item 6

## 8. Math carried explicitly

- **Reference edges as a typed relation OUTSIDE the complex** — _measures:_ referential
  entanglement between strata (which threads cite which code), the corroboration signal
  finding-0021 used manually. _valid when:_ extraction is deterministic and
  precision-gated (bp-011's bar); the store is unreachable from every balance
  computation (Item 8 proves it). _fails its keep if:_ the inventory's edge set never
  disambiguates anything a consumer cares about (the note's §2.7 clause-3 razor — then
  the store idles as recorded provenance, harmless, and B-d never builds on it).

## 9. Non-goals

Lane 2 (semantic proposals, correlator-family, blessing-gated); consumers of these
edges (B-d / Item 10 s(C,D) feature — their own gates); modifying ANY existing edge or
complex machinery; symmetrization (Q3 default recorded).

## 10. Stop-and-raise conditions

bp-011 reported no-signal (this plan should then be declined at the gate, not built —
halt if blessed anyway and the inventory says empty); corpus-endpoint identity (Q2)
turns out to need catalog changes (out of scope — finding + park); any Item 8 drift.

## 11. Parked decisions

| Decision           | Default recorded              | Rejected alternatives (why)                           | Re-entry condition                                        |
| ------------------ | ----------------------------- | ----------------------------------------------------- | --------------------------------------------------------- |
| edge symmetry      | directed as extracted         | auto-symmetrize (invents assertions)                  | a consumer needs the undirected view (symmetrize on read) |
| corpus endpoint id | path (notes) / digest (vault) | digest-everywhere (design notes lack catalog digests) | notes enter a catalog                                     |

## 12. Dependency & ordering summary

bp-011 (patterns) + bp-012 (endpoints) → this. Items 6 → 7 ∥ 8. B-d (the detangling
consumer) remains gated on Track D — the note's family ends here until then.
