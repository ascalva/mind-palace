---
type: journal
plan: bp-124
started: 2026-07-27
updated: 2026-07-27
---

# Journal — bp-124 (the orchestrator seat substrate and its handoff generator)

## 2026-07-27 — Item 1 closed: the seat directory and its two hand-authored artifacts

**Status line.** `docs/roles/orchestrator/{journal,readings}.md` exist, are tracked, and the
NARRATIVE purity rule survived contact — Item 1's falsifier did **not** fire.

**Completed — Item 1.**
- `docs/roles/orchestrator/journal.md` — bootstrap entry carrying all seven checkpoint sections
  (Status line / Completed / In-flight / Next action / Open questions / Context-manifest delta /
  Markers). Acceptance grep `grep -nEo '\b[0-9a-f]{7,40}\b'` over the file → **no matches**
  (exit 1). The entry names `bp-125`, `bp-126`, `finding-0234` by id and states no status, no
  count, no sha, no `path:line`.
- `docs/roles/orchestrator/readings.md` — the MEASURED log, one bootstrap row
  (`uv sync --frozen --extra dev`). Row shape `| timestamp | command | result |` as a markdown
  table, chosen so the DERIVED pane can take "latest row per command" by *file order* (append-only)
  without parsing timestamps — see the Item 2 note below on why that matters for idempotence.
- **Item 1's falsifier (a real entry is unwritable without a derivable value) did not fire.** The
  entry is genuine seat judgement — why files beat the queue as substrate, why the migration is
  deliberately not here, what V4 asks of the first weeks of use. The purity rule cost nothing.

**⚑ Decision recorded — the compaction-capsule marker (bp-127 F1b needs this).** The seat journal's
header pins the marker as the literal heading **`## CAPSULE — <date>`**, and defines the
authoritative segment as *the latest such heading plus every entry above it* (entries are newest-
first in this file, so "after the capsule" in §2.8's newest-last phrasing is "above it" here).
Nothing else in the file uses that heading. bp-127's F1b lint should key on exactly that string.

**In-flight.** Item 2 — `scripts/handoff.py`.

**Next action.** Write `scripts/handoff.py`: argparse CLI per plan §6, importing `board`'s scan
functions and `_cap`/`MAX_ROW`, rendering the `role` scope tree-pure.

**Open questions.** One, carried into Item 2 and 3 — see the next entry: the idempotence pin says
the rendering is a pure function of *the artifact tree*, and `data/queue.sqlite` is not the
artifact tree. Resolution is recorded at Item 3.

**Context-manifest delta.** Read beyond the manifest: `docs/findings/finding-0235.md` (filed after
this plan was written; it bears directly on Item 4 — a corrupted `track:` value in a ratified note
already produces a phantom orphan, so the pre-existing board rendering is *wrong* in a way Item 4
must not accidentally "fix" or worsen), `.claude/hooks/_lib.py:169-244` (the parser's exact
scalar/`#` semantics), `scheduler/queue.py` state constants (lowercase `queued`/`running`, and
`lease_expires_at`), `pyproject.toml` `[tool.mypy]` (confirmed `scripts`+`tests` enrolled; no edit
needed), `docs/inbox/owner-questions.md` (entry shape — `- key: value` bullets under a
`## oq-NNNN` heading, *not* per-question front matter; that decides how Item 4 reads a `track:`
off an owner question).

**Markers.** Base check: this worktree branched from `ac83ca3`, one commit *ahead* of the expected
`dd2fa3f`; the delta is only the bp-125/126/127 readiness blessings, which touch no file in this
plan's scope. `.claude/state/active-plan` is **absent** in this worktree, so `scope-guard` is in
orchestrator posture (denylist only) — write_scope is self-enforced here and audited post-hoc by
the Stop gate.

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
