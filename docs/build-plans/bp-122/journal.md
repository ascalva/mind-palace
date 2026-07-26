---
type: journal
plan: bp-122
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-122 (make the two self-mod tests hermetic, so the deploy gate stops lying)

> ## ⚑ BUILD COMPLETE — do NOT `/resume` this plan
> §7 Item 1 is built and its acceptance is met on both legs: the two target files are green **with a
> `config/local.toml` overlay present** (σ = 0.58, the owner's oq-0024 value), and the deploy gate's
> own command — `gate_cmd` verbatim — is **`2098 passed, 11 skipped, 21 deselected, 0 failed`** under
> that same overlay. The falsifier passed at **four** further σ values, and the forbidden fix
> (literal `0.62 → 0.58`) was constructed and **measured red**, so §7's rejection is empirical rather
> than argued. Committed on `worktree-agent-a84cf5d22c1f258e6`; **not pushed**.
>
> The plan is left at `status: in-progress` deliberately. Flipping it to `complete` is the
> ORCHESTRATOR's single-writer duty; a builder does not self-declare done.
>
> **What `/triage` owes:** flip bp-122 → `complete` + seal with `cost.actual` · **close
> finding-0214** — its re-entry condition is discharged verbatim, including the clause "*and the
> local CI-equivalent tier is green on a machine carrying a `config/local.toml` overlay*" and its own
> falsifier ("*set `similarity_threshold` to a third value in `local.toml` and re-run*") · note on
> **oq-0024** that its sweep axis stays open and that this was its *second* consequence (a builder
> may not edit an owner question) · **finding-0212 remains open** (a duty, not a code defect) and
> this session is a clean worked example for it: the local gate and CI now measure the same thing on
> this seam · ⚑ **the deploy gate's local half is unblocked** — no `--deselect`, no `--skip-tests`.
> **No finding was filed** (nothing in §10 fired).

Delegated builder, isolated worktree `agent-a84cf5d22c1f258e6`, branch
`worktree-agent-a84cf5d22c1f258e6`, based on `origin/main` = **`06b1b11`**
("bless(bp-123): proposed → ready") — the expected base, verified before starting.

Contract: `builder`. One item (§7 Item 1), one sitting.

---

## ⚑ Read this first — the worktree had NO `config/local.toml`, so the RED had to be simulated

`config/local.toml` is gitignored (`.gitignore:25`) and untracked, so it exists **only in the
owner's main checkout**, not in a worktree. `REPO_ROOT` is derived from the loader's own file path
(`core/kernel/config/loader.py:22`, `_LOCAL = REPO_ROOT / "config" / "local.toml"`), so in this
worktree `get_config()` returned the shipped default σ = **0.62** and both target tests **passed
trivially — proving nothing**, which is exactly the false green §7 warns about ("Green with the
overlay absent proves nothing; the overlay's presence is the test condition").

So this session **created** `config/local.toml` in *this worktree only* with
`[dreaming] similarity_threshold = 0.58`, reproduced the RED, made it green, ran the falsifier at a
third value, and then **deleted the file before committing**. The owner's main-checkout copy was
**never touched** — it was read once (read-only) per §2 manifest item 5, to confirm the oq-0024
rationale, and nothing else. Since the file is gitignored, its temporary presence cannot appear in
any commit.

---

## Checkpoint 1 — §2 manifest read; the RED reproduced under a simulated overlay

### §2 manifest — all six read in order, and what they settled

1. **`docs/findings/finding-0214.md`** — the diagnosis, not re-derived. Two assertions, one cause;
   escalated to `blocker` because `gate_cmd` (`launcher.py:586-597`) is byte-for-byte the tier
   these two fail. Its own falsifier ("set σ to a third value in `local.toml` and re-run") is the
   same one §7 names.
2. **`tests/integration/test_selfmod.py`** — line refs **accurate**: `_cfg` at `:35-42`, `_loop`
   `:45-51`, `_change` `:54`, the failing assertion `:76`. `_cfg` already performs the exact
   nested `dataclasses.replace` idiom the fix needs, on `selfmod`; the pin is one field over.
3. **`tests/integration/test_selfmod_cli.py`** — accurate: `_loop` `:25-33` (config built inline in
   two statements, no `_cfg` helper), failing assertion `:38`, and the assertion is a **formatted
   string** (`"0.62 -> 0.66" in out`), not a float compare.
4. **`core/kernel/config/loader.py:117-121`** — `DreamingConfig` is `@dataclass(frozen=True)` with
   `similarity_threshold: float`, so `dataclasses.replace` is the correct and only idiom.
5. **`config/local.toml`** (main checkout, READ ONLY) — `:47` holds `similarity_threshold = 0.58`
   under a comment block that is itself the oq-0024 record: it explicitly says *"This is the
   INSTANCE overlay, not the shipped default: defaults.toml keeps 0.62 so a fresh clone and CI are
   unchanged, and reverting is deleting these lines"* and that *"the σ-sweep harness (oq-0024 part
   b / bp-046) is what replaces this guess with a curve; oq-0024 STAYS OPEN on that axis."* That
   last clause is the whole warrant for §3's Q5 ruling: **σ is expected to move again**, so any fix
   that encodes today's σ is a fix with a scheduled expiry date.
6. **`ops/lifecycle/launcher.py:586-597`** — `gate_cmd` confirmed verbatim as the deploy gate's
   fifth condition, including the single finding-0105 deselect. This plan's acceptance *is* that
   command.

Also read (not in the manifest, needed to know *which* file the overlay lands in):
`config/loader.py` — a pure re-export facade of `core.kernel.config.loader` (bp-067/finding-0103);
both test files import `get_config` from it, so the real `load_config` that runs is core's, and
`REPO_ROOT` is per-checkout.

### Environment note (worktree-only friction, no bearing on the fix)

A fresh worktree `.venv` has no dev extras, so the first `uv run pytest` died with
`Failed to spawn: pytest`. Fixed with `uv sync --frozen --extra dev` — the same command CI uses
(`.github/workflows/ci.yml:38`). Not a defect; recorded so a resumer does not re-diagnose it.

### Measured — the false green, then the real RED

Before the overlay existed (worktree as cloned):

```
uv run pytest tests/integration/test_selfmod.py tests/integration/test_selfmod_cli.py -q
  ->  18 passed in 0.45s          # ⚑ the trivial pass. σ = 0.62, the assertions' own literal.
```

After creating the simulated overlay (`[dreaming] similarity_threshold = 0.58`):

```
uv run python -c "from config.loader import get_config; print(get_config().dreaming.similarity_threshold)"
  ->  0.58                        # the overlay reaches the loader, as finding-0214's Q2 says

uv run pytest tests/integration/test_selfmod.py tests/integration/test_selfmod_cli.py -q
  ->  2 failed, 16 passed in 0.15s
```

The two failures are **finding-0214's two, character for character**:

```
FAILED tests/integration/test_selfmod.py::test_good_change_traverses_the_gate_and_is_kept
  current_value=0.58 ... assert 0.58 == 0.62                                (test_selfmod.py:76)
FAILED tests/integration/test_selfmod_cli.py::test_propose_list_show_history
  assert '0.62 -> 0.66' in 'proposed #1: #1 [proposed] dream_similarity_threshold: 0.58 -> 0.66  (tighten themes)'
                                                                            (test_selfmod_cli.py:38)
```

That is the RED demo. The overlay's presence is the test condition, and it now holds.

### Next

Apply §6's pinned interface — a module-level `_SIGMA` constant used by **both** the fixture and the
assertions, in each file independently (no cross-import between the two test modules, per §4).

---

## Checkpoint 2 / SEAL — Item 1 closed; falsifier passed; forbidden fix measured red; gate green

### Status

**§7 Item 1 is complete and both legs of its acceptance are met.** The change is committed on this
worktree's branch and not pushed. `config/local.toml` (the simulation) has been deleted; the owner's
main-checkout copy was never written.

### Completed — §7 Item 1

The fix is §6's pinned interface, applied twice and independently:

- `tests/integration/test_selfmod.py` — a module constant `_SIGMA = 0.62`, pinned into the fixture
  via `dreaming=dataclasses.replace(cfg.dreaming, similarity_threshold=_SIGMA)` inside the existing
  `_cfg` nested-`replace` call (extended, not restructured, per §4), and the assertion at what is
  now `:86` reads `p.current_value == _SIGMA`.
- `tests/integration/test_selfmod_cli.py` — the same constant declared **independently** (not
  imported from the sibling module: §4 forbids coupling the two suites), the inline two-statement
  config build extended with the same `dreaming=` pin, and the render assertion is now
  `f"{_SIGMA} -> 0.66"`.

The f-string form is exact, not approximate: `ops/selfmod_cli.py:36` renders
`f"#{p.id} [{p.status}] {p.lever}: {p.current_value} -> {p.target_value}"`, i.e. plain `str(float)`,
so `f"{_SIGMA} -> 0.66"` produces the identical `"0.62 -> 0.66"` substring. No format spec needed.

⚑ **`0.62` now appears exactly once per file** — the `_SIGMA` definition. Verified by grep: no
literal σ survives in any assertion, which was §6's flagged failure mode.

Nothing else in either file was touched. The rollback, boiling-frog, master-switch, unattended and
`cmd_*` tests are byte-identical (§5).

### The evidence, in the order it was produced

| # | Condition | Code | Result |
|---|---|---|---|
| 0 | no overlay (worktree as cloned) | pre-change | **18 passed** — the false green §7 warns of |
| 1 | overlay σ = 0.58 | pre-change | **2 failed**, 16 passed — finding-0214's two, verbatim |
| 2 | overlay σ = 0.58 | **post-change** | **18 passed** |
| 3 | overlay σ = 0.60 | post-change | **18 passed** ← §7's named falsifier |
| 4 | overlay σ = 0.71 | post-change | **18 passed** |
| 5 | overlay σ = 0.555 | post-change | **18 passed** (both bound edges of σ ∈ [0.55, 0.75] probed) |
| 6 | overlay σ = 0.58 | **forbidden fix** (literal → 0.58) | 18 passed — *looks* fixed |
| 7 | overlay σ = 0.60 | **forbidden fix** | **2 failed** ← §7's rejection, MEASURED |

Rows 6–7 are the part worth keeping: §7 says the `0.62 → 0.58` edit "fails this and must be
rejected", and rather than take that on argument the forbidden fix was actually constructed (the
pre-change files, `sed`ed) and run. It is green only on the one value it special-cases and red on the
next, exactly as predicted. The real fix's rows 3–5 are green on every value. (The two files were
backed up to the scratchpad before this demo and restored from it after; the restored tree was
re-grepped to confirm all six `_SIGMA` sites are intact.)

