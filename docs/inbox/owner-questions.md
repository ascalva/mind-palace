# Owner questions

The one file the owner answers. Orchestrator-maintained (`/triage` batches
routed `design | math | direction` findings here; never dripped). Each entry
carries a `default_if_unanswered` with a **park condition**, so an unanswered
question degrades to a parked item with a re-entry — never a stalled builder (§10).

To answer: edit the entry's `answer:` line and flip `status: open → answered`.
`/triage` then sweeps the answer back to its origin artifact and marks it `swept`.

Entry shape: `status`, `origin`, `blocking` (bool), `question`, `default_if_unanswered`
(with park), `answer`.

---

## oq-0001 — Should CLAUDE.md re-home any of the pre-BP-000 domain digest?
- status: swept
- origin: docs/findings/finding-0001.md
- blocking: false
- question: BP-000 replaced the pre-BP-000 CLAUDE.md (mind-palace operating rules)
  with the persona-neutral workflow constitution, keeping only a pointer to the
  domain layer (`CONSTITUTION.md` / `BUILD-SPEC.md` / `CONVENTIONS.md`). Dropped
  from the auto-loaded surface: the 12-item non-negotiables digest, the repo map,
  the "current phase" marker, and the live-verification directive. All remain in
  `BUILD-SPEC.md` / `CONVENTIONS.md` / git history. Do you want any of that digest
  re-homed into the constitution (which costs tokens every turn), or is the
  pointer sufficient?
- default_if_unanswered: pointer-only stands (workflow constitution stays lean per
  §5). Parks as finding-0001; re-entry — owner answers here, or a `direction`
  finding reports a session missing dropped context.
- answer: Re-home the **safety-critical non-negotiables digest** (only). Ratified as
  amendment A2 (warrant: finding-0001): §5 now exempts the domain bright-line digest
  from the constitution thinness rule — an out-of-context guardrail is not a
  guardrail, so it stays inline in the always-loaded body, not behind a pointer. The
  *other* dropped items (repo map, current-phase marker, live-verify directive) are
  operational context, not guardrails, and stay pointer-only per §5 — they remain in
  `BUILD-SPEC.md` / `CONVENTIONS.md` / git history. Landed by bp-001 in CLAUDE.md.

---

## oq-0002 — Fold bp-002 and bp-003 into the formal lifecycle (`complete`), or leave held at `proposed`?
- status: swept
- origin: docs/PROGRESS.md — the standing "Owner-pending (non-blocking)" lifecycle decision
  recorded in the bp-002 note (2026-07-05) and the bp-003 note (2026-07-06, backfilled)
- blocking: false
- question: bp-002 (amendment A3) and bp-003 (amendment A4) each landed and committed under owner
  authority but never took the owner-only `proposed → ready` blessing, so both sit at
  `status: proposed` while their work is terminal — a split board against bp-000/bp-001/bp-004
  (`complete`). Fold both into the formal `ready → in-progress → complete` lifecycle to match
  bp-004, or leave them held at `proposed` as landed-but-unblessed?
- default_if_unanswered: leave held at `proposed` (the recorded state); re-entry — owner rules
  here, or a `direction` finding reports the split board causing confusion.
- answer: **FOLD BOTH TO `complete`, matching bp-004 — uniform board, no drift** (owner ruling,
  2026-07-06). Enactment respects the blessing gate: the **owner** supplies the missing
  `proposed → ready` blessing by hand on `docs/build-plans/bp-002/plan.md` and
  `docs/build-plans/bp-003/plan.md` (owner-only, never in-session, §10); the **orchestrator** then
  flips `ready → complete`, seals each journal, and writes the PROGRESS checkpoints. An agent
  `proposed → complete` shortcut is deliberately NOT used — it would bypass the readiness gate
  (see finding-0009). bp-002's §14-parked pre-hoc `status: ready` denylist is a separate item,
  unaffected. Swept into the combined bp-002 + bp-003 seal checkpoint (`docs/PROGRESS.md`, 2026-07-06).

---
