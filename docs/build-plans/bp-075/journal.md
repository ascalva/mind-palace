# bp-075 — journal

## 2026-07-19 — minted at graduation (orchestrator, session-36, fable pass)

Graduated from `dn-exhaust-lane` minutes after the owner ratified it
(`d3366a5`) — capture → note → ratify → plan in one evening, same arc as
bp-074. Grounding was done at design time (config-pinned ingest roots
`defaults.toml:46` / `local.toml:12`; scripts-side `get_config` precedent
`verify_attestation.py:25`; the docket no-core AST-test pattern
`test_docket.py:120-134`) and is cited in §3. One question left deliberately
code-settled by the builder: loader passthrough for a new `[exhaust]` table
(§3 Q2) — with a hard stop-and-raise if it turns out to need `core/`.

Builder discipline notes: never write outside the repo (`~/.mind-palace/**`
is live data — the real exhaust dir materializes at first orchestrator use);
the writer places content, never composes it.

Status: `proposed`. Awaiting the owner's `palace bless bp-075` + hand commit.

## 2026-07-19 — build session (delegated builder, worktree agent-a6fdccce)

**Gate + worktree sync.** The worktree branched from `e83b6c6` (pre-blessing);
the owner's blessing `76534e7` (`proposed→READY`, bp-075+bp-076) sat one commit
ahead on `main`. My branch had no commits ahead, so I fast-forwarded
(`git merge --ff-only main`, `e83b6c6..76534e7`) to pick up the blessing. Plan
now `status: ready`; build gate passes honestly (I did NOT flip the blessing —
the owner did). Wrote `.claude/state/active-plan`, flipped `ready→in-progress`.

**Context read (§2 order).** plan whole · dn-exhaust-lane (§2 contract) ·
`config/defaults.toml` ([vault] pattern) · **`config/loader.py` + the real
`core/config/loader.py`** · docket precedent + its AST test.

**Q2 SETTLED — schema'd loader, needs `core/` → STOP-and-raise (finding-0115).**
`config/loader.py` is a thin FACADE re-exporting `core.config.loader` (bp-067).
The real loader (`core/config/loader.py`) is **schema'd**: `load_config()` reads
`raw = tomllib.loads(...)`, then constructs a **frozen `Config` dataclass** with
one typed field per named section (`ollama`, `vault`, `effectors`, …). Unknown
tables in `raw` are **silently dropped** — a new `[exhaust]` table would parse
but never surface. Two hard consequences:
1. Surfacing `[exhaust]` via `get_config()` requires an `ExhaustConfig`
   dataclass + a `Config` field + a `load_config()` wiring block — **all in
   `core/config/loader.py`**, which §5 lists as deliberately OUT of write_scope.
2. The plan's §6 pinned access pattern `cfg["exhaust"]["path"]` is
   **unimplementable as written**: `Config` is a frozen dataclass — not
   subscriptable, no `exhaust` attribute. (The real form would be
   `get_config().exhaust.path` once the field exists.)

This is precisely §3 Q2 / §10 / Item 1's falsifier ("loader requires a `core/`
change to surface the table"). Filed **finding-0115** (spec-fidelity →
orchestrator; mirror of finding-0104, same file, same class). The resolution is
a scope decision only the orchestrator/owner can make (grant a core/ write, or
bless a config-only reader) — I do NOT widen write_scope myself.

**Cascade → what proceeds, what parks.**
- **Item 1 (config root):** the DATA half is in-scope and ratified (note
  §2.1/§2.2 pin the exhaust root in config). Added the `[exhaust]` table to
  `config/defaults.toml` per §6 — correct, low-regret, de-risks the follow-up.
  The CODE half (get_config passthrough) is **parked** on finding-0115.
- **Item 2 (invariant test)** and **Item 3 (writer):** both are pinned to read
  the exhaust root via `get_config()` — the exact blocked surface. **Parked**,
  re-entry = finding-0115 resolved (the config surface, or a blessed reader,
  lands). Building them against a config-only tomllib reader would deviate from
  the §6 pinned interface AND duplicate the loader's overlay precedence
  (`defaults←levers←local`) — a DRY defect; not a builder's call to make.
