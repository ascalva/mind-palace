# BP-010 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Seal — 2026-07-11 — /triage — bp-010 `complete`, journal sealed

**Seal.** Guard live (`4fe6ad4`): 11/11 harness, ratchet 750, live smoke on the real ratified
record. finding-0025 → promoted (A8 ratified `8a5131e`, implemented here); oq-0011 swept;
`docs/inbox/proposed-amendment-A8.md` deleted per the signing-desk contract. First act under
the new guard: the code-observation-projection note placed directly at `draft` by the
orchestrator — the capability this amendment exists to grant, exercised minutes after it
landed. No narrative entries after this line.

---


## Entry — 2026-07-11 — Items 12+13+14 complete: guard live, 11/11 green

**Item 13 first (TDD):** harness written, run RED against pre-A8 code — (a) draft-allow and
(e) new-note-allow FAILED as predicted (location denylist), immutability cases passed
trivially. Non-vacuity proven per the falsifier.
**Item 12:** DENYLIST loses `docs/design-notes/**` (comment banner cites A8); `cmd_scope_check`
gains the 1b status arm (on-disk ratified/superseded → DENY with the A8 message; draft/new fall
through to capability); `_head_status_of()` added (git show HEAD:, parse_front_matter,
_normalize_status — A5 parity); `cmd_stop_audit` gains session-universal (b2): any design note
modified/deleted whose HEAD status is ratified/superseded blocks close.
**Harness: 11/11 PASS** — incl. laundering (d), comment-evasion laundering (d2), deletion (c2),
A3 untracked-blessing regression (f2), and the clean-tree no-false-block control (g).
**Live smoke:** scope-guard --standalone on ratified agent-workflow.md → DENY with A8 message.
**Item 14:** CLAUDE.md digest updated (three-entry denylist + status rule); _lib.py comment
banner. Ratchet 750 green; ruff clean; ast syntax check on _lib.py before first hook re-entry.
**Note:** this session ran UNDER the pointer (active-plan=bp-010) — every Edit above passed
through the very scope-guard being modified; the session's own Stop-gate is the final test.

---


## Entry — 2026-07-11 — session start: halt-check passed, harness-first (TDD)

**Halt-check (§0):** A8 entry present in `agent-workflow.md` §16 (ratified `8a5131e`; edit 3
landed `a19e030`). Blessing committed. Pointer set (`.claude/state/active-plan = bp-010`) — this
session runs UNDER the plan's own write_scope; the live hooks are the integration test.
**Order:** Item 13 harness first, run RED against pre-A8 `_lib.py` (falsifier: a harness that
passes on the old code is vacuous), then Item 12, then Item 14. Contracts confirmed:
`scope-guard.sh --standalone <path>` (rc 0 allow / rc 2 deny); `journal-gate.sh --standalone
[--diff-file <p>]` (block = rc 2); `CLAUDE_PROJECT_DIR` overrides ROOT → temp-repo isolation.

---


## Markers
