---
type: build-plan
id: bp-106
track: ops
status: in-progress
design_ref: []
contract: builder
write_scope:
  - core/typedshims/psutil.py
  - ops/lifecycle/launcher.py
  - ops/type_gate.py
  - tests/unit/test_typedshim_psutil.py
  - tests/unit/test_type_gate.py
  - tests/unit/test_code_corpus.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 120k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/findings/finding-0198.md
  - docs/findings/finding-0176.md
  - docs/design-notes/type-system-as-core-audit.md
  - docs/build-plans/bp-105/journal.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0198.md
---

# Build Plan — the boundary shim is real: quarantine psutil, and make the one-file rule enforceable

## 0. Mode & provenance

Corrective. bp-105 shipped a raw `psutil` import at `ops/lifecycle/launcher.py:145`, warranted
inline and filed as **finding-0198**, because `core/typedshims/psutil.py` was absent from bp-105's
`write_scope` and CLAUDE.md forbids routing around a scope boundary. This plan discharges that
hand-off.

It is deliberately **not only** the mechanical move. Investigation (§3) established that the
one-file rule the move restores is **pure convention with zero mechanical enforcement** — which is
why the violation could be authored, reviewed, gated and merged without anything objecting. This is
the second recorded instance of the same shape: **finding-0176** is structurally identical
(*"bp-100 cannot reach its own objective inside its write_scope — the LanceDB typedshim is the fix,
and it is not writable"*), and its resolution, **bp-103 Item 1**, is the template this plan follows.

Per the owner's standing rule that *a property is only real when a test or ratchet proves it*, the
plan fixes the instance **and** builds the enforcement.

## 1. Objective

Raw `psutil` is touched in exactly one file, and a raw import of any shimmed dependency outside its
shim fails the gate.

### 1.2 Non-goals (explicit — see §9)

Not introducing a `duckdb` shim (§3 Q2 establishes duckdb resolves typed and needs none), not
widening the psutil shim beyond the two accessors bp-105 needs, not changing `_supervisor_alive`'s
D1/D2 semantics or any bp-105 test outcome, and not touching the finding-0191 write_scope-
partition question this is an instance of.

[INFERENCE] These are inferred from right-sizing, not from an owner statement. Read them at the
gate — a wrong non-goal fails silently forever (finding-0150).

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/findings/finding-0198.md` — the warrant, including the OPEN hand-off paragraph
2. `core/typedshims/psutil.py` — 46 lines; the destination and its idiom
3. `core/typedshims/lancedb.py` — the sibling shim bp-103 widened; the adapter precedent
4. `tests/unit/test_typedshim_lancedb.py:1-20` — **the model for Item 3's test**, and the source of
   the "the shim is HONEST, not a laundering proxy" framing
5. `ops/lifecycle/launcher.py:126-215` — `_CLOCK_SLACK_S`, `_process_identity`, `_supervisor_alive`
6. `ops/type_gate.py` — the whole file; `_EXCLUDED_DIRS`, `_imported_roots`, the two
   `*Violation` dataclasses, `bare_ignores`, `main()`
7. `docs/design-notes/type-system-as-core-audit.md:196-200` — the §2.5 **Boundary wrappers** clause
8. `pyproject.toml:149-157` — which deps are shimmed vs `ignore_missing_imports`
9. `tests/unit/test_code_corpus.py:275-292` — the one legitimate exemption (§3 Q4)
10. `docs/build-plans/bp-105/journal.md` Checkpoints 1–2 — why D1/D2 exist, so Item 2 does not
    "simplify" them away

**Does core already have this?** Yes, and that is the entire point — `core/typedshims/psutil.py`
already owns raw `psutil`, and `ops/type_gate.py` already owns AST-scan-and-fail. **Item 4 must not
build a new scanner**: it extends the existing one. Reuse `_EXCLUDED_DIRS`, the `Violation`
dataclass shape, and `main()`'s 0/1 contract.

## 3. Investigation & grounding  <!-- Part A -->

Done in session-47; every answer below is cited, so the builder starts from measurement.

- **Q1 — Is the one-file rule enforced by anything?** **No.** Nothing in `ops/type_gate.py`,
  `ops/import_lint.py`, `scripts/check_imports.py`, `.claude/hooks/*.sh`, `.github/workflows/ci.yml`
  or `[tool.ruff]` mentions `typedshims`. `pyproject.toml` references it twice — a coverage `omit`
  (`:93`) and a prose comment (`:150`) — neither of which enforces anything. There is no
  `flake8-tidy-imports`/`banned-api` config. **The rule is a docstring sentence.** This is the root
  cause of finding-0198, and it is why the fix cannot stop at the move.

- **Q2 — Which dependencies are actually in scope for the rule?** Exactly three:
  `lancedb`, `sknetwork`, `psutil` (`pyproject.toml:149-151`; shims exist for all three).
  **`duckdb` is NOT** — it is absent from both the shim list and the `ignore_missing_imports`
  override (`:155-157`), and the Tier-2 mypy floor is 0 errors, which it could not be if an
  unshimmed untyped `duckdb` were imported by `core/stores/telemetry.py:20`. So duckdb resolves
  typed and its raw imports are legitimate. §2.5 lists it as a *candidate*; V2 evidently cleared it.

- **Q3 — How many live violations exist today?** **Two**, and only two:
  - `ops/lifecycle/launcher.py:145` — raw `psutil` (bp-105; this plan's Item 1/2).
  - `tests/unit/test_code_corpus.py:280` — raw `lancedb`.

- **Q4 — Is the `test_code_corpus.py` violation sloppiness or legitimate?** **Legitimate, and it
  must survive.** It builds a *pre-bp-099 legacy table with no `current` column*
  (`:279-285`) to prove the additive migration preserves rows. The shim cannot construct that
  table — constructing a schema the shim refuses to model is the whole point of the test. A rule
  with no waiver mechanism would force this test to be deleted or the shim to grow a
  test-only backdoor. **Both are worse than the rule.** Hence Item 4's waiver (§6).

- **Q5 — Can the shim keep `psutil`'s exceptions inside it?** This is the load-bearing design
  question, and the code settles it. `_supervisor_alive` must never raise, and the states it must
  distinguish are `NoSuchProcess` and `AccessDenied` — **`psutil` types**. A thin *raising* facade
  (the `process_rss` idiom, `psutil.py:31-33`) therefore forces its caller to either import
  `psutil` to name them in an `except`, or catch bare `Exception`. **A boundary shim that raises
  third-party exceptions has not quarantined the dependency** — it has moved the import and left
  the type dependency. The shim must absorb them and return `None`. Precedent exists in the same
  file: `loadavg_1m() -> float | None` (`:41-45`) already returns Optional rather than leaking a
  platform failure.

- **Q6 — Is the psutil shim tested at all?** **No.** `tests/unit/test_typedshim_lancedb.py` exists
  (bp-103 Item 1, warrant finding-0176); there is no psutil counterpart. `core/vitals.py:19` and
  `ops/lifecycle/launcher.py:381,1118` are its only callers.

**Additional risks surfaced during reading:** `process_rss` (`psutil.py:31`) carries the same
latent exception leak Q5 describes — it raises `NoSuchProcess` at its caller. It is **out of scope
here** (no caller currently catches it, and changing its signature is a separate blast radius), but
it should be filed rather than silently noticed. See §10.

## 4. Reconciliation  <!-- Part B -->

- **`core/typedshims/psutil.py:3-5`** — *"This module is the ONE place core touches the raw
  package; the vitals path reads system measurements through these typed functions only."*
  → **cross-ref: extension.** The claim becomes true again (Item 1) and becomes *checkable*
  (Item 4). Amend the docstring to say the rule is enforced by `ops.type_gate`, and that the scope
  is the whole repo, not only `core/` — bp-105's violation was in `ops/`, which the current wording
  arguably does not cover. Do not silently rewrite: state that the sentence was aspirational until
  bp-106.

- **`ops/lifecycle/launcher.py:136-140`** — the `warrant(finding-0198)` paragraph explaining why
  the probe is quarantined in the launcher → **banner: correction.** The warrant is discharged;
  the comment must not survive as a fossil justifying a condition that no longer exists. Replace
  with the shim import, and leave one line recording that D1/D2 rely on the two accessors.

- **`docs/findings/finding-0198.md`** — the *"Open hand-off"* section → **banner: correction.**
  A builder may not edit an existing finding, so this is recorded here as owed to `/triage` at
  seal, not performed by the builder.

## 5. Write scope

`core/typedshims/psutil.py` (the two accessors — Item 1), `ops/lifecycle/launcher.py` (rewire to
the shim, drop the raw import — Item 2), `ops/type_gate.py` (the third scan — Item 4),
`tests/unit/test_typedshim_psutil.py` (new — Item 3), `tests/unit/test_type_gate.py` (new or
extended — Item 4), `tests/unit/test_code_corpus.py` (**one waiver comment only** — Item 5).

Deliberately OUT of scope: `core/vitals.py` (an existing shim caller, unchanged),
`tests/unit/test_restart_trustworthy.py` (bp-105's falsifiers must pass **untouched** — that is
Item 2's acceptance), `pyproject.toml`, `.github/workflows/ci.yml` (the gate already runs
`uv run python -m ops.type_gate`; no wiring change is needed — verify, do not edit), and every
foundation-denylist file.

## 6. Interfaces pinned inline

**Item 1 — the two accessors. Match the file's existing idiom** (`psutil.py:41-45`), Optional-
returning per §3 Q5:

```python
def process_create_time(pid: int) -> float | None:
    """Unix epoch seconds at which `pid`'s process was created, or None if unreadable.

    None, never an exception: `psutil.NoSuchProcess` / `AccessDenied` are psutil TYPES, so a
    raising facade would force every caller to import psutil to name them — moving the import
    while keeping the dependency. Absorbing them here is what makes the quarantine real."""


def process_name(pid: int) -> str | None:
    """`pid`'s process name (e.g. 'launchd', 'python3.13'), or None if unreadable.

    `name()` and not `cmdline()`: on macOS `cmdline()` raises AccessDenied for a foreign owner
    (measured against pid 1) while `name()`/`exe()` read fine — and a foreign owner is the
    deployed case, the daemon running as the `ouroboros` principal."""
```

Catch `Exception` inside each (the shim is the quarantine; breadth belongs here, not at the
caller), with a `# noqa: BLE001` warrant comment matching the launcher's current one.

**Item 2 — the launcher, after rewiring.** `_process_identity` collapses to a composition; its
`(create_time, name)` tuple contract and `_supervisor_alive`'s D1/D2 logic are **unchanged**:

```python
def _process_identity(pid: int) -> tuple[float | None, str | None]:
    """`(create_time_epoch, process_name)` for `pid` — either component None when unreadable.

    Both probes go through `core/typedshims/psutil.py`, the ONE module that touches raw psutil
    (type-system-as-core-audit §2.5, enforced by `ops.type_gate`). Unreadable is ambiguity, and
    ambiguity REFUSES — the owner ruling on finding-0186."""
    from core.typedshims.psutil import process_create_time, process_name
    return (process_create_time(pid), process_name(pid))
```

**Item 4 — the scan. The shimmed set and the waiver token, pinned:**

```python
# Dependency -> the ONE module permitted to import it raw (§2.5 boundary wrappers).
# duckdb is deliberately ABSENT: it resolves typed, so it needs no shim (bp-106 §3 Q2).
_SHIMMED: dict[str, str] = {
    "psutil":    "core/typedshims/psutil.py",
    "lancedb":   "core/typedshims/lancedb.py",
    "sknetwork": "core/typedshims/sknetwork.py",
}
_WAIVER = "typedshim-exempt:"   # inline, with a REASON, on the import line
```

The waiver deliberately mirrors the bare-ignore scan's shape (`ops/type_gate.py:183-195`): the
existing rule there is *every `# type: ignore` must carry an error code*; the new rule is *every
raw shimmed import outside its shim must carry a reason*. **Reuse `_EXCLUDED_DIRS`, the frozen
`Violation` dataclass shape with `__str__`, and `main()`'s print-then-`return 0 if ok else 1`
contract.** Do not write a second scanner.

## 7. Items

Ordered by blast radius: additive (read-only surface) → rewire → prove → enforce → waive.

### Item 1 — the psutil shim grows the two accessors

- **Objective:** `core/typedshims/psutil.py` exposes `process_create_time` and `process_name`.
- **Files:** `core/typedshims/psutil.py`
- **Acceptance test:** both return real values for `os.getpid()`; both return `None` for a pid
  above the ceiling (`2**22`) rather than raising.
- **Falsifier:** *either accessor propagates a `psutil` exception to its caller.* If it does, the
  quarantine is nominal — the caller still needs psutil to handle it (§3 Q5), and Item 2's
  `except Exception` would have to stay, which is the defect this plan exists to remove.
- **Invariants:** additive only; the four existing exports keep their signatures; local
  measurement only, no network (Invariant 2).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the launcher stops touching raw psutil

- **Objective:** `import psutil` no longer appears anywhere in `ops/`.
- **Files:** `ops/lifecycle/launcher.py`
- **Acceptance test:** ⚑ **`tests/unit/test_restart_trustworthy.py` passes UNCHANGED — all 24
  tests, with no edit to that file.** It is bp-105's falsifier set, including
  `test_a_recycled_pid_does_not_brick_start` and
  `test_a_pid_recycled_onto_a_long_lived_system_process_does_not_brick_start`. That it passes
  untouched is what proves this is a refactor and not a behaviour change.
- **Falsifier:** *any bp-105 test needs editing to accommodate the move.* That would mean the
  identity semantics changed under cover of a mechanical refactor — stop and raise (§10).
- **Invariants:** D1 (postdates the row) and D2 (not a Python interpreter) keep their exact
  meanings; `_CLOCK_SLACK_S` keeps its value and its warrant; ambiguity still REFUSES.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the psutil shim gets a test, like its lancedb sibling

- **Objective:** close §3 Q6 — the shim is no longer the only untested boundary wrapper.
- **Files:** `tests/unit/test_typedshim_psutil.py` (new)
- **Acceptance test:** model on `tests/unit/test_typedshim_lancedb.py`. Cover: real values for
  self; `None` (not an exception) for a dead pid; `process_name` readable for a **root-owned
  foreign process** (pid 1 — the deployed `ouroboros` case, measured in bp-105); and the honesty
  property — **the shim's declared surface is the WHOLE surface**, i.e. it is not a laundering
  `__getattr__` proxy onto raw psutil.
- **Falsifier:** *a raw-psutil attribute is reachable through the shim module.* Same falsifier
  bp-103 pinned for lancedb; a shim that proxies has quarantined nothing.
- **Invariants:** no network, no subprocess; must pass on a freshly-booted CI runner (do **not**
  assert on pid 1's `create_time` being old — that is uptime-dependent and would be flaky; assert
  only that it is *readable*).
- **Touches stored data?** No. **Parallelizable?** Yes, with Item 4. **Depends on:** Item 1.

### Item 4 — the rule becomes mechanical: a third `type_gate` scan

- **Objective:** a raw import of a shimmed dependency outside its shim, without a warranted
  waiver, fails `uv run python -m ops.type_gate`.
- **Files:** `ops/type_gate.py`, `tests/unit/test_type_gate.py`
- **Acceptance test:** the scan returns zero violations on the tree at HEAD (after Items 2 and 5),
  and `main()` prints an OK line alongside the two existing scans. Unit-test the scan against
  synthetic trees: a raw import in the shim itself → OK; outside it → VIOLATION; outside it with
  `# typedshim-exempt: <reason>` → OK; with a bare `# typedshim-exempt` and **no reason** →
  VIOLATION.
- **Falsifier:** ⚑ **reintroducing bp-105's exact line at `ops/lifecycle/launcher.py` leaves the
  gate green.** The scan must catch the very import that caused finding-0198 — a ratchet that
  cannot reproduce its own warrant is decoration. Demonstrate this explicitly.
- **Invariants:** function-local imports (`import psutil` inside a `def`) must be caught — bp-105's
  violation *was* function-local, so an AST walk that only inspects module level reproduces the
  hole; `_EXCLUDED_DIRS` still skips `.venv`/`__pycache__`/`docs`/`.claude`; the scan stays
  read-only (no writes, no network, no subprocess), matching the module docstring's promise.
- **Touches stored data?** No. **Parallelizable?** Yes, with Item 3. **Depends on:** none (but the
  gate only goes green once Items 2 and 5 land).
- **Note:** CI already runs `uv run python -m ops.type_gate` (`.github/workflows/ci.yml`, type-gate
  job). **Verify this; do not edit the workflow.** "Wiring is part of finishing" is already
  satisfied here — confirm it rather than assume it.

### Item 5 — the one legitimate exemption is warranted, not deleted

- **Objective:** `tests/unit/test_code_corpus.py:280` carries an explicit reason and passes Item 4.
- **Files:** `tests/unit/test_code_corpus.py`
- **Acceptance test:** the line becomes
  `import lancedb  # type: ignore[import-untyped]  # typedshim-exempt: builds a pre-bp-099 legacy
  table the shim cannot model (the migration under test)`, the test still passes, and Item 4's scan
  reports zero violations.
- **Falsifier:** *the exemption is used to make the test easier rather than to express something
  the shim genuinely cannot do.* If a shim call could construct that table, waive nothing — widen
  the shim or rewrite the test.
- **Invariants:** the migration test's meaning is unchanged; exactly one line moves.
- **Touches stored data?** No. **Parallelizable?** Yes. **Depends on:** Item 4 (token must be
  pinned first).

## 8. Math carried explicitly

N/A — no mathematical object. This plan moves an import and adds an AST scan.

## 9. Non-goals

- **No `duckdb` shim.** §3 Q2 establishes it resolves typed. Creating one would be cargo-culting
  §2.5's *candidate* list over its own V2 finding.
- **No widening of the psutil shim** beyond the two accessors. `cpu_percent`, `loadavg_1m`,
  `virtual_memory`, `process_rss` are untouched.
- **No change to `process_rss`'s raising signature** despite the latent leak (§3, additional
  risks) — file it (§10), do not fold it in.
- **No behaviour change to `_supervisor_alive`.** Item 2 is a refactor; its acceptance is that
  bp-105's tests pass unedited.
- **Not fixing finding-0191** (write_scope is not a partition of the diff). This plan is an
  *instance* of it; the systemic remedy — the integrator plan, or a seal gate detectable by
  arithmetic — is separate and larger.
- **No repo-wide sweep of `# type: ignore` warrants.**

## 10. Stop-and-raise conditions

- **A bp-105 test in `test_restart_trustworthy.py` requires editing to pass** ⇒ **STOP.** That is
  a behaviour change wearing a refactor's clothes, and it means the identity semantics moved.
- **The Item-4 scan cannot catch a function-local import** without re-implementing a scanner that
  duplicates `ops/import_lint.py` or `scripts/check_imports.py` ⇒ **STOP and raise**: whether the
  three AST walkers should be unified is a design question and an owner-visible DRY call, not a
  builder's.
- **The scan finds violations beyond the two in §3 Q3** ⇒ **STOP**, enumerate them, and file
  before waiving anything. A ratchet whose first act is to grant itself waivers is not a ratchet.
- **File (do not fix) the `process_rss` exception leak** as a new finding, cross-referencing
  finding-0198 §3 Q5.
- Any blessing transition (`proposed→ready`, `draft→ratified`) — the builder must never perform one.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| How an exemption is expressed | Inline `# typedshim-exempt: <reason>` at the import site | **Central allowlist in pyproject/type_gate** — rots: a path list outlives the reason and nobody rereads it, and it moves the justification away from the code. **No waiver at all** — forces deleting the legitimate migration test (§3 Q4) or growing a test-only shim backdoor; both worse than the rule | Owner objects to a third inline-comment protocol; then a central list with a mandatory reason column |
| Whether `tests/` is in the scan's scope | **Yes, in scope** — the one violation there is legitimate and is waived explicitly, which is more honest than a blanket exemption that would hide future real ones | **Exempt `tests/` wholesale** — cheapest, and precisely how the rule decayed into a docstring in the first place | A test-only violation class appears that the waiver cannot express |
| `process_rss`'s raising signature | Left raising; filed as a finding | **Fix it here** — widens the blast radius into `core/vitals.py`, an unrelated caller, inside a corrective plan | The finding is triaged, or a caller actually needs to handle the failure |

## 12. Dependency & ordering summary

```
Item 1 (shim accessors)  ──┬──► Item 2 (rewire launcher)  ──┐
                           └──► Item 3 (shim test)          ├──► gate green
                                Item 4 (type_gate scan) ────┤
                                Item 5 (warrant the waiver) ┘   (5 depends on 4's token)
```

Item 1 is the only hard prerequisite. Items 3 and 4 are parallelizable with each other; Item 4 is
independent of 1–3 and could be built first, but is sequenced after so its "zero violations at
HEAD" acceptance is reachable in one pass. **Item 4 is the item that matters** — Items 1–3 fix one
instance, Item 4 is why there will not be a third. One session; the whole plan is a move, a scan,
and two test files.
