---
type: build-plan
id: bp-003
status: complete
created: 2026-07-05
updated: 2026-07-06
links:
  - docs/design-notes/agent-workflow.md
  - docs/findings/finding-0007.md
objective: "Install amendment A4 — replace docs/templates/build-plan.md with the ratified investigate→reconcile→plan template, and upgrade the graduate skill (to a grounded planning pass that reads code, cites path:line, proposes banner-or-cross-reference reconciliation, emits a proposed plan approved item-by-item, and implements nothing) and the build-plan skill (to the richer template semantics: per-item acceptance AND named falsifier, the math three-clause field-guide, blast-radius ordering, and N/A-marking discipline); verify finding-0007 is already promoted → A4."
contract: builder
design_ref: "docs/design-notes/agent-workflow.md §3 (per-item + section schema, ¶ ending line 74), §7 (graduate/build-plan skill upgrades, line 161), §16 amendment A4 (line 272)"
write_scope:
  - "docs/templates/build-plan.md"
  - ".claude/skills/graduate/**"
  - ".claude/skills/build-plan/**"
  - "docs/build-plans/bp-003/**"
  - "docs/findings/**"
context_manifest:
  - "docs/design-notes/agent-workflow.md §3 (schema ¶, line 74), §7 (skill entries, line 161), §16 A4 (line 272)   # the ratified contract A4 installs — the per-item/section fields, the two skill upgrades, the amendment rationale"
  - "docs/findings/finding-0007.md                        # warrant for A4 (already `promoted`); the discovery that hand-written prompts out-carry the bootstrap template; this plan installs the mechanism it was promoted into"
  - "docs/templates/build-plan.md                          # the OLD (bootstrap-era) template being replaced — read before overwriting so the delta is legible"
  - ".claude/skills/graduate/SKILL.md                      # the skill upgraded to the investigate→reconcile→plan grounded planning pass"
  - ".claude/skills/build-plan/SKILL.md                    # the skill upgraded to the richer template semantics"
  - "docs/build-plans/bp-002/plan.md + journal.md          # the proven pattern for a plan minted at `proposed` and HELD there under direct owner instruction; journal-as-evidence"
acceptance:
  - "1. docs/templates/build-plan.md is installed verbatim to the owner-provided A4 form. Every required section is present and in order: §0 Mode & provenance, §1 Objective, §2 Context manifest, §3 Investigation & grounding, §4 Reconciliation, §5 Write scope, §6 Interfaces pinned inline, §7 Items (per item: Objective / Acceptance test / Falsifier / Invariant(s) / Touches stored data? / Parallelizable? + Depends on), §8 Math carried explicitly, §9 Non-goals, §10 Stop-and-raise conditions, §11 Parked decisions, §12 Dependency & ordering summary — plus the top banner mandating that every section is required and inapplicable ones are marked `N/A — <reason>`, never omitted. Matches §3/§16 A4 (per-item acceptance AND named falsifier; path:line-cited investigation; banner-vs-cross-reference reconciliation; math measures/valid-when/fails-its-keep-if; blast-radius ordering; dependency-edge/parallelizable marking)."
  - "2. The graduate skill (.claude/skills/graduate/SKILL.md) references docs/templates/build-plan.md and enforces the investigate→reconcile→plan grounded planning pass: for a plan touching existing code, graduation READS the code, answers open questions with path:line citations (and says 'the code does not settle this' rather than infer), proposes doc/code reconciliation as banner-on-correction / cross-reference-on-extension (never silent replacement), emits a `proposed` plan the owner approves item-by-item, and IMPLEMENTS NOTHING. Greenfield/mechanical plans mark the grounding sections N/A."
  - "3. The build-plan skill (.claude/skills/build-plan/SKILL.md) references the template and enforces the richer semantics: per-item `acceptance` AND a distinct named `falsifier`; the §8 math three-clause field-guide (measures / valid when / fails its keep if); §7 blast-radius ordering (read-only sensing → reversible writes → irreversible/external effects); and the N/A-marking discipline (a required section that does not apply is `N/A — <reason>`, never omitted)."
  - "4. Dry-run: graduating a trivial (greenfield, mechanical) ratified note through the UPDATED graduate + build-plan skills against the NEW template yields a well-formed `proposed` plan whose inapplicable sections (§3 Investigation, §4 Reconciliation, §8 Math) are each marked `N/A — <reason>`, with NO implementation emitted and NO required section omitted — i.e. the A4 falsifier does not fire. (Executed in the session scratchpad; not committed as a real artifact.)"
  - "5. finding-0007 verified terminal at `status: promoted` → A4 (line 4); this plan installs the mechanism it was promoted into. No write to the finding is required."
