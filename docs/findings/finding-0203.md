---
type: finding
id: finding-0203
status: open             # open → routed → resolved | promoted
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-110/plan.md
  - docs/design-notes/dn-supervision-and-liveness.md
  - docs/brainstorms/owner-cockpit.md
ftype: spec-fidelity     # blocker | spec-defect | question | discovery
origin_plan: orchestrator
route: builder
resolution: null
---

# bp-110 uses bare `§N` for TWO different documents, including once inside a docstring

## What

`docs/build-plans/bp-110/plan.md` writes bare `§N` references that resolve to **two different
files**, disambiguated only by surrounding prose:

| line | ref | actually means |
|---|---|---|
| 69, 71 | `§2.3`, `§2.7`, `§2.10` | **the design note's** sections (`dn-supervision-and-liveness`) — recoverable because line 69 sits under a heading naming the note |
| 82, 109, 131, 152 | `§10` | **the plan's own** §10 (Stop-and-raise conditions) |
| 105 | `§2.3` | the note's — recoverable only from the prose *"The note's §2.3 wording"* |
| **237** | `§2.3` | the note's — **inside a Python docstring**, with no qualifier |

Line 237 is the one that matters:

```python
    and the tier-2 claim in §2.3 is false."""
```

This is pinned source text the builder is instructed to write into the codebase. Once it lands in
a `.py` file, the disambiguating prose does not travel with it — and the destination file has no
§2.3 at all, so a future reader has no local way to recover which document was meant.

## Why it matters

bp-110 is **the integrator** — the chokepoint plan that bp-111, bp-113, and bp-114 all depend on,
and the one whose §6 pins the read-only facade whose leakage §10 makes a STOP. It is blessed-pending
and about to be built. A builder reading line 237 must resolve `§2.3` correctly to know which claim
is being falsified; the two candidate §2.3s (the plan's own §2 is "Context manifest", the note's
§2.3 is the handler survey stating the worker is handed *"never a `VectorStore`"*) are not
interchangeable, and §2.3 of the note is precisely the section bp-110 exists to patch a gap in.

This is not a hypothetical class of defect — it is the **specific reference the plan's central
design decision turns on**, written in the form least able to survive being copied.

## Re-entry condition

Not parked; nothing is blocked. Fix at bp-110's build, or before it starts.

## Routing

`builder` (`spec-fidelity`) — mechanical and local. The remedy is to qualify the cross-document
references so each is self-contained. Minimal form, no new convention required:

- line 237 and line 105 → name the document explicitly in the text
  (e.g. *"the tier-2 claim in dn-supervision-and-liveness §2.3"*), since a docstring must stand
  alone.
- lines 69/71 are acceptable as-is (the enclosing heading names the note) but would be clearer
  qualified.
- the `§10` references are unambiguous — they are self-references within the plan — and need no
  change.

## Discovered by

Grounding the owner's reference-standard proposal
(`docs/brainstorms/owner-cockpit.md`, the 2026-07-25 capsules). The general problem — a bare `§N`
carries no indication of *which document* it indexes, and this corpus uses the form 673× for `§3`
and 580× for `§6` — is design input for that standard, tracked there. **This finding is only the
concrete instance in a plan about to be built**, and stands on its own whether or not the standard
is ever adopted.
