# bp-018 journal

## 2026-07-12 — session 1 start: setup, baselines, Q3 re-grep (builder)

**Status:** in-progress flipped (builder's flip); env synced (`uv sync --all-extras` —
worktree venv lacked dev extras); baselines pinned pre-change: `ruff check .` clean,
argless `uv run mypy` = **Found 69 errors in 20 files (checked 334 source files)** (the
pinned tail the gate must reproduce).

**Q3 re-grep at HEAD (plan §3 obligation):** callers of
`add_batch|is_projected|mark_projected` are `ops/code_sensor.py` (in scope),
`tests/unit/test_code_observations.py` (in scope), **and
`tests/unit/test_code_projection.py:111`** — `obs.is_projected(sha)` one-arg, a test
file the plan's Q3 inventory missed and write_scope omits. Not a §10 stop (test callers
are anticipated); it is a scope-grant gap. Resolution (finding-0047, spec-fidelity,
builder-resolves): honor §6(c) pins for `add_batch` (keyword-only required
`interpreter`) and `mark_projected` (required third arg) — their only callers are in
scope — and give `is_projected` alone `interpreter: str | None = None` where `None` =
"projected under ANY interpreter" (exactly the semantic that call site asserts). The
forgotten-arg hazard this default reopens is pinned shut by Item 4's bump→re-projects
acceptance test. Deviation annotated in code comment + finding.

Also checked: no existing test pins `_RESET_GUARD`/`reset_targets` (my Item 4 test will
be the first pin); `tests/unit/test_reference_extraction.py` constructs
`CodeSensor`+store but only via defaults — stays green untouched.

**Item 1 CLOSED** (commit `f8a2f95`): `INTERPRETER_VERSION = "1.0.0"` in
`ops/code_sensor.py` (§6(a) verbatim); `tests/unit/test_interpreter_versions.py` pins
`phi_code → ("1.0.0", 55e88303…)` over sources `(ops/code_sensor.py,
ops/code_snapshot.py)`; fingerprint = sha256 over (path, NUL, bytes, NUL) per file.
Acceptance run: 2 passed at HEAD; **falsifier-demo**: one appended byte →
`test_source_hash_matches_the_pin[phi_code]` RED (assertion message carries the
bump-or-re-pin instructions + the new hash); revert → green. Side-effect audit before
the demo: the test only reads file bytes + imports `ops.code_sensor` (regex compiles,
class defs — no store writes/network/subprocess); mutation restored from a scratchpad
backup, not `git checkout` (which would have eaten the Item 1 edit). Pre-commit gate:
ruff clean, argless mypy still 69 (335 files — new file adds zero), fast suite 838
passed / 7 skipped. NOTE for Items 3–4: every later edit to `ops/code_sensor.py`
re-reds the ratchet — each such commit re-pins the hash at 1.0.0 in the same commit,
journaled as a **declared refactor** (plumbing passes the version through; the batch
content φ_code emits is unchanged, so no worldview change — the same honesty argument
as §6(d)'s 1.0.0 backfill).

**Item 2 CLOSED** (commit `e4bf8a6`): `core/stores/observation_history.py` per §6(b) —
DDL verbatim; `archive` INSERT OR IGNORE on (store, identity_json, interpreter);
`chain` oldest-first by rowid (supersession only appends, so rowid IS generation
order), returns superseded rows verbatim; `count(store|None)`. Identity keys per
member in module registry `IDENTITY_KEYS = {"code": (commit_sha, path, qualname)}` —
the pinned 3-tuple archive shape carries rows not identity dicts, so the sidecar
extracts identity via the member's registered key columns (key-columns-only coupling,
lighter than the §11-rejected diff-grain coupling; bp-019 registers 'agent').
Acceptance: 9 passed — round-trip ordered, re-archive changes nothing (count + payload
pinned), per-member/family counts, unknown member = KeyError, **append-only pinned
structurally** (class-surface sweep: no delete/update/remove/…-shaped method; dunders
excluded — py3.13 dataclasses mint `__replace__`, a new-instance constructor, not a
row path), no-provenance-parameter sweep, open-helper path. Falsifier considered: an
API path that removes/mutates an archived row — none exists to call (swept), and a
second identical archive leaves count at 1. Ruff clean, argless mypy 69 (337 files),
fast suite 847 passed.

**finding-0047 FILED (spec-fidelity, route builder, resolved in-plan):** Q3's caller
inventory missed `tests/unit/test_code_projection.py:111` (`is_projected(sha)`
one-arg); write_scope omits that file. Resolution: `is_projected` alone gets
`interpreter: str | None = None` (None = ANY interpreter — the exact semantic that
call site asserts); `add_batch`/`mark_projected` keep the §6(c) pin verbatim. Hazard
guarded by Item 4's bump→re-projects test. Orchestrator may restore the pin at merge
per the finding's re-entry note.

**Next action:** Item 3 — `code_observations.py` migrations (§6(d) ALTER-add
interpreter, §6(e) projections copy-rename idempotent), new write API (§6(c) as
amended by finding-0047), §4 reconciliations (mark_projected comment rewrite +
docstring ledger-half cross-ref), new tests (i)–(v); acceptance (v) runs on a COPY of
the MAIN checkout's live store in the scratchpad (never open the original for write;
sqlite3 backup API from a read-only URI connection). Item 3's commit also carries the
minimal mechanical sensor call-site updates (pass INTERPRETER_VERSION) so the commit
is green; ratchet re-pin at 1.0.0 in the same commit = declared refactor (journaled).

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-self-sensing` (B-a; V2's
version-identity design; the owner's ledger-class reset ruling pinned as the
sidecar-file mechanism, §11). Grounding verified in-session: the degenerate
`is_projected(sha)` no-op path (`ops/code_sensor.py:207-208`), the promise-comment at
`code_observations.py:205-207`, `_RESET_GUARD` at `launcher.py:77-78`, sole-caller
check (Q3). No code written. Awaiting the owner's `proposed → ready` hand edit.
