# retrospective-as-an-artifact-type

## 2026-07-27T06:40:00Z

```capsule
topic: retrospective-as-an-artifact-type
date: 2026-07-27
status: OWNER RULED — the type is approved; the TEMPLATE is to be designed in a Fable session.
         This capsule is the starting point for that pass, not the design.

seed: |
  Owner, verbatim: "yes, create a new retrospective file type, but let's use a fable session to
  design the proper template used for retrospective documents, so create a brainstorm as a
  starting point."

occasion: |
  docs/brainstorms/the-unchecked-claim.md was written as a retrospective and filed as a brainstorm
  because no type existed. It fits neither shape — which is the argument for the type.
```

## WHY THE EXISTING TYPES DO NOT HOLD IT

| type | orientation | unit | why it fails |
|---|---|---|---|
| brainstorm | **forward** — ideas, possibilities | a topic | a retrospective looks **backward at measured events** |
| finding | backward | **an instance** | a retrospective is a **class**, and it spans plans |
| design note | forward | a decision | a retrospective **decides nothing**; it is evidence for later decisions |
| journal | backward | **one plan, one session** | a retrospective spans a **wave**, and outlives the plans |
| deskcheck | backward | a track's delivery | it evaluates **the thing built**, not **how the building went** |

⇒ The gap is real: **an artifact that looks backward, at a class, across plans, and decides
nothing.** It is the only artifact whose subject is *the process rather than the product*.

## THE MATERIAL THAT ALREADY EXISTS — the Fable pass should design against these, not in the abstract

Three retrospectives were written **before the type existed**. They are the corpus to generalize
from, and their disagreements are the design questions:

1. **`the-unchecked-claim.md`** — six instances of a claim reaching a durable artifact unchecked.
   Shape: fence (what is *not* in scope) → instance table → structural diagnosis → candidate rule →
   what actually caught them → open → **not claimed**.
2. **`context-load-as-a-feedback-loop.md`** — the context explosion. Shape: measurements table →
   **named loops** (L1–L5) → a **diagnostic signature** → levers ranked weakest-first.
3. **`finding-0249`** — the vacuous-pass class. Filed as a *finding* because no type existed, and it
   strains the finding shape: it is a class with seven instances, not an instance.

⚑ **All three converge on one move: instances → structural diagnosis → transferable rule.** That
convergence is the strongest evidence for what the template's spine should be.

## ⚑ THE QUESTIONS THE FABLE PASS MUST ANSWER — not rhetorical; each has a real fork

**Q1 — What is the trigger?** A retrospective is worthless if written whenever someone feels
reflective, and worthless if never written. Candidates: on a **wave/track close**; on the **Nth
instance** of a repeated defect (finding-0249 became worth writing at ~5); on the **owner asking**.
`[INFERENCE]` The N-instance trigger is the only mechanical one — but N is unknown and probably
domain-dependent.

**Q2 — Where does it sit in the artifact chain?** `CLAUDE.md` says findings are the **only** channel
from build back to design, re-entering through the same gate brainstorms do. ⚑ **Does a
retrospective re-enter, or is it terminal evidence?** If it can propose, it needs a gate. If it
cannot, its rules must still reach the skills somehow — and today that path runs through a
brainstorm and a build plan. **Do not casually add a second channel into design**; that constraint
is load-bearing and was chosen deliberately.

**Q3 — Does it have a state machine?** Findings have `open → swept`. Notes have
`draft → ratified`. A retrospective may be **immutable once written** (a record of what was true
then) — in which case *correcting* one means writing another that supersedes it, and the
supersession chain is itself the record. `[INFERENCE]`

**Q4 — What makes it falsifiable?** This repo ratifies falsifiers, not proofs. A retrospective
claims *"this class of thing happened, for this reason."* ⚑ What would prove it wrong? Candidate:
every instance must carry **re-checkable coordinates** (file, commit, transcript row, measurement)
so a reader can re-derive rather than re-read — which is the very lesson the first two
retrospectives arrived at independently.

**Q5 — What forbids it from becoming the accumulator?** ⚑ Measured last night: the seat surface
reached **568 lines — exactly the size of the resume brief it replaced** — in one day. A
retrospective type that grows without bound recreates the disease it exists to diagnose. Does the
template cap length? Force supersession over append? Require a rule as the *terminal section*, so a
retrospective with no transferable rule is malformed by construction?

**Q6 — Does it own the prose analogue?** `the-false-success-rule.md` (owner-agreed) governs
**tests**: name the degenerate input, assert the check reddens. Its prose twin — *plausible becomes
evidence for true* — is **not yet ruled on**. If retrospectives are where process rules are made,
that twin may belong to this type rather than to `build-plan`.

