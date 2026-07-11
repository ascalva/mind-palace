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

## Entry — 2026-07-11 — Item 6 continued: agents/ green (16 → 0)

**agents/ambassador/agent.py.** `Ambassador.server: object` carried only a comment describing
its real shape (`.chat(tier, messages, **kw) -> str`) — the exact "duck-typed object hides the
real interface" T2 shape the audit note names. `ModelServer` (core/models/server.py) is a
concrete class, but tests substitute a bare `FakeServer` (`tests/integration/test_librarian.py`)
that doesn't inherit from it — tightening to the concrete class would break that
substitutability. Fixed with a local **Protocol** (`ChatServer`, structural — the right tool
for "some object with this method," not requiring inheritance): `server: ChatServer`.

`verdict_transport: Callable[[object], object] | None` was actually **unsound by
contravariance** — I verified with a scratch mypy repro
(`/private/tmp/.../scratchpad/test_variance.py`) that `Callable[[object], X]` REJECTS a
narrower callable like `Callable[[SignedVerdict], VerdictRecord]` (parameter types are
contravariant), so this annotation would never have accepted the real
`build_verdict_receiver()` output — it happened not to error only because `build_ambassador`
passes it through an untyped kwarg. Retyped `Callable[..., object] | None`
(`...` = "some opaque single-purpose callable"), which is both type-sound and preserves the
deliberate design boundary (verdict-authority.md §4: the Ambassador never learns
SignedVerdict/VerdictRecord's shape — that would leak verdict internals across the
transport-only seam). Confirmed accepting with a second scratch repro. This is NOT an `Any`
widening (falsifier check: `Callable[..., object]` is strictly more informative than `Any`,
and strictly more honest than the unsound `object` it replaced).

**agents/ambassador/__init__.py.** Same `config: object | None` → `Config | None` fix as
scheduler (bp-006's dominant family), `Config` imported directly from `config.loader`.

**Verification:** `uv run mypy agents/` → clean; repo-wide grep for `^agents/` → empty (16 →
0). `ruff check .` clean; pytest 743 passed / 4 skipped. Commit `eb3980c`.

**Per-item running state:** eval 1→0 ✓ · scheduler 10→0 ✓ · agents 16→0 ✓ · ops 74→? next ·
scripts 0 (clean) · tests 243 (Item 7, not started).

**Next action:** `ops/` (74 errors, the largest non-test package) — grep shows `ops/lifecycle/
launcher.py`, `ops/ledger.py`, `ops/backup/plan.py`, `ops/effect_*.py`, `ops/selfmod.py`,
`ops/ci_witness.py`, `ops/apply.py` as the hot files; same families expected (config: object,
bare-dict type-arg, CompletedProcess type-arg) plus launcher.py's genuinely different
`Callable[[], Job]` vs `Callable[[], None]` and a psutil import-untyped (candidate for the
existing psutil boundary shim in `core/typedshims/psutil.py` — reuse rather than re-solve).

---

## Entry — 2026-07-11 — Item 6 continued: ops ledger family + apply/code_sensor (ops 74 → 51)

**ops/apply.py (2), ops/code_sensor.py (2).** Mechanical: `read_overlay`/`write_overlay`'s
`{section: {key: value}}` typed `dict[str, dict[str, float | int]]` (the exact scalar
`_format`/`write_overlay` already coerce to — no guessing, read the coercion code first);
`build_code_sensor`'s `config: object | None` → `Config | None`, same family as scheduler/agents.

**ops/effect_ledger.py (5), ops/ledger.py (6) — the propose/decide ledger family.** Same
`config: object | None` fix on `open_effect_ledger`/`open_ledger`. `EffectRecord.params` and
`propose()`'s `params` typed `dict[str, str]` (matched to `core/effect_proposal.py`'s already-
strict convention for the identical shape — this ledger is downstream of that proposal type, so
consistency matters more than re-deriving). `Proposal.metrics` / `mark_validated` /
`mark_rolled_back` typed `dict[str, Any]` (open validation-metrics payload, JSON-serialized,
no fixed key set — the open-payload convention, not TypedDict).

