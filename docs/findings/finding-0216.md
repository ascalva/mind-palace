---
type: finding
id: finding-0216
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-123/plan.md
  - config/defaults.toml
ftype: spec-defect
origin_plan: bp-123
route: builder
resolution: null
---

# bp-123 Item 3's acceptance grep spans eight directories its write_scope cannot reach — 13 live `local.toml` instructions survive the rename, three of them printed to the owner at runtime

## What

Item 3's acceptance test is:

> `grep -rn 'local\.toml' config/ core/ ops/ scheduler/ edge/ agents/ eval/ scripts/ docs/runbook.md`
> returns only the loader's deliberate `_LEGACY_OVERLAY` line and its comment.

That grep covers **eight directories**, but `write_scope` grants only **three files inside them**
(`core/kernel/config/loader.py`, `config/defaults.toml`, `core/models/inference.py`). So the
criterion is **unsatisfiable within the plan's own capability**, and it is not a judgement call at
the margin: §3's Q1/Q2 undercounted. Q2 put the code/config-comment total at "~10 in code/config
comments"; the true figure inside the acceptance grep's own directories is **~24 across 10 files**,
of which 13 in **6 files** are live instructions this plan cannot touch.

Everything below was left as-is. All of it is *instructional* text (the class Item 3 exists to fix),
not the historical record §9 correctly protects.

### ⚑ Tier 1 — emitted to the owner AT RUNTIME, now naming a file the loader refuses to read

These are not comments. They are strings the system prints or writes, so after bp-123 they actively
instruct the owner to edit a filename that triggers `ConfigMigrationError`.

| Where | What it does |
|---|---|
| `ops/backup/run.py:25` | prints to stderr: `no [backup] repository configured (set it in config/local.toml)` |
| `scripts/build_sandbox_image.sh:17` | echoes: `built $TAG. Enable it for this machine in config/local.toml:` |
| `ops/apply.py:33-34` | the **generated header written into `config/levers.toml`** on every self-mod knob write: `"# ... The loader overlays config/local.toml ON TOP of this, so a human override in local.toml always wins."` — a stale name persisted into a live file the owner reads |

### Tier 2 — comments and docstrings, misleading on read

| Where | Note |
|---|---|
| `ops/apply.py:10-11` | module docstring: "The loop NEVER edits the owner's hand-authored `config/local.toml`" |
| `ops/sandbox/Containerfile:9` | "then point the sandbox at it (config/local.toml)" |
| `scripts/sandbox.py:14` | module docstring naming `config/local.toml` |
| `config/tuning.toml:4` | "This manifest is subordinate to config/local.toml" |
| `eval/harness/tuning.py:8,9,35,125` | four references, incl. the note §2.6 quote "subordinate to local.toml" |

### Tier 3 — a stale SYMBOL name, which this grep does not even catch

`config/loader.py:11` (the outside facade) reads: *"tests that MONKEYPATCH loader internals
(`LEVERS_OVERLAY`/`_LOCAL`/`get_config`) must patch `core.config.loader`"*. bp-123 §11 renamed
`_LOCAL` → `_INSTANCE_OVERLAY`, so **`_LOCAL` no longer exists**. This line now points a future test
author at a symbol that will `AttributeError` under `monkeypatch.setattr`. It survives the acceptance
grep only because it says `_LOCAL`, not `local.toml` — i.e. the criterion as written would have
passed while leaving a genuinely broken instruction in place.

### Separately: the `[planes]` instruction was wrong before this plan, not just stale

`config/defaults.toml`'s `[planes]` comment claimed the block is read "via a direct tomllib parse
(with the local.toml overlay honored)" and told the reader to "flip it in config/local.toml, not
here". Both halves are false, **independently of the rename**:

- `scripts/verify_planes.py` calls `get_config()`, and the same comment correctly notes there is
  deliberately **no `PlanesConfig`** — schema'd loading drops unknown sections — so the verifier
  learns nothing about `[planes]` from config at all.
- The only actual reader, `tests/unit/test_plane_migration.py:397`, does
  `tomllib.loads((REPO_ROOT / "config/defaults.toml").read_text(...))` — `defaults.toml` **directly**,
  honoring no overlay whatsoever.

So flipping `[planes] enabled` in the per-machine overlay is **inert**. Rather than translate a false
instruction into the new filename, bp-123 removed the overlay claim and left an inline pointer to
this finding. **Where that master switch should actually live is a design call, not a comment fix**,
and it is deliberately not made here.

## Why it matters

The plan's own §7 Item 3 falsifier is *"the grep still finds an instructional reference — meaning a
future setup or recovery walk-through still points at the dead filename."* That falsifier **is
tripped**, and bp-123's guard sharpens the cost rather than softening it: before this plan a stale
name was mildly confusing, but now `config/local.toml` is the name that makes config loading
**refuse**. Tier 1 is the sharp edge — the system will tell the owner, in its own runtime output, to
create the one file guaranteed to break it.

The `ops/apply.py:33-34` case is the most durable: it bakes the dead name into generated content, so
it keeps reappearing in a live file until fixed.

Meta-lesson for graduation, and the reason this is filed as `spec-defect` rather than just fixed: an
acceptance test whose *verification surface* (8 directories) is broader than the plan's *write
capability* (3 files in them) cannot pass by construction. The **build-plan** skill should require
these two to be reconciled at graduation — either narrow the grep to the files in `write_scope`, or
widen `write_scope` to cover what the grep asserts.

## Re-entry condition

Not parked — bp-123's Items 1 and 3 completed within scope, and every residual reference is
enumerated above with an exact path and line, so no re-derivation is needed.

Discharged when a follow-up touches the 7 files listed (Tiers 1–3) and
`grep -rn 'local\.toml' config/ core/ ops/ scheduler/ edge/ agents/ eval/ scripts/` returns only
`core/kernel/config/loader.py`'s deliberate `_LEGACY_OVERLAY` constant, its comment, and the two
guard messages (which must name the legacy file — that is their job). The work is mechanical and
comment-only; it is a **one-item follow-up plan for the orchestrator to mint at `/triage`**, and it
pairs naturally with §11's "delete the legacy guard once every instance has migrated" cleanup.

The `[planes]` question is a separate, non-mechanical thread and should be routed on its own: should
the `[planes] enabled` master switch be overlay-driven (give it a real schema + reader), or should
the instruction be dropped as `defaults.toml`-only?

## Routing

`spec-defect` / `codebase` → **builder**. Resolved as far as this plan's capability allows: the three
in-scope files are corrected, the false `[planes]` claim is removed rather than translated, and the
residue is enumerated here instead of being fixed by widening `write_scope` (CLAUDE.md: "A denial
means narrow the scope or file a finding — never route around"). The remaining edits need a
capability bp-123 does not have, so they need a follow-up plan rather than a builder decision.
