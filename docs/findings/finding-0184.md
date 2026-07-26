---
type: finding
id: finding-0184
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/build-plans/bp-104/plan.md
  - docs/research/security-planes.md
  - docs/design-notes/type-system-as-core-audit.md
  - .claude/hooks/_lib.py
  - docs/design-notes/agent-workflow.md
ftype: spec-defect
origin_plan: bp-104
route: orchestrator
resolution: routed → owner (oq-0044b); security-planes.md is draft yet a ratified note AND the live denylist stand on it
---

# The three-plane security composition is load-bearing but lives in a DRAFT research note

> **Triage 2026-07-26 (session-52) — batched to `oq-0044` part (b).**
> `docs/research/security-planes.md:2-4` is still `type: research, status: draft` — while two things
> already stand on it: **ratified** `dn-type-system-as-core-audit` takes its three-plane composition
> as doctrine, and the **live foundation denylist cites it as its origin** —
> `.claude/hooks/_lib.py:27` reads verbatim *"(design-note §6, §10; origin: security-planes.md)"*,
> with `DENYLIST` at `:35-39` holding three entries, **narrower than the note's candidate
> enumeration**, exactly as this finding predicted. `oq-0012` ratified only the *extension*, never the
> base note. Unratified means its falsifier can never be a plan's acceptance criterion.

## What

`docs/research/security-planes.md` is `type: research, status: draft` at
`009b726` (its own header says "Placement: `docs/research/` pending ratification;
candidate for promotion to `docs/design-notes/`"). Two things nevertheless rest
on it today:

1. **A ratified design note takes it as doctrine.**
   `dn-type-system-as-core-audit` (**ratified**) §1.1: *"`security-planes.md`
   assigns the code plane to types … Doctrinally this adds nothing to the
   three-plane composition. It is a conservative extension: the mechanism the code
   plane already assumed."* Its §3.1 then states the note "licenses no change to
   the three-plane composition itself." A ratified note is thus scoped *by
   reference to* an unratified artifact.

2. **A live enforcement mechanism cites it as its origin.**
   `.claude/hooks/_lib.py:27` (verified at `009b726`):

   ```
   # --- Foundation-file denylist (design-note §6, §10; origin: security-planes.md).
   ```

   The `DENYLIST` beneath it (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`)
   is refused to every session, orchestrator included. Its stated warrant — the
   research note's §2 invariant, *"the builder's write capability never covers the
   files that define representability"* — is unratified.

The book cannot cite the note (drafts are barred, `dn-agent-workflow` §3), so
Chapter 2 of the design manual states the *mechanisms* (import firewall, type
tiers, denylist, capability lattice) without the composition argument that says
**why three separate instruments are needed and why none substitutes for
another** — including the note's own falsification clause ("the composition claim
fails if a demonstrated attack crosses planes").

## Why it matters

This is the boundary chapter's missing thesis. The manual can show that types
constrain what compiles, that provenance constrains what data may influence, and
that capabilities constrain who may redefine either — but it cannot state, on the
record, the claim that ties them: *the planes do not overlap and do not substitute
for one another.* Without it the chapter reads as a list of defences rather than
an argument for a composition, which is exactly the "knowledge dump" failure the
scribe contract names.

Beyond the book: an unratified frame is an unfalsifiable one in practice. The
composition's falsifier is stated in the research note and nowhere else, so no
build plan can name it as an acceptance criterion and nothing forces it to be
tested. Meanwhile `dn-type-system-as-core-audit` — which *is* ratified — has a
scope clause ("licenses no change to the three-plane composition") whose referent
the record does not bless.

## Proposal

Promote `docs/research/security-planes.md` to a design note and ratify it, per
its own header's stated intent. Its §2 candidate enumeration of the foundation
file set is explicitly marked "to be verified against the repo before
ratification" — that verification is now cheap, because the denylist it predicted
exists in code (`_lib.py:35`) and is narrower than the enumeration (three entries,
not the full candidate list). The reconciliation between predicted set and
enforced set is itself worth recording.

## Re-entry condition

The owner ratifies a design note carrying the three-plane composition. A
`/scribe` run then adds the composition argument as Chapter 2's opening thesis
(it is currently written as the manual's own reading of the ratified mechanisms,
which is honest but weaker) and cites the denylist's origin.

## Routing

`spec-defect` bearing on **design** → the orchestrator; owner input required
(ratification is owner-only). Not a blocker: bp-104 wrote the chapter from the
ratified mechanisms and stated its organizing frame as the manual's reading
rather than as a ratified claim.
