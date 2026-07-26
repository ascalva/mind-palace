---
type: finding
id: finding-0208
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - scripts/board.py                                            # :123 declared, :142 parsed, :150 assigned — never consumed
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md    # §3(4), the consequence this makes vacuous
  - docs/tracks/ops.md                                          # :7 — the only manifest that populates it
  - .claude/skills/delegate/SKILL.md                            # :57-59 "an unrecorded audit reads as audit: owed"
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# `board.py`'s `audit_refs` is parsed but never consumed — so "audit: owed" is a claim no code makes

## What

Found by a delegated read-only grounding pass during session-51.

`audit_refs` is declared on the `Track` dataclass (`scripts/board.py:123`), parsed out of each
track manifest's front matter (`scripts/board.py:142` —
`audit = [str(x) for x in (fm.get("audit_refs") or []) if not _is_absent(x)]`), and assigned onto
the constructed `Track` (`scripts/board.py:150`).

**And that is all.** It is never rendered into `docs/TRACKS.md` or `docs/DESKCHECK-QUEUE.md`, never
read by `track_phase`, never read by `is_owed`, and never referenced anywhere else in the file. A
full-file scan finds no consumer. Of the track manifests, only `docs/tracks/ops.md:7` populates it;
every other manifest declares `audit_refs: []`.

So the field is *collected* and *discarded*.

## Why it matters

1. **It makes a ratified design note's consequence vacuous.** `dn-autopilot-and-delegated-blessing`
   §3(4) states that autopilot runs *"appear in `docs/DESKCHECK-QUEUE.md` with `audit_refs`
   mandatory — an autopilot entry without both gate verdicts is malformed and reads 'audit: owed.'"*
   Nothing reads the field, so nothing can find an entry malformed, and no entry can read
   "audit: owed." The guarantee is unimplemented, not merely unenforced.
2. **The delegate skill leans on the same idea.** `.claude/skills/delegate/SKILL.md:57-59` — the
   audit *"is a named artifact, not a vibe: the deskcheck … evaluates the track against its DoD
   **and** its audit, so an un-recorded audit reads as 'audit: owed' on the board."* The board does
   not say that today, and cannot.
3. **It is the failure mode this repo has named before.** A field that exists, parses, and is
   dutifully filled in by manifests, while nothing downstream ever reads it, is indistinguishable
   from a working mechanism right up until someone depends on it. That is the same class as
   finding-0187's *"an untested switch is a claim, not a mechanism."*

## Re-entry condition

Not blocking. It blocks nothing today because no autopilot run exists to be malformed. It becomes
**load-bearing the moment AP7** (the audit-gates / board-integration plan of the autopilot family)
is built, since AP7's whole acceptance rests on the board reflecting audit presence. Fold the fix
into AP7 rather than minting a standalone plan — the renderer change and the mandatory-field check
are the same edit.

## Routing

`spec-defect`, and the resolution is entirely within the codebase — render the field, and decide
whether an empty `audit_refs` on a deskcheck-pending track should surface as "audit: owed" — so it
routes to the **builder**, not the orchestrator. No design ruling is required: the ratified note
(§3(4)) and the delegate skill (:57-59) already state the intended behaviour; the code simply does
not implement it.

⚑ One judgment call for whoever builds it, worth stating rather than discovering: `audit_refs`
currently lives on the **track manifest**, while §3(4) talks about **deskcheck-queue entries**.
Whether the field belongs on the track, on the deskcheck record, or both is not settled by either
source. If the builder cannot settle it from the artifacts, that half escalates as a `design`
finding rather than being guessed.
