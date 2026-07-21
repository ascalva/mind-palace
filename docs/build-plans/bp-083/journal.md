# Journal — bp-083 (M0)

**Status:** proposed (awaiting owner `proposed → ready` blessing, by hand).
**Design ref:** `docs/design-notes/inner-outer-core.md`.

## Graduation — 2026-07-21 (session-40)

Minted `proposed` by `/graduate` over the three ratified notes (`fbea48d`). Decomposition and
grounding done in a single orchestrator context (subagent-assisted decomposition parked, §14);
seams/instruments re-verified on disk at HEAD `d08da37`. No implementation performed —
graduation implements nothing (A4). The plan's §3 carries the grounding citations; §6 pins the
interfaces verbatim so a fresh builder infers no design.

Next: owner blesses `proposed → ready` by hand, then `/build bp-083` in a fresh (delegated)
session.

## Build — 2026-07-21 (delegated builder, worktree branch)

**Build HEAD:** worktree branch synced to `main` (`4212306`, bp-087 sealed) before building — the
graduation was at `d08da37`; bp-084/085/086/087/088 plans landed on main since. Built at current
main.

### Q3 — `core/__init__.py` import-free? CONFIRMED.
`[GROUNDED core/__init__.py:1-17]` — a module docstring only, zero `import`/`from` statements. The
strict-semantics precondition (§2.3) holds; the fixed point does not collapse. Guarded structurally
by `test_core_init_is_import_free`.

### The computed fixed point — |INNER| = 30 (= Appendix A's 29 + `core.rings`).
Recomputed the strict-v2 predicate over `core/**` at HEAD: base =
`(sys.stdlib_module_names ∖ NETWORK_MODULES ∖ {sqlite3}) ∪ {numpy, scipy}`, strict closure
(ancestor `__init__`s counted, relative imports resolved, `from core.pkg import sub` resolved to a
submodule when it exists). Total core modules at HEAD: **141** (135 at `97c245c` — the tree grew,
the ring did not). Computed inner **before** adding `core/rings.py`: **exactly 29, byte-identical to
Appendix A** (zero delta — `expected - computed = ∅`, `computed - expected = ∅`). Falsifier F6
satisfied by construction, no hand-editing toward green.

**The only delta vs Appendix A's 29: `+core.rings`.** The map module this plan creates is itself
stdlib-only ⇒ it computes inner, and assertion B1 ("pure ⇒ the map must claim them") forces it to
declare itself. Added `"core.rings"` to `INNER`; recompute now equals the 30-member declared set
both directions. This is a correct, principled +1 (the artifact is inner by construction, §2.4-A),
NOT a stale-tree symptom — well inside the 20–40 sanity band.

### The three assertions (§2.4-B) — all GREEN.
1. `test_inner_ring_is_the_computed_fixed_point` — computed == declared, both directions. PASS.
2. `test_outer_never_imported_by_inner` — per-member direction law, own message per member. PASS.
3. `test_scanner_sees_known_impurities` — honesty guard: excludes `sealing`, `stores.chatlog`,
   `stores.vectorstore`, `temporal.spine`, `complex.spectral`; `|INNER| >= 20`. PASS.
Plus `test_core_init_is_import_free` (the Q3 structural guard). 4 passed.

### Files (write_scope, exactly two new files).
- `core/rings.py` — stdlib-only; declares `INNER` (30), `MATH_3P={numpy,scipy}`,
  `PLUMBING_STDLIB={sqlite3}`. Inner by construction.
- `tests/unit/test_inner_ring.py` — the born-green ratchet; fixed-point computation lives IN the
  module (P4); deliberate second copy of the outer scanner's AST pattern (NOT a shared helper);
  imports `NETWORK_MODULES` from `ops.import_lint`, ring constants from `core.rings`.

`test_core_self_containment.py` UNCHANGED (pillar 2). Next: full attestable-green gate, then commit.
