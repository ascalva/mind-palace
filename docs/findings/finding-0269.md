---
type: finding
id: finding-0269
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/hooks/_lib.py
  - docs/design-notes/session-handoff-gate.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0267.md
  - docs/findings/finding-0268.md
ftype: codebase
origin_plan: bp-123
route: orchestrator
resolution: null
---

# Stop clause (a) still carries the exact circularity that clause (e) was re-specified to remove — diagnosed, measured and repaired 130 lines away in the same file, and never applied to its sibling

## What

`_lib.py:848`:

```python
if os.path.getmtime(j_abs) < last_commit:
    reasons.append(f"(a) journal '{journal}' mtime predates the last commit — checkpoint before close (§9).")
```

`last_commit` is HEAD's committer timestamp. The prescribed working order (§9, the checkpoint skill)
is **write the journal, then commit it**. That order *guarantees* the journal's mtime precedes the
commit that carries it. So clause (a) fires **because** the session did the right thing, and fires
again after every subsequent commit.

The same defect in clause (e) was found, measured and repaired. The repair rationale is in this very
file at `_lib.py:987-1012`:

> (e) blocked unless an UNVERSIONED state file's mtime was >= the last-commit time … Both halves
> were circular: **EVERY post-write commit re-armed the mtime** … Measured cost of the circularity:
> **108 firings (99 fork-deduped) over 8 days across 16 sessions, 302 file-operations on it, peak
> day 36.**

Clause (e) was cut over to key on `.claude/state/session-baseline` mtime instead, precisely so that
"a late commit cannot re-arm this check … the circularity cut by re-spec rather than by trust."

**Clause (a) was left on `last_commit`.** The diagnosis, the measurement, the named recovery and the
working replacement all already exist, in the same function, ~130 lines apart.

## Why it matters

**Clause (a) does not converge.** Clause (e)'s comment advertises that its recovery "converges in
EXACTLY ONE step: regenerate, commit, close." Clause (a) has no converging recovery at all:

| escape | what it costs |
|---|---|
| commit the journal | re-arms the clause — the state that tripped it is reproduced exactly |
| write more journal, leave it uncommitted | closes, but the session ends with **uncommitted narrative** — the opposite of the discipline the gate exists to enforce |
| `touch` the journal | passes with **no content change** — pure laundering, tier 5 |

So the gate's only dischargeable-by-construction path is *end the session with the journal
uncommitted*. A gate meant to guarantee a committed checkpoint structurally rewards leaving the
checkpoint out of the commit.

Observed live twice in one session (2026-07-27, bp-123's close): fired, journal written and committed
in response, fired again on identical grounds.

## The class, not just the instance

This is the third member of a family now visible in one week — `finding-0267` (the emitter and the
purity lint disagree about which side of the capsule marker is authoritative), `finding-0268` (the
readings parser silently drops any row whose command contains a pipe), and this one:

⚑ **Every consumer of the journal implements its own private parse of it, and none of them share a
definition of "the journal's current entry."** Clause (a) uses mtime-vs-commit. Clause (e) uses
mtime-vs-session-baseline. Clause (f) walks to the last `## ` heading excluding two hardcoded
strings. The emitter stops at `## Markers`. The lint splits on the capsule marker. Five readers,
five grammars. A change to the file's shape re-scopes each of them differently and silently, which
is exactly how `finding-0267` happened.

The recurring-defect rate here is not bad luck; it is the predicted output of N ad-hoc parsers over
one mutable prose format with no schema.

## Proposed direction (design-level, not a patch)

Do **not** fix clause (a) in isolation — that reproduces the pattern (a sixth private fix). The
finding proposes one parser that yields a typed journal structure (entries, timestamps, standing
sections, capsule marker, follow-through block), with clauses (a)/(e)/(f), the emitter, the lint and
the §2.8 gauge all reduced to **queries over that structure**. That is a net deletion of code, and it
makes "the readers disagree" unrepresentable rather than merely currently-false.

⚑ This bears directly on `bp-128`, which is blessed and ready and repairs clause (f)'s parse alone.
`bp-128` is not wrong, but landing it first adds a sixth grammar to a file that needs one. Sequencing
is an owner call.

## Status

Open. Routed to the orchestrator: this is `direction`-adjacent — the instance is `codebase` and
fixable in a line, but the proposal it carries changes what several ratified clauses are specified
against, so it should not be resolved by a builder in passing.
