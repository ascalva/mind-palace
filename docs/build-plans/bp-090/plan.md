---
type: build-plan
id: bp-090
track: inner-outer-core
status: ready
design_ref:
  - docs/design-notes/inner-outer-core.md
contract: builder
write_scope:
  - core/**
  - tests/**
  - eval/**
  - ops/**
  - scheduler/**
  - agents/**
  - scripts/**
  - config/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/inner-outer-core.md
  - docs/findings/finding-0148.md
  - docs/build-plans/bp-083/plan.md
  - docs/build-plans/bp-089/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0148.md
---

# Build Plan — K1: the born inner ring moves to `core/kernel/**` (M2 wave 1, physical migration)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from the **ratified** `dn-inner-outer-core` §2.7-M2 + §3 ("licenses the
M2 wave plans and the M3 flip upon ratification + the §2.7 entry gates"). Entry gates
evaluated at graduation (finding-0148, re-verified here): (a) ratification landed `fbea48d`
2026-07-21; (b) K1's membership (the born set) is stable across ≥2 sealed plans (bp-083 born,
bp-089 unchanged — S1 only added); (c) no open plan names any K1 module; (d) K1 is
**import-closed alone** — an AST closure scan at graduation (HEAD `438cef2`) found zero
core-rooted imports leaving the set. Investigation and planning produced this; implementation
proceeds item-by-item on owner approval. The `proposed → ready` blessing is the owner's, by
hand; no agent flips readiness.

## 1. Objective

Physically relocate the 30-member born inner ring to `core/kernel/**` (module rename
`core.X → core.kernel.X`, subpaths preserved) with repo-wide repoint, both ratchets green at
every commit and zero behavior change.

## 2. Context manifest

1. `docs/design-notes/inner-outer-core.md` — §2.4 (enforcement artifacts A–D), §2.7 (target
   layout, the move-commit contract, wave rules), Appendix A — the governing design.
2. `core/rings.py` — the live map (37 members; the S1 seven marked by comment) + the
   names-not-paths discipline (`:17-18`).
3. `tests/unit/test_inner_ring.py` — the equality/direction/honesty tests every commit must
   keep green; also carries module-name strings to rename (Item 4).
4. `tests/unit/test_core_self_containment.py` — the outer ratchet. **READ-ONLY (pillar 2).**
5. `docs/findings/finding-0148.md` — why this plan exists; the gate evaluation.
6. `docs/build-plans/bp-089/plan.md` — the S1 precedent for map-diff discipline.
7. `scripts/check_imports.py` + the local CI gate list (§6) — the per-commit gate.

## 3. Investigation & grounding

- **Q1 — exact K1 membership.** `INNER` (`core/rings.py:51-89`) minus the S1 seven (marked
  `:70,75,82-86`) = **30 modules**: `core`, `core.agent_scope`, `core.complex`,
  `core.complex.balance`, `core.complex.curvature`, `core.complex.hodge`,
  `core.complex.laplacian`, `core.complex.support`, `core.complex_types`, `core.config`,
  `core.config.loader`, `core.constitution`, `core.ingest`, `core.ingest.amend`,
  `core.ingest.chunk`, `core.ingest.logseq`, `core.ingest.pipeline`, `core.ingest.verify`,
  `core.matching`, `core.mirror`, `core.provenance`, `core.recursion`, `core.rings`,
  `core.scope`, `core.selfcheck`, `core.stores`, `core.stores.rawstore`,
  `core.stores.sourceset`, `core.typedshims`, `core.velocity_view`. Of these, **`core` (the
  root `__init__`) does not move** — it is the parent package; 29 file/package moves.
- **Q2 — closure.** AST scan at `438cef2`: every core-rooted import inside K1 resolves into
  K1 — the wave is import-closed against kernel-so-far = ∅ (§2.7's wave rule satisfied).
  Recompute at build HEAD (Item 1) before any move.
- **Q3 — map survives renames mechanically.** `core/rings.py:17-18`: the map "names modules
  (`"core.scope"`), never paths — so an M2 directory move … is a mechanical rename here."
- **Q4 — test domains are move-neutral.** The outer ratchet's domain is `core.rglob("*.py")`
  (§2.4-C — "every file under `core/` stays bound … no matter which directory M2 moves it
  to"); the inner test recomputes over `core/**` likewise. Files stay under `core/` ⇒ both
  domains preserved.
- **Q5 — importer surface (recompute at HEAD).** At graduation: **291 files** import K1
  modules — tests 155, core 89, scripts 19, ops 9, eval 8, scheduler 8, agents 2, config 1.
- **Q6 — string references (the F8 scanner-blindness class).** Exactly 4 `.py` files carry
  K1 module names as *strings*: `core/rings.py` (the map itself),
  `tests/unit/test_inner_ring.py`, `tests/integrity/test_eval_isolation.py`,
  `tests/integrity/test_shadow_isolation.py`. Item 4 re-greps at HEAD (mock.patch targets /
  importlib strings are invisible to both scanners — note §2.1's stated limitation).
- **Q7 — split packages (two physical homes, anticipated by §2.7).** `complex`, `ingest`,
  `stores`, `config`, `typedshims` move only their inner members; each outer residue needs a
  package `__init__.py` so its outer submodules stay importable. The existing (pure, inner)
  init text moves with the kernel home; the residue receives a NEW minimal docstring-only
  init. New pure modules (kernel + residue inits) enter the computed fixed point ⇒ the map
  must claim them (§2.4-B1's new-module rule) — the map GROWS by the new package modules;
  the exact count is computed, not asserted (expect ≈ +6–12).
- **Q8 — `core.config` is `core/config/` (in-core), NOT the top-level `config/` package.**
  The top-level `config/` (defaults.toml, `config/loader.py`) is untouched as a *source*;
  it appears in write_scope only because 1 file there imports a K1 module (repoint only).
- **Q9 — `core.rings` moves too** (→ `core.kernel.rings`): an inner member left outside the
  kernel tree would break the M3 end-state (map == kernel-tree). Its importers (the inner
  test; any script) repoint like everything else.

**Additional risks surfaced during reading:** the honesty-guard test asserts known-OUTER
exclusions (`sealing`, `stores.chatlog`, `stores.vectorstore`, `temporal.spine`,
`complex.spectral`) — all stay at unchanged paths, so it is move-neutral; verify green, don't
edit assertions. Editor/CI configs referencing `core/` paths (mypy/ruff sections in
`pyproject.toml`) — `pyproject.toml` is NOT in write_scope; if a per-path override names a
moved file, STOP and raise (§10) rather than widen scope silently.

## 4. Reconciliation

- `core/rings.py` — "The `INNER` set below was recomputed at build HEAD (bp-083)…" →
  **[cross-ref: extension]**: the K1 move commit renames the 30 entries to `core.kernel.*`,
  adds the new package modules the computation claims, and appends a `# K1 (bp-090)` note to
  the module docstring recording the wave. Every membership change is that one reviewable
  diff (§2.4-A), forced by the equality test.
- `dn-inner-outer-core` §2.7 sketch ("K1 — the born-29") → **[cross-ref: extension, no note
  edit — A8]**: actual born set is 30 (Appendix-29 + `core.rings` self-claim, recorded in
  rings.py:42-43); this plan's manifest is the computed truth per the note's own
  "expectation, not authority" discipline (F6).

## 5. Write scope

Front-matter globs = the moved subtree (`core/**`), the map, and every package that imports a
K1 module (291 files at graduation: tests, core, scripts, ops, eval, scheduler, agents,
config) — repoint-only outside `core/**` and `tests/**`. Deliberately OUT:

- `tests/unit/test_core_self_containment.py` — in-glob but **forbidden** (pillar 2: the outer
  ratchet file is unchanged by this program). Repoint edits to it are impossible by
  construction (it imports no core module by name — it scans paths).
- `ops/import_lint.py` `NETWORK_MODULES` — read, never edited.
- `eval/golden/**`, `eval/golden.py`, `CONSTITUTION.md` — foundation denylist (structurally
  denied regardless of the `eval/**` glob).
- `docs/**` — historical `path:line` mentions in notes/findings stay as written (they are
  commit-anchored readings; rewriting history is not repointing).
- `pyproject.toml`, `.claude/**`, `config/defaults.toml` values — not granted; a needed edit
  there is a stop-and-raise.

Carried test files: `tests/**` broadly, because 155 test files import moved modules (the
retrofit rule) — including the 3 string-ref test files (Q6) that pin module names.

## 6. Interfaces pinned inline

**The move-commit contract (dn-inner-outer-core §2.7-M2, verbatim obligations per commit):**
`git mv` (subpaths preserved: `core/scope.py → core/kernel/scope.py`,
`core/complex/laplacian.py → core/kernel/complex/laplacian.py`, `core/stores/rawstore.py →
core/kernel/stores/rawstore.py`) + repo-wide repoint + map rename + **outer count
unchanged** + inner test green + the full local CI gate. No re-export facades/alias shims —
ever (owner no-alias-wrappers rule; bp-065 clean-break precedent).

**The map declaration (`core/rings.py:32-39,51-89`):** `MATH_3P = {"numpy","scipy"}`,
`PLUMBING_STDLIB = {"sqlite3"}`, `INNER: frozenset[str]` of module names. Post-K1 the set
contains: `core`, the S1 seven at unchanged names, the 30 renamed to `core.kernel.*` (minus
`core` which stays, plus `core.kernel` and the computed new package inits).

**The full local CI gate (per-commit):** `ruff check` · `uv run scripts/check_imports.py` ·
mypy (scripts floor 0; tests baseline 69) · `ops.type_gate` · `uv run pytest` with the two
standing deselects (the finding-0103 ratchet's node-CI deselect pair). pytest alone is NOT
sufficient.

**Inner-test obligations (§2.4-B):** B1 computed==declared both directions; B2 direction law
(outer never imported by inner); B3 honesty guard (known impurities excluded; set
non-trivially large).

## 7. Items

### Item 1 — recompute and pin the manifest at build HEAD (read-only)

- **Objective:** re-run the fixed point + K1 closure scan + importer/string-ref greps at the
  build's HEAD; record the exact move list, importer file list, and expected post-move map.
- **Files:** `docs/build-plans/bp-090/journal.md` only.
- **Acceptance test:** journal carries the three lists; `uv run pytest
  tests/unit/test_inner_ring.py` green before any change; recomputed map == rings.py (37).
- **Falsifier:** recompute ≠ the declared 37, or K1 closure violations found ⇒ the map is
  stale (F6) or a coupling landed since graduation — STOP, file a finding, re-graduate.
- **Invariant(s):** none touched (read-only).
- **Touches stored data?** no. **Parallelizable?** no. **Depends on:** none.

### Item 2 — the kernel skeleton + the moves, commit-wise green (reversible)

- **Objective:** `git mv` the 29 movable members into `core/kernel/**` in package-clustered
  commits (suggested: leaf modules · complex · config · ingest · stores · typedshims ·
  rings), each commit carrying its slice's repo-wide repoint + map rename + residue/kernel
  `__init__` additions, and passing the FULL §6 gate (both ratchets, CI) — never a red
  intermediate state. Fewer, larger commits are acceptable iff each is green.
- **Files:** moved modules (old→new paths), `core/kernel/**/__init__.py` (new), residue
  package inits (new), `core/rings.py`, the ~291 importer files.
- **Acceptance test:** after the final commit — `uv run pytest` green; inner-ring test green
  with the renamed map; outer ratchet count **identical** to Item-1's baseline;
  `git grep -nE '\b(from|import) core\.(scope|mirror|provenance|complex|ingest|stores\.(rawstore|sourceset)|config|agent_scope|matching|recursion|selfcheck|velocity_view|complex_types|constitution|typedshims|rings)\b'`
  restricted to `*.py` returns zero old-name imports.
- **Falsifier:** any commit where the outer count moves (a violating module moved, or a move
  minted a violation) or the inner test cannot be made green by map-rename alone ⇒ the wave
  is not the clean fixed-point slice the design claims — halt, revert the commit, finding.
- **Invariant(s):** no-laundering clause §2.4-D1–D4; no alias shims; zero behavior change
  (pure relocation — no source-line edits beyond import statements and the map).
- **Touches stored data?** no (code tree only; stores untouched).
- **Parallelizable?** no. **Depends on:** Item 1.

### Item 3 — the string-reference sweep (F8 class) (reversible)

- **Objective:** update module-name *strings* (patch targets, isolation-test lists, the map)
  that the import repoint cannot see; re-grep at HEAD for stragglers.
- **Files:** `tests/integrity/test_eval_isolation.py`, `tests/integrity/test_shadow_isolation.py`,
  `tests/unit/test_inner_ring.py`, plus any fresh grep hits.
- **Acceptance test:** `git grep -l '"core\.\(scope\|mirror\|provenance\|…\)"' -- '*.py'`
  (the Item-1 pattern) returns only files whose remaining strings are deliberate (documented
  in the journal); full suite green.
- **Falsifier:** a runtime/test failure traced to a stale string module path after this item
  ⇒ the sweep pattern was incomplete; extend the pattern, re-run, journal the miss.
- **Invariant(s):** isolation tests still assert the SAME properties (renamed, not weakened).
- **Touches stored data?** no. **Parallelizable?** no. **Depends on:** Item 2.

### Item 4 — the end-state verification pass (read-only)

- **Objective:** prove the wave landed whole: full local CI gate; both ratchets; the
  §2.7-M2 per-commit contract audited over the actual commit list; kernel-tree == the moved
  30 minus `core`.
- **Files:** journal only.
- **Acceptance test:** every §6 gate command exits 0; `ls core/kernel/` matches the manifest;
  outer count unchanged from baseline; the seal-ready checklist in the journal.
- **Falsifier:** any gate red, or the map contains a `core.kernel.*` entry with no file (or
  vice versa) ⇒ the equality test's domain missed something — stop, finding, no seal.
- **Invariant(s):** all of §6. **Touches stored data?** no.
- **Parallelizable?** no. **Depends on:** Items 2–3.

## 8. Math carried explicitly

N/A — no mathematical object implemented; the ring predicate and its tests exist (bp-083);
this plan relocates files under an unchanged computation.

## 9. Non-goals

No K3 members move (the S1 seven stay put — bp-091). No K2 packaging-debt remedies. No edits
to the outer ratchet, `NETWORK_MODULES`, or any ratified note. No M3 flip. No doc rewrites.
No behavior change of any kind. No alias/re-export shims. No new tests beyond renames (the
enforcement already exists and is the point).

## 10. Stop-and-raise conditions

Item-1 recompute mismatch (F6). Any outer-ratchet count delta at any commit. Any edit that
would touch `tests/unit/test_core_self_containment.py`, `ops/import_lint.py`,
`pyproject.toml`, or a foundation-denylist path. A discovered import of a K1 module from
`edge/` (bright-line implications — file the finding; do not repoint silently). Any need to
split the wave (spec-defect finding + park; the orchestrator re-graduates — never re-split
mid-build). Any blessing (none exist in this plan's path — refuse if one appears).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| M3 flip accounting for `core` (root init) + residue inits (map == kernel-tree modulo them) | out of scope; map stays authoritative | folding the flip into K1 (conflates a move with a predicate change) | M3's own plan, when map == kernel-tree and outer ratchet == 0 |
| K2 (the 13 lax-inner packaging-debt promotions) | untouched | riding them on K1 (each needs its own remedy first — §2.7-M1) | each remedy lands, then moves as a later small commit |
| historical `core/...py` path-mentions in docs/ | left as written | mass doc rewrite (rewrites commit-anchored history; the reference sensor keys readings by commit) | never — by design |

## 12. Dependency & ordering summary

Items strictly linear 1→2→3→4 (each gate feeds the next). This plan conflicts with
everything (repo-wide repoint): `parallelizable_with: []`; no other plan may be in flight.
**bp-091 (K3) is strictly after this seals** — bp-090's seal is also the second sealed plan
that closes K3's §2.7 stability window. CI-1 (dn-code-ingest-pipeline, when ratified) should
be sequenced after K1 or accept one extra repoint — orchestrator's call at that graduation.
