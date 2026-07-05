---
type: build-plan
id: bp-001
status: complete
created: 2026-07-05
updated: 2026-07-05
links:
  - docs/design-notes/agent-workflow.md
  - docs/findings/finding-0001.md
  - docs/findings/finding-0003.md
  - docs/inbox/owner-questions.md
objective: "Finalize amendments A1 and A2 of the ratified agent-workflow note: re-anchor journal-gate (c) to HEAD, confirm (b) is untracked-inclusive, re-home the domain non-negotiables digest into CLAUDE.md, and resolve the two warranting findings."
contract: builder
design_ref: "docs/design-notes/agent-workflow.md §6(b), §6(c), §5, §16 (amendments A1, A2)"
write_scope:
  - ".claude/hooks/**"
  - "CLAUDE.md"
  - "docs/build-plans/bp-001/**"
  - "docs/findings/**"
  - "docs/inbox/owner-questions.md"
context_manifest:
  - "docs/design-notes/agent-workflow.md   # §6b/§6c contracts + clarifications, §5 digest exemption, §16 A1/A2, §12 caveat"
  - "docs/findings/finding-0003.md          # warrant for A1 — the (b)-breadth + (c)-baseline reconciliation loops"
  - "docs/findings/finding-0001.md          # warrant for A2 — the dropped domain digest; oq-0001 is its owner question"
  - "docs/inbox/owner-questions.md          # oq-0001 (re-home the digest?) — to flip open→answered"
  - "CLAUDE.md (pre-BP-000, git 0b21de6^)   # source of the 12-item non-negotiables digest to re-home"
  - "CONSTITUTION.md §II/§III               # read-only cross-check that the digest is faithful to the kernel"
  - ".claude/hooks/_lib.py                  # cmd_stop_audit (c) + _diff_text + _changed_files (b) — the code deltas"
  - "docs/build-plans/bp-000/acceptance/run.sh  # prior harness (criteria 1–7); bp-001 wraps it + adds four checks"
acceptance:
  - "1. journal-gate (c) re-anchored to HEAD (A1, warrant finding-0003): the live blessing diff is computed against HEAD, not .claude/state/session-baseline. A committed '→ ratified' flip yields rc=0 (accountable to its commit author, §10); an uncommitted flip blocks close with reason. The --diff-file path is unchanged (criterion 6b stays green)."
  - "2. journal-gate (b) confirmed untracked-inclusive + file-granular (A1): _changed_files uses `git status --porcelain -uall`, filtered per-file against write_scope; an untracked out-of-scope file still blocks close (criterion 2 holds). Verified conformant; left unchanged if so."
  - "3. CLAUDE.md re-homes the domain non-negotiables digest into the always-loaded body (A2, warrant finding-0001 / oq-0001): the safety bright lines are inline, not pointer-only; the constitution stays ~1 page (the digest is the one thing exempt from thinness, §5)."
  - "4. finding-0003 → promoted; finding-0001 → resolved; oq-0001 → answered — each with a resolution/answer citing the amendment and this plan."
  - "5. Full harness green: prior bp-000 criteria 1–7 (re-run, unchanged) PLUS (c)-committed, (c)-uncommitted, (b)-regression, and digest — all PASS, zero FAIL."
non_goals:
  - "Editing docs/design-notes/** — the re-ratification of the note (A1/A2 already logged in §16) is the owner's, by hand. No agent writes a 'status: ratified' or 'proposed → ready' flip anywhere."
  - "Appending to the canonical docs/PROGRESS.md — outside this plan's write_scope, same as BP-000 (finding-0002); the completion checkpoint is the orchestrator's post-build single-writer act."
  - "Editing docs/build-plans/bp-000/** — outside write_scope; the prior harness is re-used by reference (wrapped), never modified. bp-001 gets its own acceptance/run.sh."
  - "Reworking (b) beyond the amended spec: the -uall breadth is deliberate and load-bearing (criterion 2); this plan verifies conformance, it does not narrow it."
stop_conditions:
  - "The design note is not status: ratified — halt and tell the owner (front-matter check; confirmed ratified before starting)."
  - "A `blocker` finding is filed — end the session after a fresh journal."
  - "An out-of-scope change cannot be reverted or converted to a finding."
session_budget: 1
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# BP-001 — Finalize amendments A1 and A2

## Hand-mint exception (why this plan is minted at `in-progress`)

The machinery already exists (BP-000). This plan is nonetheless minted **by hand**
at `in-progress` on the owner's direct instruction, rather than graduated through
`proposed → ready`. The justification is not bootstrap (as it was for BP-000) but
authority: A1 and A2 are amendments the owner has **already ratified** into the
note (§16); this plan only lands their mechanical consequences. The owner's
instruction to execute *is* the readiness blessing — the same hand the
`proposed → ready` gate reserves for the owner (§10). No agent performs a blessing
transition: `status: in-progress` is not a gated flip, and this plan never writes
`status: ratified` or `proposed → ready` anywhere. It flips to `complete` when
criteria 1–5 pass.

