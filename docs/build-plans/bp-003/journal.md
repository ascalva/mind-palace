# BP-003 — Build journal

Records the work installing amendment A4: the investigate→reconcile→plan build-plan
template and the two skill upgrades (graduate → grounded planning pass; build-plan →
richer template semantics). Committed artifacts are history, not scratch (§9). Narrative
entries are newest-first below the header; the `## Markers` section at the file's end
receives the mechanical lines hooks append (compactions, audits, HOOK-FAILUREs).

Fresh-agent test (§9): a session given only `plan.md` + this journal + the write-scope
files must continue without re-asking anything already answered.

---

## Seal — 2026-07-06 — /triage — bp-003 `complete`, journal sealed

**Seal.** Plan flipped `ready → complete` (`plan.md:4`) and this journal sealed by `/triage`,
enacting owner ruling oq-0002 (fold bp-003 into the formal lifecycle for a uniform board). The owner
supplied the `proposed → ready` blessing by hand (owner-only, §10); the orchestrator flipped
`ready → complete` and sealed. A4's work is committed (`9b2431f`): the investigate→reconcile→plan
template + the graduate/build-plan skill upgrades; all five acceptance criteria closed (journal
below), finding-0007 → promoted, finding-0008 filed here (later reconciled by A6/bp-004). bp-003 has
no acceptance harness; verification is the required-section grep + the no-implementation graduate
dry-run recorded below. Narrative ends here; subsequent lines are mechanical markers only.

---

## Entry — 2026-07-05 — A4 installed; all five criteria closed; findings terminal/routed

**Status.** All five acceptance criteria closed and demonstrated. The A4 template is
installed verbatim; both skills are upgraded and reconciled to it; the graduate dry-run
proves the falsifier does not fire; finding-0007 is confirmed terminal. bp-003 is
**held at `status: proposed`** by design (Provenance note): this session executed under
the owner's direct instruction but performed **no** blessing transition — it never wrote
`status: ratified` or `proposed → ready`, and it did not flip this plan. The deltas are
in the working tree, uncommitted, for the owner to review and commit. Working-tree delta
is exactly the write_scope (verified: template M, both skills M, bp-003 plan+journal ??,
findings ?? — every path IN-SCOPE, zero out-of-scope).

**Completed (per criterion).**

- **Criterion 1 — template installed verbatim (Δ1).** `docs/templates/build-plan.md`
  overwritten with the owner-provided A4 form. Mechanically verified: all thirteen
  required sections present and ordered (§0 Mode & provenance · §1 Objective · §2 Context
  manifest · §3 Investigation & grounding · §4 Reconciliation · §5 Write scope · §6
  Interfaces pinned inline · §7 Items · §8 Math carried explicitly · §9 Non-goals · §10
  Stop-and-raise conditions · §11 Parked decisions · §12 Dependency & ordering summary),
  plus the top banner mandating every section is required and inapplicable ones are
  `N/A — <reason>`, never omitted. §7 items carry Acceptance test **and** a distinct
  Falsifier, Invariant(s), the `Touches stored data?` blast-radius flag, and
  Parallelizable?/Depends-on edges; §7 mandates blast-radius ordering (read-only sensing
  → reversible writes → irreversible/external); §8 carries the three-clause math
  field-guide (measures / valid when / fails its keep if). Matches §3 (line 74) and §16
  A4 (line 272).

- **Criterion 2 — graduate skill = grounded planning pass (Δ2).**
  `.claude/skills/graduate/SKILL.md` gains the "Graduation is a grounded planning pass"
  section: investigate (read code, `path:line` citations, "code does not settle this"
  rather than infer) → reconcile (banner-on-correction / cross-reference-on-extension,
  never silent replacement) → plan (emit `proposed`, blast-radius-ordered, approved
  item-by-item). States explicitly **graduation implements nothing** — an emitted
  implementation or an omitted-rather-than-N/A section means the pass was done wrong.
  Procedure runs the grounded pass first for any plan touching existing code; references
  the template's §2–§12 map.

- **Criterion 3 — build-plan skill = richer semantics, reconciled (Δ3).**
  `.claude/skills/build-plan/SKILL.md` rewritten to the new template structure:
  front-matter set + the body sections that carry the contract; per-item **acceptance
  AND a named falsifier** with the explicit rule that a falsifier merely negating
  acceptance is not one; **blast-radius ordering**; the §8 **math three-clause
  field-guide**; and the **N/A-marking discipline** (one template not two tiers — the
  finding-0007/A4 rationale). The skill's field semantics were reconciled to the
  template (which moved `objective`/`context_manifest`/`acceptance`/`non_goals`/
  `stop_conditions` from front-matter to §1/§2/§7/§9/§10) rather than left describing
  the old shape — a within-scope skill rewrite.