**Real defect found (not a T1 behavior bug, but a broken-warrant T3 the plan's Item 6 grep
would have missed without reading it): both ledgers' `propose()` had `return self.get(new_id)
# type: ignore[return-value]`.** Once `disallow_any_generics` was in and I touched the file,
mypy started reporting `arg-type` at that line (lastrowid: `int | None` → `get(int)`) — NOT
covered by the `return-value` ignore code, so the ignore was silently doing nothing for the
actual error mypy now emits (it would still have suppressed the ORIGINAL return-value mismatch
had that fired first, but arg-type fires first and slips through). Fixed by narrowing instead
of ignoring, per the T3 preference order (bp-006 journal: narrowing > cast > ignore): `assert
lastrowid is not None` (sqlite3 always sets it after a successful INSERT — same shape as
`scheduler/queue.py`'s fix earlier this session). `ops/ledger.py` had FOUR MORE of the same
stale `# type: ignore[return-value]` pattern at every post-write re-fetch (`_decide`,
`mark_executed`, `mark_validated`, `mark_rolled_back`) — these were legitimately covering a
real (different) mismatch (`_require()` guarantees the row exists but mypy can't see that
narrowing across an intervening `UPDATE`), so replaced all four with a shared `_get_or_die()`
helper that documents the guarantee and asserts it, rather than four independent bare ignores.
Net: no bare/mismatched ignores remain in either ledger file.

**Verification:** `uv run mypy ops/apply.py ops/code_sensor.py ops/effect_ledger.py
ops/ledger.py` → clean; `ruff check .` clean (one line-length wrap needed on `mark_validated`'s
new signature); pytest 743 passed / 4 skipped. Commit `e39fe90`.

**Per-item running state:** eval 1→0 ✓ · scheduler 10→0 ✓ · agents 16→0 ✓ ·
ops 74→51 (apply/code_sensor/effect_ledger/ledger done; remaining: `ops/lifecycle/launcher.py`
21, `ops/ci_witness.py` 13, `ops/backup/plan.py` 10, `ops/lifecycle/children.py` 4,
`ops/effect_exec.py` 4, `ops/selfmod.py` 3, `ops/lifecycle/snapshot.py` 2, `ops/lifecycle/
runs.py` 2) · scripts 0 (clean) · tests 243 (Item 7, not started).

**Next action:** `ops/selfmod.py` (3) and `ops/effect_exec.py` (4) next (small, likely same
families), then the `ops/lifecycle/` cluster (launcher.py is the biggest single file at 21 —
read it fully before touching, since it has the genuinely-different `Callable[[], Job]` vs
`Callable[[], None]` mismatch and several `object`-typed attribute chains that may need a
small Protocol like agents/ambassador/agent.py's `ChatServer`), then `ops/ci_witness.py` (13)
and `ops/backup/plan.py` (10, `CompletedProcess` type-arg family — mechanical, `subprocess.run`
return types).

---

## Entry — 2026-07-11 — Item 6 continued: selfmod/effect_exec/lifecycle-cluster green (ops 74 → 45)

**ops/selfmod.py (3).** `build_golden_validator`'s `frozen_baseline`/`rolling_baseline` typed
`dict[str, float]` — read `eval/golden.py` first: `load_baseline`/`as_metrics`/`regressions`
already declare `dict[str, float]` (bp-006-era, already strict), so this is a KNOWN shape from
`eval`, not an arbitrary payload — matching it exactly, not defaulting to `dict[str, Any]`,
is the more honest fix. `ValidationResult.metrics` stayed `dict[str, Any]` (genuinely open:
nests lever name/value/regressions/per-axis drift — no fixed key set).

**ops/effect_exec.py (4).** `EffectTransport.perform`/`IrreversibleExecutor.execute`'s
`params: dict` → `dict[str, str]` (matches `ops/effect_ledger.py`'s convention for the
identical effect-params shape — same actuator-kwargs concept, same fix). `config: object |
None` → `Config | None`, `Config` added to the existing `TYPE_CHECKING` block (config stays
injectable, no new runtime import).

**ops/lifecycle/snapshot.py (2).** `build_status`/`write_status`'s snapshot dict → `dict[str,
Any]` (a deeply-nested JSON core→edge handoff, Invariant 2 boundary — genuinely open, no
single fixed shape worth a TypedDict).

**ops/lifecycle/runs.py (2).** Same `lastrowid` narrowing fix as `scheduler/queue.py` (assert
not-None instead of `int(...)`); `open_run_ledger`'s `config: object | None` → `Config | None`.

**ops/lifecycle/children.py (4) — the interesting one.** `Proc = object` was a bare type alias
with a comment describing the real shape ("Popen-like: .pid, .poll(), .terminate(), .wait(),
.kill()"). Confirmed via `tests/unit/test_children.py`'s `_FakeProc` that callers inject a
structural fake, NOT a `subprocess.Popen` subclass — so a `Protocol` is the right tool (same
judgment as `agents/ambassador/agent.py`'s `ChatServer` earlier this session), not the concrete
class. `stop()` needed one additional explicit `assert proc is not None` (the `alive()` guard
established it but mypy can't carry that narrowing across the property read).

**Verification (this entry's four files):** `uv run mypy ops/selfmod.py ops/effect_exec.py
ops/lifecycle/{snapshot,runs,children}.py` → clean; `ruff check .` clean; pytest 743 passed /
4 skipped. Commits `c5f0a94`, `0d628e2`.

**Correction to the prior commit's arithmetic:** `0d628e2`'s message estimated ops 44 → 34;
the actual re-measure is ops 74 → **45** (not 34) — `ops/lifecycle/launcher.py` picked up 1 net
new error (21 → 22) as a side effect of the `children.py` Protocol tightening (a `Child`-typed
attribute chain in launcher.py now resolves further and mypy sees one more layer). Recorded
here as the correction; the commit stays as committed (no amend) per the lossless-discipline
rule (small, frequent, forward-only commits) — this journal entry is the authoritative count.

**Per-item running state:** eval 1→0 ✓ · scheduler 10→0 ✓ · agents 16→0 ✓ ·
ops 74→45 (apply/code_sensor/effect_ledger/ledger/selfmod/effect_exec/lifecycle-{snapshot,runs,
children} all done; remaining: `ops/lifecycle/launcher.py` 22, `ops/ci_witness.py` 13,
`ops/backup/plan.py` 10) · scripts 0 (clean) · tests 243 (Item 7, not started).

**Next action:** `ops/backup/plan.py` (10 — `CompletedProcess` type-arg family, mechanical),
then `ops/ci_witness.py` (13), then `ops/lifecycle/launcher.py` (22, the largest single file —
read fully before touching; has the genuinely different `Callable[[], Job]` vs `Callable[[],
None]` mismatch, `psutil` import-untyped — reuse the existing `core/typedshims/psutil.py` shim
rather than re-solving — and several `object`-typed attribute chains needing the same
Protocol-vs-concrete-type judgment call as `ChatServer`/`Proc`).

---

## Entry — 2026-07-11 — Item 6 continued: backup/plan.py + ci_witness.py green (ops 45 → 22)

**ops/backup/plan.py (10).** `ResticRunner`'s six `CompletedProcess`-returning methods
parameterized `CompletedProcess[str]` — checked the `_run()` call site first
(`subprocess.run(..., text=True)`), so `str` is the correct type argument, not the bytes
default. `build_backup_plan`'s `config: object | None` → `Config | None`.

**ops/ci_witness.py (13) — the GitLab JSON-HTTP-boundary file.** `_get`/`_api_root` (raw
`json.load()` over the GitLab API) typed `Any` — deliberately, not `dict[str, Any]`: the same
path returns a LIST for listing endpoints (`/pipelines?...`, `/jobs?...`) and a DICT for
single-resource endpoints, so committing to `dict` would be dishonest for half the call sites.
This is the same warranted JSON-boundary shape bp-006 named for `core/models/ollama_client.py`
— `Any` at the exact ingestion point, narrowed by each caller. `pipeline_for`/`verdict`/
`attest_verdict`'s `pipe` parameter typed `dict[str, Any]` (a GitLab pipeline resource — known-
ish keys, open set, not TypedDict-worthy for a script this size). Two real invariants the
checker couldn't see were made explicit with `assert`, each citing WHY: `check()`'s `pipe is
not None` once `v != "absent"` (because `verdict(None)` is always `"absent"` — see `verdict()`
2 lines above the assert); `release()`'s `pipe is not None` once `verdict(pipe) == "green"` is
required (same reason). No behavior change — the code already relied on both invariants
implicitly (it would have raised a `TypeError`/`KeyError` at runtime had they been false); the
asserts just make the reasoning visible to both the reader and the checker.

**Verification:** `uv run mypy ops/backup/plan.py ops/ci_witness.py` → clean; `ruff check .`
clean (one line-length wrap needed on `ResticRunner.restore`); pytest 743 passed / 4 skipped.
Commit `b92cb12`.

**Per-item running state:** eval 1→0 ✓ · scheduler 10→0 ✓ · agents 16→0 ✓ ·
ops 74→**22** (everything in `ops/` done except `ops/lifecycle/launcher.py`) · scripts 0
(clean) · tests 243 (Item 7, not started).

**Next action:** `ops/lifecycle/launcher.py` (22, the last ops file — the biggest single file
in the package; read it FULLY before touching). Known shapes going in: `Callable[[], Job]` vs
`Callable[[], None]` (same fix as `scheduler/vault_sync.py`'s `_on_change` wrapper earlier this
session); `psutil` import-untyped (reuse `core/typedshims/psutil.py`, already built in bp-006 —
do not re-solve); several `object`-typed attribute chains (`.paths`, `.vault`, `.start`,
`.run`, `.stop`, `.close`) that are almost certainly the `config: object | None` family plus
one or two components needing a small Protocol (same judgment as `ChatServer`/`Proc` — check
whether tests inject a fake before reaching for the concrete class); one `list` type-arg.
Once launcher.py is green, `ops/` is 0 and Item 6 is fully done except a final repo-wide
re-verify + acceptance-test recording. Then Item 7 (`tests/`, 243 errors) starts fresh.

---

## Entry — 2026-07-11 — Item 6 COMPLETE: ops/lifecycle/launcher.py green, 0 errors outside tests/

**ops/lifecycle/launcher.py (22 → 0), the last ops/ file.** Read fully before touching (per the
plan's own guidance) — five distinct fixes:

1. **`psutil` import-untyped** — reused `core/typedshims/psutil.py` (bp-006's boundary shim)
   via `from core.typedshims import psutil`, instead of a raw `import psutil`. The shim already
   wraps exactly the one call this file makes (`virtual_memory().available`).
2. **`Components.supervisor` / `.watcher` / `.queue` / `.children`** — four bare `object` fields
   with duck-type comments, given real Protocols (`SupervisorLike`, `WatcherLike`, `QueueLike`,
   `ChildLike`). Confirmed via `tests/integration/test_lifecycle.py`'s `_FakeSupervisor`/
   `_FakeWatcher`/`_FakeQueue`/`_FakeChild` that callers inject bare fakes, never the concrete
   `Supervisor`/`VaultWatcher`/`JobQueue`/`Child` — same judgment as `ChatServer` (agents) and
   `Proc` (lifecycle/children) earlier this session. **Important nuance found while doing this:**
   a Protocol must match the ACTUAL call shape in the file, not the full real interface — my
   first draft mirrored `VaultWatcher.start(self, *, prefer="auto")` and `Supervisor.run(self,
   *, max_ticks=None)` exactly, and mypy correctly rejected `_FakeWatcher`/`_FakeSupervisor`
   (their bare `start()`/`run()` don't accept those kwargs, so they don't structurally satisfy a
   Protocol that promises callers can pass them). Narrowed both Protocols to no-arg — the only
   shape `launcher.py` itself ever calls (`c.watcher.start()`, `c.supervisor.run()`) — which is
   the correct fix, not a workaround: a Protocol should describe what THIS FILE needs, not the
   real class's full surface. `ChildLike.pid` needed a `@property`, not a plain attribute — the
   real `Child.pid` is read-only, and a Protocol attribute (unlike a property) implies a settable
   slot, which `Child` can't satisfy.
3. **`Components.health_check`/`.snapshot`, the `children` list** — `list` → `list[Flag]` /
   `list[ChildLike]` (`scheduler.router.Flag` imported under a new `TYPE_CHECKING` block,
   alongside `Config` — no new runtime import; `build_components`/`build_launcher` already
   lazily import these modules at call time for the real path).
4. **`Launcher.cfg`/`.components_factory`/`.preflight_fn`/`._run`** — `object` → `Config` /
   `Callable[[Config], Components]` / `Callable[[Config], Preflight]` / `RunRecord | None` — all
   four are already-concrete, already-imported-elsewhere types; no guessing needed.
5. **`enqueue_catchup=lambda: enqueue_vault_sync(queue, router)`** — same `Callable[[], Job]` vs
   `Callable[[], None]` shape as `scheduler/vault_sync.py`'s `_on_change` fix earlier this
   session; replaced with a named `_catchup() -> None`.

**Tooling note (the ruff --fix trap, watched for per plan §11/bp-006 journal):** `ruff --fix`
re-sorted the `build_components` import block (moved `core.typedshims` alphabetically) — no
`# type: ignore` comments were near it, so nothing was stranded, but re-ran `uv run mypy
ops/lifecycle/launcher.py` immediately after the fix anyway to confirm (still clean).

**Verification (Item 6 acceptance test, verbatim from the plan): `uv run mypy` → 0 errors
outside `tests/`.** Confirmed: repo-wide run → 245 errors, ALL in `tests/` (grep `^tests/`
against `error:` lines only, excluding multi-line `note:` continuations that share the path
prefix and inflated an earlier naive count). `ops/`, `agents/`, `scheduler/`, `scripts/`,
`eval/` — all **0**. `ruff check .` clean; pytest 743 passed / 4 skipped — unchanged behavior
across the whole Item 6 sweep (every fix was annotation-only, a Protocol, or an explicit assert
narrowing an invariant the code already relied on). Commit `35766a8`.

**ITEM 6 IS COMPLETE.** Final per-package count (post-bp-006 baseline → now): eval 1→0,
scheduler 10→0, agents 16→0, ops 74→0, scripts 0→0 (already clean). Zero T1 findings filed
during Item 6 — every error triaged as T2 (representability: bare dict/list/CompletedProcess,
duck-typed `object` params/fields, `config: object | None`) or a stale/mismatched T3 ignore
(the two ledger `lastrowid` sites, `ops/ci_witness.py`'s narrowing gaps) — no genuine T1 latent
defect surfaced in `ops`/`agents`/`scheduler`/`scripts`/`eval`, consistent with core's own T1=0
finding in bp-006.

**Next action:** Item 7 — `tests/` (245 errors as measured this entry; the plan's baseline
estimate was ~223, pre-`disallow_any_generics`-floor and pre- the two real test-file fixes
needed for `test_lifecycle.py`'s `RunRecord | None` narrowing gaps surfaced above). Start fresh:
re-measure by file, triage for hidden T1s per the plan's explicit warning ("tests' errors may
hide real T1s — a test asserting the wrong type that 'passes' because untyped"), work smallest
files first, same discipline (no blanket per-file ignores, no `ignore_errors` overrides,
assertions may gain types never lose checks).

---

## Entry — 2026-07-11 — Item 7 started: import-not-found family + effect_gate_fsm (tests 245 → 213)

**Item 7 re-measure at start:** 245 tests-package errors, 76 files. By kind: `arg-type` 133 ·
`union-attr` 36 · `import-not-found` 24 · `type-arg` 22 · `operator` 10 · `index` 5 ·
`func-returns-value` 5 · `var-annotated` 4 · `return-value` 3 · `import-untyped` 1 ·
`dict-item` 1 · `attr-defined` 1. Worked the `import-not-found` family + the single biggest
file (`test_effect_gate_fsm.py`, 14 — unrelated family) first, since import-not-found blocks
mypy from even checking a file's body in some cases and is config/convention work, not
per-error triage.

**The `fixtures` import-path split (24 errors, 17 files touched once fully traced).**
`tests/conftest.py` deliberately inserts `tests/` onto `sys.path` so `fixtures.X` resolves
bare from anywhere — but 8 files already used the fully-qualified `tests.fixtures.X` instead,
which ALSO resolves (via mypy's `explicit_package_bases` synthesizing `tests` as a namespace
package, since it's in `[tool.mypy] files`). mypy can only see one of these two live paths.

**Tried first, rejected:** adding `mypy_path = "tests"` to make the bare style resolve too —
tested in a scratch config copy, and it does clear all 24 import-not-found errors, but then
mypy refuses every `tests/fixtures/*.py` file with "Source file found twice under different
module names: fixtures.X and tests.fixtures.X" — a REAL ambiguity (the same file has two valid
dotted names simultaneously), not a false positive. Reverted.

**Chosen fix: converge on `tests.fixtures.X`** (the majority-8 style, and the one that matches
what mypy's own `files` config already believes the package tree is) across the 15 files using
the bare style, found via `grep -rl "^from fixtures\.` — a straight import-line rewrite, zero
runtime behavior change (Python already resolves both identically via `conftest.py`'s
`sys.path` insert; only what mypy can statically verify changes). Two more of the same shape
turned up only once the direct 15 were fixed and I re-ran mypy: a lazy in-function import in
`tests/quality/test_dreamer_quality.py` (a `try/except`-guarded optional real-adapter binding —
unaffected by the fix, same rewrite applied), and `tests/quality/test_diffusion_clusterer.py`
importing a SIBLING TEST FILE bare (`from test_dreamer_quality import ...`) — rewritten
`from tests.quality.test_dreamer_quality import ...`.

**A third, unrelated import-not-found: `tests/integration/test_fetcher.py`'s `import
aggregate` / `import handler`.** These deliberately mirror `cloud/fetcher`'s flat Lambda-zip
deployment via a runtime `sys.path.insert(0, FETCHER_DIR)` — a genuine T3: mypy cannot follow a
dynamic `sys.path` mutation (this is residual gap (b), named explicitly in the design note
§2.5: "(b) Dynamic dispatch... no static tier sees"). `cloud/` is Tier-3 by measurement (V1a:
zero core imports) and out of this plan's scope entirely (plan §5/§9: "Tier-3 recorded
default — not debt"; "typing `edge/`/`cloud/`" is a non-goal). A warranted `# type:
ignore[import-not-found]` citing both facts is the correct, honest resolution here — not a
workaround, and not laundering (the ignore is narrowly scoped to two lines, each with its own
warrant comment).

**`tests/property/test_effect_gate_fsm.py` (14, unrelated family — the single biggest test
file).** `dict(reversibility=..., approval=..., ...)` + `**base` / `**{**base, "field": val}`
splat patterns for building variant `EffectGateDecision`s. The bug-shape: `EffectGateDecision`
has per-field types (`ReversibilityClass`, `bool`, `ApprovalStrength`), but assembling them via
a bare `dict(...)` literal collapses the value type to their common supertype
(`dict[str, int]`, since all three are int-backed enums/bools) — so `**base` unpacking loses
per-field precision entirely, a real representability gap the property test's own construction
was hiding. Fixed with `dataclasses.replace()` over one concrete `EffectGateDecision` instance
per test (the frozen dataclass already supports this — the correct tool for "same base config,
override one field," preserving per-field types through mypy's eyes exactly). Verified
behaviorally unchanged: `pytest tests/property/test_effect_gate_fsm.py` → 8/8 pass, same as
before the edit.

**Tooling note:** `ruff --fix` re-sorted imports in all 18 touched files (import path changes
moved sort order) — confirmed no `# type: ignore` comments were near any of the touched import
blocks before running `--fix` (this file set predates any T3 ignore discipline), then re-ran
`uv run mypy` on the whole set after to confirm nothing new broke. Clean.

**Verification:** `uv run mypy` → 0 `import-not-found` remaining anywhere in the repo; `ruff
check tests/` clean; pytest 743 passed / 4 skipped (unchanged — every fix here was either an
import-path rewrite with an identical runtime resolution, a warranted ignore on genuinely
Tier-3-adjacent dynamic-path code, or a construction-pattern fix with no behavioral surface).
Repo-wide: 245 → **213** tests-package errors. Commit `f1cf8fc`.

**Per-item running state:** Item 6 fully done (0 outside tests/). Item 7: 245→213 so far
(import-not-found family: 24→0; `test_effect_gate_fsm.py`: 14→0). Remaining dominant families
per the start-of-item breakdown: `arg-type` 133 (likely largest, needs per-file triage —
fakes/stubs whose params don't match tightened core signatures is the leading hypothesis, to
verify), `union-attr` 36 (likely the same `X | None` narrowing-gap shape seen throughout ops/ —
`CatalogEntry | None`, `RunRecord | None`, etc. — `tests/integration/test_vault_sync.py` alone
has 11 of these), `type-arg` 22 (same bare-generic family as Item 6), `operator` 10, `index` 5,
`func-returns-value` 5, `var-annotated` 4, `return-value` 3, `attr-defined` 1.

**Next action:** re-measure fresh (the 245 baseline is now stale after this entry's fixes),
then work `tests/integration/test_vault_sync.py`'s `CatalogEntry | None` family (11 of its own
13 errors) as the next-biggest single file, watching per the plan's explicit T1 warning
whether any of these `| None` narrowing gaps hide a REAL bug (a test that asserts on a `.digest`
that could genuinely be `None` at runtime would be exactly the "passes because untyped" shape
the plan calls out) rather than reflexively asserting past every one.

**Cross-plan note (orchestrator, mid-run, not a course-correction for this plan's own scope):**
bp-009 merged to `main` mid-session — `finding-0028` is theirs (my own findings, if any, start
at **finding-0029**). Their churn measurement found two Tier-2 test files that Any-laundered
past the new provenance type tags (an untyped fixture + an unresolvable `fixtures.corpus`
import) — invisible until runtime because those files sat below the pre-Item-5 floor. This is
independent evidence FOR the `disallow_any_generics` floor decision already made and recorded
in `pyproject.toml` (Item 5, this journal, above) — I'm noting the corroboration here rather
than reopening the decision, since it was already made from this session's own measured delta
(zero T1, T2-only, falsifier not tripped) and bp-009's finding only reinforces it, doesn't
change it. Worth flagging: bp-009's "unresolvable `fixtures.corpus` import" sounds like the
EXACT SAME bare-`fixtures.X` vs `tests.fixtures.X` split fixed in THIS entry — if their fixture
file is a different one than the 17 touched here, it may still be broken on `main` post-merge;
re-check post-rebase (not a blocker for this plan — `core/provenance.py` is bp-009's, disjoint
from bp-007's write_scope, and the orchestrator owns the rebase, not this builder). Main is NOT
merged into this worktree and won't be by this builder (per contract: own worktree, never
merge to main / never merge main in either).

---

## Entry — 2026-07-11 — Item 7 continued: :memory:->Path family + ChatServer conformance (245 → 179)

**The `":memory:"` string-vs-Path family (22 errors, 10 files).** `DerivedStore`/
`AttestationStore`/`ProposalLedger`/`JobQueue` all declare `path: Path`; many tests pass the
bare sqlite/duckdb in-memory sentinel `":memory:"` directly as a `str`. `Path(":memory:")`
round-trips identically — verified against `DerivedStore.__post_init__`'s own `if str(self.path)
!= ":memory:"` guard — and `tests/property/test_properties.py` already used exactly this idiom,
confirming it's the established fix, not a guess. Applied mechanically (script + grep) across
10 files: `test_dreams_view.py`, `test_ambassador.py`, `test_ambassador_budget.py`,
`test_dialogue_capture.py`, `test_factory_credential_grant.py`, `test_vault_sync_wiring.py`,
`test_monitor_snapshot.py`, `test_effect_exec.py`, `dreamer_adapter.py` (fixture), `test_ops_view.py`.
Zero runtime behavior change. Commit `592d144`.

**The systemic pattern surfaced by this sweep — flagged here, not yet resolved.** Fixing the
mechanical families exposed the DOMINANT remaining shape: ~37+ of the 123 `arg-type` errors are
test doubles (`FakeEmbedder`, `_FakeWasm`, `_FakePodman`, `_FakeDrift`, `_Server`/`_Embedder`/
`_Store`, `ReplyServer`, `HashingEmbedder`, `Spy`, …) passed where core declares a CONCRETE
dataclass (`Embedder`, `ModelServer`, `VectorStore`, `RawStore`, `WasmRunner`, `PodmanRunner`,
`DriftReport`, …) rather than a Protocol — nominal typing means no amount of structural
duck-typing satisfies it. This is the exact shape `agents/ambassador/agent.py`'s `ChatServer`
Protocol (this session, Item 6) already fixed for `Ambassador.server` — the fix generalizes,
but EVERY one of those core classes is a `core/**` signature, out of this plan's write_scope.
**This is a core-signature-needed stop-and-raise (plan §10)** — see finding filed below.

**What WAS fixable in test scope (self-inflicted by my own Item-6 `ChatServer` Protocol):**
`tests/fixtures/fakes.py`'s `ReplyServer.chat(messages: list[dict])` → `list[Message]`
(`core.constitution.Message`, the TypedDict every real caller already uses) — this is MY
Protocol, not core's, so tightening the shared fixture to satisfy it is in-scope and correct.
`tests/integration/test_verdict_dispositions.py`'s `test_ambassador_transports_but_never_
applies()` constructs an `Ambassador` with bare `object()` placeholders for fields the test
never reads (only `transport_verdict()` is exercised) — `cast()` to each field's real type
(`ChatServer`/`Librarian`/`OpsView`/`Budgeter`) makes the "doesn't matter here" intent explicit
rather than silently untyped; a `list.append(...) or "value"` idiom in the same test (always
evaluates true since `append` always returns `None`, but checker-suspicious) rewritten as a
named function with an honest return. Commit `18f6323`.

**Verification:** `ruff check .` clean; pytest 743 passed / 4 skipped throughout (every fix
this entry was either str→Path with an identical round-trip, a Protocol the fixture already
structurally satisfied except for one field's element type, or a cast making an already-true
"this field is unused here" explicit). Repo-wide mypy: 245 → **179**.

**Next action:** file the core-signature finding for the Embedder/ModelServer/VectorStore/
RawStore/WasmRunner/PodmanRunner/DriftReport-as-concrete-class-not-Protocol pattern (park that
criterion with a re-entry condition, per plan §10), THEN continue with what remains fixable in
test scope: the `**dict` splat family (`Attestation.create`, `StoreAttestor.emit`,
`BackupPlan` — same `dataclasses.replace`/direct-kwargs fix as `test_effect_gate_fsm.py`),
narrow one-offs (`Network` enum vs str, `list[dict]` vs `list[Message]` in
`test_constitution.py`), and the `union-attr` family (`CatalogEntry | None`, `RunRecord | None`
narrowing gaps — watch for a hidden T1 per the plan's explicit warning).

---

## Entry — 2026-07-11 — finding-0029 filed; **dict splat family closed (179 → 165)

**finding-0029 filed** (`docs/findings/finding-0029.md`, ftype `discovery`, route
`orchestrator`) for the systemic core-injectable-as-concrete-class pattern named in the prior
entry — parked with a re-entry condition (a future core-scoped plan takes `Embedder`/
`ModelServer`/`VectorStore`/`RawStore`/`WasmRunner`/`PodmanRunner` through the same
Protocol-at-call-site treatment `ChatServer` got this session). Sequence starts at
finding-0029 per the orchestrator's mid-run note (finding-0028 is bp-009's, already merged to
`main`). Commit `98baaa9`.

**The `**dict` splat family (same shape as `test_effect_gate_fsm.py`, different call surface).**
`tests/unit/test_backup_plan.py`'s `_plan(**kw)`: `BackupPlan` is a frozen dataclass, so the
`dict()` + `**base`/`base.update(kw)` pattern became a module-level `_BASE_PLAN` instance +
`dataclasses.replace(_BASE_PLAN, **kw)` — direct rerun of the `test_effect_gate_fsm.py` fix.
`tests/integration/test_attestation_store.py`'s `_att(**kw)` and `tests/integrity/
test_attestation_signatures.py`'s `_signed(**kw)`: **different shape** — `Attestation.create`
is a classmethod FACTORY, not the dataclass itself, so `dataclasses.replace` doesn't apply.
Read every call site first (`grep _att(` / `grep _signed(`) to find which kwargs are ever
actually overridden, then rewrote each helper to take those as EXPLICIT typed keyword params
(defaults matching the original dict literal) instead of a bare `**kw` — more code than a
splat, but each parameter's real type stays visible to the checker and to a reader.
`tests/integrity/test_attestation_vault_join.py`'s one `**base` site was narrow enough (only
`vault_token_accessor` varies) for a local closure instead of a reusable helper.

**One more `type-arg` closed while in this file family:** `tests/fixtures/attestation.py`'s
`dev_public_keys() -> dict` (bare) → `dict[str, Ed25519PublicKey]` — read
`core/attestation/verify.py`'s `make_verifier(public_keys: dict[str, Ed25519PublicKey], ...)`
first rather than defaulting to `dict[str, Any]`; this fixture's return type IS
`make_verifier`'s exact input shape, a known type, not an open payload.

**Verification:** `ruff check tests/` clean; pytest 743 passed / 4 skipped; `uv run mypy` →
165 (from 179). Commit `2471443`.

**Per-item running state:** Item 6 done (0 outside tests/). Item 7: 245 → 165 so far. Findings:
finding-0029 filed (parked, not blocking). Remaining error kinds (re-measure needed for exact
current breakdown, but expect from the Item-7-start kind tally minus what's now closed):
`union-attr` ~36 (the `X | None` narrowing family — next), remaining `arg-type` (mostly the
finding-0029-shaped Fake-vs-concrete-class errors, now measured red and left as such per the
finding's park), `type-arg` remainder, `operator` 10, `index` 5, `func-returns-value` few
left, `var-annotated` 4, `return-value` 3.

**Next action:** the `union-attr` family — `tests/integration/test_vault_sync.py`'s
`CatalogEntry | None` (11 of its 13 errors) and `tests/integration/test_lifecycle.py`'s
`RunRecord | None` (both seen recurring in every mypy tail this session) are the two biggest
concentrations. Per the plan's explicit T1 warning, read each site's actual runtime guarantee
before asserting past it — some may be genuine "catalog lookup after a fresh add, never None"
narrowing gaps (T2, safe to assert); a few might reveal a real reachable None the test
currently doesn't cover (T1 — file a finding, don't silently assert).

---

## Entry — 2026-07-11 — union-attr family closed; finding-0030 filed (245 → 123)

**`test_vault_sync.py` (11) + `test_lifecycle.py` (5).** Same "narrow past a just-written row"
T2 shape. `test_vault_sync.py`: one `_entry(sync, path)` helper (assert + comment naming the
invariant: every lookup follows a `sync_path`/`rescan`/`handle_deleted` for that exact path in
the SAME test) replaces 10 repeated `sync.catalog.get(...).FIELD` sites. `test_lifecycle.py`:
same shape for `RunLedger.last() -> RunRecord | None`, a `_last()` helper; separately fixed an
unrelated `func-returns-value` in the same file (`_launcher()`'s `Components` factory used
`calls.__setitem__(...)` lambdas — `dict.__setitem__` always returns `None`, checker-flagged
even when discarded via tuple-indexing — rewritten as three named functions with `calls: dict[
str, int]` and `_health`'s real `list[Flag]` return type).

**Eight more files, same family, smaller each.** `test_ledger.py` (`Proposal | None`, a `_get()`
helper) · `test_secrets_backend_wiring.py` (a DIFFERENT sub-shape worth naming: `SecretsBackend`
is a Protocol with only `mint_token`/`read_secret`; `.addr`/`.kv_mount` are `VaultClient`-
specific, so the fix is `isinstance(backend, VaultClient)`, not a bare not-None assert — one
sibling test in the same file already had this narrowing, the other test just didn't) ·
`test_attestation_vault_join.py` (`Attestation | None`, inline) · `test_version_history.py`
(`Version | None`, inline, two sites in one test) · `test_interface_gateway.py`
(`OutboundMessage | None`, a `_response()` helper) · `test_attestor_build_wiring.py` (`Attestor
| None`, missing an `isinstance` narrow three sibling tests in the same file already had) ·
`test_properties.py` + `test_factory_live.py` (a THIRD distinct union shape:
`MintedAgent | GateRequest`, `AgentFactory.mint`'s discriminated return — fixed with
`isinstance(result, GateRequest)`, not `hasattr()`, since `hasattr` doesn't narrow a type for
mypy the way `isinstance` does on a known closed union).

**T1 check (per the plan's explicit warning): none found.** Every one of the ~20 narrowing
gaps closed this entry was traced back, per-site, to a genuine "this test just created/wrote/
looked up this exact row/entry/response in the same test function" invariant — none revealed a
test silently passing over a reachable `None` it should have asserted against.

**finding-0030 filed — pre-existing, unrelated numerical flake, NOT bp-007's.** Running the
full ratchet mid-entry hit `tests/property/test_structural_interpreters.py::test_persistence_
is_stable_under_perturbation` failing on a Hypothesis-cached example (`n=4, seed=558,
eps=1e-08`) — a float32-precision-shaped tolerance gap in the bottleneck-stability property
test, unrelated to any typing work. Verified NOT caused by this session: `git stash`ed every
bp-007 change and it still failed identically; the file is byte-identical to `bfa19e1` (pre-
bp-007). Filed as `discovery`, routed to orchestrator (math-adjacent — a numerical-precision
design question, outside a mypy-scoped plan's mandate to resolve). Cleared the local,
gitignored `.hypothesis/` cache (confirmed via `git check-ignore` / `git status --ignored` —
untracked, disposable session state, not a source-of-truth fix) so bp-007's own gate reflects
a fresh-CI state rather than an accumulated local cache. The underlying numerical question is
parked, un-silenced (no tolerance widened, no xfail applied).

**Verification:** `ruff check .` clean; pytest 743 passed / 4 skipped (after clearing the
unrelated Hypothesis cache). `uv run mypy` → 123 (from 245 at Item 7's start). Commits
`a11b7bc`, `db307e0`, `795b595`.

**Per-item running state:** Item 6 done (0 outside tests/). Item 7: 245 → **123**. Findings this
session: finding-0029 (core-injectable-as-concrete-class, parked) and finding-0030 (persistence-
stability tolerance gap, parked, unrelated). Remaining error kinds (re-measure needed for exact
current numbers): `arg-type` (mostly finding-0029-shaped, now measured-red-and-parked) ·
`type-arg` (~18, mechanical bare-generic family, same as Item 6) · `operator` (~10) · `index`
(~5) · `var-annotated` (~4) · `return-value` (~3) · `func-returns-value` (~2 left) ·
`import-untyped`/`dict-item`/`attr-defined` (1 each).

**Next action:** re-measure fresh, then the `type-arg` remainder (mechanical, same convention as
Item 6 — should be fast), `test_cron.py`'s `SimpleNamespace`-as-`Job` shape (visible in every
mypy tail this session — check whether it's finding-0029-shaped or genuinely different before
deciding fix-in-scope vs park), then `operator`/`index`/`var-annotated`/`return-value` in
whatever order groups best by file. Aim: drive to the finding-0029 floor (the point where every
remaining error is the parked core-injectable-as-concrete-class shape, or a fresh distinct
family worth its own judgment call).

---

## Markers
