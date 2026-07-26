---
type: build-plan
id: bp-123
track: ops
status: proposed
design_ref: []
contract: builder
write_scope:
  - core/kernel/config/loader.py
  - config/defaults.toml
  - core/models/inference.py
  - .gitignore
  - docs/runbook.md
  - tests/unit/test_config_split.py
  - tests/unit/test_code_ingest_wiring.py
  - tests/unit/test_inference_seam.py
  - tests/integration/test_levers_overlay.py
  - tests/integration/test_secrets_backend_wiring.py
session_budget: 1
cost:
  estimate:
    model: sonnet
    tokens: 60k
  actual: null
depends_on: []
parallelizable_with: [bp-122]
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/brainstorms/legal-corpus-sibling.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the per-machine overlay becomes `config/ouroboros.toml`, and cannot be silently lost

## 0. Mode & provenance

No investigation finding warrants this; it is an **owner naming ruling**, 2026-07-26: *"stop using
local.toml, it will be ouroboros.toml"*. The rationale is the established mind-palace/Ouroboros
split — `mind-palace` is the framework, **Ouroboros** is this live instance (named by its own
founding note), so the instance's own overlay should carry the instance's name rather than the
generic "local". Authority to act is that ruling; the readiness blessing (`proposed → ready`)
remains the owner's, by hand. `warrant: null` — this corrects no committed defect.

## 1. Objective

Rename the per-machine config overlay from `config/local.toml` to `config/ouroboros.toml`
everywhere it is *operative*, with a fail-loud guard that makes it impossible for the owner's
existing overlay to be silently ignored after the change.

## 2. Context manifest

Read in this order, whole files before citing:

1. `core/kernel/config/loader.py:15-35` — `REPO_ROOT`, `_CONFIG_DIR`, `_DEFAULTS`, `_LOCAL`
   (`:29`), `LEVERS_OVERLAY` (`:34`). The comment block at `:17-20` explains why the toml *data*
   stayed at repo root when the loader moved into `core` (bp-067) — that reasoning is unaffected
   here and must not be disturbed.
2. `core/kernel/config/loader.py` — the `_overlay` merge and every docstring mentioning
   `local.toml` (`:25-28, :226, :237, :262, :302, :305`). The precedence rule is load-bearing:
   `levers.toml` is overlaid **under** the human overlay so a hand override always wins.
3. `config/local.toml` — the owner's live overlay, and ⚑ **the single most important file in this
   plan**: it is gitignored, holds owner ruling oq-0024's σ retune plus its full rationale, and
   exists in exactly one copy with no version-control backup.
4. `.gitignore:22-27` — the two overlay entries and their comments.
5. `docs/runbook.md` — the operational doc that tells the owner to create/edit this file. The one
   doc in the repo whose staleness would actively mislead.
6. The five test files in `write_scope` — every one monkeypatches the **symbol** `_LOCAL`, not the
   filename, so none of them breaks functionally. §3 Q3 explains why they are in scope anyway.

## 3. Investigation & grounding

- **Q1 — how many operative references are there?** ⚑ Exactly **one**: `loader.py:29`
  (`_LOCAL = _CONFIG_DIR / "local.toml"`). Everything else that mentions `local.toml` in code is a
  comment or docstring. Measured by grep across `*.py`/`*.toml`/`*.sh`.
- **Q2 — how many references exist in total?** ~10 in code/config comments, **50 files under
  `docs/`**, and 6 test files. The docs figure is the trap: most of those are *historical records*
  (findings, journals, brainstorms, ratified design notes) that correctly name the file as it was
  called when they were written. §9 pins them as a non-goal.
- **Q3 — do the tests break?** No, and this was checked rather than assumed. All five patch the
  symbol (`monkeypatch.setattr(loader, "_LOCAL", …)` /
  `monkeypatch.setattr("core.kernel.config.loader._LOCAL", …)`), so a filename change is invisible
  to them. They are in `write_scope` only because §11's parked decision defaults to renaming the
  *symbol* too, which does touch those five call sites.