non_goals:
  - "Editing docs/design-notes/** — A4 is already ratified into §3/§7/§16 by the owner's hand; this plan lands only its mechanical consequence (the template + the two skills). No agent writes `status: ratified` or `proposed → ready` anywhere."
  - "Flipping bp-003 `proposed → ready` (or to in-progress/complete). That readiness blessing is owner-only and owner-manual (§10), mechanically fenced by gate-guard (Edit path) and the Stop-gate (c) audit (Bash path). This session performs NO blessing transition; the journal, not a status flip, carries completion evidence (as bp-002)."
  - "Implementing anything through the graduate dry-run. The whole point of A4's graduate upgrade is that graduation implements nothing; the dry-run PROVES that discipline, it does not build. Emitting an implementation would BE the falsifier firing."
  - "Rewriting this plan (bp-003/plan.md) in the NEW template shape. bp-003 is, by construction, the last plan written against the OLD template (it installs the new one), so it follows the bp-002/old-template body shape for self-consistency and honest provenance."
  - "Appending to the canonical docs/PROGRESS.md — outside write_scope; the completion checkpoint is the orchestrator's post-build single-writer act (as with bp-000/bp-001/bp-002, finding-0002)."
stop_conditions:
  - "The design note is not `status: ratified` — halt and tell the owner (front-matter check; confirmed `ratified`, line 4, before starting)."
  - "A `blocker` finding is filed — end the session after a fresh journal."
  - "An out-of-scope change cannot be reverted or converted to a finding."
session_budget: 1
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# BP-003 — Install amendment A4 (investigate→reconcile→plan template + the two skill upgrades)

## Provenance — the last plan against the old template; minted at `proposed` and held there

bp-003 is **self-hosting in the same sense BP-000 was**: it is the last build plan
written against the *old* (bootstrap-era) template, and its deliverable is the *new*
one. It therefore follows the old-template body shape (as bp-002 does) — Provenance,
Deltas, Interfaces pinned inline, Steps/deliverables, Acceptance evidence — rather than
its own output form. Writing bp-003 against the template it replaces is the honest
record of the transition.

As with bp-002, two things are held apart:

- **Authority to act** — the owner's direct instruction in this session *is* the
  authorization to install A4. A4 itself is already the owner's ratified amendment
  (§16, warranted by finding-0007); the work here lands only its mechanical
  consequence (the template file and the two skills).
- **The readiness blessing** — `proposed → ready` is an owner-only, owner-manual
  front-matter edit (§10), mechanically fenced by `gate-guard` (Edit path) and the
  Stop-gate (c) audit (Bash path). This session performs **no** blessing transition
  anywhere: it never writes `status: ratified` or `proposed → ready`, and it does not
  flip this plan out of `proposed`.

Consequently the plan is the artifact-of-record for the capability (`write_scope`),
the pinned A4 contract, and the acceptance set, while the **journal** carries the
completion evidence. If the owner wishes to fold this into the formal
`ready → in-progress → complete` lifecycle, that is a hand blessing made outside a
session; the audits accept a *committed* blessing and block only an uncommitted one.

## Deltas (the whole of the work)

