# Journal — bp-086 (AL-1)

**Status:** in-progress (bp-086 build session, worktree `agent-aa760562444400815`).
**Design ref:** `docs/design-notes/agentic-loop.md` §2.3 / §3 AL-1.

## Graduation — 2026-07-21 (session-40)

Minted `proposed` by `/graduate` over the three ratified notes (`fbea48d`); blessed `ready` by
owner (front-matter `status: ready` at build start). The plan's §3 carries the grounding
citations; §6 pins the interfaces verbatim.

## Build session — 2026-07-21

**Worktree note.** This worktree was created at `d08da37`, before bp-086's plan/journal were
committed to main (`4212306`). The five write_scope FILES (`core/scope.py`, `core/agent_scope.py`,
the three test files) are byte-identical to main at build start (verified by `diff -q`); the
plan.md + journal.md were materialized into the worktree working tree so scope-guard + journaling
operate. No merge performed.

### Item 12 — `PRIVATE_STRATA` + `zone_admissible` (the law) — DONE

`core/scope.py`, placed beside `DEPLOYED_WORLD_CEILING`.

- `PRIVATE_STRATA: frozenset[Stratum] = _downward_close(_BASE_STRATA - {Stratum.WORLD})` — every
  grantable stratum except `world` (WIDEST-exclusion default, plan §3 Q3). Derived from `⊤_Σ`, so it
  carries refinements (a scope naming only `mirror_authored` still counts private); FOUNDATION and
  the HYPOTHETICAL overlay are excluded by construction (not in `_BASE_STRATA`).
- `zone_admissible(s) -> bool` = `not (s.sigma.strata & PRIVATE_STRATA) or s.authority.world is
  WorldReach.NONE` — the cross-coordinate implication `Σ ⊓ PRIVATE_STRATA ≠ ⊥ ⇒ W_world = NONE`.
  Deliberately NOT an `Ideal` (which is Σ-only); it is a law-predicate (§2.3, gap G-D).
- Module docstring cross-references §2.3 as the warrant (plan §4).
- **OWNER QUESTION (parked, not blocking):** whether `ops`/`reference` should count as "private" —
  default keeps them IN (strongest law). Flagged in the `PRIVATE_STRATA` comment; owner call at
  proposed→ready.

### Item 13 — the three profile constructors — DONE

`core/agent_scope.py`, appended after `dreamer_scope` (same precedent shape; pure-core).

- `internal_actor(strata=None, *, hypothetical=False)` — Σ = `top()` (or granted downset), optional
  ∪{HYPOTHETICAL}; E=⊤; T=(commit,∗) cut-clock; A=(READ_PROPOSE, 1, NONE). Zone-admissible via
  W_world=NONE.
- `external_proposer(strata=(MIRROR_AUTHORED,))` — Σ=mirror_authored/narrower; E=⊤; T=(N,∗);
  A=(READ_PROPOSE, 0, NONE). Propose-only. Zone-admissible via W_world=NONE.
- `external_executor(reach=SENSING)` — Σ=⊥; E=⊥; T=(now,∗); A=(READ, 0, reach). Holds world reach;
  zone-admissible via Σ=⊥ (antecedent false) — the inversion's other corner. `reach` is vocabulary,
  wires nothing (finding-0011 deployed ceiling NONE unchanged).

### Item 14 — tests — DONE

- `test_scope.py`: the G-D zone-law block. **F-AL3 crux —
  `test_zone_law_REFUSES_a_constructable_private_read_with_world_reach`**: a hand-built, well-typed
  ⊤_Σ scope with `W_world=SENSING` (and single-refinement variants at every reach) is REFUSED by
  `zone_admissible` — the structural refusal the note demands. Plus admits-when-NONE,
  admits-⊥-Σ-at-any-reach, admits-world-only, and the membership pin.
- `test_scope_laws.py`: `test_private_strata_membership_is_pinned` — exact membership, drift-guarded.
- `test_agent_scope.py`: the five profile-region tests — IA broad/private/no-world + grant/hypothetical
  respect; EA-p propose-only/mirror_authored; EA-x ⊥-Σ holds world reach; all-three
  zone-admissible-by-construction; IA delegation-never-widens (Scope.meet reused).

**F-AL3 verdict: the adversarial refusal WORKS.** A violating deployed grant is constructable and
`zone_admissible` structurally refuses it — the §2.3 derivation is a ratchet, not decorative. No
stop-and-raise; no design finding needed.

### Attestable-green gate (each leg separately)

- `ruff check .` → **All checks passed!**
- `scripts/check_imports.py` → **OK** (core imports no zone/networking; scope.py + agent_scope.py
  stay pure-core).
- `mypy core agents eval ops scheduler scripts` → **Success: no issues found in 237 source files.**
- argless `mypy` → tail **`Found 69 errors`** (== tests baseline; NO new type reds).
- `python -m ops.type_gate` → **OK** (tier-2 membership + bare-ignore scan).
- `pytest` (blast radius: full `tests/unit` + `tests/integrity/test_clock_laws.py`, the only importer
  of the changed modules outside unit) → **1090 passed, 4 skipped, 1 failed**. The single red is
  `test_core_imports_nothing_outside_core` (finding-0103 ratchet, **RED BY DESIGN**, deselected in
  the green gate) — confirmed identical failure with my changes stashed at base `d08da37`; its
  offenders are factory/interface/ops_view/reference_view/sensing/temporal — none mine. The new 64
  scope/profile/law tests all GREEN; the existing role-constructor + scope-law tests still GREEN.
  (Note: the plain `uv run pytest -q` over the WHOLE tree was starved to 0% CPU by ~3 sibling
  worktree builders contending for the memory ceiling — non-negotiable #8; the blast-radius run +
  suite-wide mypy over all 502 files establish no-new-reds without the contended full run.)

**Owner question parked (not blocking):** `PRIVATE_STRATA` ships as the widest exclusion — every
grantable stratum except `world` (ops/reference IN). Whether ops/reference should count as "private"
for this law is the owner's call at proposed→ready (plan §3 Q3 / §10).

Build complete on the worktree branch. NOT merged; status left `in-progress` (orchestrator flips to
complete on merge).
