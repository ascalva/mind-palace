---
type: finding
id: finding-0223
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-106/plan.md                  # §3 Q3's census, §5's write_scope, §10's STOP
  - ops/type_gate.py                                 # raw_shim_imports + the parked _RAW_SHIM_SCAN_IS_FATAL
  - tests/unit/test_restart_trustworthy.py           # the unwaivable violation, line 21
  - tests/unit/test_type_gate.py                     # where detection IS enforced meanwhile
  - docs/findings/finding-0198.md                    # the warrant bp-106 discharges
  - docs/findings/finding-0211.md                    # bp-121, which created the violation
  - docs/findings/finding-0191.md                    # write_scope is not a partition of the diff
ftype: spec-fidelity
origin_plan: bp-106
route: builder
resolution: null
---

# bp-106's ratchet lands one line short of fatal: the third raw-psutil import is in a file bp-106 may not touch

## What

bp-106 §3 Q3 censused the live violations of the §2.5 boundary-wrapper rule as **"Two, and only
two"**, and §10 made a census miss a **STOP** condition: *"the scan finds violations beyond the two
in §3 Q3 ⇒ STOP, enumerate them, and file before waiving anything. A ratchet whose first act is to
grant itself waivers is not a ratchet."*

Item 4's scan found **four**, not two. Enumerated:

| # | Site | Status after bp-106 |
|---|---|---|
| 1 | `ops/lifecycle/launcher.py:159` — raw `psutil` (bp-105, finding-0198) | **FIXED** — Items 1+2 moved it into the shim |
| 2 | `tests/unit/test_code_corpus.py:280` — raw `lancedb` | **WAIVED** — Item 5, in `write_scope`, §3 Q4 established it as legitimate |
| 3 | `tests/unit/test_typedshim_psutil.py:32` — raw `psutil` | **WAIVED** — created by Item 3 itself, in `write_scope` |
| 4 | ⚑ `tests/unit/test_restart_trustworthy.py:21` — raw `psutil` | **UNWAIVABLE BY bp-106** — see below |

Entry 4 is the finding. It did not exist when bp-106 was written: it was added on **2026-07-26 by
`e49a715`** (`build(bp-121): D2 probes the executed interpreter, not the argv0 name`, warrant
finding-0211) — the same day, hours before this build. §3 Q3's census was accurate when authored.

**It is a legitimate exemption, in exactly the category §3 Q4 already recognized.** The test
monkeypatches `psutil.Process` on the real module object and constructs `psutil.NoSuchProcess`, in
order to pin process shapes the host cannot be made to have (a console-script `name()` on Linux, an
`AccessDenied` `exe()`) — which is the only way finding-0211's cross-platform regression can be
tested at all, since the bug was invisible on macOS for 55 consecutive red CI runs. The shim cannot
supply either the module object or the exception type without becoming the laundering `__getattr__`
proxy that `test_typedshim_psutil.py`'s own falsifier forbids. So it needs a one-line waiver, not a
rewrite.

**And bp-106 may not write that line.** `tests/unit/test_restart_trustworthy.py` is named in §5 as
deliberately OUT of `write_scope`, and Item 2's acceptance is that it *"passes UNCHANGED — all 24
tests, with no edit to that file"*, because passing untouched is the proof that the psutil move was a
refactor and not a behaviour change. `scope-guard` denies the edit pre-hoc; CLAUDE.md is
unconditional — *"a denial means narrow the scope or file a finding — never route around."*

That is a three-way bind: the plan cannot reach its own "zero violations at HEAD" acceptance without
either (a) editing a file it is forbidden to edit, (b) hardcoding a self-granted exception, which is
literally what §10 forbids, or (c) reddening `uv run python -m ops.type_gate`, the authoritative
CI gate — which after finding-0211 has only just come back green and which hard-blocks
`mind-palace deploy`.

**What was built instead** — recorded here because it is a deviation from §7 Item 4's acceptance:

- `raw_shim_imports()` is complete, reuses `_imported_roots`/`_EXCLUDED_DIRS`/the `Violation` shape
  (no second scanner), and is proven on 16 planted fixtures — including
  `test_the_scan_catches_bp105s_exact_violation_line`, which replants finding-0198's import
  character-for-character, function-local and with its original warrant comment, and requires it be
  caught. Item 4's named falsifier is discharged.
- `main()` runs it and PRINTS every violation, but `_RAW_SHIM_SCAN_IS_FATAL = False` keeps it out of
  the exit code for now. **Detection is not on the honour system**: the live tree is asserted in
  `tests/unit/test_type_gate.py::test_the_live_tree_has_exactly_the_one_known_parked_violation`,
  which CI's `ratchet` job runs. A NEW bp-105-shaped import goes red **today** — the property
  finding-0198 proves was missing is in place. Only the *last* violation is tolerated, by name, and
  the test goes red when it is fixed, so the parked state cannot be forgotten.

