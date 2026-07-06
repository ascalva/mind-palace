---
type: build-plan
id: bp-002
status: complete
created: 2026-07-05
updated: 2026-07-06
links:
  - docs/design-notes/agent-workflow.md
  - docs/findings/finding-0005.md
  - docs/findings/finding-0004.md
objective: "Land amendment A3 — make the Stop-gate (c) blessing detector untracked-inclusive over docs/design-notes/** and docs/build-plans/**/plan.md so a Bash-minted plan at status: ready is caught — and lock finding-0004's ambient-path exclusion, resolving finding-0005 → promoted and finding-0004 → resolved."
contract: builder
design_ref: "docs/design-notes/agent-workflow.md §6(c) (untracked-inclusive clarification), §16 (amendment A3); finding-0004 ambient-path exclusion"
write_scope:
  - ".claude/hooks/**"
  - ".gitignore"
  - "docs/build-plans/bp-002/**"
  - "docs/findings/**"
context_manifest:
  - "docs/design-notes/agent-workflow.md §6(c), §16 A3   # the ratified contract A3 implements — (c) untracked-inclusive over the blessing surfaces; and the §6 ambient-path-exclusion paragraph (finding-0004)"
  - "docs/findings/finding-0005.md                        # warrant for A3 — the Bash-minted `ready` plan that escapes every gate; option (a) is this code delta"
  - "docs/findings/finding-0004.md                        # the ambient-path case — gitignore `.claude/settings.local.json`; option (a)"
  - ".claude/hooks/_lib.py                                # cmd_stop_audit (c) + _diff_text_head/_blessing_in_diff — where the untracked-inclusive scan is added"
  - ".claude/hooks/journal-gate.sh                        # the Stop wrapper (ALLOW/BLOCK→rc); unchanged, used by the harness standalone"
  - "docs/build-plans/bp-001/acceptance/run.sh            # prior harness (wraps bp-000); bp-002 wraps it by reference and adds the A3/0004 checks"
  - ".gitignore                                           # confirm `.claude/settings.local.json` is present (committed 868ed17) — finding-0004 (a)"
acceptance:
  - "1. A3 in `.claude/hooks/_lib.py` (§6c, warrant finding-0005): the Stop-gate (c) audit is untracked-inclusive over `docs/design-notes/**` and `docs/build-plans/**/plan.md`. It reads the on-disk front-matter of *untracked* plan/design files (`git ls-files --others --exclude-standard`) and flags a new file already at a blessed status (plan `ready`, note `ratified`) as a from-nothing blessing — the case invisible to `git diff HEAD` and to gate-guard (Edit/Write-only). The tracked-diff path (`_blessing_in_diff`) is unchanged."
  - "2. A1 preserved intact: because the new scan reads only *untracked* files, a *committed* blessing (tracked, in HEAD) never trips it — a committed → ready plan yields rc=0 (self-clears, §6c). Verified by the committed-blessing check."
  - "3. finding-0004 (a) ambient-path exclusion: `.gitignore` carries `.claude/settings.local.json` (committed 868ed17); the file is untracked, so its permission-cache churn never reaches the audit's working-tree diff and no longer trips (b)."
  - "4. Full harness green (`docs/build-plans/bp-002/acceptance/run.sh`): all 18 prior criteria (bp-000 1–7 + bp-001 A1/A2, re-run by reference) PLUS 0005-regression (untracked `ready` blocks, cites blessing + file), 0005-legit (untracked `proposed` does NOT block), committed-blessing (committed `ready` rc=0), (c)-uncommitted-plan (in-place flip still blocks), and 0004 (tracked churn blocks / gitignored churn clean) — all PASS, zero FAIL."
  - "5. finding-0005 → promoted (warrant for A3, code delta + regression cited); finding-0004 → resolved (gitignore + regression lock cited)."
non_goals:
  - "Editing docs/design-notes/** — A3 is already ratified into §6(c)/§16 by the owner's hand; this plan lands its mechanical consequence only. No agent writes a `status: ratified` or `proposed → ready` flip anywhere."
  - "Flipping this plan `proposed → ready` (or to in-progress/complete). That readiness blessing is owner-only and owner-manual (§10); it is deliberately NOT performed here — see the provenance note below. The work is executed under the owner's direct instruction; the journal, not a status flip, carries the completion evidence."
  - "Appending to the canonical docs/PROGRESS.md — outside write_scope; the completion checkpoint is the orchestrator's post-build single-writer act (as with BP-000/BP-001, finding-0002)."
  - "The stronger *pre-hoc* denylist of `docs/build-plans/**/plan.md` `status: ready` writes — parked in §14 (added by A3) for an owner ruling; A3 is the post-hoc catch only. Not built here."
  - "Editing docs/build-plans/bp-000/** or bp-001/** — the prior harnesses are re-used by reference (wrapped), never modified. bp-002 gets its own acceptance/run.sh."
stop_conditions:
  - "The design note is not status: ratified — halt and tell the owner (front-matter check; confirmed `ratified`, line 4, before starting)."
  - "A `blocker` finding is filed — end the session after a fresh journal."
  - "An out-of-scope change cannot be reverted or converted to a finding."
session_budget: 1
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# BP-002 — Land amendment A3 (Stop-gate (c) untracked-inclusive) + lock finding-0004

## Provenance — why this plan is minted at `proposed` and stays there

Unlike BP-001 (minted at `in-progress` under a documented hand-mint exception), this
plan is minted at **`status: proposed`** and is **not** flipped by any agent. Two
things are held apart:

- **Authority to act** — the owner's direct instruction in this session *is* the
  authorization to implement A3. A3 itself is already the owner's ratified amendment
  (§16, warranted by finding-0005/0004); the work here only lands its code
  consequence.
- **The readiness blessing** — `proposed → ready` is an owner-only, owner-manual
  front-matter edit (§10), mechanically fenced by `gate-guard` (Edit path) and the
  Stop-gate (c) audit (Bash path — the very thing A3 hardens). This session performs
  **no** blessing transition anywhere: it never writes `status: ratified` or
  `proposed → ready`, and it does not flip this plan out of `proposed`.

Consequently the plan is the artifact-of-record for the capability (`write_scope`),
the pinned contract, and the acceptance set, while the **journal** carries the
completion evidence and the green harness is the proof. If the owner wishes to fold
this into the formal `ready → in-progress → complete` lifecycle, that is a hand
blessing they make outside a session; the audits (now including A3) will accept a
*committed* blessing and block only an uncommitted one.

## Deltas (the whole of the work)

1. **journal-gate (c) → untracked-inclusive (§6c, A3, warrant finding-0005).** In
   `.claude/hooks/_lib.py`, the (c) blessing detector must also read *untracked*
   plan/design paths. The tracked path (`git diff HEAD -- docs/design-notes
   docs/build-plans` scanned by `_blessing_in_diff`) sees a *flip of an existing
   artifact* but is blind to a plan/note **minted fresh through Bash** directly at a
   blessed status: that file is untracked, so it is absent from `git diff HEAD` and
   never triggers `gate-guard` (PreToolUse Edit/Write/MultiEdit only). This left the
   `proposed → ready` blessing mechanically unenforced against a Bash-minting agent —
   the exact asymmetry A1 fixed for (b) but left open in (c). The detector now unions
   the tracked diff with the untracked set (`git ls-files --others --exclude-standard`
   under the two prefixes), reads each candidate's on-disk `status:`, and treats a new
   file already at `ready` (plan) / `ratified` (note) as a blessing *from nothing*.

2. **finding-0004 (a) ambient-path exclusion (§6, warrant finding-0004).**
   `.claude/settings.local.json` is a per-machine permission cache the Claude Code
   permission system rewrites whenever a new command is approved. Gitignored, it never
   enters the audit's working-tree diff, so its churn stops tripping the (b) scope
   audit. This is already committed (`.gitignore`, 868ed17) and reinforced by a
   machine-global ignore; this plan **confirms** it and **locks** it with a regression.

Then: `finding-0005 → promoted` (A3 warrant), `finding-0004 → resolved`, each citing
this plan and the delta.

## Interfaces pinned inline

**Stop-gate (c) contract, as amended (§6c).** `cmd_stop_audit`, in the (c) block,
runs both:
- the existing tracked scan — `diff = _diff_text_head()` (or `--diff-file <path>`),
  then `_blessing_in_diff(diff)`; unchanged, so a *committed* blessing self-clears
  (not in `git diff HEAD`) and an *uncommitted in-place flip* still blocks; and
- the new untracked scan — `_untracked_blessing()`, which enumerates
  `git ls-files --others --exclude-standard -- docs/design-notes docs/build-plans`,
  filters with `is_design_note` / `is_build_plan`, reads on-disk `status_of`, and
  returns a reason iff a design note is `ratified` or a plan is `ready`.

Both append `(c) …` reasons; the wrapper maps any reason → `BLOCK` → exit 2. The scan
is untracked-only, so it can never fire on a committed blessing (the A1 guarantee).
`--exclude-standard` honors .gitignore, so an ambient ignored path is never scanned.

**Blessing classification (unchanged).** `is_design_note(p)`: under
`docs/design-notes/`, `.md`, not the dir itself. `is_build_plan(p)`: under
`docs/build-plans/`, basename `plan.md`. Legitimate creation status: plan `proposed`,
note `draft` — those are NOT blessings and must pass (the 0005-legit criterion, and
the §14 caveat that the catch must not block `/graduate`).

**finding-0004 mechanism.** No `_lib.py` change is needed for 0004: `git status
--porcelain -uall` (used by `_changed_files`) and `git ls-files --others
--exclude-standard` both omit ignored paths, so gitignoring the file is the whole fix.

## Steps / deliverables

- Edit `.claude/hooks/_lib.py`: add `_untracked_under()` + `_untracked_blessing()`;
  call the latter in the `cmd_stop_audit` (c) block after `_blessing_in_diff` (delta 1).
- Confirm `.gitignore` carries `.claude/settings.local.json` and the file is untracked
  (delta 2; already committed 868ed17 — verify, do not duplicate).
- `docs/build-plans/bp-002/acceptance/run.sh`: wrap the bp-001 harness (prior 18,
  unmodified, by reference) and add 0005-regression, 0005-legit, committed-blessing,
  (c)-uncommitted-plan, and 0004 (before/after).
- Flip `finding-0005 → promoted`, `finding-0004 → resolved`, each with a resolution
  citing A3, this plan, and the regression.

## Acceptance evidence

Each criterion is demonstrated in `journal.md` (newest entry first) and reproduced by
`docs/build-plans/bp-002/acceptance/run.sh`. The new checks run in **isolated
throwaway git repos** (`CLAUDE_PROJECT_DIR` pointed at a temp dir with a copy of the
hooks) so real untracked / committed / uncommitted blessing states are staged without
touching the main repo. The prior harness is invoked by reference (bp-001 wraps
bp-000, snapshot-restoring bp-000/journal.md), so bp-000/** and bp-001/** are left
byte-identical.
