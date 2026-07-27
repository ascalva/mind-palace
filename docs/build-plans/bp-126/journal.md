---
type: journal
plan: bp-126
started: null
updated: 2026-07-26
---

# Journal — bp-126 (the cutover: clause (e′), the re-point, and the brief's retirement)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Third of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑⚑ **THE HIGHEST-BLAST-RADIUS PLAN IN THE FAMILY. IT IS ATOMIC BY NECESSITY, NOT BY TASTE.**
  It deletes an artifact every agent reads at every SessionStart, re-points the hook that reads
  it, and replaces the Stop clause that demands it — in one diff. The intermediate states are all
  broken:
  - delete the brief, keep clause (e) → **every orchestrator session that commits can never
    close** (a missing brief is infinitely stale, `_lib.py:909-913`). Repo-wide deadlock.
  - replace clause (e), keep the old surface → SessionStart shows a brief nothing maintains.
  - re-point, keep clause (e) → the orchestrator writes a brief it cannot see.
  Land it whole or revert it whole.
- ⚑ **VERIFY THE LINE NUMBERS YOURSELF BEFORE CITING THEM.** Clause (e) is
  `.claude/hooks/_lib.py:892-920`; the posture guard is `:899`; the commits-this-session guard is
  `:908`; **the getmtime is `:911`**. **`:762` is clause (a)** — the *journal* mtime check. The
  live brief mis-cites `:762` as clause (e)'s getmtime (note §2.2), and that stale citation
  propagated into a design prompt. This is the defect exhibiting itself; do not re-copy it.
- ⚑ **Item 12's falsifier is the one that matters: one-step convergence.** After regenerating and
  committing, a second close must ALLOW. If it still blocks, the circularity has been reproduced
  in new clothes and the note's central by-construction claim (§2.10) is false. **Prove the whole
  sequence in the test** — block → regenerate → commit → close → ALLOW — not just the block.
- ⚑ **Item 14 is irreversible and gated on a human-grade verification.** Before deleting: read
  `docs/roles/orchestrator/handoff.md` + the journal's authoritative segment and confirm the
  in-flight unit and the next action are answerable **from those alone**. The brief has no
  history. Copy it to a scratch path outside the repo first.
- **The "no live reference remains" criterion is scoped to FIVE files**, deliberately: 38 files
  in the tree contain `resume-brief`, and nearly all are ratified notes (A8 — unwritable),
  findings, historical journals, `CHANGELOG.md`, brainstorms, `docs/book/`, `docs/PROGRESS.md`,
  `docs/PARKING-LOT.md`. A repo-wide grep criterion would be **unbuildable**. §3 Q5 enumerates
  the five.
- **`--check`'s mechanism is not pinned** (§3 Q2 — subprocess vs import). The plan bounds it with
  three criteria: no second `git` call (the owner DRY rule stated at `_lib.py:738-743`), fail-open
  on any generator error, never runs a MEASURED command. **Measure the Stop latency and record it
  as a MEASURED reading** — that is what settles the choice.
- **`session-brief.sh`'s baseline write at `:63-65` is untouched.** Clause (e′) check 2 keys on
  that file's mtime, and clause (c)'s consumer chain depends on it. So is the worktree-aware
  `ROOT` resolution (`:19-26`) and the deskcheck-owed line (`:51-61`).
  *(Note: A9's text cites the baseline write as `session-brief.sh:52`; it is `:65` in the tree
  today. A9 lives in a ratified note — record, do not edit.)*
- **`docs/roles/**` is in `write_scope` because this plan's own close is judged by the clause it
  installs.** Once (e′) lands, closing requires a fresh rendering and a seat-journal entry.
  Without that entry the builder would be denied the very files its new gate demands.
- **Amendment A10 and the `dn-session-handoff-gate` partial supersession are BOTH owner
  hand-acts.** `scope-guard` denies a ratified note pre-hoc (`_lib.py:435-441`) and Stop (b2)
  blocks the Bash path (`_lib.py:797-824`). See `docs/findings/finding-0233.md`. Draft the A10
  text here for a one-paste landing; attempt neither edit.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f).
- The **A10 amendment text**, drafted for the owner: §5 gains the role registry, §6's journal-gate
  clause enumeration extends to (e′), §9 states the seat generalization.
- The **partial supersession** of `dn-session-handoff-gate` §2.2–2.3 is effective on this merge.
  Record the effective commit here; the owner records it in the amendment log. `superseded_by` on
  that note is deliberately **not** set (note §1.1 — the note is not wholly replaced).
- The **Stop-latency measurement** for (e′) check 1 — as a MEASURED reading in
  `docs/roles/orchestrator/readings.md`, and repeated here.
- Re-verify at `/build` time that **no other plan holds `.claude/hooks/**`.** Scanned clean at
  graduation (2026-07-26) across bp-111…bp-119 and bp-123, but the ops wave is live.
