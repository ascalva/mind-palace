---
type: finding
id: finding-0025
status: promoted
ftype: spec-defect
origin_plan: null # surfaced in owner–orchestrator design review, triggered by finding-0024 (bp-005 denylist collision)
route: orchestrator
created: 2026-07-07
updated: 2026-07-11
links:
  - docs/design-notes/agent-workflow.md # the spec this defects against / amends
  #- docs/findings/finding-0024.md  # the collision that triggered this, design note 0024 was not needed, removed.
resolution: promoted → amendment A8 (ratified 8a5131e, owner's hand; implemented 4fe6ad4, bp-010 — 11/11 harness incl. laundering + deletion + A5-parity cases)
---

# finding-0025 — The design-note denylist guards on LOCATION when the real invariant is STATUS

> **Triage 2026-07-09 (/triage):** routed → orchestrator. Design-changing spec-defect →
> **promotion proposed as amendment A8** (A7 is taken by finding-0009/oq-0003), warrant
> this finding, batched for owner ratification at `owner-questions.md` **oq-0011**; flips
> to `promoted` on acceptance, then a builder lands the `_lib.py` change per §Disposition.
> **Live evidence since drafting:** bp-005's design-note half could only land via an
> owner **temp-lift of the global deny** (`d6e518f` lift → `f5d435d` restore) — a
> hand-operated bypass standing in for exactly the missing status-aware capability this
> finding specifies. Note: `finding-0024.md` (linked above) was deleted, owner-instructed,
> when the lift resolved the bp-005 collision (see bp-005 plan addendum); its substance
> is summarized under §"How it surfaced". Re-entry per oq-0011's park condition.

## Summary

The foundation denylist protects `docs/design-notes/**` as a whole directory, making
_every_ design note — draft or ratified — unwritable by any agent session. This is
the wrong axis. The invariant actually worth protecting is that the **ratified**
design record is tamper-proof to agents; there is no reason to forbid agents from
_creating and iterating on draft_ notes. By denying the directory instead of the
status, the current guard blocks the core orchestrator workflow — brainstorm → draft
a design note → graduate to a build plan — which is the primary reason the
orchestrator exists. The fix is to make the guard **status-aware** (ratified/superseded
notes immutable to agents; draft notes writable; the draft→ratified transition
owner-only), reusing the front-matter-status machinery already present in `_lib.py`.

This finding was drafted against a full read of `.claude/hooks/_lib.py` (current at
2026-07-07). Exact line numbers are deliberately omitted; the implementing plan's
grounded-graduation pass MUST re-confirm every function and call site named below
against the live file before editing, per the standard `path:line` discipline.

## How it surfaced

finding-0024: bp-005's `write_scope` listed `docs/design-notes/**` to let the
orchestrator convert statusless notes to front-matter format. A plan's `write_scope`
cannot re-grant a denylisted path (task instructions nest inside the constitution,
never override it — `cmd_scope_check` applies the denylist in step 1, before the
plan-scope check), so the design-note half of bp-005 was **unexecutable by any
agent** — the builder's Bash writes were caught by the Stop-gate and correctly
reverted. finding-0024 framed this as "bp-005 is ill-formed." True but shallow: the
deeper defect is that the _denylist itself_ is mis-drawn, such that a whole class of
legitimate agent work (authoring and converting draft notes) is structurally
impossible. bp-005 didn't ask for something wrong; it asked for something the guard
forbids for the wrong reason.

## The two properties in tension (both are real; the current guard sacrifices one)

1. **Agents must be able to author design notes.** The orchestrator's purpose is
   the brainstorm → note → plan flow. If a design note can only ever be created by
   the owner's hand in an editor, that flow does not exist — every note becomes
   manual authorship, and the orchestrator is reduced to a plan-runner. This is the
   capability the location-based denylist destroys.

2. **The ratified design record must be tamper-proof to agents.** This was the
   denylist's real rationale (`_lib.py` DENYLIST comment: "the sacred fixed points…
   the ratified design record"), and it is the same property that made this
   conversation's corpus audit trustworthy: the design record is authoritative
   _because_ no agent can silently rewrite a ratified note.

The location-based denylist collapses these by protecting _all_ notes to preserve
property 2 — and in doing so destroys property 1. The distinction it erases is
exactly the one the rest of the system runs on: **unblessed working material is
agent-writable (like a build plan); a blessing is agent-immutable (like a sealed
artifact).** A draft note is unblessed working material. A ratified note is a
blessing.

## Why STATUS is the correct axis, and what the code already provides

The property worth protecting is not "this file lives in `docs/design-notes/`" but
"this note has been ratified." The guard should read the note's front-matter
**status**, and the helpers to do so already exist in `_lib.py`:

- `is_design_note(path_rel)` — already classifies a design-note path (and correctly
  excludes the bare directory).
- `status_of(path_rel)` — already reads a file's **on-disk** front-matter status and
  normalizes it (`_normalize_status`, A5) against comment evasion.
- `cmd_gate_check` already keys on on-disk status (`cur = status_of(fp)`) to gate the
  `→ratified` transition.

So the corrective is the same pattern as A3/A5/A6 — the guard was checking the wrong
thing (location), and the fix makes it status-aware using machinery already built.
The change is _more_ contained than a from-scratch guard would be, because
`is_design_note` and `status_of` already exist.

## Proposed rule (for the amendment to specify precisely)

Replace the blanket `docs/design-notes/**` denylist entry with a status-aware guard.
`CONSTITUTION.md`, `eval/golden/**`, and `eval/golden.py` stay on the hard denylist
**untouched** — only the design-notes entry changes.

- **Draft design notes → agent-writable.** An agent may create a new note at
  `status: draft`, and edit a note whose on-disk status is `draft`, subject to the
  normal plan `write_scope` check. This is a draft-write, identical in trust to
  writing a build plan. (bp-005's conversion — statusless/prose-status note → `draft`
  front-matter — becomes a _legal_ operation, not a bracketed override.)
- **Ratified / superseded design notes → agent-immutable.** If the note's committed
  status is `ratified` or `superseded`, no agent write is permitted — not to its
  content, and not to its status. This is the tamper-proof-record guarantee, scoped
  to exactly the notes that carry a blessing. (Superseded notes are part of the
  accountable historical record; agents evolve them only via the proposal path.)
- **The draft→ratified transition → owner-only, unchanged.** `cmd_gate_check`
  continues to deny any agent setting `status: ratified` (and `proposed→ready` on
  plans). The new content-write rule and the existing transition rule compose.

## CORRECTION 1 — gate-guard is NOT sufficient on its own (a new content check is required)

An earlier draft of this finding implied the fix mostly reuses `gate-guard`. Reading
the code shows that undersells the gap. `cmd_gate_check_hook` returns ALLOW early when
the incoming write sets **no status line** (`new_status is None`). So `gate-guard` is
silent on a write that edits a ratified note's **body without touching its status
line** — which is precisely a write that must be blocked (an agent altering ratified
_content_). Today the _denylist_ catches that, because it blocks all writes to the
path regardless of content. Therefore: **removing the denylist and leaning on
gate-guard would leave body-only edits of ratified notes unguarded.** The amendment
must add a status-aware **content** guard, not merely extend gate-guard.

Where it goes (implementer to confirm against live `_lib.py`): the design-notes
branch belongs in `cmd_scope_check`, at the point the denylist is applied today
(step 1, before the plan-scope check). Sketch of the intended logic — NOT
final code, the builder writes and grounds it:

    if is_design_note(fp):
        st = status_of(fp)              # on-disk status; None if new file
        if st in ("ratified", "superseded"):
            DENY  # immutable blessed/historical record
        # else (draft or new) -> fall through to the normal plan-scope check
    # CONSTITUTION.md / eval/golden* remain in the hard DENYLIST, checked as today

## CORRECTION 2 — the pre-hoc vs Stop-audit asymmetry on laundering (the real hazard)

The rule must defend against **laundering**: an agent flips a ratified note back to
`draft` in a write, then edits it freely. The defense depends on reading the note's
**committed** (HEAD) status, and the two enforcement layers see different on-disk
state at the moment they run — this is the subtle, security-critical part:

- **Pre-hoc (`cmd_scope_check`, Edit/Write path):** the write has NOT happened yet,
  so the file on disk is still the OLD (ratified) version. `status_of(fp)` correctly
  returns `ratified` and the guard denies. Reading current on-disk status is correct
  here.
- **Post-hoc (`cmd_stop_audit` (b) branch, Bash path):** the Bash write has ALREADY
  happened, so the file on disk is the NEW laundered version (`draft`). A naive
  `status_of(fp)` at Stop would read `draft` and **miss the violation.** The Stop-side
  design-note check therefore must NOT use current on-disk status — it must compare
  the target's status **against HEAD** (the committed version), exactly as
  `_diff_text_head` / `_blessing_in_diff` already read HEAD for blessing detection.
  A design note whose HEAD status is `ratified`/`superseded` and whose working-tree
  copy has been modified at all (content or status) is a violation, regardless of
  what the working-tree status now says.

This asymmetry is the difference between a real guarantee and a trivially bypassable
one. It is named here because it is easy to miss; the implementer must handle both
layers, and the Stop-side HEAD comparison is the non-obvious half.

_Open sub-question for the implementer (defer — needs live-code judgment):_ the
cleanest mechanism for the Stop-side check — extend `_changed_files` filtering to
consult HEAD status for design-note paths, or add a dedicated
`_ratified_note_modified()` helper paralleling `_untracked_blessing()`, or fold it
into `_blessing_in_diff` (which already walks the HEAD diff and could flag any `+`/`-`
line in a note whose HEAD status is ratified). The builder/orchestrator has the
context to choose; this finding does not prescribe the mechanism, only the required
property (HEAD-status-keyed, catches body-only laundered edits via Bash).

## CORRECTION 3 — the fix is small and surgical (helpers already exist)

Net scope of the change, for the implementing plan to confirm and bound:

- `cmd_scope_check`: replace the design-notes arm of the denylist with the
  status-aware content guard (Correction 1). `CONSTITUTION.md` / `eval/golden*`
  unchanged.
- `cmd_stop_audit` (b): add the HEAD-status-keyed design-note-immutability check
  (Correction 2) so the Bash path is covered, symmetric to how (c) is
  untracked-inclusive.
- `DENYLIST`: remove ONLY `docs/design-notes/**`; keep the other three entries.
- `cmd_gate_check`: unchanged (still gates the ratified/ready transitions).

The helpers `is_design_note` and `status_of` already exist and are exactly the right
primitives, which is why this is an extension of existing machinery rather than a new
mechanism.

## Two-layer enforcement (the guarantee must survive the Bash path)

Consistent with the existing model, and made explicit because a body-only edit is a
new attack the denylist covered for free:

- **Pre-hoc** (`cmd_scope_check`): Edit/Write to a design note allowed only if its
  on-disk status is `draft` (or the note is new); denied if `ratified`/`superseded`.
- **Post-hoc** (`cmd_stop_audit`): a Bash-mediated modification of a note whose HEAD
  status is `ratified`/`superseded` is caught at session close (HEAD-keyed, per
  Correction 2). Pre-hoc porous, post-hoc tight — the ratified-note guarantee must
  hold against Bash, not just Edit/Write, exactly as the current denylist does.

## How this preserves — not weakens — the guarantees

- **The corpus audit's trustworthiness survives.** What made it trustworthy was that
  _ratified_ notes could not be silently altered by an agent. Under the status-aware
  rule that holds exactly — including against body-only and laundered edits, once
  Corrections 1 and 2 land. Only _draft_ notes become agent-writable, and a draft is
  by definition not part of the blessed record.
- **Ratified notes still evolve — through the accountable path, not by mutation.**
  Agent-immutability channels every change through supersession (a new note plus
  warrant) or a finding plus owner ratification — the same accountable path the
  supersession lifecycle already prescribes. The immutability is what _forces_
  evolution through that path instead of silent edits.
- **The blessing gates are untouched.** Draft→ratified and proposed→ready remain
  owner-only.

## Disposition

Routed → orchestrator. This is a `spec-defect` warranting an **amendment to
`agent-workflow.md`** (next amendment id — provisionally A7; renumber if A7 is taken
by finding-0009's gate-egress fix) that:

1. Removes `docs/design-notes/**` from the foundation denylist (keeping the other
   three entries) and specifies the status-aware guard: draft-writable,
   ratified/superseded-immutable, keyed on committed status, laundering-proof.
2. Adds the content-guard (Correction 1) and the Stop-side HEAD-keyed check
   (Correction 2); leaves `cmd_gate_check` as-is.
3. Updates the denylist/enforcement descriptions in the note (the §§ that document
   the denylist and the `scope-guard`/`journal-gate`/`gate-guard` contracts —
   implementer to locate the current section numbers).
4. Is implemented by a build plan whose grounded pass re-confirms every `_lib.py`
   reference here, with a harness regression proving, each with a clean
   non-vacuous control: (a) draft-note write ALLOWS; (b) ratified-note **content**
   (body-only, no status change) write DENIES pre-hoc; (c) Bash body-only edit of a
   ratified note BLOCKS at Stop (HEAD-keyed); (d) ratified→draft laundering write
   DENIES pre-hoc AND its Bash form BLOCKS at Stop; (e) new-note-at-draft creation
   ALLOWS; (f) `CONSTITUTION.md` / `eval/golden*` still DENY (regression — the other
   denylist entries untouched).

This finding also **resolves finding-0024**: bp-005's design-note conversion is not
ill-formed work to be hand-done or bracketed around; it is legal once the guard is
status-aware. Recommend bp-005's design-note half stay parked until this amendment
lands, then resume as a normal draft-write conversion (no denylist override).

## Notes for the implementing agent (defer to live context)

- Re-confirm all `_lib.py` function names, call sites, and section numbers against
  the live file — this finding names them from a 2026-07-07 read but does not cite
  line numbers, by design.
- Choose the Stop-side HEAD-comparison mechanism (open sub-question under Correction
  2); the finding fixes the required property, not the implementation.
- Confirm whether `settings.local.json` or any other config mirrors the DENYLIST and
  must be updated in lockstep — this finding did not verify that mirror.
- Confirm the amendment's exact section-number edits against the current
  `agent-workflow.md` structure.
