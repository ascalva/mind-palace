---
description: Reflection sweep — route findings, batch owner questions, propose promotions, seal journals, checkpoint PROGRESS.
---
Run the reflection sweep (§11). This is the reflection stage made mechanical; the
orchestrator is the single writer of `PROGRESS.md`, `owner-questions.md`, plan
status fields, and finding triage annotations. Use the **finding** skill for
typing/routing rules.

Sweep, in order:

1. **Route open findings** in `docs/findings/` by `ftype` (finding skill):
   - `codebase | spec-fidelity` → belongs to the builder; note it and leave for
     the owning plan's session. Do not resolve it here.
   - `design | math | direction` (and `question`) → set `route: orchestrator`,
     flip `open → routed`. If owner input is needed, draft an entry in
     `owner-questions.md` (id, origin link, question, `blocking` bool,
     `default_if_unanswered` **with a park condition**) so an unanswered question
     degrades to a parked item with re-entry, never a stalled builder (§10).
   - `blocker` → surface prominently; it gates its origin plan.
2. **Propose promotions.** A `discovery` or `spec-defect` that changes design →
   propose a design-note supersession (or amendment) **warrant-linked** to the
   finding (three-place: P, P′, warrant; `supersession-lifecycle.md`). You draft;
   the owner ratifies or declines at the same blessing gate. On owner acceptance
   the finding flips `→ promoted`. Never edit a design note yourself.
3. **Seal completed plans.** For each plan now `complete`: append a `PROGRESS.md`
   checkpoint entry (built / verified / next / decisions) and mark the journal
   `sealed` (append a seal line; stop appending narrative entries).
4. **Sweep answered owner questions** back to their origin artifacts (fold the
   answer into the finding/plan), mark the question `swept`.
5. **Surface book debt** (§11): if a design note has been ratified or superseded
   since `docs/book/SYNC.md`, note it and offer to run `/scribe`.
6. **Surface owed deskchecks** (the third inbox — dn-track-board-and-deskcheck-gate
   D4). If any plan `status` or `track:` changed this sweep, regenerate the board
   first (`uv run scripts/board.py --write` — TRACKS.md + DESKCHECK-QUEUE.md are
   DERIVED, never hand-edited). Then read the queue (`docs/DESKCHECK-QUEUE.md`; count
   via `uv run scripts/board.py --queue-count`) and surface each owed track beside
   findings and OQ — kept raised until the owner approves each; a track is not closed
   until its deskcheck is approved. This step READS and surfaces — it adds no writer,
   and it NEVER flips a verdict (owner-only, by hand, like the two blessings).
7. Report a terse summary: routed, batched, promoted, sealed, swept, deskchecks
   surfaced (owed count).
