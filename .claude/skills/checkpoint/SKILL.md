---
name: checkpoint
description: The journal contract — semantic-boundary triggers, the required section shape, and the fresh-agent test that makes context disposable. Use when writing a journal entry or deciding whether to resume vs compact.
---

# checkpoint — the journal contract (§9)

The journal is the deliverable of the note-taking obligation: it makes context
disposable. `docs/build-plans/<id>/journal.md`, alive while `in-progress`, sealed
by `/triage` on completion. **Committed** — history, not scratch.

## When to write — semantic boundaries, not a feeling

Write at every semantic boundary:
- an acceptance criterion closed,
- a commit made,
- a finding filed.

Do **not** rely on "context feels high." Boundaries plus the Stop gate make
staleness structurally bounded to one criterion. If a compaction fires mid-
criterion, the `compaction-marker` line tells the next turn to re-verify against
the journal, not the summary.

## Required sections — newest entry first

1. **Status line** — one sentence, the current truth.
2. **Completed** — per criterion, with commit refs.
3. **In-flight** — what is mid-motion and its exact state.
4. **Next action** — single and concrete enough to execute without thought.
5. **Open questions** — typed and routed (or finding-linked).
6. **Context-manifest delta** — files read beyond the manifest; files that proved
   irrelevant.
7. **Markers** — mechanical lines appended by hooks (compactions, audits,
   HOOK-FAILUREs). Keep these in a `## Markers` section at the file's end where
   hooks append.

## Seal entries carry a read map

A **SEAL** entry (the final entry, written on completion) additionally carries a
`read-map` fenced block: the load-bearing ~15% of the diff as `path:line: why`
quickfix lines (design first, then load-bearing code, then falsifier-encoding
tests; mechanical coverage counted, not listed). `scripts/readmap.py <plan-id>`
emits the **last** such block verbatim for a vim `:cfile` walk. Format spec:
`docs/supplemental/cockpit.md` → "The read-map block format" (bp-072). Legacy prose
seals are not back-filled; `readmap.py` exits 1 on them rather than guess.

## Seal entries answer follow-through

A **SEAL** entry additionally carries a `## Follow-through` block — the five
questions that turn a ledger-close into an *honest* one (design-note D5; the
"completion-claims honesty" rule). The Stop gate's **clause (f)** greps the
journal tail for this exact header and BLOCKs a seal-to-`complete` without it, so
the header must be verbatim:

```
## Follow-through
- **Built?** …
- **Wired / delivered (or why dormant)?** …
- **Does a consumer use it?** …
- **Track state (what remains on this track)?** …
- **Opened a new track/finding?** …
```

Answer each honestly — "built but NOT wired" is a valid, expected answer (a track
is DONE only when deskchecked; DONE ≠ sealed). The block is additive to the
read-map; both live in the seal entry. On completion the plan is **ready to
deskcheck** — file it into `docs/DESKCHECK-QUEUE.md`; the owner's verdict (the
third gate) closes the track, never the seal.

## The fresh-agent test — the acceptance bar

A new session given **only** `plan.md` + this journal + the write-scope files must
continue **without asking anything already answered**. If it would have to ask,
the journal is under-specified — enrich the Next action and In-flight before you
stop.

When this holds, **resume strictly dominates compaction**: the journal is
audited, committed, reviewable; a compaction summary is lossy and unreviewable.
Norm: kill sessions freely between criteria and resume fresh (`/resume`);
compaction is the mid-criterion fallback only.

## On the way out

The Stop gate (`journal-gate`) blocks close if the journal predates the last
commit, if the worktree holds out-of-scope changes, if the diff since baseline
contains a blessing/verdict transition, or — on a seal to `complete` — if the
journal tail lacks the `## Follow-through` block (clause (f)). So the last act
before stopping is always a fresh, truthful journal entry.
