---
name: checkpoint
description: The journal contract — semantic-boundary triggers, the required section shape, and the fresh-agent test that makes context disposable. Use when writing a journal entry or deciding whether to resume vs compact.
---

# checkpoint — the journal contract (§9)

The journal is the deliverable of the note-taking obligation: it makes context
disposable. **Committed** — history, not scratch.

The contract has **two instances**, and everything below applies to both unless a
section names one:
- **the plan journal** — `docs/build-plans/<id>/journal.md`, alive while
  `in-progress`, sealed by `/triage` on completion. The default; a builder's
  journal is always this one.
- **the seat journal** — `docs/roles/<role>/journal.md`, never sealed because a
  seat is never finished. See "The seat journal" below.

⚑ **The two `## Seal entries …` sections below are PLAN-JOURNAL ONLY**, because
only a plan seals. A seat journal never carries a read-map block and never
carries a `## Follow-through` block, and Stop-gate clause (f) — which greps a
sealed plan's journal tail for that verbatim header — never applies to it. A
seat's equivalent of a seal is a **compaction capsule**, which is a different act
with a different shape.

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

## The seat journal — the same contract, one scope up

`docs/roles/<role>/journal.md` is the **NARRATIVE** half of a role's state
(`dn-role-state-and-scoped-handoff` §2.5). The agent is a disposable *occupant*;
the seat persists, and every successor inherits its memory. **The contract is the
same one:** the same seven required sections, the same semantic-boundary triggers,
the same fresh-agent bar. Three things differ, and only three.

**1. It is never sealed, so it compacts instead.** A plan ends; a seat does not.
When the active segment grows past a working threshold (~300 lines — a knob, not
an invariant), a `/triage` sweep writes a **compaction capsule**: one entry
carrying forward every still-live judgement (open watch-items, standing traps,
in-flight intent) and naming the range it supersedes. Prior entries are **retained
beneath it, marked superseded** — keep-and-link, never delete-and-replace
(`finding-0164` / `finding-0168`). The capsule marker is the literal heading
`## CAPSULE — <date>`, and the **authoritative segment** is the latest such
heading plus every entry above it. Everything below is history: readable,
ingestable, and **non-binding** — a fresh occupant may read capsule-plus-suffix
and stop there.

**2. NARRATIVE purity is enforced, not merely encouraged.** A seat entry **names
artifacts by stable id** (`bp-110`, `finding-0227`, `oq-0051`) and **never states
a machine-derivable value** — no commit hashes, no plan statuses, no counts, no
`path:line` into code that moves. The id is the join key; the value lives in the
DERIVED pane (`handoff.md`), which is regenerated rather than remembered. A
measurement — a suite result, a usage probe — goes to `readings.md` with its
timestamp, and the entry keeps only the judgement about it. This is honest tier 4:
hash-shaped tokens and status-transition phrasing are lintable; the rest is
review-grade. If a judgement genuinely cannot be written without a derived value,
that is a finding against the rule — **not** a licence to smuggle it in words
("the sha ending in 4b2").

**3. Its "next action" is a queue, not a criterion.** A plan journal's Next action
is the next step of one unit. A seat's is the next *unit*, and the seat is where
the ordering judgement lives — which is exactly what a generator cannot derive.

A seat entry written at a clearing boundary also carries the next session's
recommended `/model` + `/effort` (context-economy skill).

## The fresh-agent test — the acceptance bar

A new session given **only** the scope's bundle must continue **without asking
anything already answered** — for a plan, `plan.md` + its journal + the
write-scope files; for a seat, `handoff.md` + the journal's authoritative
segment. If it would have to ask, the journal is under-specified — enrich the
Next action and In-flight before you stop.

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