**Row 1 is also the non-tautology proof (§3 Q5, §7 invariants).** The assertion is substantive
precisely because it *did* go red when the loop's observed value diverged from the pinned one — a
tautological form (`p.current_value == cfg.dreaming.similarity_threshold`, or reading `get_config()`
inside the assertion) could not have produced row 1's failure at all, since it compares the loop's
source against itself. What the assertion now proves is *the loop propagated the σ it was handed*,
which is a real property of `SelfModLoop.propose`; what it no longer does is depend on which machine
runs it. No test was deselected, skipped or `xfail`ed, and `gate_cmd` was not touched (§9).

### Local gate — all six legs, exact numbers

Run with `uv run` throughout; legs 1–5 after the change, leg 6 **with the σ = 0.58 overlay in place**
(the owner-machine condition — running it without the overlay would have proved nothing):

| Leg | Command | Result |
|---|---|---|
| ruff | `uv run ruff check .` | **All checks passed!** |
| import firewall | `uv run python scripts/check_imports.py` | **OK** — core imports no zone/networking module |
| mypy strict region | `uv run mypy core agents eval ops scheduler scripts` | **Success: no issues found in 258 source files** (0 errors) |
| mypy full | `uv run mypy` | **Found 69 errors in 20 files (checked 550 source files)** — the pinned tests baseline, **unmoved** |
| type gate | `uv run python -m ops.type_gate` | **OK** — tier-2 membership OK, bare-ignore scan OK |
| deploy gate | `gate_cmd` verbatim (see §2.6) | **2098 passed, 11 skipped, 21 deselected, 0 failed** in 75.36s |

