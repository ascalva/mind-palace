---
name: build-plan
description: Semantics of the build-plan template (docs/templates/build-plan.md) — write_scope as capability, §2 context manifest, §7 per-item acceptance AND named falsifier, blast-radius ordering, §8 math field-guide, N/A-marking discipline, and pinning interfaces inline so a builder never infers design. Use when authoring or reviewing a build plan.
---

# build-plan — template semantics

A build plan is a **capability plus a contract**: it grants exactly the write
surface a session needs and tells a fresh agent everything it must know without
reading the design. Template: `docs/templates/build-plan.md` — thirteen required
sections, §0 Mode & provenance through §12 Dependency & ordering summary. Every
section appears in every plan; an inapplicable one is `N/A — <reason>` (below),
never omitted.

## Front-matter fields

- **`write_scope` (the capability).** Glob list, least-privilege. Mechanically
  enforced by `scope-guard` (pre-hoc deny) and the `journal-gate` audit (post-hoc,
  catches Bash writes) — not a suggestion (§2, §6 of the design note). Grant the
  narrowest set of globs that lets the plan close. The plan's own `plan.md` and
  `journal.md`, and `docs/findings/**`, are always writable and need not be listed.
  Never include a foundation file (`CONSTITUTION.md`, `docs/design-notes/**`,
  `eval/golden/**`) — the denylist overrides write_scope regardless.
- **`design_ref`.** The ratified design-note id(s) this plan graduates from.
- **`depends_on` / `parallelizable_with`.** Plan/item ids that must complete before
  this may start, and plans that may run concurrently (requires disjoint
  write_scope). §12 restates these in prose.
- **`session_budget: 1`.** Always one. Plans are session-sized by construction; if
  the work will not fit ONE session, SPLIT at graduation, never mid-build.
- **`supersedes` / `superseded_by` / `warrant`.** Set when this P′ replaces a
  defective P on a `spec-defect` warrant finding (three-place, never edit-in-place).

## Body sections that carry the contract

- **§0 Mode & provenance.** For a grounding plan, records that investigation and
  planning produced it and implementation proceeds item-by-item on owner approval;
  separates authority-to-act (the owner's instruction) from the readiness blessing
  (owner-only `proposed → ready`). No agent flips readiness.
- **§2 Context manifest (the read list).** Ordered. A fresh agent reads exactly
  these, in order, and can then build. If building needs a file not listed, that is
  a manifest defect — the journal records the delta and a richer resume/plan fixes
  it. Keep it minimal and sufficient.
- **§3 Investigation & grounding / §4 Reconciliation.** The graduate grounded pass
  fills these for a plan touching existing code: `path:line` citations ("code does
  not settle this" where true), and banner-on-correction / cross-reference-on-
  extension proposals — never a silent replacement. `N/A — greenfield` / `N/A —
  nothing corrected or extended` otherwise. (graduate skill.)
- **§7 Items — per-item acceptance AND a named falsifier.** Each item carries:
  - **Acceptance test** — runnable, checkable by a machine or a crisp observation:
    a test passes, a file parses, a command exits 0, a hook denies with the right
    reason. Avoid "works well."
  - **Falsifier** — the observable that would show the item FAILED or its approach
    is WRONG, **distinct** from acceptance. Acceptance says "it works"; the
    falsifier names the thing that, if seen, means it does not, or the assumption is
    false. Every item carries both. A "falsifier" that only negates the acceptance
    test ("acceptance didn't pass") is not one — name the *independent* observable
    that would disconfirm the approach.

    **Falsifier-demo runs carry a side-effect audit** (owner-ratified 2026-07-12;
    warrant: finding-0039 / oq-0017): the demo discipline — run a NEW suite once
    against the PRE-change module and show the red — executes old code by design,
    and old code may hold live side-effecting functions. Before any demo run,
    enumerate the pre-change module's live-action functions (network calls,
    credential access, dispatches, writes) and mock/skip them for the run. The
    incident-in-fact: a demo run live-rotated a real PAT (benign only because that
    path was fail-safe).
  - **Invariant(s)** it must not violate; **Touches stored data?** (the blast-radius
    flag — if yes, a dry-run / verification pass precedes the real write);
    **Parallelizable?** and **Depends on** edges.

  **Order items by blast radius:** read-only sensing → reversible writes →
  irreversible / external effects. The safest, most reversible work lands first, so
  a stop-and-raise costs the least already-spent blast radius.
- **§8 Math carried explicitly.** For each mathematical object the plan implements,
  a three-clause field-guide entry: *measures* (what it measures) · *valid when*
  (the assumptions that make it valid) · *fails its keep if* (the observable that
  shows it is not earning its place). Formalism earns its place here or is cut.
  `N/A — no mathematical object implemented` otherwise.
- **§9 Non-goals / §10 Stop-and-raise conditions.** Non-goals bound scope creep;
  stop-and-raise names when the builder STOPS and surfaces rather than proceeds — an
  owner-level question (park the criterion, continue others; never block on owner), a
  discovered spec defect (file a finding), a blast-radius surprise, or a blessing it
  would have to perform (it must not).
- **§11 Parked decisions / §12 Dependency & ordering summary.** Each parked decision
  records the default, the rejected alternatives *with reasons*, and a re-entry
  condition + named prerequisite. §12 maps the item dependency edges and the
  blast-radius phase order — the same map `/graduate` used to size the plan.

## N/A-marking discipline — one template, not two tiers

Every one of the thirteen sections is present in every plan. A section that does not
apply is marked `N/A — <one-line reason>`, never silently omitted. The explicit N/A
is an accountability act: it records that the author considered the section and
judged it inapplicable, on the record. This is why there is one richer template
rather than a lean/heavy split — N/A gives a trivial plan the same relief a two-tier
scheme would, without forcing a routing decision at graduation that could
under-ground a plan mistyped as trivial (finding-0007 / A4). Sections most often
N/A: §3, §4, §8. **Never** N/A on a plan touching existing code (§3/§4) or
implementing a mathematical object (§8).

## Pin interfaces inline — the cardinal rule (§6)

Copy every signature, schema, invariant, and constant the builder must honor
**verbatim** into §6 Interfaces pinned inline. Never write "see the design note" or
"follow the existing pattern." The builder must be able to build correctly with
*only* the plan + manifest + journal in context. A plan that forces the builder to
infer design is defective — that inference is exactly where drift enters. When in
doubt, over-pin.

## Status lifecycle

`proposed → ready → in-progress → complete | parked | superseded`.
- `proposed→ready` is the owner's blessing (hand edit; `gate-guard` denies agents on
  the Edit path, the Stop-gate (c) audit catches a Bash-minted `ready` — A3).
- `ready→in-progress` is `/build`. `in-progress→complete` is the orchestrator on
  acceptance. `→parked` **requires** a re-entry condition. `→superseded` mints P′ on
  a warrant finding (three-place, never edit-in-place).