- **Criterion 4 — dry-run graduate, falsifier does not fire (Δ4).** In the session
  scratchpad: a trivial ratified note (`dn-add-license`, greenfield/mechanical) →
  graduated to a `proposed` plan (`bp-dryrun-license/plan.md`) on the new template.
  Mechanically checked: all thirteen sections present; §3 Investigation, §4
  Reconciliation, §8 Math each `N/A — <reason>`; the single §7 item carries an
  Acceptance test **and** a distinct Falsifier (acceptance = presence + single expected
  diff; falsifier = substantive MIT-text divergence). **No implementation emitted** —
  proven by the git working tree: the dry-run wrote only to the scratchpad, and the
  repo delta contains no LICENSE and nothing outside bp-003 scope. (Incidental: the repo
  already has a committed LICENSE at `848323b`, which is exactly the §10 stop-and-raise
  condition the dry-run plan anticipated — the plan's own discipline held.) The A4
  falsifier (an emitted implementation, or an omitted-rather-than-N/A section) does not
  fire → the graduate + build-plan upgrades took.

- **Criterion 5 — finding-0007 verified terminal (Δ5).** `status: promoted`,
  `ftype: discovery`, `warrant_for: A4`, `resolution: promoted → agent-workflow.md
  amendment A4`. The design note warrant-links it in the links block (`:15`), the
  amendments list (`:24`), and the A4 log entry (`:272`). bp-003 installed the mechanism
  A4 describes; no write to the finding was required.

**Findings.**

- `finding-0008` **filed (spec-defect, routed → orchestrator).** The ratified §3
  front-matter schema (`agent-workflow.md:74`, reinforced `:66`) still lists
  `objective`, `context_manifest`, and `re_entry` as *front-matter* keys, but the A4
  template realizes them as body sections (§1/§2/§11) and drops them from front-matter.
  The **same drift reaches the command files** (`graduate.md:17`, `build.md:26-27`,
  `scribe.md:16`), which is the sharper edge: a literal `/build` on a *new-template*
  plan would look for front-matter `acceptance`/`context_manifest`/`non_goals`/
  `stop_conditions` that now live in §2/§7/§9/§10 — un-bitten only because every plan so
  far (bp-000..bp-003) was minted on the old template. Only `re_entry` has a template-
  side mechanical stake (the parked-gate); the rest is legibility + the command glue.
  Proposed default: reconcile the *descriptions* to the template (prose-only §3
  amendment + a small command-file plan), template unchanged. Not resolved here — bp-003
  touches no design notes or commands (out of scope + foundation denylist), and this is
  the owner's design call. Per the instruction "park design questions as findings, don't
  block on me," work continued and closed.

**In-flight.** None. Clean terminal boundary: A4 installed, all five criteria closed and
verified, findings terminal (0007) / routed (0008), plan + journal written.

**Next action (owner / orchestrator).** Review the working-tree delta and commit it
(`docs/templates/build-plan.md`, `.claude/skills/graduate/SKILL.md`,
`.claude/skills/build-plan/SKILL.md`, `docs/build-plans/bp-003/**`,
`docs/findings/finding-0008.md`). Optionally: `/triage` to route finding-0008 (batch to
`owner-questions.md` if not ruled inline) and write the canonical `docs/PROGRESS.md`
checkpoint (orchestrator single-writer, out of this plan's scope by design). If the owner
wants bp-003 in the formal lifecycle, the `proposed → ready` flip is theirs to make by
hand; the audits accept a *committed* blessing and block only an uncommitted one.

**Open questions.** finding-0008 (routed, non-blocking) — owner design call on the
front-matter-vs-body field placement across §3 + the command files. None blocking.

**Context-manifest delta.** Read beyond the manifest: `docs/templates/finding.md` (to
file finding-0008 on the correct schema), `docs/build-plans/bp-002/journal.md` (the
journal-as-evidence pattern for a proposed-and-held plan). A repo-wide grep for the moved
field names surfaced the command-file drift folded into finding-0008. Nothing proved
irrelevant.

**Verification.** Template sections + N/A marks + per-item acceptance/falsifier checked
by grep against the required-section set. Dry-run no-implementation proven via the git
working tree (scratchpad-only writes; repo delta = bp-003 scope, zero out-of-scope).
finding-0007 terminal state and A4 warrant-links confirmed by grep of the finding and the
design note.

---

## Markers
