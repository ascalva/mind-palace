---
type: finding
id: finding-0057
status: open
created: 2026-07-12
updated: 2026-07-12
links:
  - core/stores/observation_history.py
  - docs/build-plans/bp-019/plan.md
ftype: spec-defect
origin_plan: bp-019
route: builder
resolution: null
---

# bp-019's write_scope omits `core/stores/observation_history.py`, but the design requires an `IDENTITY_KEYS["agent"]` registration there

## What

`core/stores/observation_history.py` already anticipates this plan: its module docstring
says "'agent' lands with bp-019" (`:13`), the DDL comment says `'code' | 'agent' (bp-019)`
(`:48`), and the `IDENTITY_KEYS` dict comment says "bp-019 registers 'agent': (commit_sha,
stream, subject_id, key)" (`:62`) — but the dict itself (`:63-65`) still only has `"code"`.
bp-019's `write_scope` does not list `core/stores/observation_history.py` anywhere (front
matter or §5), so `AgentObservationStore.add_batch()`'s supersession path (calling
`history.archive("agent", ...)`) and `chain_for()` (calling `history.chain("agent", ...)`)
will `KeyError` on `IDENTITY_KEYS["agent"]` the first time either fires against a REAL
`ObservationHistoryStore` — confirmed by reading `_identity_json()`
(`observation_history.py:72-76`): a bare `IDENTITY_KEYS[store]` lookup, no `.get` fallback.

Confirmed structurally: `python3 .claude/hooks/_lib.py scope-check
core/stores/observation_history.py` returns `DENY` under the active bp-019 plan — the gap
is real, not a misreading.

## Why it matters

Without the one-line registration, any real supersession (a bumped `INTERPRETER_VERSION`
re-projecting) or any `chain_for()` call against the live `ObservationHistoryStore` raises
`KeyError` instead of archiving/reading — a silent-until-triggered defect that would
surface at bp-020's backfill or at φ_self's first version bump, not now (Item 5's own
same-interpreter-idempotence and no-history-store-raises tests don't exercise it, since
they don't hit a REAL history store's bumped-interpreter path with `store="agent"`).

## Re-entry condition

None needed to continue THIS session: not a blocker. Item 5's acceptance test ("bumped-
interpreter supersession archives to the family sidecar under `store='agent'`") is
satisfiable today by registering `IDENTITY_KEYS["agent"]` in the test's own local
monkeypatch/fixture (in-scope: `tests/unit/test_agent_observations.py`), which exercises
the SAME code path (`archive()`/`chain()` internals) without writing to the out-of-scope
production file. Re-entry: when the orchestrator (or a follow-up one-line-grant plan)
lands the actual `IDENTITY_KEYS["agent"] = ("commit_sha", "stream", "subject_id", "key")`
entry in `core/stores/observation_history.py` — a single dict-literal line, same
"ONE LINE + comment" discipline this plan already grants for `.githooks/post-commit` and
`ops/lifecycle/launcher.py` (§6(g)/(h)) — the monkeypatch in the test suite can be dropped
in favor of the real registration (a follow-up test-file-only edit, in-scope).

## Routing

`spec-fidelity` — the builder (this session) resolves it: proceeds using an in-test
registration of `IDENTITY_KEYS["agent"]` (monkeypatched onto the real
`observation_history` module within `tests/unit/test_agent_observations.py`, scoped to
each test that needs it) so the falsifier-grade acceptance tests (bumped-interpreter
supersession, chain query) exercise the REAL `ObservationHistoryStore.archive()`/`chain()`
code paths end-to-end, not a mock. Flags for the orchestrator: bp-019's write_scope should
have included `core/stores/observation_history.py` for exactly one line (the dict entry
the file's own comments already prescribe) — recommend a tiny follow-up grant (or amending
this plan's write_scope before merge) so the registration lands in the shipped file rather
than living only inside test-local monkeypatches.