## Deltas (the whole of the work)

1. **journal-gate (c) → diff against HEAD (§6c, A1, warrant finding-0003).** In
   `.claude/hooks/_lib.py`, the blessing detector must compare the working tree to
   `HEAD`, flagging only an *uncommitted* `→ ratified` / `proposed → ready` flip. A
   blessing already committed must yield `rc=0` — it is accountable to its commit
   author, which is exactly §10's "deliberate, logged." The prior implementation
   diffed against `.claude/state/session-baseline` (HEAD-at-SessionStart), so a
   blessing *committed mid-session* kept firing until the baseline was re-anchored
   by hand (finding-0003 addendum). `session-baseline` is retained **only** for the
   SessionStart brief's "what changed this session" narration; enforcement no
   longer reads it.

2. **journal-gate (b) → untracked-inclusive, file-granular (§6b, A1).** Confirm the
   scope audit computes the delta with `git status --porcelain -uall` (equivalently
   `git diff --name-only ∪ git ls-files --others --exclude-standard`), filtered
   per-file against `write_scope`. `-uall` is required: plain `git diff` omits new
   files and plain `--porcelain` collapses a wholly-new directory to one entry that
   won't match a deeper scope glob. This is load-bearing for criterion 2 (a
   Bash-written file is *untracked*). It is expected to already conform from BP-000;
   verify against the amended clause and leave unchanged if so.

3. **CLAUDE.md → re-home the domain digest (§5, A2, warrant finding-0001 / oq-0001).**
   The safety-critical non-negotiables are the one category exempt from the
   constitution thinness rule: an out-of-context guardrail is not a guardrail. The
   12-item digest (recoverable from the pre-BP-000 CLAUDE.md at git `0b21de6^`, and
   cross-checkable against `BUILD-SPEC §3` / `CONSTITUTION §II–III`) is re-homed
   into the always-loaded body. Every *other* constitution token stays on the
   thinness ledger; the digest does not.

Then: `finding-0003 → promoted` (A1), `finding-0001 → resolved` and
`oq-0001 → answered` (A2), each citing the amendment and this plan.

## Interfaces pinned inline

**journal-gate (c) contract (§6c).** `cmd_stop_audit`, when not given
`--diff-file`, computes the blessing diff as
`git diff HEAD -- docs/design-notes docs/build-plans` and scans it with
`_blessing_in_diff` (unchanged). Decision surface unchanged: `ALLOW` /
`BLOCK: <reason>` on stdout; the bash wrapper maps `BLOCK` → exit 2. The
`--diff-file <path>` branch (used by the crafted-diff test) is untouched.

**journal-gate (b) contract (§6b).** `_changed_files()` →
`git status --porcelain --no-renames -uall`, one repo-relative path per line
(chars `[3:]`). `cmd_stop_audit` (b) flags any changed path that matches neither
`write_scope ∪ {plan.md, journal.md, docs/findings/**}` nor is a foundation
denylist file. Sound only under worktree isolation (§4).

**Blessing classification (unchanged).** `is_design_note(p)`: under
`docs/design-notes/`, `.md`, not the dir itself → a `+status: ratified` line is a
blessing. `is_build_plan(p)`: under `docs/build-plans/`, basename `plan.md` → a
`+status: ready` line is a blessing.

**Digest exemption (§5).** The domain bright-line digest stays inline in the
auto-loaded surface. The full list remains authoritative in `BUILD-SPEC §3`;
CLAUDE.md carries the digest, not a pointer to it.

## Steps / deliverables

- Edit `.claude/hooks/_lib.py`: re-anchor (c) to HEAD (delta 1); verify (b) breadth
  (delta 2, likely no change).
- Edit `CLAUDE.md`: insert the non-negotiables digest into the auto-loaded body
  (delta 3).
- `docs/build-plans/bp-001/acceptance/run.sh`: wrap the bp-000 harness (prior
  criteria 1–7, unmodified, via reference) and add (c)-committed, (c)-uncommitted,
  (b)-regression, digest.
- Flip `finding-0003 → promoted`, `finding-0001 → resolved`, `oq-0001 → answered`.

## Acceptance evidence

Each criterion is demonstrated in `journal.md` (newest entry first) and reproduced
by `docs/build-plans/bp-001/acceptance/run.sh`. The new (c) and (b) checks run in
**isolated throwaway git repos** (`CLAUDE_PROJECT_DIR` pointed at a temp dir with a
copy of the hooks) so real committed/uncommitted blessing states can be staged
without touching the main repo — the temp repo writes a *stale* session-baseline
to prove enforcement ignores it. The prior harness is invoked by reference and its
one mutation (a HOOK-FAILURE marker appended to the sealed bp-000 journal by
criterion 7) is snapshot-restored, so bp-000/** is left byte-identical.
