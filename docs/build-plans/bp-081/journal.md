# bp-081 journal

## 2026-07-21T02:40Z — minted at graduation (session-39, orchestrator)

Plan minted `proposed` from ratified `dn-synchronic-diachronic-dreamer` (§2.6, H-0 rider +
H-1). No build session yet. The spine invariant: NO promotion path from HYPOTHETICAL — its
violation is an immediate stop, never a gated variant. Parallelizable with bp-079 (disjoint
write_scope). Awaiting owner blessing.

## 2026-07-21 — Item 7 DONE (H-0: the HYPOTHETICAL stratum element)

**Contract read whole**: CONSTITUTION, CLAUDE.md, CONVENTIONS, plan (§2/§6/§7), journal.
Re-verified every §6 `path:line` at HEAD (`core/scope.py` Stratum:55-74, SLICE:527-536,
admissible/req:603-624; `core/graph/composed.py` whole; `core/mirror.py:86-94`;
`core/temporal/spine.py:159-274`). NOTE: `tests/unit/test_scope.py` is the CARRIED lattice-laws
file (375 lines, exists); `tests/unit/test_scope_laws.py` did NOT exist — created it as the
member-set pin the plan carries beside it.

**Change (additive only)**: `core/scope.py` — added `Stratum.HYPOTHETICAL = "hypothetical"` and
EXCLUDED it from `_BASE_STRATA` (so ⊤_Σ omits it). Design call, grounded in note §2.6-1 ("default
grants exclude it"): unlike the DIALOGUE precedent (a base stratum IN top()), the overlay must be
named EXPLICITLY — so "default grants exclude HYPOTHETICAL" is STRUCTURAL. It is NOT the denylist:
a scope that names it is admissible (≠ FOUNDATION). No operator (meet/join/⊑) touched; `_BASE_STRATA`
is top()'s membership, not a lattice operator. ⊤_Σ is byte-identical to before the element existed,
so the additive property holds and NO existing law weakened.

**Acceptance (all green, 41 passed)**: default grants exclude HYPOTHETICAL (top() + arbitrary
`.of(...)`); a multi-stratum {durable, HYP} read demands SLICE (COMMIT clock / explicit cut
satisfy it); `req_admissible` fails a read naming HYP under a grant (even ⊤_Σ) that omits it;
𝔇-subtraction unaffected; lattice laws hold over a HYP-carrying population. **Falsifier NOT
triggered**: no existing assertion weakened — only additive tests + the new pin file.

Ratchet: no new core→sibling import (staging/scope import only core+stdlib). Count unchanged.

## 2026-07-21 — Item 8 DONE (the staging store)

**New file** `core/stores/staging.py` — append-only, generation-clocked sqlite store. `N_hyp` clock
(genesis gen 0; each `stage` admission and each `tombstone` sweep is ONE monotone tick, logged in
`staging_generations`). `StagedItem`/`StagedRow` carry would-be stratum + would-be provenance +
content digest as ROW DATA (stratum ≠ provenance). Reads are generation-addressed (`read_at(g)`,
`subspace_at`) and reproducible. Expiry = tombstone (SD-d): `tombstone(row_ids)` ticks a sweep
generation and stamps `tombstoned_at_gen`; the row leaves `read_at(g'≥tick)` but survives in
`all_rows()`/at its pre-tombstone generation. Would-be HYPOTHETICAL/FOUNDATION refused
(`IllegalWouldBeStratum`). Imports ONLY core (config/provenance/scope) + stdlib.

**THE SPINE INVARIANT proven structurally** (`test_no_promotion_path_exists_by_api_surface_scan`):
(1) module AST import-scan → no durable-store module imported; (2) no public method named with a
promotion verb; (3) no method signature references a durable-store type. No `promote`/`untombstone`
inverse exists. Wall never orders (read SQL ordered by generation, not `at` — Law C4 asserted).

**Acceptance (11 passed)**: append advances generation monotone; batch shares one generation; rows
carry stratum/prov/digest; generation-addressed reproducible reads; tombstone-removes-keeps-record;
API-surface no-promotion scan; core+stdlib-only. **Falsifier NOT triggered** — no path copies a
staged row durable-ward (none is even reachable). Ratchet: unchanged (core+stdlib only).

## 2026-07-21 — Item 9 DONE (the overlay at the composed assembly)

`core/graph/composed.py` — refactored the assembly body into private `_assemble(nodes, edge_groups)`
(DRY: `compose` and `compose_staged` both route through it, the flatten unchanged). Added
`E_STAGED` constant and `compose_staged(..., staged_edges, *, grant)`: a THIRD class at ASSEMBLY,
gated by the Σ-visibility test — `grant` MUST name `Stratum.HYPOTHETICAL` else `StagedGrantRequired`.
New import `from core.scope import Scope, Stratum` (core→core; NO ratchet change).

**Acceptance (12 passed; 8 existing UNMODIFIED)**: staged-free `compose_staged` is bit-identical to
`compose` (sim + edge_classes); a staged overlay presents the MirrorGraph surface and the REAL
σ*/conductance run over it (staged bridge joins two components, chain a-b-c-d, conductance > 0);
E_STAGED retained in per-class attribution (both-class pair keeps both tags, max weight);
**FALSIFIER tooth** — `compose_staged` under a durable-only grant raises `StagedGrantRequired`
(staged rows unconstructable at assembly without the capability). **Item 9 falsifier NOT triggered**
— no existing guard assertion changed.

## 2026-07-21 — Item 10 DONE (expiry sweep + isolation battery) + finding-0130 (Q3 park)

**New `ops/staging_sweep.py`** (machinery-side, read/tombstone-only): `run_sweep(store, *, now_wall,
dry_run=True)` finds live rows whose wall TTL passed `now_wall`, and (non-dry-run) tombstones them at
one fresh N_hyp tick. `resolve_wall_to_generation(events, wall) -> GenerationInterval` is the D8
resolver: INTERVAL-VALUED + AMBIGUITY-WIDENING (non-monotone/skewed bookmarks widen the bracket and
set `ambiguous`; a wall beyond every bookmark is `future`). Wall enters ONLY the resolver + the
per-row TTL threshold — never orders rows (Law C4).

**Q3 STOP-AND-RAISE honored → finding-0130 (spec-defect, route: builder).** Trough registration
needs `scheduler/cron.py` + `router._PINNED_KINDS` + launcher cadence — ALL outside write_scope. Did
NOT widen. Landed `run_sweep` as a callable; PARKED the wiring. Re-entry: a scheduler-scoped plan
(natural home bp-082) wires it as a pinned trough job like `chat_events`/`integrate`.

**Acceptance (12 passed)**: sweep advances generation + tombstones expired, gone from EVERY readable
view (default + per-subspace + pinned-current); only passed TTLs expire; no-TTL rows never expire;
dry-run reports without ticking; resolver interval-valued (clean bracket) + ambiguity-widening
(skew) + future-marking; Law C4 (generation-ordered reads). **Isolation BATTERY (§2.6-4)**: durable
zero-scan after a full staged dispatch (recording durable fake sees zero writes; no staged digest
leaks); `MirrorView` + staged row → `NonMirrorRowError` (asserts against core/mirror.py, no edit);
cut-less composed read → `SliceError`. **Falsifiers NOT triggered**: no expired item visible after
sweep; no wall ordering. Ratchet: `ops/staging_sweep.py` is ops→core (correct arrow) — no change.

## 2026-07-21 — ALL ITEMS DONE; local CI gate green; ready for orchestrator review

Six-leg gate on branch (all green):
- `ruff check .` → All checks passed!
- `scripts/check_imports.py` → Import firewall (I2): OK — core imports no zone/networking module.
- `mypy` core modules (scope, staging, composed, staging_sweep) → Success, no issues (4 files);
  new/changed test files (5) → Success, no issues.
- `ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK.
- `pytest` green gate (live/podman/needs_* deselected + the two policy deselects) →
  **1742 passed, 11 skipped, 21 deselected** (baseline 1707 → +35 new: H-0/8/9/10 acceptance).

**Ratchet (finding-0103): UNCHANGED.** None of the touched core files appears in
`test_core_imports_nothing_outside_core` — staging/scope/composed import ONLY core + stdlib
(core→core), sweep is ops→core (correct arrow). No new core→sibling edge.

Findings filed: **finding-0130** (spec-defect, route: builder) — Q3 sweep trough-registration
parked (scheduler internals outside write_scope); `run_sweep` landed as a callable.

Scope confirmation: wrote ONLY write_scope files + journal + `docs/findings/finding-0130.md`.
Untouched (as pinned): `MIRROR_READABLE`, `core/mirror.py` (asserted against, never edited), every
durable-store writer, the scheduler package, all design notes. The scope OPERATORS in `core/scope.py`
(meet/join/⊑) were not touched — only the additive enum element + its `_BASE_STRATA` exclusion.

THE SPINE INVARIANT holds: NO promotion path from HYPOTHETICAL exists — proven by the Item 8
API-surface scan (no durable-store import, no promotion-verb method, no durable-store-typed
signature) and the Item 10 durable zero-scan battery. No "gated" promotion was written (none exists).

## 2026-07-21 ~06:15 ET — SEALED (orchestrator, session-39)

Merged to main `--no-ff` (single-writer). Builder commit 8f70eca touched ONLY its 9 write_scope
files + journal + finding-0130 (verified via `git show --stat`); disjoint from bp-080 (census.py/
interpreters.py). Base at 01e006b — 3-way merge kept main's bp-080 + brainstorm captures.

Orchestrator re-ran the FULL 6-leg gate on main: ruff clean · import firewall OK · mypy (scope/
staging/composed/staging_sweep) Success · type_gate OK · pytest **1769 passed, 10 skipped, 21
deselected**. finding-0103 ratchet UNCHANGED (all touched core files import core+stdlib only;
staging_sweep is ops→core). Green.

cost.actual: opus (claude-opus-4-8, tier verified), 217,049 tok, 100 tool_calls, ~23 min, 0.87×.
Status ready→complete. Worktree removed.

H-0+H-1 done: Stratum.HYPOTHETICAL (additive, excluded from _BASE_STRATA ⇒ default grants exclude
it structurally) + append-only generation-clocked staging store (spine invariant PROVEN by
API-surface scan — no promotion path) + the overlay at the composed assembly (E_STAGED, grant-gated)
+ the expiry sweep (D8 wall→generation, Law C4) + the isolation battery.

⚑ finding-0130 (spec-defect, builder-lane, OPEN): the sweep's trough-tier scheduler WIRING is out
of scope — run_sweep landed as a tested callable, wiring parked. Orchestrator annotation: re-entry
is NOT bp-082 (fixture-based) but a future "make the subspace live" plan (Track-G-style: build dark,
wire when the owner turns HYPOTHETICAL on). Harmless now — nothing stages rows in the live daemon.

Unblocks bp-082 (H-2, the capstone — depends on bp-079✓ + bp-081✓).
