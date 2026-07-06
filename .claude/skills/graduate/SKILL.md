---
name: graduate
description: Decompose a ratified design note into session-sized build plans. Use when running /graduate — decomposition rules, session-sizing heuristics, and the split-at-graduation-never-mid-build discipline.
---

# graduate — turning a ratified note into build plans

A design note is a *decision*; a build plan is a *session*. Graduation is the
translation, and it is where scope is set. Do it once, deliberately, from a
single context that holds the whole note. The output is one or more `proposed`
plans on `docs/templates/build-plan.md` — never an implementation (A4).

## Graduation is a grounded planning pass, not a one-shot decomposition (A4)

For any plan that **touches existing code**, graduation is *investigate →
reconcile → plan*, and it stops before implementing:

1. **Investigate — read the code, ground every claim.** Fill the template's §3
   Investigation & grounding: answer each open question with a `path:line`
   citation. Where the code does not settle a question, **say so** ("the code
   does not settle this; <what would>") — never infer design to make the plan
   look finished. A plan asserting current behavior without a citation is
   ungrounded, which is the defect A4 exists to kill.
2. **Reconcile — propose, never silently replace.** Fill §4 Reconciliation: for
   each doc or code passage this design corrects or extends, quote it and propose
   a **banner-on-correction** (a correction is announced as a correction) or a
   **cross-reference-on-extension** (an extension links the thing it extends).
   Never a quiet edit. A correction to committed code is called out and carried by
   an item in §7, not slipped in.
3. **Plan — emit `proposed`, approved item-by-item.** Order §7 items by blast
   radius (read-only sensing → reversible writes → irreversible/external effects).
   Each item is independently approvable and carries per-item acceptance **and** a
   named falsifier (build-plan skill). The owner approves the plan item-by-item at
   the `proposed → ready` gate.

**Graduation implements nothing.** Reading, citing, and planning are the whole
job; the first line of code is a *build* session (`/build`), a separate context.
Emitting an implementation — or omitting a required section instead of
`N/A`-marking it — means the pass was done wrong. Greenfield or
trivial-mechanical plans mark §3/§4 (and §8) `N/A — <reason>`; the N/A is still an
act of judgment, on the record.

## The one discipline: split at graduation, never mid-build

All plan boundaries are decided here, with the entire note in view. A builder
mid-session that discovers its plan is too big does **not** re-split — it files a
`spec-defect` finding and parks; the orchestrator re-graduates. This keeps
session boundaries a property of the design, not of a tiring builder's context.
(Subagent-assisted decomposition is parked, §14 — graduate in a single context.)

## Session-sizing heuristic

One plan = one session of an Opus builder at max effort that lands with:
- a single coherent objective statable in one sentence;
- a `write_scope` a reviewer can hold in their head (a handful of globs);
- acceptance criteria that are *runnable* — a test passes, a file exists and
  parses, a command exits 0 — not "looks good";
- interfaces it depends on already pinned (see below), so it reads no design.

Split when any of these breaks: the objective needs an "and"; the write_scope
sprawls across zones (`core/` **and** `edge/`); acceptance can't be checked
without a human judgment call; or the context manifest exceeds what a fresh agent
can read and still build. Prefer more, smaller plans — resume is cheap, oversized
sessions are not.

## Pin interfaces inline (delegates to the build-plan skill)

Every plan copies the signatures, schemas, and invariants its builder must honor
**verbatim** into the plan — never "see the design note." A builder must never
infer design. This is the single most common decomposition defect; get it right
here. (Details: build-plan skill.)

## Procedure

1. Verify `status: ratified` (the command already gated; re-confirm).
2. Read the whole note. List the atomic units of work it licenses.
3. Cluster units into session-sized plans by the heuristic above. Order them by
   dependency; note cross-plan ordering in each plan's §12.
4. **For any plan touching existing code, run the grounded pass first**: read the
   code and fill §3 Investigation (`path:line` citations; "code does not settle
   this" where true) and §4 Reconciliation (banner-or-cross-reference proposals).
   Implement nothing.
5. For each plan: instantiate `docs/templates/build-plan.md` → `status: proposed`,
   least-privilege `write_scope`, ordered §2 context manifest, §7 items ordered by
   blast radius with per-item acceptance **and** named falsifier, invariants, the
   `Touches stored data?` flag, and dependency/parallelizable edges, §8 Math
   field-guide where a mathematical object is implemented, `session_budget: 1`,
   interfaces pinned inline (§6). **Every template section is present**; an
   inapplicable one is `N/A — <reason>`, never omitted. Create the plan's
   `journal.md` (alive).
6. Cross-link every plan to the note (`design_ref`, `links`).
7. Emit `proposed` only. The proposed→ready blessing is the owner's, by hand.

## Supersession, not editing

If a plan is later found defective, do not edit it in place. Mint P′ that grounds
on the `spec-defect` warrant finding; flip P to `superseded` with `superseded_by`.
Same three-place relation as claim supersession (`supersession-lifecycle.md`) —
the discredited plan stays inspectable.