## THE DELIVERABLE

`docs/templates/retrospective.md`, matching the house shape of the existing templates
(`build-plan.md`, `design-note.md`, `finding.md`, `deskcheck.md`) — every section required, with
`N/A — <reason>` as the explicit accountability act rather than silent omission.

⚑ **The template must be validated against all three existing retrospectives.** If it cannot hold
`the-unchecked-claim`, `context-load-as-a-feedback-loop`, and `finding-0249` without deforming
them, it is wrong — those were written by the need, before the form.

## NOT DECIDED HERE

Everything above is a question or an `[INFERENCE]`. The owner ruled **that** the type exists and
**that** a Fable session designs its template. Nothing in this capsule is the template.

## 2026-07-27T — THE FABLE PASS: template designed, Q1–Q6 answered

```capsule
topic: retrospective-as-an-artifact-type
date: 2026-07-27
status: TEMPLATE WRITTEN — docs/templates/retrospective.md. Designed against the three-artifact
        corpus; validated by walking each against it. Owner has not blessed anything here.

decisions:
  - Q1 (trigger): converted from a trigger into a VALIDITY condition — owner ask or observed
    class, but well-formed only with ≥3 instances spanning ≥2 origins (front-matter `instances`
    + `origins`, greppable). Below that it is a finding. [INFERENCE] N=3 is a chosen floor
    (corpus min is 5); owner may re-tune.
  - Q2 (chain): TERMINAL EVIDENCE. No second channel into design — findings stay the only one
    (dn-agent-workflow §11). Required §6 exits: every rule names the gated artifact that carries
    it onward (finding | brainstorm | plan | owner-question) or says "evidence only". Citable as
    evidence, NEVER a warrant. Corollary: no blessing gate on its states, because no authority
    is conferred — the corpus already practiced this (0249's rule exited via
    the-false-success-rule brainstorm, not by the finding self-authorizing).
  - Q3 (states): open → sealed → superseded, agent-performable (journal precedent). `followup`
    declared at write time (the after-reading that completes a baseline) lands as ONE dated
    block, then seal. Sealed = closed except ⚑ CORRECTION banners (the pattern
    context-load-as-a-feedback-loop already used). New instances ⇒ successor, never append.
  - Q4 (falsifiable): two levels. Instance: every ledger row carries a re-checkable coordinate
    or an explicit `relayed — unverified` marker (the-unchecked-claim's own rule, applied to the
    type that records it). Class: §4 diagnosis is a MEMBERSHIP TEST that must admit every ledger
    row and exclude a required §2 near-miss — all three corpus docs drew that fence
    independently (0248's two halves; healthy journals vs clause-4; 0249's "close cousin").
  - Q5 (accumulator): four structural guards — pulled-never-pushed (never in a mandatory read
    path; the resume brief's disease was push), 150-line hard cap [INFERENCE: corpus max 137],
    growth by supersession-with-recompression only, and §6 forbids resident open items (every
    item has a named onward home). Terminal-rule requirement: a rule must name its observable
    and list "would have caught: #…" against the ledger — catches-nothing ⇒ malformed.
  - Q6 (prose analogue): the template ENFORCES the prose rule inside its own borders (ledger
    coordinates, §3) but does NOT mint the repo-wide ruling — that stays open in
    the-unchecked-claim's exit, owner-gated. A template cannot casually own a rule the owner
    has not ruled on.

validation:
  - the-unchecked-claim: maps section-for-section (fence→§2, table→§3, diagnosis→§4, what-
    caught-them→§5, rule+open→§6, not-claimed→§7). Zero deformation.
  - context-load-as-a-feedback-loop: measurements + L1–L5 survive intact (§3 constrains
    coordinates, not shape); signature IS a §4 membership test; healthy-journal question moves
    open_questions→§2 fence (sharpening); before/after framing becomes `followup` first-class.
    Closest misfit: the graph/dreamer generalization — held as [INFERENCE] reach in §4, its
    design consequence exits via §6 rather than residing.
  - finding-0249: sheds the finding front-matter it strained (ftype/route/resolution), keeps
    everything else; its postscript is a ready-made §2 near-miss; its proposed actions are the
    §6 exits that in fact already exited (the-false-success-rule).

open_questions:
  - N=3 floor and 150-line cap — both [INFERENCE], owner-tunable at first use.
  - Migration of the three existing retrospectives into docs/retrospectives/ — needs a plan;
    not done here (form only, no instances minted).
  - Whether a lint (instances-count vs ledger rows, coordinate column non-empty, cap) is worth
    a ratchet — per the false-success rule it would need its own degenerate input named.

next_steps:
  - Owner reviews docs/templates/retrospective.md; first real instance is the live test.
```
