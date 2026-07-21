---
type: finding
id: finding-0144
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/build-plans/bp-084/plan.md         # S1 — the plan this blocks
  - docs/design-notes/inner-outer-core.md   # §2.6b the ruling; Appendix A the +7 preview
  - core/temporal_view.py                    # Issue A — importer of both moved symbols, OUT of write_scope
  - core/temporal/complex.py                 # Issue A — build_citation_complex seam (:34/:59)
  - core/temporal/boundary.py                # Issue A — supersession_poset seam (:25/:114)
  - core/recursion_ops.py                    # Issue B — ClaimOpStore inline sqlite (:53/:62)
  - core/stores/authored_supersession.py     # Issue B — DRY audit: distinct, does NOT cover claim_ops
  - core/integrator.py                       # Issue C — Integrator/build_integrator stay outer
  - scheduler/cron.py                        # Issue C — out-of-scope importer of core.integrator
  - ops/lifecycle/launcher.py                # Issue C — out-of-scope importer of core.integrator
ftype: spec-fidelity
origin_plan: bp-084
route: orchestrator        # needs a write_scope amendment + one design decision — beyond builder capability
resolution: null
---

# bp-084 (S1) cannot deliver the atomic +7 as written — three write-scope / grounding gaps

## TL;DR

The S1 fixed-point computation is sound (shedding the four seam files' store imports does promote
the seven modules). But the **clean-break repoint** (bp-065, no alias shim) and the **persistence
homes** cannot be executed inside the given `write_scope`. Two of the three seam-clusters — the
temporal family (5 of the 7 modules) and `recursion_ops` — are **hard-blocked**; the third
(integrator) is achievable but its promotion-set *name* is wrong. No code was written; the tree is
pristine. Stopping clean per the plan's §10 and the honesty mandate rather than forcing a broken
`INNER` or routing around scope-guard (which is active and correctly denies the out-of-scope edits).

Item 3 (the read-only DRY audit) is **complete** and recorded below — it is the one item that could
run.

## Issue A — temporal cluster BLOCKED: `core/temporal_view.py` is an importer of both moved symbols and is NOT in `write_scope`

`[GROUNDED]` The seam relocation moves `supersession_poset` (`boundary.py:114`) and
`build_citation_complex` (`complex.py:59`) → `core/temporal/acquire.py`, shedding
`from core.stores.versions import VersionStore` (`boundary.py:25`) and
`from core.stores.reference_edges import ReferenceEdgeStore` (`complex.py:34`). Clean-break
(plan §4, bp-065) forbids a re-export shim and requires repointing **every** importer in the same
commit.

The actual importers of the two moved symbols (grepped at HEAD `bf16865`):
- `core/temporal_view.py:56` — **top-level** `from core.temporal.complex import (… build_citation_complex …)`, used at `:187`.
- `core/temporal_view.py:340` — lazy `from core.temporal.boundary import … supersession_poset`.
- the write-scoped tests (`test_temporal_complex`, `test_temporal_view`, `test_temporal_operators`, `test_temporal_view_live`, `test_temporal_isolation`).

`core/temporal_view.py` is **not** in `write_scope` and `scope-guard.sh` is active — it denies the
edit. A top-level import of a symbol that has left `complex.py` is an `ImportError` at module load,
hard-breaking `core.temporal_view` and everything that imports it. The no-alias rule forbids leaving
a shim behind in `complex.py`/`boundary.py`.

**Plan grounding error:** plan §4 (line 130-132) names the importers as `core/temporal/atlas.py`
and `eval/harness/*`. Neither imports the moved symbols (verified — `atlas.py` imports
`core.temporal.spine` + `core.scope` only; no `eval/harness/*` hit). The real importer,
`core/temporal_view.py`, is omitted. Because `operators`/`superconnection`/the `temporal` package
`__init__` all sit atop `complex`, the cluster is all-or-nothing: **5 of the 7** (`core.temporal`,
`.boundary`, `.complex`, `.operators`, `.superconnection`) cannot shed within scope.

**Remediation:** add `core/temporal_view.py` to `write_scope`. Its two import lines then repoint to
`core.temporal.acquire` (top-level for `build_citation_complex`, lazy for `supersession_poset`) —
a mechanical two-line change, zero behavior change. (The `__init__.py` must also DROP the two moved
symbols from its imports/`__all__`, else the package re-imports them from `acquire` and stays outer.)

## Issue B — `recursion_ops` BLOCKED: no in-scope home for the `ClaimOpStore` persistence

`[GROUNDED]` To make `core.recursion_ops` inner it must shed `import sqlite3` (`:53`) and
`from core.stores.derived import DerivedStore` (`:62`). That relocates the concrete `ClaimOpStore`
(inline `claim_ops` sqlite table) plus the DerivedStore-consuming functions (`apply_operations`,
`stale_closure`, `open_claim_op_store`) out of the module. What remains inner is the pure
vocabulary (`OpKind`, `Supersede`, `AttachDefeater`, `RecordWarrant`, `ClaimOp`, `ApplyReport`,
`DialogueOp`, `DialogueAnalyzer`, `no_op_analyzer`, `_op_id`, `_utcnow`, `DIALOGUE_CONCLUSION`).