1. **Install `docs/templates/build-plan.md` (the A4 form, §3/§16).** Overwrite the
   bootstrap-era template with the ratified investigate→reconcile→plan template
   (owner-provided, verbatim). The new template carries, by construction: a top banner
   that **every section is required** and an inapplicable one is `N/A — <reason>`,
   never omitted; §3 Investigation & grounding (open questions answered with
   `path:line`, "the code does not settle this" instead of inference); §4
   Reconciliation (banner-on-correction / cross-reference-on-extension, never silent
   replacement); §7 Items ordered by **blast radius** (read-only sensing → reversible
   writes → irreversible/external effects), each item carrying `Acceptance test` **and**
   a distinct **`Falsifier`**, `Invariant(s)`, a `Touches stored data?` blast-radius
   flag, and `Parallelizable?`/`Depends on` edges; §8 Math carried explicitly (each
   object's three-clause field-guide: *measures* / *valid when* / *fails its keep if*).

2. **Upgrade the graduate skill (§7) to a grounded planning pass.** For a plan touching
   existing code, graduation is no longer a one-shot decomposition: it **reads the
   code**, answers each open question with a `path:line` citation (or explicitly records
   "the code does not settle this" and what would), proposes doc/code reconciliation as
   **banner-or-cross-reference** (never silent replacement), and emits a `proposed` plan
   the owner **approves item-by-item**. It **implements nothing** — that bright line is
   the graduate half of the A4 falsifier.

3. **Upgrade the build-plan skill (§7) to the richer template semantics.** Document the
   per-item **acceptance AND named falsifier** (distinct: acceptance says "it works,"
   the falsifier names the observable that would show it doesn't or the approach is
   wrong); the §8 **math three-clause field-guide** (measures / valid-when /
   fails-its-keep-if); §7 **blast-radius ordering**; and the **N/A-marking discipline**.

Then: **verify** `finding-0007` is already `status: promoted → A4` (it is — the finding
was the warrant for the amendment this plan installs; no write needed).

## Interfaces pinned inline

**A4 required-section set (the template must carry all, in order; §3/§16).** §0 Mode &
provenance · §1 Objective · §2 Context manifest · §3 Investigation & grounding · §4
Reconciliation · §5 Write scope · §6 Interfaces pinned inline · §7 Items · §8 Math
carried explicitly · §9 Non-goals · §10 Stop-and-raise conditions · §11 Parked
decisions · §12 Dependency & ordering summary. Plus the banner: *every section required;
inapplicable → `N/A — <reason>`, never omitted*.

**A4 per-item field set (§3, line 74; §7 template semantics).** Each §7 item carries:
`Objective` · `Files` · **`Acceptance test`** (runnable) · **`Falsifier`** (the
observable that would show the item failed or its approach is wrong — *distinct from*
acceptance) · **`Invariant(s)`** it must not violate · **`Touches stored data?`**
(blast-radius flag; if yes, a dry-run/verification pass precedes the real write) ·
**`Parallelizable?`** and **`Depends on`** edges. Items are ordered by blast radius:
read-only sensing → reversible writes → irreversible/external effects.

**A4 math field-guide (§8, three clauses; §16 "measures / valid-when /
fails-its-keep-if").** For each mathematical object: *measures:* what it measures ·
*valid when:* the assumptions that make it valid · *fails its keep if:* the observable
that shows it is not earning its place. Required only for a plan implementing a
mathematical object; `N/A — no mathematical object implemented` otherwise.

**A4 graduate discipline (§7, line 161; §16 A4).** For a plan touching existing code,
graduation READS the code, answers open questions with `path:line` citations (says "the
code does not settle this" rather than infer), proposes reconciliation as
banner-or-cross-reference (never silent replacement), emits a `proposed` plan approved
item-by-item, and **implements nothing**.

**N/A discipline (§3, §16 A4).** One template, not two tiers. A required section that
does not apply is marked `N/A — <reason>`; the explicit N/A is itself an accountability
act (the author considered the section and judged it inapplicable, on the record).
Sections most often N/A on greenfield/trivial-mechanical plans: §3 Investigation, §4
Reconciliation, §8 Math. Never N/A on a plan touching existing code or implementing a
mathematical object.

**Blessing fences (unchanged; §6, §10).** No agent may write `status: ratified` or
`proposed → ready`. `gate-guard` denies the Edit path pre-hoc; the Stop-gate (c) audit
(untracked-inclusive since A3) blocks the Bash path. bp-003 is minted at `proposed` and
never flipped in-session.

## Steps / deliverables

- **Δ1** — `docs/templates/build-plan.md`: overwrite with the owner-provided A4 template,
  verbatim. Confirm all thirteen required sections (§0–§12) plus the N/A banner are
  present and ordered, and that §7 items carry acceptance **and** falsifier, invariants,
  the stored-data flag, and dependency/parallelizable edges. (Acceptance 1.)
- **Δ2** — `.claude/skills/graduate/SKILL.md`: add the investigate→reconcile→plan
  grounded-planning-pass discipline; state "implements nothing"; point at the new
  template. (Acceptance 2.)
- **Δ3** — `.claude/skills/build-plan/SKILL.md`: add the per-item acceptance-AND-falsifier
  semantics, the §8 math three-clause field-guide, §7 blast-radius ordering, and the
  N/A-marking discipline; point at the new template's section map. (Acceptance 3.)
- **Δ4** — Dry-run in the session scratchpad: a trivial (greenfield, mechanical) ratified
  note → graduate → a well-formed `proposed` plan with §3/§4/§8 marked `N/A — <reason>`,
  no implementation emitted, no required section omitted. Record the outcome in the
  journal. (Acceptance 4.)
- **Δ5** — Verify `docs/findings/finding-0007.md` is `status: promoted → A4`; record the
  verification in the journal. No write to the finding. (Acceptance 5.)

## Acceptance evidence

Each criterion is demonstrated in `journal.md` (newest entry first). The template
sections are checked against the A4 required-section set above; the skill disciplines are
checked against §7/§16; the dry-run's N/A-marking and no-implementation are the concrete
proof that the graduate + build-plan upgrades took (the A4 falsifier: an emitted
implementation or an omitted-rather-than-N/A section). The deltas land in the working
tree, uncommitted, for the owner to review and commit; bp-003 is held at `proposed` by
design (see Provenance).
