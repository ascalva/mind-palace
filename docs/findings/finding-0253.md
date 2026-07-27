---
type: finding
id: finding-0253
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - CONVENTIONS.md                                        # §Testing — "always A/B against a baseline snapshot, never scored cold"
  - docs/design-notes/role-state-and-scoped-handoff.md    # §2.11 F2's judge; §2.9's three-artifact seat
  - scripts/handoff_drill.py                              # judge_blocked
  - docs/build-plans/bp-127/plan.md                        # Item 17
ftype: design
origin_plan: bp-127
route: orchestrator
resolution: null
---

# F2's judge is quote-verified, not baseline-A/B'd — a deliberate deviation from CONVENTIONS §Testing, recorded rather than smoothed over

## What

§2.11 makes one half of F2 subjective: *"any `BLOCKED:` line whose answer a judge locates inside
the bundle … the one genuinely subjective check, **run as a model-judge A/B against the last
passing baseline per CONVENTIONS §Testing, never scored cold**."* CONVENTIONS §Testing says the
same: *"Use a model-judge only for subjective cases, always A/B against a baseline snapshot, never
scored cold."*

`scripts/handoff_drill.py` **does not carry a stored baseline.** It judges each `BLOCKED:` line
against the bundle directly, and requires the judge to produce **evidence**:

> Output EXACTLY one of: `ABSENT` / `PRESENT: <a verbatim quote from the bundle that answers it>`

The harness then checks that the quote is a **literal substring of the bundle**. A judge that
answers `PRESENT` but cannot quote it is counted **ABSENT**, mechanically, with a note saying the
quote check caught it.

## Why it was built that way

1. **A stored baseline would be a fourth standing seat artifact**, and note §2.9 enumerates exactly
   three (`journal.md` NARRATIVE, `readings.md` MEASURED, `handoff.md` DERIVED). Minting a
   `drill-baseline.json` is a design decision about the seat's artifact set — not a builder's call,
   and not licensed by anything bp-127 graduates.
2. **`readings.md` cannot carry it.** A MEASURED row is `(timestamp, command, one-line result)`; the
   baseline a judge A/B needs is the previous run's bundle and its full `BLOCKED:` set.
3. **The reason for the convention is satisfied by other means.** "Never scored cold" exists so a
   judge is not asked for an absolute quality verdict it has no scale for. This judge is not asked
   for a *quality* verdict at all — it is asked a locate-or-not question about a text in front of
   it, and its answer is then **verified against that text by code**. Judging against the artifact
   is a comparison; it is simply not the *temporal* comparison the convention names.

## Why it matters anyway — what the deviation costs

Quote-verification is strictly stronger than a cold score against **fabrication**, and strictly
weaker than a baseline A/B against **drift**. Specifically:

- A judge that becomes systematically *more* permissive over model versions — quoting a
  tangentially related line and calling it an answer — would not be detected. A baseline A/B would
  show the verdict changing while the bundle did not.
- There is no record of "the last passing judgement", so a FAIL cannot be triaged as *the handoff
  got worse* versus *the judge got stricter*. That distinction is exactly what a baseline buys, and
  it is the one the note asked for.

So the honest summary is: the deviation is defensible and argued, it is not free, and the thing it
gives up is drift detection — the same property the frozen-anchor discipline exists to protect
elsewhere in this system (CONSTITUTION §IV, "judge by comparison against a known-good baseline").

## Options for the owner

| option | cost | what it buys |
|---|---|---|
| **A — leave it** (default; what bp-127 ships) | none | fabrication-proof judging; no drift detection |
| **B — mint a fourth seat artifact** (`drill-baseline.json`, gitignored or tracked) | a §2.9 amendment; one more thing to keep fresh | the convention as written |
| **C — carry the baseline in the drill's own MEASURED row**, as a hash of `(bundle, blocked-set, verdict)` | a wider result cell; a hash is not a diff | detects *that* something changed, never *what* |

`[INFERENCE]` C looks like the cheapest thing that would honour the convention's intent without
growing the artifact set, but it is not ruled and it is not built.

## Re-entry condition

Three real `/triage` drill runs. If every run's judge verdict is stable on a stable bundle, the
drift risk is theoretical and option A stands on evidence rather than on argument. If a verdict
moves while the bundle does not, that is the baseline's absence being felt, and B or C becomes the
answer.

## Routing

`design` → the orchestrator. It is a deviation from a ratified note's own instruction and from
CONVENTIONS, so it is the owner's call, not a builder's; and the note is agent-immutable (A8).
