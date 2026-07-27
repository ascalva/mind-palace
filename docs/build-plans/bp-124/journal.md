---
type: journal
plan: bp-124
started: null
updated: 2026-07-26
---

# Journal — bp-124 (the orchestrator seat substrate and its handoff generator)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`) in one context into a **four**-plan family (bp-124…bp-127). The note's §3
sketched two; the graduation departed from it — the reasons are in `docs/findings/finding-0234.md`
and in each plan's §12. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **This is the zero-blast-radius plan of the family. Keep it that way.** No gate change, no
  deletion, no skill edit, no migration. If a criterion seems to want one, it belongs to bp-125,
  bp-126, or bp-127 — file a finding rather than reaching.
- ⚑ **The idempotence pin is the family's keystone.** A rendering that embeds a HEAD sha or a
  `now()` has no fixed point and would re-arm clause (e′) forever — the current brief's
  circularity, mechanized. If Item 2's falsifier fires (two renders differ), **stop**: bp-126
  cannot be built on top of it.
- **The generator home was ruled at graduation**, not left open: a sibling `scripts/handoff.py`
  importing `board`, because `board.py`'s CLI is substring matching (`if "--write" in argv`) and
  its `--write` writes **both** board files unconditionally (`scripts/board.py:439-445`). §3 Q1
  carries the grounding; §11 carries the re-entry condition.
- **The note's §2.3 claim that the orphan check covers findings/oqs "for free" is FALSE.**
  `board.py` scans exactly four globs — `docs/tracks/*.md`, `docs/build-plans/*/plan.md`,
  `docs/design-notes/*.md`, `docs/deskchecks/*.md` (`:136,162,188,203`). Findings and
  `docs/inbox/owner-questions.md` are never scanned. Item 4 makes the claim true; that is why
  `scripts/board.py` and `tests/unit/test_board.py` are in `write_scope`.
- **Item 4's falsifier is a no-op check.** No finding or oq carries a `track:` today, so a correct
  extension changes **nothing** in `docs/TRACKS.md` beyond the docstring. Any other diff means
  the scan treats an absent key as an orphan — which would flood the coordinate check with 232
  false rows.
- **`pyproject.toml` is deliberately not in scope.** `[tool.mypy] files` already lists `scripts`
  and `tests` (`pyproject.toml:128`), so new files there are enrolled automatically. Do not add
  an entry with no criterion behind it.
- **V3 is parked, not resolved** (§11): read-only SQLite vs the live supervisor's WAL. The pane
  ships; non-contention is *expected*, never tested. Do not write a test that pretends otherwise.
- **The queue open must never create `data/queue.sqlite`.** Use the `file:…?mode=ro` URI form and
  prove absence-after-run in a test. Creating it breaches the single-writer model
  (`scheduler/queue.py:17-18`).

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by Stop-gate clause (f) (`.claude/hooks/_lib.py:929-937`).
- Record whether `next_action` proved **derivable** from the tree (Item 5). **bp-127 reads this
  journal to decide V1** — if the field could only be hand-written, say so plainly here; that is
  V1 landing early and bp-127's drill degrades to judge-only.
- Record whether the inline queue read stayed under ~15 lines (§3 Q5); if not, the
  `ops.lifecycle.snapshot` import earns its place and a `codebase` finding should say so.