The last row is §7's "real acceptance" and is the fifth `Launcher.deploy` gate byte-for-byte. A
test-only diff cannot move mypy's baseline off 69, and it did not — 69 exactly, not 70.

### In-flight

Nothing. The tree is clean apart from this journal, the two test files, and the `ready → in-progress`
status flip that `/build` step 2 requires.

### Next action

**Orchestrator only** — merge this branch, flip `status: in-progress → complete`, seal with
`cost.actual`, and close finding-0214 (see the banner at the top of this file for the full list of
what `/triage` owes). Nothing remains for a builder; do not `/resume`.

### Open questions

None routed, and **no finding filed** — no §10 stop condition fired:

- the gate is **not** still red after Item 1 (0 failed), so the "third divergence from CI" condition
  did not trigger;
- the falsifier's third-value run went **green**, not red;
- `config/local.toml` byte-for-byte restoration was **not at risk in this worktree** — the file did
  not exist here, so there was nothing of the owner's to restore. The one that holds his oq-0024
  ruling lives in the main checkout and was opened read-only, once. Its σ line still reads
  `similarity_threshold = 0.58` and its mtime is unchanged (`Jul 26 02:48`, hours before this
  session). ⚑ A future builder should note this asymmetry: **the plan's §7/§10 assume the
  owner-machine layout, and a worktree does not have it.** Getting a real RED requires simulating
  the overlay, and forgetting to simulate it converts the whole acceptance into a no-op.
- no temptation to widen `write_scope` arose; the fix fit entirely inside the two named files.

### Context-manifest delta

Read beyond §2's six:

- `config/loader.py` — needed to confirm the facade re-exports core's loader, so the `get_config()`
  the tests call is the one whose `REPO_ROOT` is per-checkout. This is *why* a worktree sees 0.62.
- `core/kernel/config/loader.py:22-34` — `REPO_ROOT = Path(__file__).resolve().parent×4`, hence
  `_LOCAL = <checkout>/config/local.toml`. The mechanism behind the "no overlay here" problem.
- `ops/selfmod_cli.py:35-36` — `_fmt`'s exact render string, so the CLI f-string is exact.
- `config/defaults.toml:262-274` — confirms σ = 0.62 is the shipped default and documents the
  bound σ ∈ [0.55, 0.75], which is what made 0.555 and 0.71 sensible falsifier values.
- `.github/workflows/ci.yml:38` — `uv sync --frozen --extra dev`, the fix for the empty worktree venv.

Proved irrelevant: nothing in §2 was stale or wasted — unusually, all six line references were
accurate as written.

### Read map

```read-map
tests/integration/test_selfmod.py:35: the design in six comment lines — why a pinned σ is load-bearing and not decoration
tests/integration/test_selfmod.py:51: the pin itself — dataclasses.replace on the frozen DreamingConfig, the one-field extension of an existing idiom
tests/integration/test_selfmod.py:86: the assertion that made row 1 go red — substantive, not tautological (§3 Q5)
tests/integration/test_selfmod_cli.py:24: why this constant is duplicated ON PURPOSE rather than imported from the sibling suite (§4)
tests/integration/test_selfmod_cli.py:49: the same fact as a formatted string — the shape that would have been missed by pinning only the fixture
```

+0 new tests (18 unchanged tests, 2 of them re-pointed); the diff is 25 insertions, 4 deletions
across two files. Mechanical coverage: none — this plan adds no test, it makes two existing ones
mean what they claim.

## Follow-through

- **Built?** Yes. §7 Item 1, the plan's only item, complete: both files pin σ in the fixture and
  assert against the pin. RED reproduced first, then GREEN, then a falsifier green at four further σ
  values, and the forbidden fix constructed and measured red.
- **Wired / delivered (or why dormant)?** **Delivered, and there is no ON switch to build** — this
  is a test-hermeticity fix, so "wired" means the gate that consumes it actually runs it, and it
  does: `gate_cmd` verbatim is `0 failed` under the owner's σ overlay. Nothing is flag-off or
  dormant. Committed on `worktree-agent-a84cf5d22c1f258e6`, **not pushed** — merge is the
  orchestrator's.
- **Does a consumer use it?** Yes, and it is the consumer that motivated the plan:
  `Launcher.deploy`'s **gate 5** (`ops/lifecycle/launcher.py:586-597`). Its command is byte-for-byte
  the tier these two tests were failing, so this diff is what lets `mind-palace deploy` past gate 5
  on the owner's machine without `--skip-tests`. `pytest` in CI is the second consumer and was never
  broken there — that asymmetry *was* the bug.
- **Track state (what remains on this track)?** This plan's track is empty. Still open around it:
  **oq-0024's sweep axis** (the σ-sweep harness that replaces the 0.58 guess with a curve — bp-046),
  **finding-0212** (the seal-attests-the-local-gate *duty*, a process gap with no code, explicitly a
  §9 non-goal here), and **bp-123** (the `local.toml → ouroboros.toml` rename, deliberately kept off
  this blocker fix). The other **57** `get_config()`-calling test files were **not** audited — §11
  parks that, and its re-entry condition is a third such false red or a proposed
  `get_config()`-in-tests lint.
- **Opened a new track/finding?** **No.** No §10 condition fired and nothing needed routing. One
  observation is recorded in Open questions above rather than as a finding, because it is guidance
  for a future reader rather than a defect: a plan whose acceptance depends on a **gitignored**
  machine-local file cannot be verified in a worktree without simulating that file, and the
  simulation is easy to skip because skipping it yields a *green* board. If that pattern recurs in a
  second plan it becomes a finding worth filing; on one instance it is a journal note.

### Ready to deskcheck

Per the deskcheck rule, this is **ready to deskcheck**, not done. The orchestrator should file it
into `docs/DESKCHECK-QUEUE.md`. The deskcheck is one command on the owner's own machine, where the
real `config/local.toml` lives:

```
uv run pytest tests/integration/test_selfmod.py tests/integration/test_selfmod_cli.py -q
```

Expected: **18 passed** — with his σ = 0.58 untouched and no overlay editing, no deselect, no skip.
For the fuller check, `gate_cmd` itself should now reach `0 failed`, and `mind-palace deploy` should
pass gate 5 once the daemon is up. A builder in a worktree cannot perform this check — that is
precisely why the RED had to be simulated here.