## Why it matters

1. **The rule is one line from mechanical, and the line is trivial.** Everything expensive — the
   scan, the waiver protocol, the falsifier reproduction, the fixtures — is built and green. What
   remains is a comment on one import line.
2. **It is a clean, small instance of finding-0191** (*write_scope is not a partition of the diff*),
   and a sharper one than bp-105's: bp-105 could at least quarantine its violation behind a helper,
   whereas here the plan's own success criterion is unreachable inside its scope. The arithmetic is
   as simple as an instance gets: one file, one line, one token. Worth attaching to finding-0191 as
   evidence when the systemic remedy (an integrator plan, or a seal gate detectable by arithmetic)
   is designed.
3. **The census-vs-reality gap is itself the recurring shape.** bp-106 was authored 2026-07-25 and
   built 2026-07-26; one intervening commit invalidated both a §3 investigation answer *and* a §6
   pinned interface (§6 pins two accessors; bp-121 made the launcher read three). A plan's §3
   measurements are perishable, and nothing currently re-measures them at build start. bp-106's
   §10 caught this one only because its author thought to make a census miss a stop condition —
   that is not a general mechanism.
4. **A second exemption class is now evident, not hypothetical.** Two of the four sites (entries 3
   and 4) are *tests of a boundary*, which structurally must reach the raw package. §11's parked
   decision *"whether `tests/` is in the scan's scope"* recorded "Yes, in scope" on the evidence of
   ONE test violation; there are now two, and both are legitimate. The inline-waiver mechanism
   handles them fine — this is not an argument for exempting `tests/` — but the class deserves
   naming in the design note so the next reader does not mistake it for sloppiness.

## Re-entry condition

Add the waiver to `tests/unit/test_restart_trustworthy.py:21`, from any plan whose `write_scope`
includes that file (or the orchestrator, at `/triage`):

```python
import psutil  # type: ignore[import-untyped]  # typedshim-exempt: patches `psutil.Process` and names `NoSuchProcess` to pin process shapes the host cannot have (finding-0211); the shim cannot hand those out without becoming a laundering proxy
```

Then, in the same change: flip `_RAW_SHIM_SCAN_IS_FATAL` to `True` in `ops/type_gate.py` (its
comment carries this instruction), and replace the live-tree test's parked assertion with
`assert raw_shim_imports(REPO_ROOT) == []`. The test's failure message says the same thing, so the
suite will demand it. Total diff: three lines, and the rule is fully mechanical.

**Two smaller items owed in the same pass:**

- `tests/unit/test_restart_trustworthy.py:237-239` — `_fake_psutil`'s docstring says
  *"`_process_identity` imports psutil lazily inside its own body (warrant finding-0198)"*. After
  bp-106 the lazy import is in `core/typedshims/psutil.py`; the *mechanism* it depends on
  (attribute resolution at call time) is unchanged and all 37 tests pass, but the prose is one hop
  stale. Same file, same reason it was not fixed here.
- `docs/findings/finding-0198.md`'s *"Open hand-off"* section is now discharged and should be
  marked so (bp-106 §4 records this as owed to `/triage`; a builder may not edit an existing
  finding).

## Routing

`spec-fidelity` → the builder resolves and continues, which is what happened: the instance is
fixed, the ratchet is built, the residue is parked with the exact re-entry above and nothing is
blocked. Two items in it are nonetheless **orchestrator-visible on purpose** and should not be
silently closed at `/triage`:

- the §11 parked decision on `tests/` scope now has more evidence behind it (point 4);
- point 3 — that a plan's §3 census silently perishes between authoring and build — is a
  `direction`-shaped observation about the graduate→build gap, not a codebase defect. It belongs
  with finding-0191 rather than being resolved here.

## Also noted, not fixed (bp-106 §10's fourth clause)

`core/typedshims/psutil.py`'s `process_rss` still **raises** `psutil.NoSuchProcess` at its caller
rather than returning `None`, which is the same exception leak §3 Q5 rules out for the accessors
bp-106 moved. §9 makes not changing it an explicit non-goal (it would widen the blast radius into
`core/vitals.py`, an unrelated caller, inside a corrective plan) and §10's last clause requires it
be filed rather than folded in — so it is filed here rather than as a separate finding, since it
shares this one's file and its §11 parked-decision row (*"`process_rss`'s raising signature — left
raising; filed as a finding"*). It is now pinned by a test
(`test_the_pre_bp106_surface_still_behaves` asserts the raise), so the behaviour cannot drift
unnoticed while the decision waits. Re-entry: a caller actually needs to handle the failure, or the
decision is triaged.