**Item 3 DRY audit — result: NO existing `core/stores/*` covers `claim_ops`.**
- `core/stores/authored_supersession.py` (`:14`, `:29`, `:169`) explicitly documents claim
  `supersede` (dialogue, `recursion_ops`) as a **distinct** edge type from its own owner-declared
  K₀↔K₀ authored-historical supersession — different semantics (owner-authorized, no warrant, mints
  no derived alternative). Not a drop-in.
- `core/stores/versions.py` = note-version `supersedes` over one `doc_id` — different relation.
- No `claim_ops` / `attach_defeater` / `record_warrant` table exists anywhere under `core/stores/`.

⇒ A **new** persistence module is genuinely needed (the owner's reuse-before-reimplement rule is
NOT breached — there is nothing to reuse; the plan's §10 stop-and-raise "a store already covers it"
does not fire). The correct home is a new `core/stores/claim_ops.py` — but `core/stores/**` is
**explicitly out of `write_scope`** (plan §5). The plan's contemplated in-scope homes (Item 3:
`acquire.py` / `integrator_math.py`) are both wrong: `integrator_math.py` is inner (cannot hold
sqlite); `core/temporal/acquire.py` is the *temporal* package — housing dialogue claim-ops there is
semantically incoherent (claim-supersede is explicitly NOT temporal/version supersession, §4A C3).

**Blast radius is small:** the only non-test references to `ClaimOpStore`/`apply_operations` are
comments/docstrings (`core/complex/build.py:150`, `core/stores/derived.py:226`,
`core/stores/authored_supersession.py`); the only real imports are in the write-scoped tests
(`test_dialogue_ops`, `test_edge_partition`).

**Remediation (design decision, orchestrator/owner):** create `core/stores/claim_ops.py` for the
concrete `ClaimOpStore` + `open_claim_op_store`, add it to `write_scope`, and decide whether
`apply_operations`/`stale_closure` (which need `DerivedStore` + the store) live there or in a small
outer `core/recursion_acquire.py`. Either way the pure vocabulary stays in `recursion_ops.py`
(inner), typed against local `Protocol`s if `apply_operations` is kept there.

## Issue C — integrator: the +7 names `core.integrator`, but the in-scope promotion is `core.integrator_math`

`[GROUNDED]` Plan §1/§6 and note §2.6b/Appendix A name `core.integrator` in the +7. Item 5's own
mechanism, however, keeps the `ledger`/acquisition in `integrator.py` (outer — §6 pins
"the ledger field stays with the OUTER acquisition part") and extracts the pure gauge instruments
(`IntegrationReport`, `CoverageGauge`) to `core/integrator_math.py` (inner). That promotes
`core.integrator_math`, **not** `core.integrator`.

Making `core.integrator` *itself* inner (the note's literal wording) is **unachievable in scope**:
it requires moving `Integrator`/`build_integrator` out of `integrator.py`, which breaks
out-of-scope importers `scheduler/cron.py:39` and `ops/lifecycle/launcher.py:238` (both import from
`core.integrator`; neither in `write_scope`). So the plan's *mechanism* is the only in-scope option
and is correct — the promotion-set **name** is the documentation slip.

This one is **builder-resolvable by annotation** and the split is cleanly doable in scope (create
`integrator_math.py`, repoint `integrator.py` + the two write-scoped integrator tests; external
importers untouched). It is recorded here (not committed solo) only because A and B block the atomic
+7 regardless — committing a lone +1 that also deviates from the named set would muddy the re-run.

**Resolution to adopt:** the +7 reads `core.integrator_math` in place of `core.integrator`; fix the
name in plan §1/§6 and note Appendix A when the plan is re-graduated. Final `|INNER|` unchanged (37).

## Recomputed expectation (unchanged count, one renamed member)

The achievable +7 → `INNER` (37 members, up from 30): `core.integrator_math`, `core.recursion_ops`,
`core.temporal`, `core.temporal.boundary`, `core.temporal.complex`, `core.temporal.operators`,
`core.temporal.superconnection`. The outer ratchet (`test_core_imports_nothing_outside_core`, 19)
is untouched — every moved import is core-internal.

## Why it matters

F10 exists for "a named module fails to enter after its seam sheds ⇒ coupling beyond the audited
seams." Here the modules *would* enter (the fixed-point simulation is right); what fails is the
**executability** of the clean-break repoint and the persistence homes inside the granted
capability. Forcing `INNER` (adding members whose importers still `ImportError`, or whose stores
have no home) would ship a red tree and violate the no-alias / scope-guard / no-silent-change
discipline. The plan needs a small, precise amendment, not a workaround.

## Re-entry condition

Re-run bp-084 once the plan is amended: (1) add `core/temporal_view.py` to `write_scope`;
(2) add a decided claim-ops persistence home (recommend `core/stores/claim_ops.py`) to
`write_scope`; (3) correct the +7 member name `core.integrator` → `core.integrator_math` in §1/§6
(and note Appendix A). With those three edits the plan is mechanically executable as designed —
Item 3's DRY audit above need not be repeated.

## Routing

`spec-fidelity` → **orchestrator** (not builder-self-resolvable): (1) and (2) are `write_scope`
amendments a builder cannot grant itself ("narrow the scope or file a finding — never route
around"), and (2) also carries a `design` sub-question (the claim-ops store's exact home/shape).
(3) is a pure annotation the orchestrator folds into the re-graduation.
