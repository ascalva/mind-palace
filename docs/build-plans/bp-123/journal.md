---
type: journal
plan: bp-123
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-123 (the per-machine overlay becomes `config/ouroboros.toml`)

> ## ⚑⚑ ITEM 2 IS OWED ON MERGE — the orchestrator must run it, in the MAIN checkout
>
> This was a **delegated worktree build, scoped by the orchestrator to Items 1 and 3 only**.
> Item 2 was **not attempted and could not be**: it moves `config/local.toml`, which is gitignored
> and untracked, so it exists **only in the owner's main checkout** — there is no such file in this
> worktree (verified: `ls config/` shows `defaults.toml`, `tuning.toml`, `loader.py`,
> `secrets_backend.py`, `__init__.py`, `sweeps/` and nothing else).
>
> ⚑ **The moment Item 1 lands in the main checkout, config loading there REFUSES** — because a
> legacy `config/local.toml` does exist there. **That is the intended design, not a bug**; it is the
> entire point of Item 1 and the reason §12 orders Item 1 → Item 2 strictly. Everything that reads
> config (the daemon, `palace`, most of pytest) stays refused until the `mv` is done. The full
> hand-off, with the exact commands and the readings the plan requires, is
> **Checkpoint 3 — "Item 2, owed on merge"** below. Nothing there needs re-deriving.

Delegated builder session, worktree `worktree-agent-a385f65305e0f74a5`, branched from
`origin/main` @ **`06b1b11`** ("bless(bp-123): proposed → ready") — verified before starting, base
matches the orchestrator's stated expectation. Contract: `builder`.

**Committed on the branch, NOT pushed. Plan left at `status: in-progress`** — flipping to
`complete` is the orchestrator's single-writer duty, and it is not earned until Item 2 runs.

---

## Checkpoint 1 — §2 manifest read; Item 1 built, all four guard states demonstrated

### §10 stop conditions cleared before touching anything

- **Daemon is DOWN** (§10's first condition, §3's Q5). No pidfile under `data/run/`, no
  `data/*.pid`, no python supervisor process; `data/logs/palace.out.log` was last written
  **2026-07-24 22:30**, two days stale. The `launchctl` entries that do exist are
  `com.mind-palace.vault` (the unseal helper) and `com.mind-palace.backup`/`token-rotate`, none of
  which is the reasoning daemon. So there is no live process to mis-load config mid-flight.
- **σ-before-the-move (§10's second condition) is NOT checkable from this worktree** and is
  deliberately deferred to the orchestrator with Item 2 — see Checkpoint 3. Reading it here would
  have measured the wrong tree.

### §2 manifest — read in order; three things worth not re-deriving

1. **§3's Q1 is exactly right: one operative reference.** `loader.py:29`
   (`_LOCAL = _CONFIG_DIR / "local.toml"`). Confirmed by grep — every other `local.toml` in `*.py`
   is a comment or docstring.
2. **§3's Q3 is right about the mechanism but off by one on the count.** It says "all five patch the
   **symbol** `_LOCAL`". In fact only **four** of the five write_scope test files patch it
   (`test_code_ingest_wiring.py:54`, `test_inference_seam.py:339`, `test_levers_overlay.py:20,32,39`,
   `test_secrets_backend_wiring.py:43`). The fifth, `test_config_split.py`, contained only a *prose*
   reference at `:30` — no patch site. This changed nothing about the work (that file is where the
   new guard tests belong anyway) but a future reader should not go hunting for a fifth patch site.
3. **⚑ A `_CONFIG_DIR`-only monkeypatch is a NO-OP, which matters for how §7's acceptance is
   satisfied.** §7 Item 1 asks for the guard tests with "`_CONFIG_DIR` patched into `tmp_path`", but
   `_INSTANCE_OVERLAY` / `_LEGACY_OVERLAY` / `LEVERS_OVERLAY` are all derived from `_CONFIG_DIR` **at
   import time** — patching `_CONFIG_DIR` alone would leave every derived constant still pointing at
   the real `config/`, i.e. the test would silently be running against live state, the one thing §6
   and §10 forbid. So the helper `_isolated_config_dir` patches **all four**. `_DEFAULTS` is
   deliberately left alone (the committed defaults are the baseline being overlaid).
   I did *not* make the guard re-derive its paths from `_CONFIG_DIR` at call time, which would have
   matched §7's wording literally: that would put two sources of truth on the same path (the guard
   re-deriving while `_overlay` uses the module global) — the duplication the owner treats as a
   defect. Single source of truth = the module constants; tests patch those.