- **Item 4 (cockpit guide):** documents the writer command (Item 3). **Parked**
  with the lane — shipping an owner adopt-by-hand guide for an unbuilt writer
  would document vapor. Re-entry = Items 1–3 land.

Net this session: `[exhaust]` config table (in-scope forward progress) +
finding-0115 (the deliverable — grounding caught a scope/interface defect before
any wasted implementation, the finding-0104 pattern). Plan stays `in-progress`
with 3 parked items; the orchestrator makes the scope call.

---

## Session 2 (2026-07-20) — RESUME after finding-0115 resolved (owner Option A)

**Context.** Plan AMENDED (`bdcd9bc`): write_scope WIDENED to include
`core/config/loader.py` + `config/loader.py` (owner picked Option A of
finding-0115 — the narrow, single-purpose `ExhaustConfig` mirror). finding-0115
now `status: resolved`. The `[exhaust]` table data half (Item 1) already landed
`9bb4d3b` — NOT re-added. Resuming Items 1(code)/2/3/4.

**Item 1 (code half) — DONE.** In `core/config/loader.py`:
- Added `ExhaustConfig` frozen dataclass (single `path: Path` field) right after
  `VaultConfig` — the faithful mirror.
- Added `exhaust: ExhaustConfig` as a REQUIRED field on `Config`, positioned in
  the required block right after `vault`. Safe because grep confirmed NO direct
  `Config(...)` construction anywhere in tests — every test uses `load_config()`
  or `dataclasses.replace()`, both of which populate/preserve the field. Only
  the single `Config(...)` call in `load_config()` needed the new arg.
- Wired `exhaust=ExhaustConfig(path=Path(raw["exhaust"]["path"]).expanduser())`
  after the `vault=VaultConfig(...)` block — direct subscript (mirrors vault;
  `[exhaust]` is always present in defaults.toml).
- Re-exported `ExhaustConfig` in the `config/loader.py` facade import list + its
  `__all__`.
- **Acceptance MET:** `get_config().exhaust.path` → `/Users/ascalva/.mind-palace/exhaust`
  (expanduser'd, no `~`), `isinstance ExhaustConfig` True, `vault.path` unchanged.
  Verified via a live `uv run python -c` load.

**Items 2 + 3 — DONE** (`tests/unit/test_exhaust_report.py` + `scripts/exhaust_report.py`).

*Item 2 (ingest invariant).* Enumerated the ingest source roots in a documented
`_ingest_source_roots(cfg)` helper: `cfg.vault.path` (corpus — consumers
core/ingest/*, scheduler/vault_sync.py) and the chat transcripts dir
(`cfg.chat.transcripts_dir or _default_transcripts_dir()` — scheduler/chat_sync.py;
reuses the sensor's OWN resolver, DRY). Grep confirmed these are the only two
config-pinned roots the pipeline reads owner content FROM (the `[paths]` entries
are the system's own output stores, not ingest sources). This is a semantically-
grounded enumeration of the ingest lanes, NOT drift-prone literal-path pinning —
so the §7 falsifier ("cannot enumerate generically → finding") did NOT fire. Check
= `is_relative_to(exhaust)` after `expanduser().resolve()` (symlink-normalized).
Two tests: (a) real merged config → offenders == []; (b) test-of-the-test — a
`dataclasses.replace` config planting vault INSIDE exhaust → offender flagged.

*Item 3 (writer).* `scripts/exhaust_report.py`: `place_report()` copies a composed
HTML file to `<exhaust>/reports/YYYY-MM-DD-<plan>-<slug>.html`, `mkdir -p reports/`,
raises `FileExistsError` on an existing target unless `force`; `main()` maps that to
exit 1 with guidance, prints the dest on success (exit 0). Reads the root via
`get_config().exhaust.path` (SSOT). Imports = stdlib + `config` only; AST test
asserts NO `core` import (docket precedent) and imports ⊆ the allowed set.

SAFETY: I did NOT invoke the real CLI — with the real config it would write to
`~/.mind-palace/exhaust/` (outside the repo, live owner data, forbidden). All 5
writer tests drive `main()`/`place_report()` against a stubbed tmp exhaust root
(monkeypatched `get_config`). 7/7 green: `pytest tests/unit/test_exhaust_report.py`.