- **Q4 — ⚑ what happens on the owner's machine the moment the code changes?** His overlay is still
  named `local.toml`, so the loader would stop reading it and **σ would silently revert from 0.58 to
  0.62**, along with every other flag he has enabled there (`[secrets]`, `[attestation]`,
  `[runtime]`, …). A silent config reversion on the live instance is the whole risk of this plan,
  and it is why §7 Item 1 builds a guard *before* Item 2 moves anything.
- **Q5 — is the daemon running?** No — it is down (`deploy: no live run`). So there is no live
  process to mis-load config mid-flight, which makes this the right window for the change. Confirm
  it is still down at build time; if it is up, stop and ask (§10).

**Additional risk surfaced during reading:** the file move in Item 2 is **invisible to git** —
`config/local.toml` is untracked, so neither `scope-guard` nor the `journal-gate` diff audit can see
it happen or un-happen. That makes the journal the *only* record. Item 2 therefore requires the
before/after σ readings to be written into the journal, not merely observed.

## 4. Reconciliation

- `core/kernel/config/loader.py:25-28` — the `_LOCAL` docstring comment (*"a gitignored
  config/local.toml that overlays the committed defaults…"*) → **[banner: correction]**: rewrite for
  the new name, keeping the *substance* (why a per-machine overlay exists, and that a fresh clone /
  CI has none so flags stay off-by-default) verbatim in meaning. The safety argument is unchanged;
  only the filename moves.
- `core/kernel/config/loader.py:31-33` — the precedence comment (*"Overlaid UNDER local.toml below,
  so a human override in local.toml always wins over a loop-tuned knob — human authority stays
  supreme"*) → **[cross-ref: extension]**: update the name, and do not weaken the sentence. It is
  the only place that states human-over-loop precedence as a principle.
- `config/defaults.toml` — seven comments instructing the reader to "flip it in config/local.toml"
  (`:73, :77, :105, :240, :248, :307, :321, :340, :345`) → **[cross-ref: extension]**: these are
  live *instructions*, not history, so they must be updated or they will tell the owner to edit a
  file the loader no longer reads.
- `docs/runbook.md` → **[banner: correction]**: same reasoning, higher stakes — it is the doc
  followed during setup and recovery.

## 5. Write scope

Ten paths. `core/kernel/config/loader.py` — `_LOCAL`'s definition, the migration guard, and the
docstrings/comments naming the file; **not** the `_overlay` merge semantics, not `LEVERS_OVERLAY`,
not `REPO_ROOT`/`_CONFIG_DIR`. `config/defaults.toml` — comment text **only**; ⚑ **no value in that
file changes**, in particular not `[dreaming] similarity_threshold`, which stays 0.62 so a fresh
clone and CI are unaffected. `.gitignore` — add the new entry, keep the old. `docs/runbook.md` — the
overlay instructions. `core/models/inference.py:79` — a one-line comment. The five test files —
`_LOCAL` patch sites and their comments.

Deliberately **out of scope**: `config/local.toml`'s *content* (its lines are the owner's ruling;
Item 2 moves the file, it does not edit it); `tests/integration/test_selfmod*.py` (bp-122's
territory — the two plans are `parallelizable_with` each other precisely because these sets are
disjoint); the ~49 historical `docs/` files (§9); `docs/design-notes/**` in general, where
`ratified` notes are agent-immutable under A8; the foundation denylist.

## 6. Interfaces pinned inline

Current:

```python
_LOCAL = _CONFIG_DIR / "local.toml"
```

Target shape — the rename plus the guard, which is the reason this plan is not a find-and-replace:

```python
_INSTANCE_OVERLAY = _CONFIG_DIR / "ouroboros.toml"
_LEGACY_OVERLAY = _CONFIG_DIR / "local.toml"        # pre-2026-07-26 name; retained ONLY to refuse

# raised at load time, never swallowed:
#   legacy present, new absent  -> the overlay would be silently ignored: REFUSE, name the mv
#   both present                -> ambiguous authority: REFUSE, do not guess which one wins
```

⚑ **The guard must refuse, not warn.** A warning on a config path is a false green one level down:
the process comes up with the wrong σ and every flag off, and the owner learns about it from
behaviour rather than from an error. Both branches must be reachable in a test with `_CONFIG_DIR`
patched to `tmp_path` — never against the real `config/` dir.

⚑ **The guard is not permanent scaffolding.** It exists so one specific migration cannot lose data.
§11 records when it may be deleted.

## 7. Items

### Item 1 — rename the overlay symbol and path, and add the fail-loud migration guard

- **Objective:** the loader reads `config/ouroboros.toml`, and refuses to load at all if a legacy
  `config/local.toml` is present in a state where its contents would be ignored or ambiguous.
- **Files:** `core/kernel/config/loader.py`, `.gitignore`, plus the `_LOCAL` patch sites in the five
  test files (mechanical, per §11's default).
- **Acceptance test:** two new tests with `_CONFIG_DIR` patched into `tmp_path`: legacy-only →
  raises and the message contains both filenames; both-present → raises. Plus
  `uv run pytest tests/unit/test_config_split.py tests/unit/test_code_ingest_wiring.py
  tests/unit/test_inference_seam.py tests/integration/test_levers_overlay.py
  tests/integration/test_secrets_backend_wiring.py -q` green, and `uv run mypy core … scripts`
  at 0 errors.
- **Falsifier:** with the guard in place, rename the real overlay away and confirm the loader
  **refuses** rather than coming up with defaults. If it comes up quietly, the guard is decorative
  and Q4's silent-reversion risk is still live. ⚑ Run this against a **copy** in `tmp_path`, never
  against `config/local.toml` itself.
- **Invariant(s) it must not violate:** overlay precedence is unchanged (`levers.toml` under the
  human overlay); a machine with **neither** file present must still load cleanly with committed
  defaults — that is CI, and a guard that breaks a fresh clone is worse than the problem.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** none.

### Item 2 — move the owner's live overlay, and prove σ survived

- **Objective:** `config/local.toml` becomes `config/ouroboros.toml` on this machine, with evidence
  that the overlay is still being read.
- **Files:** none in `write_scope` — this item is a filesystem move of an **untracked** file.
- **Acceptance test:** record σ **before** (`uv run python -c` reading
  `get_config().dreaming.similarity_threshold` → expect `0.58`), perform the move, record σ
  **after** → still `0.58`, and confirm the loader does not raise. Both readings go **in the
  journal**: git cannot witness this move, so an unrecorded one is unauditable (§3's added risk).
- **Falsifier:** σ reads `0.62` after the move — the overlay is no longer being read, i.e. exactly
  Q4's silent reversion, now caught by measurement instead of by surprise weeks later.
- **Invariant(s) it must not violate:** the file's **bytes are unchanged** — it carries owner ruling
  oq-0024 and its rationale. `mv`, never rewrite. Verify with a checksum taken before the move.
- **Touches stored data?** ⚑ It moves owner-authored machine state that is not in version control.
  Take a copy into the scratchpad first; a lost overlay is unrecoverable from the repo.
- **Parallelizable?** No.  **Depends on:** Item 1 (the guard must exist before the file moves, so a
  half-done migration refuses loudly instead of running on silent defaults).

### Item 3 — update the docs and comments that *instruct* rather than record

- **Objective:** no live instruction anywhere tells a reader to edit a file the loader ignores.
- **Files:** `config/defaults.toml` (comments only), `docs/runbook.md`, `core/models/inference.py:79`
- **Acceptance test:** `grep -rn 'local\.toml' config/ core/ ops/ scheduler/ edge/ agents/ eval/
  scripts/ docs/runbook.md` returns only the loader's deliberate `_LEGACY_OVERLAY` line and its
  comment. `uv run ruff check .` green.
- **Falsifier:** the grep still finds an instructional reference — meaning a future setup or recovery
  walk-through still points at the dead filename.
- **Invariant(s) it must not violate:** no *value* in `defaults.toml` changes; comment text only.
  Historical `docs/` files are not touched (§9).
- **Touches stored data?** No.
- **Parallelizable?** Yes, with Item 1.  **Depends on:** none.

## 8. Math carried explicitly

N/A — a filename and a guard; no mathematical object.

## 9. Non-goals

- **Not** rewriting the ~49 historical `docs/` references (findings, journals, brainstorms, design
  notes). They record what the file was called at the time and are correct as written; `ratified`
  notes are additionally agent-immutable under A8. Only *instructional* text is in scope (Item 3).
- **Not** making the overlay name instance-*derived* (e.g. resolved from an instance identity so a
  second instance reads `legalsib.toml`). The owner named a specific file; see §11.
- **Not** touching `config/levers.toml` or the loop-vs-human precedence rule.
- **Not** changing any config **value**, and specifically not σ. bp-122 is the plan that stops tests
  from caring what σ is; this plan must not "fix" that by moving the value.
- **Not** editing the contents of the owner's overlay for any reason.

## 10. Stop-and-raise conditions

- **The daemon is UP at build time** → **stop and ask.** Item 2 moves the config file the live
  process resolves; doing that under a running supervisor is a different plan with a drain in it.
- σ reads anything other than `0.58` *before* Item 2's move → **stop.** The starting state is not
  what this plan was written against, and moving files on a misunderstood machine is how overlays
  get lost.
- The checksum of the moved file differs before vs after → **stop immediately** and restore from the
  scratchpad copy. An owner ruling was just corrupted.
- A guard branch cannot be tested without patching the real `config/` dir → **stop**; that is a
  testability defect worth a finding, not a licence to test against live state.
- Any temptation to widen `write_scope` into `docs/design-notes/**` → file a finding.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Fixed filename vs instance-derived name | **Fixed `ouroboros.toml`** — the owner's words, and it needs no identity mechanism that does not yet exist | Derive from an instance id now (invents a multi-tenancy seam ahead of any second instance, and `docs/brainstorms/legal-corpus-sibling.md` says the cheapest first move there is an *audit*, not a mechanism) | The multi-tenancy audit runs, or a second instance is actually stood up — then this becomes its first real requirement |
| Rename the symbol `_LOCAL` → `_INSTANCE_OVERLAY` | **Yes** — five mechanical monkeypatch sites. A symbol whose name contradicts what it points at is how bp-121's bug got written (`name` holding an interpreter path) | Keep `_LOCAL` (smaller diff, but leaves a name that now means the *legacy* file — actively confusing beside `_LEGACY_OVERLAY`) | — decided |
| How long the legacy guard lives | Until the owner confirms the migration on every instance he runs, then deleted in a one-line follow-up | Keep it forever (permanent scaffolding for a one-time move); delete it in this plan (defeats its purpose) | Owner confirms migration complete |
| The ~49 historical doc references | Left alone | Bulk find-and-replace (rewrites history, and would edit agent-immutable ratified notes) | Never — this is the correct end state |

## 12. Dependency & ordering summary

Three items. **Item 1 → Item 2** is strict and safety-ordered: the guard must exist before the file
moves, so a partially-applied migration refuses loudly rather than running on silent defaults. Item 3
is independent and may go first or last. `parallelizable_with: [bp-122]` — disjoint write scopes
(bp-122 owns `tests/integration/test_selfmod*.py`; this plan owns none of them).

Blast radius, in phase order: Item 1 is a read-path change plus a new refusal; Item 2 touches
**owner machine state outside version control** and is the one irreversible-ish step in the plan
(hence the checksum, the scratchpad copy, and the journal-recorded before/after readings); Item 3 is
comments. No stored data, no external effects, no migration of persisted records.
