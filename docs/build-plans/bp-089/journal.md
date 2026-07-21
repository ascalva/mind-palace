# Journal — bp-089 (S1′)

**Status:** proposed (supersedes bp-084 on `finding-0144`; awaiting owner `proposed → ready`).
**Design ref:** `docs/design-notes/inner-outer-core.md` §2.6b.

## Minted — 2026-07-21 (session-40), by the orchestrator

bp-084 (S1) was graduation-defective — its `write_scope` could not deliver the atomic +7. The
delegated builder ran the read-only DRY audit (Item 3), hit the wall, and STOPPED CLEAN (no code),
filing `finding-0144` (spec-fidelity → orchestrator). Per the graduate discipline (supersession,
not in-place editing), bp-089 is minted with the three corrections + the naming fix (see §0-bis):
`write_scope` += `core/temporal_view.py`, `core/temporal/__init__.py`, `core/stores/claim_ops.py`;
the +7 promotes `core.integrator_math` (new inner), not `core.integrator` (stays outer, keeps the
ledger). Item 3 is pre-completed (recorded in finding-0144) — the builder skips it.

Importer discovery redone repo-wide (the graduation defect was incomplete): the moved temporal
symbols are imported by `core/temporal_view.py` (`:56/:187/:340/:348`) + `core/temporal/__init__.py`
(`:18,22,50,69`) + the six temporal test files (already in scope). `IntegrationReport`/`CoverageGauge`
have NO external importer — that split needs no extra repoint. Final `|INNER| = 37`.

Next: owner blesses `proposed → ready`, then `/build bp-089` (run against post-M0 main; `git merge
main` first if the worktree is stale). bp-084 stays inspectable, superseded.
