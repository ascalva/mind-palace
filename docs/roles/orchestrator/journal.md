---
type: seat-journal
seat: orchestrator
created: 2026-07-26
updated: 2026-07-26
---

# Seat journal — orchestrator

The **NARRATIVE** half of the orchestrator seat's state (`dn-role-state-and-scoped-handoff` §2.5).
The agent is a disposable occupant; this file is the seat's memory, and every successor inherits
it. Append-only: entries are added at the top, never deleted and never rewritten in place
(keep-and-link, `finding-0164` / `finding-0168`).

**What belongs here — and what must not.** Only judgement a generator could not write: what to
spawn, what to watch, what was tried and rejected, an ordering intent. Everything mechanically
derivable from the artifact tree belongs in `handoff.md`, which is regenerated rather than
remembered; everything that is the result of *running* something belongs in `readings.md` with its
timestamp attached. **The purity rule (§2.5): narrative names artifacts by their stable id and
never states a machine-derivable value** — no commit hashes, no statuses, no counts, no
`path:line` into code that moves. The id is the join key; the value lives in the derived pane.

**Entry shape** — the checkpoint contract (`.claude/skills/checkpoint/SKILL.md`) generalized from a
plan to a seat, same seven sections: Status line · Completed · In-flight · Next action · Open
questions · Context-manifest delta · Markers.

**Compaction (§2.8), and the marker a linter can find.** When the active segment grows past a
working threshold, a `/triage` sweep writes a **compaction capsule**: one entry carrying forward
every still-live judgement and naming the range it supersedes. Prior entries stay beneath it,
marked superseded — retained, readable, non-binding.

> ⚑ **The capsule marker is the literal heading `## CAPSULE — <date>`.** The **authoritative
> segment** is the latest such heading plus every entry above it; everything below it is history.
> A fresh occupant may read capsule-plus-suffix and stop there. Tooling that lints or bounds this
> file keys on that exact heading — nothing else in this file may use it.

---

## 2026-07-26 — the seat is opened

**Status line.** The seat now has a home of its own; the handoff it hands over is generated rather
than remembered, and this file holds only what a generator cannot say.

**Completed.** The seat's three artifacts exist and are tracked, so they are present in every
checkout a successor might start from — a worktree, a fresh clone, a machine with nothing running.
That portability was the constraint that decided the substrate: the scheduler's queue has better
durability and better concurrency semantics than files do, and it still lost, because a handoff
that cannot be read with the system down is not a handoff. The queue earns its place as an *input*
to the derived pane instead, which is the shape `dn-role-state-and-scoped-handoff` argued for.

**In-flight.** The migration of the outgoing resume brief into this seat has **not** happened — it
is `bp-125`, and it must run where the brief actually lives, which is not a worktree. Until it
lands and `bp-126` follows it, the outgoing brief and this seat both exist, and the seat's
occupant carries both. That double bookkeeping is deliberate and temporary; `finding-0234`
records why the halves cannot be reordered.

**Next action.** Read `handoff.md` for the derived picture, then continue the topmost unit it
names. Nothing in this file needs re-deriving by hand — if a fact feels absent here, check whether
it is a derived fact that belongs in the pane instead.

**Open questions.** Whether perishable capture lists belong in this journal or should become
brainstorm files immediately is deliberately unsettled — the note parks it as V4 and the first
weeks of real use are the evidence. Do not resolve it by habit; resolve it by noticing which
choice a successor thanks you for.

**Context-manifest delta.** None — this is the first entry, and it was written from the design's
own ruling rather than from any prior seat state. No content was carried over from the outgoing
brief; carrying it is `bp-125`'s job and doing it here would fabricate the judgement it is
supposed to preserve.

**Markers.** None.

---

## Markers

<!-- Mechanical lines appended by hooks (compactions, audits, HOOK-FAILUREs) live here. -->
