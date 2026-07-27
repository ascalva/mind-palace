---
type: finding
id: finding-0267
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-role-state-and-scoped-handoff.md
  - docs/roles/orchestrator/journal.md
  - docs/findings/finding-0245.md
  - docs/findings/finding-0249.md
ftype: spec-fidelity
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The first capsule blinds both instruments that watch the seat journal: the emitter and the linter disagree about what the authoritative segment is

## What

Discovered by measurement while writing this journal's **first** compaction capsule — the act that
creates the condition. Before a capsule exists, both instruments agree by accident, because "no
capsule" means "the whole file". The disagreement is unreachable until the first capsule lands, and
it is total the moment it does.

The seat journal is **newest-at-top**. §2.8 and the file's own preamble define the authoritative
segment as *"the latest `## CAPSULE — <date>` heading plus every entry above it"*. Two consumers
implement that sentence, and they do not compute the same set:

| consumer | what it takes | measured, this file, with the capsule at the top |
|---|---|---|
| `session-brief.sh` (awk) | capsule heading **+ its body**, stopping at the next `## ` heading | **230 lines** |
| `scripts/handoff.py` `authoritative_segment` | `lines[: capsule_index + 1]` — everything **above** the heading, plus the heading | **39 lines** |

The linter's 39 lines are the file's front matter and preamble — boilerplate — plus the capsule's
heading line. **The capsule's body is below its own heading, so it falls outside the linted
segment entirely**, while being exactly what the emitter ships into every session.

⚑ **Verified by mutation, not by reading** — the discipline this seat has been repeating all week:

```
CONTROL                      segment=  39   violations=0
MUTANT-A (impurity planted INSIDE the capsule body)    segment=  39   violations=0   <-- SURVIVED
MUTANT-B (same impurity planted ABOVE the capsule)     segment=  40   violations=3   <-- caught
```

The planted impurity was a hex-shaped token, a `status:` field, and a status arrow — three of the
exact shapes `lint_narrative` exists to catch. Inside the capsule body, **all three survive**.

## Why it matters

Two instruments go quiet at once, and both go quiet **reporting success**:

1. ⚑ **The purity lint becomes vacuous.** It now checks 39 lines of documentation that nobody writes
   judgement into, and reports `OK — 0 violations`. Note that the `vacuous` false-success guard does
   **not** fire, because the preamble is non-empty prose — the guard was built for an empty segment,
   and this segment is full, just full of the wrong thing. This is precisely `finding-0249`'s class:
   *a check that passes without testing its claim*, arriving on the very surface built to detect it.
   It also silently "fixed" a genuine FAIL: the 7 real purity violations this file carried before
   compaction are now below the capsule and invisible to the lint, without any of them being
   repaired.

2. ⚑ **The §2.8 threshold gauge measures the wrong side of the marker.** `journal_segment_lines`
   now reports **39 against a ~300 threshold**, so the compaction instrument built for
   `finding-0245` will report "comfortably under" **permanently** — no matter how large the capsule
   or the emitted segment grows. The gauge that exists to demand the *next* capsule can never fire
   again. The instrument was built and validated on a file with zero capsules, so its own acceptance
   test could not have caught this.

Both are strictly worse than having no instrument, because both report green.

⚑ **Which one is right is a genuine design question, not an obvious bug.** Under append-at-top,
"entries above the capsule" means *entries written after it* — of which there are correctly zero at
the moment of compaction. The linter is a faithful reading of the specified sentence; the sentence
plus the placement convention together make the segment degenerate. The emitter's reading — the
capsule **and its body**, being what a fresh occupant is actually bound by — is the one that matches
intent. The specification needs to say which, because right now it licenses both.

## Re-entry condition

Reopens immediately at the design level — this should be settled **before** the next capsule is
written, and certainly before anyone reads a green `--lint` verdict on this file as evidence of
anything. Concretely it reopens when either: (a) `dn-role-state-and-scoped-handoff` §2.8 is amended
to state which side of the marker the segment includes; or (b) any plan touches
`scripts/handoff.py`'s `authoritative_segment` or `journal_segment_lines`. Until then, **treat
`--lint` OK and the segment-length figure on this file as uninformative**, and use the emitter's
measurement (`session-brief.sh --standalone | wc -l`) as the real gauge.

## Routing

`spec-fidelity` → routed to the **orchestrator**. The ambiguity is in the design note's own
sentence, so a builder cannot settle it against the spec — the spec is what is underdetermined. It
is closely related to `finding-0248` and `finding-0252` (clause (f) matching the wrong thing, in
both directions) and belongs in the same repair: all three are the same underlying error of *keying
a check on physical file position in a file whose convention is temporal*. `bp-128` is the natural
home for the family, and its §2 manifest should carry this alongside `finding-0252`.
