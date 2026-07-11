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

## Markers
