# BP-001 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Committed — this is history, not scratch (§9). Narrative entries are newest-first
below the header; the `## Markers` section at the file's end receives the
mechanical lines hooks append (compactions, audits, HOOK-FAILUREs).

Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Entry — 2026-07-05 — verified; plan complete; journal sealed

**Status.** BP-001 **complete**. Criteria 1–5 all met and independently verified;
plan flipped `in-progress → complete`; this journal is sealed below. Two
out-of-scope worktree files remain for the owner to reconcile (both surfaced, not
touched) — that is the designed §12 fail-loud terminal state, not a defect.

**Verification (4-reviewer adversarial workflow — all resolved).**
- **c-code-correctness → pass.** A1 (§6c) correct: (c) calls `_diff_text_head()`
  (`git diff HEAD …`), no longer reads session-baseline, no dangling `_diff_text`.
  Empirically a committed blessing self-clears under a *stale* baseline; uncommitted
  (working-tree, staged, Bash) still blocks; `--diff-file` unchanged; empty-repo/no-HEAD
  fails safe. Reviewer proved the old code would have wrongly BLOCKED the committed case.
- **harness-fidelity → pass.** Ran it: bp-000 13/13, bp-001 5/5; bp-000/** left
  byte-identical; the (c)-committed crux proven non-vacuous (reverted-code → FAIL,
  new → PASS); `-uall`-stripped → (b) FAIL, absent digest → digest FAIL. Real guard.
- **digest-fidelity → pass.** All 12 items intact, correct order, no weakening;
  consistent superset of CONSTITUTION §II/§III; CLAUDE.md ~1 page, no bloat.
- **discipline-state → concern (resolved).** 4/5 clean (no design note touched, no
  blessing authored — the only `ratified`/`ready` literals are test DATA in run.sh
  and prose in plan.md; finding/oq states + terminals correct; plan schema-complete).
  The one concern was `bin/mp-env.sh` unacknowledged — resolved below (owner's WIP).

**Actions taken from the review.**
- **Item-12 fidelity restored (sacred bound).** The digest reviewer flagged item 12
  compressing "speech synthesis/recognition" → "speech" and dropping the emphasis on
  "**only** the owner's pre-registered number." The digest is exempt from thinness,
  so full fidelity wins for a safety line: CLAUDE.md item 12 now restores both. All
  bright-line absolutes were already intact; this is fidelity, not a fix.
- **finding-0005 filed (discovery, non-blocking).** Verification surfaced a real,
  orthogonal enforcement gap: a build plan minted *fresh at `status: ready` via Bash*
  escapes gate-guard (Edit-only) AND the Stop-gate ((c) `git diff HEAD` misses an
  untracked new file; build-plans aren't denylisted so (b) sees only a scope issue,
  or nothing in orchestrator posture). Design notes are safe (denylist). Recommended
  fix: make (c) untracked-inclusive (symmetric to A1's own (b) logic). Routed to
  orchestrator, parked; **not** in bp-001's A1/A2 scope.

**Out-of-scope worktree state (surfaced, NOT touched — owner reconciles, §12).**
- `bin/mp-env.sh` — the **owner's** parallel work (worktree/tmux workflow automation),
  created during this session in the shared worktree. Exactly the §12 caveat case:
  the builder sees an untracked out-of-scope file it did not author and must refuse
  to touch it or weaken its own audit. Left as-is; owner commits/reconciles.
- `.claude/settings.local.json` — harness permission cache auto-mutated by approvals
  (see **finding-0004**). Left as-is; owner reconciles (recommend gitignore).
The Stop-gate (b) correctly blocks close on both — the fail-loud signal working, not
a session violation. This session authored neither.

**Completed criteria.** 1 (c→HEAD) ✓; 2 (b untracked-inclusive, verified conformant,
no change) ✓; 3 (digest re-homed, fidelity-verified) ✓; 4 (finding-0003 promoted,
finding-0001 resolved, oq-0001 answered) ✓; 5 (harness green 18/18) ✓.

**In-flight.** None.

**Next action (orchestrator, post-BP-001).** Owner: reconcile the two out-of-scope
files (commit `bin/mp-env.sh`; commit-or-gitignore `settings.local.json`) and commit
the bp-001 delta. Then `/triage` can route finding-0004 and finding-0005 (both
`discovery`, both non-blocking) and, if wanted, mint their one-plan fixes. The
canonical `docs/PROGRESS.md` completion entry is the orchestrator's single-writer act
(out of bp-001 scope by design, as with BP-000 / finding-0002).

**Open questions.** `finding-0004` (Stop-gate flags harness-managed
`settings.local.json`) and `finding-0005` (Bash-minted `ready` plan escapes gates) —
both `discovery`, routed to orchestrator, parked with re-entry, **not blocking**.

**Context-manifest delta.** No new manifest reads beyond the prior entries. The
adversarial verification ran as a background subagent workflow (read-only reviewers);
its transcripts live under the session's `subagents/workflows/` dir.

**Seal.** Sealed 2026-07-05 as the final BP-001 act (hand-driven finalization; in
normal operation `/triage` seals a completed plan's journal). Narrative entries end
here; the `## Markers` section still receives mechanical hook lines.

---

## Entry — 2026-07-05 — all deltas landed; harness green (18/18); findings resolved

**Status.** BP-001 substantively complete. Three deltas implemented, both
warranting findings resolved (0003 promoted, 0001 resolved), oq-0001 answered, and
the full acceptance harness is green: bp-000 criteria 1–7 (PASS=13) re-run by
reference + the four bp-001 checks (PASS=5) = **18/18, FAIL=0**. A fresh machinery
friction was surfaced as finding-0004 (non-blocking). Pending: an adversarial
verification pass, then flip plan `in-progress → complete` and seal.

**Completed (per criterion, each reproduced by `acceptance/run.sh`).**
- **Δ1 — journal-gate (c) → HEAD (A1, finding-0003).** `_lib.py`: `_diff_text(baseline)`
  → `_diff_text_head()` doing `git diff HEAD -- docs/design-notes docs/build-plans`;
  `cmd_stop_audit` (c) no longer reads `.claude/state/session-baseline`. Proven by
  the (c)-committed check: a committed `→ ratified` flip staged under a
  *deliberately stale* baseline yields `rc=0` (self-clears) — red under the old
  code, green now; and (c)-uncommitted still blocks (rc=2, cites blessing). The
  `--diff-file` branch is untouched, so criterion 6b stays green.
- **Δ2 — journal-gate (b) untracked-inclusive (A1).** Verified conformant, no
  change: `_changed_files()` already uses `git status --porcelain --no-renames
  -uall` (file-granular, untracked-inclusive), filtered per-file in `cmd_stop_audit`.
  (b)-regression check: an untracked out-of-scope `core/rogue.txt` blocks close
  (rc=2, names the file) — criterion 2 holds.
- **Δ3 — CLAUDE.md digest re-homed (A2, finding-0001/oq-0001).** 12-item
  non-negotiables digest inserted into the always-loaded body (from pre-BP-000
  CLAUDE.md at git `0b21de6^`, cross-checked vs CONSTITUTION §II–III). digest check:
  all six representative bright lines present inline. Constitution still ~1 page;
  the digest is the one thing exempt from thinness (§5).
- **Findings/oq.** `finding-0003 → promoted` (A1 warrant, code delta + regression
  cited). `finding-0001 → resolved` and `oq-0001 → answered` (re-home the digest
  only; other dropped items stay pointer-only). Session brief now reports Unswept
  findings and Open owner questions as computed live (was 2 and 1).

**In-flight.** Adversarial verification workflow (independent reviewers on the (c)
change, harness fidelity, digest faithfulness, scope/finding-state discipline). On
clean: flip plan to `complete`, seal this journal.

**Next action.** Run the verification workflow; address any confirmed finding;
then flip `docs/build-plans/bp-001/plan.md` status `in-progress → complete` and add
the seal entry.

**Open questions.** `finding-0004` (Stop-gate (b) flags harness-managed
`.claude/settings.local.json`) — `discovery`, routed to orchestrator, parked with
re-entry, **not blocking**. Recommendation inline: gitignore the file (local
permission cache). This session did **not** touch that file — surfaced per the §12
reconcile protocol; the owner reconciles at commit.

**Context-manifest delta.** No new manifest reads beyond those noted in the prior
entry. Note: `.claude/settings.local.json` is auto-mutated by the permission system
(the finding-0004 trigger); `.claude/state/session-baseline` is overwritten to HEAD
by every `session-brief` run (gitignored, and (c) no longer reads it).

---

## Entry — 2026-07-05 — plan hand-minted; deltas begin

**Status.** BP-001 in-progress. Confirmed `docs/design-notes/agent-workflow.md`
front-matter is `status: ratified` (line 4) with §16 recording A1 (finding-0003)
and A2 (finding-0001) — the top-of-plan front-matter check passes. Plan and this
journal minted by hand (hand-mint exception documented in plan.md: the owner's
execute instruction is the readiness blessing; no agent flips a gated status).

**Completed.**
- Reconnaissance: read `_lib.py` (the `cmd_stop_audit` (c) branch reads
  `.claude/state/session-baseline`; `_changed_files` already uses
  `git status --porcelain -uall`), the bp-000 harness, both warranting findings,
  oq-0001, the pre-BP-000 CLAUDE.md (git `0b21de6^`, the 12-item digest source),
  and CONSTITUTION §II/§III (digest cross-check — faithful).
- Set `.claude/state/active-plan → docs/build-plans/bp-001/plan.md` (gitignored,
  via Bash) so scope-guard grants bp-001's capability. Minted `plan.md` (in-progress,
  gate-guard allowed) and this journal.
- Confirmed prerequisites: finding-0002 is terminal (`resolved`), so the 2 unswept
  findings are exactly 0001+0003 — resolving both drops the brief to 0.
  `.claude/hooks/__pycache__` is gitignored (won't trip the (b) audit).

**In-flight.** None; at a clean boundary before the first edit.

**Next action.** Delta 1 — edit `.claude/hooks/_lib.py`: re-anchor the (c)
blessing detector to diff `git diff HEAD -- docs/design-notes docs/build-plans`
instead of reading session-baseline; drop the baseline param from `_diff_text`;
keep the `--diff-file` branch intact. Then unit-check the decision string.

**Open questions.** None so far. Design questions, if any surface, route as typed
findings (park with re-entry; never block).

**Context-manifest delta.** Read beyond the manifest: `docs/findings/finding-0002.md`
(to confirm the terminal-status count) and `.claude/settings.json` (to confirm hook
registration + the git allowlist the harness relies on). Nothing proved irrelevant.

---

## Markers
