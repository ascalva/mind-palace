# BP-007 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Entry — 2026-07-11 — start: plan flipped `ready → in-progress`; Item 5 measurement + floor decision

**Status.** Plan flipped to `in-progress` (legal builder transition). Building in worktree
`.claude/worktrees/agent-a7311e30e485c40ab` on branch `worktree-agent-a7311e30e485c40ab`
(own worktree per delegation contract; never merging to main).

**Item 5 — re-measure (post-bp-006).** `uv run --extra dev mypy` (current config, unchanged):
**296 errors in 83 files** (322 source files checked). By Tier-2 package (grep on path
prefix, matches plan's rough expectations closely):

| package   | plan's rough estimate | measured 2026-07-11 |
|-----------|------------------------|----------------------|
| tests     | ~221                   | 221                  |
| ops       | ~42                    | 43                   |
| agents    | ~16                    | 16                   |
| scheduler | ~10                    | 10                   |
| scripts   | ~6                     | 0                    |
| eval      | (unlisted)             | 0                    |

**Unplanned discovery: `edge`/`config` leak into the run.** `edge` (9 errors) and `config`
(4 errors) are NOT in `[tool.mypy].files` and are Tier-3 by the note's own V1a measurement
(zero core imports, confirmed again by grep here) — but mypy follows imports transitively
from files that ARE in the list (`ops`, `agents`, `scheduler`, `scripts` all `import config`;
`scheduler/interface.py` and `scripts/monitor.py` `import edge`), so their errors surface in
the run anyway. This is a **codebase/spec-fidelity** finding, self-resolved (not routed): the
fix is a `pyproject.toml` per-module override — `[[tool.mypy.overrides]] module = ["edge.*",
"config.*"]` / `follow_imports = "silent"` — which keeps them out of error-reporting (Tier-3,
recorded default, per §2.5) while core/Tier-2 modules that reference their types still get
checked normally. Verified: 296 → 283 with the override added, 322 source files still checked
(nothing silently excluded from analysis, only from **error reporting** on Tier-3 paths).
`config/**` was never in write_scope to begin with (edge/cloud are the plan's named
out-of-scope; config weren't discussed — the override is the only lever available, since
editing those files is out of scope regardless). Recorded here, not filed as a separate
finding — self-resolved per the routing rule (mechanical, no design judgment involved).

**Floor decision — `disallow_any_generics`: ADOPTED.** Measured the delta by adding
`disallow_any_generics = true` to the global `[tool.mypy]` block (test config, not yet
committed): 296 → 364, **delta = +68**, all 68 are `type-arg` (bare generic containers:
`dict`, `list`, `CompletedProcess`, `Sequence`, `set`, `Counter` missing type params). Split
by writability: **54 in write_scope** (ops 31, tests 22, eval 1) vs **14 out of scope**
(edge 13, config 1 — fully absorbed by the `follow_imports=silent` override above, confirmed
by combined test run: 364 → 337 with both changes applied).

**Falsifier check (plan Item 5, verbatim): "the stricter floor adds only T3 friction (zero
T1/T2 in the delta) — record and stay at the base floor."** NOT tripped: all 54 in-scope
delta errors are T2 (representability — real shape info the type system currently can't see:
untyped dicts crossing signatures, `subprocess.CompletedProcess` left ungenerified, an
untyped `Counter`/`Sequence`/`set`). Zero T1 in the delta (no behavior-changing defect
detected merely by adding the flag). This is genuine T2 signal, mechanically cheap to close
(same `dict[str, Any]` / concrete-type-param convention bp-006 already established) — **floor
raised to `check_untyped_defs` + `disallow_any_generics`**, recorded in `pyproject.toml` with
today's date and this reasoning inline.

**Decision, made explicit for Items 6–7:** fix the 54 in-scope `type-arg` sites as part of the
same sweep (they are now baseline errors under the adopted floor, not a separate pass) —
`dict[str, Any]` for open payloads per bp-006's convention, concrete element/value types
(e.g. `CompletedProcess[str]`, `dict[str, int]`) where the call site makes the shape obvious
without guessing.

**Acceptance evidence (Item 5):** journal table above; `pyproject.toml` floor comment
updated in the same commit as the override. Commit `6db461b`.

**True post-floor baseline for Items 6–7** (`uv run --extra dev mypy`, both config changes
applied): **337 errors total** in 90 files (322 checked) — tests 243, ops 74, agents 16,
scheduler 10, scripts 0, eval 1 (`edge`/`config` no longer surface, per the override).

---

## Entry — 2026-07-11 — Item 6 in progress: eval + scheduler green (16 → 0 combined)

**eval/golden.py (1 → 0).** `Retriever = Callable[[str, int], Sequence[dict]]` → `Sequence[dict[str,
Any]]` — the docstring already names the open shape (`{"title": ..., optionally "_distance":
...}`), so `dict[str, Any]` is the correct open-payload convention (bp-006), not a TypedDict
(no fixed key set is promised — only a minimum).

**scheduler/queue.py (T2/T3, 1 error).** `JobQueue.enqueue` called `self.get(int(cur.lastrowid))`
where `cur.lastrowid: int | None` per the sqlite3 stubs. Read the call site: `lastrowid` is
populated by sqlite3 after any successful `INSERT` into a rowid table (this table has no
`WITHOUT ROWID`) — same shape as bp-006's duckdb `fetchone()` count(*) family ("None
unreachable; narrow"). Replaced the unsound `int(...)` call (which would raise a
different, more confusing exception than an assert if the stub's `None` were ever real) with
`assert cur.lastrowid is not None` + comment, then pass the narrowed `int` straight through.

**scheduler/vault_sync.py + scheduler/interface.py (9 errors, the `config: object | None`
family).** Same T2 family bp-006 closed in `core/` — fixed identically: `Config` imported
directly from `config.loader` (both files already depend on `config` transitively; no import
cycle — `config.loader` does not import `scheduler`), `config: object | None` → `config:
Config | None` at both call sites (`build_vault_watcher`, `build_conversation_runtime`).
`vault_sync.py`'s `on_change` lambda was also a genuine T2: `VaultWatcher.on_change` (core,
sealed) declares `Callable[[], None]`, but the lambda `lambda: enqueue_vault_sync(queue,
router)` returns `Job` — Python discards it at runtime (no behavior change) but the type
was dishonest. Replaced the lambda with a named `_on_change() -> None` that calls
`enqueue_vault_sync` for effect and returns nothing — the annotation now says what the code
actually guarantees.

**Verification:** `uv run mypy scheduler/` → clean; repo-wide `uv run mypy | grep '^scheduler/'`
→ empty (scheduler fully green, 10 → 0). `ruff check .` clean; pytest 743 passed / 4 skipped
(no behavior change — all fixes were annotation-only or narrowed an unreachable-None call,
consistent with Item 6's invariant). Commit `12c96f0`.

**Per-item running state:** eval 1→0 ✓ done · scheduler 10→0 ✓ done · agents 16→? next ·
ops 74→? next · scripts 0 (already clean, nothing to do) · tests 243 (Item 7, untouched so far).

**Next action:** `agents/` (16 errors, mostly the same `config: object | None` family per
the grep above — `agents/ambassador/__init__.py`), then `ops/` (74, the largest package).

---

## Markers