### What Item 1 changed

`core/kernel/config/loader.py`:

- `_LOCAL` → **`_INSTANCE_OVERLAY = _CONFIG_DIR / "ouroboros.toml"`** (§11's decided default), plus
  a retained **`_LEGACY_OVERLAY = _CONFIG_DIR / "local.toml"`** that is *never read as config* and
  exists only so the guard can refuse.
- New **`ConfigMigrationError(RuntimeError)`** and **`_refuse_on_legacy_overlay()`**, called as the
  first statement inside `load_config`'s `if path is None:` branch — *before* either overlay is
  applied. An explicit `path` bypasses the whole chain, guard included: that stays a verbatim read
  of the file the caller named, which is what keeps `load_config(_DEFAULTS)` assertions working.
- Docstring/comment updates at the four *instructional* sites (`[secrets] grant_roles`, `[backup]`,
  `[selfmod]`, `[runtime]`) and the precedence comment.

**Precedence is unchanged** (Item 1's invariant): `_overlay(raw, LEVERS_OVERLAY)` still runs before
`_overlay(raw, _INSTANCE_OVERLAY)`, so a human override still beats a loop-tuned knob. I kept the
"human authority stays supreme" sentence intact and only moved the filename, per §4.

`.gitignore`: added `config/ouroboros.toml`, **kept** `config/local.toml`. The old entry stays for a
reason now written into the file — an un-migrated machine must not be able to *commit* its overlay
while the guard is telling it to `mv`.

The five test files: `_LOCAL` → `_INSTANCE_OVERLAY` at every patch site, three test names updated
off "local"/"local_toml", and — the one judgement call — **each site that drives the default
`load_config()` path also now redirects `_LEGACY_OVERLAY` into `tmp_path`.** Without that these
tests would assert differently depending on whether the machine running pytest happens to still
have a pre-rename `config/local.toml`; with it they are hermetic. This is squarely §6's "never
against the real `config/` dir", and it is also what will keep the suite green in the main checkout
during the window between merge and Item 2.

### Item 1 acceptance + falsifier — all four states driven for real

Not just asserted in tests: the loader was driven directly with every path redirected into a
throwaway tmp dir. Verbatim output:

```
STATE A - neither file present (fresh clone / CI): must load CLEANLY
  loaded OK; sigma = 0.62 (committed default); secrets.enabled = False

STATE B - overlay under the NEW name: must be READ
  loaded OK; sigma = 0.58 (from the overlay)

STATE C - BOTH present: must REFUSE as ambiguous
  ConfigMigrationError:
    two per-machine config overlays are present, and which one carries authority is ambiguous:
        <tmp>/local.toml  (the pre-2026-07-26 name)
        <tmp>/ouroboros.toml  (the current name)
    Refusing to load rather than guess which one wins. Merge whatever you still need out of
    local.toml into ouroboros.toml by hand, then remove the legacy file:
        rm <tmp>/local.toml

STATE D - LEGACY ONLY (owner's machine post-merge, pre-Item-2): must REFUSE
  ConfigMigrationError:
    the per-machine config overlay was renamed local.toml -> ouroboros.toml on 2026-07-26, and
    this machine has not been migrated:
        <tmp>/local.toml  exists (the old name — NO LONGER READ)
        <tmp>/ouroboros.toml  is missing (the name the loader reads)
    Loading now would silently ignore every setting in local.toml and come up on the committed
    defaults instead. Refusing to load. Move the file — `mv`, never rewrite, the bytes are an
    owner ruling:
        mv <tmp>/local.toml <tmp>/ouroboros.toml
```

- **State A is Item 1's named invariant** and it is also this worktree's own condition, so a
  mistake here could not have hidden: CI and a fresh clone still load from committed defaults.
- **States C and D are the two required refusal branches.** Both `raise`; neither warns.
- **State B → D is §7's falsifier**, run against a copy in tmp: σ demonstrably reads `0.58` from the
  overlay, and after the file is renamed back to the legacy name the loader **refuses** instead of
  quietly returning `0.62`. Had it returned `0.62`, the guard would be decorative and Q4's
  silent-reversion risk would still be live.
- Both refusal messages **name both filenames and give the exact command**, because per the
  orchestrator's brief that message is the owner's only instruction at that moment.

Four new tests in `tests/unit/test_config_split.py` pin exactly these: the two refusal branches, the
neither-present invariant, and the falsifier. Targeted run of all five write_scope test files:
**47 passed**.

Note the worktree needed `uv sync --extra dev` first — a fresh worktree venv has no pytest.

---

## Checkpoint 2 — Item 3 done in scope; its acceptance grep is NOT clean, and cannot be. finding-0216

### What Item 3 changed

`config/defaults.toml` — **comment text only, verified mechanically**: filtering the diff to
non-comment, non-blank changed lines returns nothing, and `similarity_threshold` is still `0.62`
(§5's ⚑, and the invariant that keeps a fresh clone and CI unaffected). Eight comment sites moved to
the new name. `core/models/inference.py:79` — the one-line comment. `docs/runbook.md` — ten
references, plus a **new "The per-machine config overlay" subsection under Setup** carrying the
rename, the precedence rule, and the `mv` the guard demands. That doc is the one followed during
setup and recovery, so it is where the migration note earns the most.

### ⚑ Item 3's acceptance criterion is unsatisfiable within write_scope — filed as finding-0216

The criterion greps **eight directories** (`config/ core/ ops/ scheduler/ edge/ agents/ eval/
scripts/` + the runbook) but `write_scope` grants **three files inside them**. §3's Q2 undercounted:
it estimated "~10 in code/config comments"; the real figure inside the grep's own directories is
**~24 across 10 files**, of which **13 in 6 files** are live instructions this plan cannot touch.
I did not widen scope (CLAUDE.md: a denial means narrow the scope or file a finding, never route
around). All of it is enumerated with exact path:line in **finding-0216** — three tiers, of which
**Tier 1 is the sharp one: three references are emitted to the owner AT RUNTIME**
(`ops/backup/run.py:25` stderr, `scripts/build_sandbox_image.sh:17` echo, and `ops/apply.py:33-34`,
which bakes the dead name into the generated `config/levers.toml` header on every knob write). After
this plan those strings tell the owner to edit the one filename that makes config loading refuse.

Also caught, and invisible to that grep: **`config/loader.py:11`** names the symbol `_LOCAL`, which
§11's rename deleted. A future test author following it gets an `AttributeError` from
`monkeypatch.setattr`. The acceptance grep would have passed while leaving that broken.

### A pre-existing defect found while editing, NOT introduced here — the `[planes]` instruction

`config/defaults.toml`'s `[planes]` comment claimed the block is parsed "with the local.toml overlay
honored" and told the reader to "flip it in config/local.toml, not here". **Both halves are false,
independently of the rename**, and I checked rather than assumed: `scripts/verify_planes.py` only
calls `get_config()`, and the same comment correctly says there is deliberately no `PlanesConfig`
(schema'd loading drops unknown sections), so the verifier gets nothing about `[planes]` from config.
The sole real reader is `tests/unit/test_plane_migration.py:397`, which parses
`config/defaults.toml` **directly**, honoring no overlay at all. Flipping `[planes] enabled` in any
per-machine overlay is therefore **inert**.

Rather than faithfully translate a false instruction into the new filename, I removed the overlay
claim and left an inline pointer to finding-0216. **Where that master switch should live is a design
call, and I did not make it** — it is routed in the finding as its own thread.

### The local gate — all six legs, on the final tree

| Leg | Result |
|---|---|
| `uv run ruff check .` | **All checks passed** (one E501 I introduced in a docstring, fixed) |
| `uv run python scripts/check_imports.py` | **OK** — core imports no zone or networking module |
| `uv run mypy core agents eval ops scheduler scripts` | **Success: no issues found in 258 source files** (0 errors) |
| `uv run mypy` | **69 errors in 20 files** (checked 550) — exactly the baseline, unmoved |
| `uv run python -m ops.type_gate` | **OK** — Tier-2 membership OK, bare-ignore scan OK |
| `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' --deselect …` | **2102 passed, 11 skipped, 21 deselected, 0 failed** in 59s |

⚑ **Zero failures — the two finding-0214 `test_selfmod*.py` failures did NOT appear**, exactly as the
orchestrator predicted for a worktree with no `config/local.toml`. So nothing here masks bp-122's
territory, and no failure in this run belongs to anyone else.

Diff is exactly the ten `write_scope` paths + `plan.md` (the status flip alone) + this journal + the
new finding. Nothing else touched.

---

## Checkpoint 3 — ⚑ Item 2, owed on merge: the orchestrator's runbook

Item 2 was **out of this build's delegated scope and impossible here**: `config/local.toml` is
gitignored and untracked, so it lives only in the owner's main checkout. Attempting it in a worktree
would have no-op'd or hit the wrong tree.

### ⚑ The one thing to get right: σ-before must be read BEFORE the merge

This is the sequencing trap, and it follows from Item 1 working correctly. The moment Item 1 lands
in the main checkout — where a legacy `config/local.toml` **does** exist — `get_config()` raises
`ConfigMigrationError`. So the plan's "record σ before" reading **cannot be taken through the loader
after merging**. Two ways out; the first is preferred:

- **Take σ-before pre-merge** (loader still reads `local.toml`), then merge, then `mv` immediately.
- Or read the file directly, bypassing the loader, which works in either state (fallback below).

### Expect the main checkout to be broadly RED between merge and the `mv`

Not a regression — the guard doing its job. **59 test files** reach the default config path, plus
`palace`/`mind-palace` won't start. **Do the `mv` immediately after merging, before running the
suite.** (The five write_scope test files are hermetic — they redirect `_LEGACY_OVERLAY` into
`tmp_path` — but the rest of the suite is not, and making it so was not in scope.)

### The commands, in order

```sh
cd /Users/ascalva/mind-palace

# 0. PRE-FLIGHT (§10): the daemon must be DOWN. It was down at build time (2026-07-26): no
#    data/*.pid, no python supervisor process, data/logs/palace.out.log stale since 07-24 22:30.
#    Re-confirm; if it is UP, STOP — §10 makes that a different plan, with a drain in it.

# 1. σ BEFORE — ⚑ run this BEFORE merging bp-123. Expect exactly 0.58.
#    §10: anything other than 0.58 => STOP. The starting state is not what the plan assumes.
uv run python -c "from config.loader import get_config; print(get_config().dreaming.similarity_threshold)"

#    Fallback if you have already merged (bypasses the loader, so the guard cannot interfere):
uv run python -c "import tomllib,pathlib; print(tomllib.loads(pathlib.Path('config/local.toml').read_text())['dreaming']['similarity_threshold'])"

# 2. Scratchpad copy FIRST — untracked, gitignored, ONE copy, carries owner ruling oq-0024's
#    σ retune plus its rationale. Unrecoverable from the repo if lost.
cp -p config/local.toml ~/ouroboros-overlay-backup-2026-07-26.toml

# 3. Checksum BEFORE
shasum -a 256 config/local.toml

# 4. …merge this branch…  then THE MOVE — `mv`, never rewrite (§10 / Item 2's invariant)
mv config/local.toml config/ouroboros.toml

# 5. Checksum AFTER — must equal step 3. If it differs: STOP IMMEDIATELY and restore from step 2.
shasum -a 256 config/ouroboros.toml

# 6. σ AFTER — must still print 0.58, and must not raise.
uv run python -c "from config.loader import get_config; print(get_config().dreaming.similarity_threshold)"

# 7. Confirm the suite comes back
uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' \
  --deselect 'tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core'
```

### Readings to record in this journal (git cannot witness the move — §3's added risk)

| Reading | Expected | Actual |
|---|---|---|
| σ before the move | `0.58` | _owed_ |
| sha256 before | (record it) | _owed_ |
| σ after the move | `0.58` | _owed_ |
| sha256 after | identical to before | _owed_ |
| `get_config()` raises after? | no | _owed_ |

**Item 2's falsifier:** σ reads **`0.62`** after the move ⇒ the overlay is no longer being read —
Q4's silent reversion, caught by measurement instead of by surprise weeks later. Also expect the two
finding-0214 `test_selfmod*.py` failures to reappear in the main checkout once config loads again;
those are bp-122's, not this plan's.

### What else /triage owes

- Flip **bp-123 → `complete`** and seal with `cost.actual` — **only after Item 2's readings are in**.
  Items 1 and 3 are done; Item 2 is not, so `complete` is not yet earned.
- Route **finding-0216** (filed here): the mechanical residue is a one-item follow-up plan; the
  `[planes]` master-switch question is a separate, non-mechanical thread needing an owner ruling.
- Note against §11's third row that the legacy guard's **deletion condition is now written into the
  code** (`_LEGACY_OVERLAY`'s comment and the runbook both say it goes once every instance has
  migrated), so the cleanup is discoverable without re-reading this plan. It pairs with
  finding-0216's follow-up.
- **Deskcheck**: per the deskcheck rule this is not done until shown working. The natural deskcheck
  is Item 2's before/after σ readings on the real machine plus a `palace start` that comes up.

---

## Checkpoint 4 — Item 2's readings, taken in the main checkout. ⚑ The move had ALREADY been performed; only the record was owed

Orchestrator session, main checkout, 2026-07-27. Checkpoint 3 handed this over as "run the runbook";
what I found is that **steps 0–6 of that runbook had already been executed** — by an earlier hand, on
2026-07-26, without recording anything. So this checkpoint is not a build; it is the **recovery of an
unrecorded measurement**, and it is exactly the failure §3 predicted: git cannot witness this move, so
an unrecorded one is unauditable.

### What the tree showed before I touched anything

| probe | observed |
|---|---|
| `config/ouroboros.toml` | present, 2914 bytes, mtime 2026-07-26 02:48 |
| `config/local.toml` | absent |
| `.gitignore` covers the new name | yes — `git check-ignore -v` → `.gitignore:28` |
| scratchpad backup at the prescribed path | present — `~/ouroboros-overlay-backup-2026-07-26.toml`, same size, same mtime (`cp -p` preserves it) |
| Item 1 landed on main | yes — `core/kernel/config/loader.py` carries `_INSTANCE_OVERLAY`, `_LEGACY_OVERLAY`, `ConfigMigrationError`, `_guard_legacy_overlay` |
| build branch merged | yes — `git log main..worktree-agent-a385f65305e0f74a5` empty, `git diff --stat main...` empty |
| daemon | DOWN (no `data/*.pid`, no supervisor process) — §10's first stop condition still clear |

### ⚑ A wrong turn worth recording, because the next reader will take it too

I first grepped **`config/loader.py`**, found no guard, and concluded Item 1 had never landed. That
file is a **facade** (bp-067/finding-0103) — a thin re-export whose docstring still names `_LOCAL`.
The real loader, and the plan's `write_scope` path, is **`core/kernel/config/loader.py`**. The
write_scope was right; I went to the wrong file because the facade has the more obvious name. The
facade's line 11 docstring mentioning `_LOCAL` is a **stale instructional reference** of exactly the
class Item 3 was meant to clear — and it sits outside Item 3's acceptance grep, which is
finding-0216's point restated from a new direction.

### The readings (§7 Item 2's acceptance)

| Reading | Expected | Actual |
|---|---|---|
| σ before the move | `0.58` | **`0.58`** — ⚑ see the caveat below; read from the pre-move file, not through the loader |
| sha256 before | (record it) | `a61cbc9d2d661afdd4c9abf5ebaf53955bf9c640e8ae954b43d6acecab960079` (of the `cp -p` backup) |
| σ after the move | `0.58` | **`0.58`** — through `get_config()`, in the live checkout |
| sha256 after | identical to before | **identical** — `cmp` rc 0, byte-for-byte |
| `get_config()` raises after? | no | **no** |

⚑ **The σ-before reading is a reconstruction, not the measurement the plan asked for.** Nobody took
it through the loader pre-merge, and it is now unrecordable — `config/local.toml` no longer exists
and the guard would refuse anyway. What I read is σ **as carried by the pre-move file**, via the
plan's own documented `tomllib` fallback applied to the backup. That proves the *file* carried 0.58;
it does not prove the *loader* returned 0.58 before the merge. Recorded as reconstructed rather than
quietly presented as taken.

### The falsifier is refuted, and by a stronger reading than the plan specified

Item 2's falsifier is "σ reads `0.62` after the move ⇒ the overlay is no longer read." What makes the
σ-after reading dispositive is that **`config/defaults.toml:277` carries `similarity_threshold = 0.62`**
and `config/ouroboros.toml:44` carries `0.58`. So the two hypotheses — *overlay read* vs *silent
reversion to committed defaults* — predict **different** values, and the loader returns the overlay's.
Q4's silent-reversion risk is closed by measurement, independent of the missing pre-reading.

### Still owed at the moment of writing

`uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'` with the
finding-0103 deselect (runbook step 7) is **in flight** and not yet reported. Expected per the
seat's readings log: the two known live failures (finding-0103 core-self-containment,
finding-0226 dream-v2). Checkpoint 3 also predicts the two finding-0214 `test_selfmod*.py` failures
**reappear** here now that config loads again — those are bp-122's, not this plan's. **`complete` is
not earned until that run is reported in this journal**, so the status flip is deliberately not made
in this checkpoint.

### Next action

Report the suite, then seal: flip `bp-123 → complete` with `cost.actual`, write the `## Follow-through`
block, and route `finding-0216`. The deskcheck remains Item 2's σ readings on the real machine plus a
`palace start` that comes up — **not run here**, because starting the daemon is owner-gated and §10
wanted it down for the duration.
