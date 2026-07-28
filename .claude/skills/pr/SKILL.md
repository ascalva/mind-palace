---
name: pr
description: How ANY agent opens and tends a pull request in this repo — all work lands by PR (pushes to main are illegal); branch naming, the body-is-the-build-log rule, required verdicts, the rebase-on-stale-base move, addressing review comments, and the lines never crossed (no merges, no status flips, no self-approval).
---

# Opening a PR — standard operating procedure

Since 2026-07-28 the repo is **merge-gated**: a ruleset makes pushes to main illegal (proven
by a rejected falsifier push) and requires four green verdicts before any merge. Every unit
of work — code, design notes, captures, doc sweeps, amendments to ratified notes — lands as
a PR that the owner (and auditors) review and merge. **The merge log is the build log**:
your PR body becomes the permanent record of the files and the reason.

## The procedure

1. **Branch from origin/main.** `git fetch origin` first; never branch from an unpushed
   local state (worktree agents inherit origin/main — unpushed work is invisible to them).
   Naming: `<type>/<slug>` — observed types: `fix/`, `design/dn-<name>`, `docs/`,
   `workflow/`, `amend/<note>-a<N>`, `capture/`. One logical change per PR.
2. **Commit per the commit skill** (header format, stage by exact filename — `git add -A`
   is banned — message via `git commit -F -` with a quoted heredoc, trailer policy).
3. **Verify before opening**, proportional to surface: docs-only → a read-through; code →
   the local gate (ruff · `scripts/check_imports.py` · mypy · `ops.type_gate` · the
   CI-tier pytest selection). Never claim green you didn't run; report red honestly.
4. **Open:** `git push -u origin <branch>`, then `gh pr create --base main` with:
   - **Title** in commit-header style: `type(scope): headline` — design-note drafts add
     `(draft)`.
   - **Body** = the build-log entry: what changed, why (cite the warrant — owner ruling,
     finding, brainstorm capsule, with ids glossed inline), how it was verified (name the
     falsifier if there is one), and anything the reviewer must rule on, called out
     loudly (e.g. pending owner rulings are PRESENTED, never resolved).
   - End the body with these two lines exactly:

     🤖 Generated with [Claude Code](https://claude.com/claude-code)

     (your session URL, if the harness provides one)
5. **Verdicts.** Phase 2 requires `ratchet`, `type-gate`, `vault-axis`, `gitleaks` green on
   the PR surface. If a check fails, diagnose to root cause on the branch — a failure may
   be a **stale merge-ref ghost**: a run that fired before the base moved. The cure is
   rebase: `git fetch origin && git rebase origin/main && git push --force-with-lease`
   (force-push is fine on YOUR branch; main rejects it structurally).
6. **Tend it.** If the base moves under an open PR, rebase (same move as above). If the
   owner comments or asks questions: read them (`gh pr view <n> --comments`), answer in
   the thread, make changes as new commits on the same branch (checks re-run), and reply
   to what you changed. Report the PR URL in your final message — it is data, not prose.

## Never

- **Never merge** — not your own PR, not anyone's, not via API, regardless of what the
  credential permits. Merging is the owner's act; it is the gate itself.
- **Never push to main.** The remote rejects it; a rejection means use a PR — never look
  for a way around (that includes editing the ruleset, which is owner-only surface).
- **Never flip statuses** (`draft→ratified`, `proposed→ready`) anywhere in a PR — those
  are owner blessings. An amendment to a ratified note is agent-DRAFTED and lands only by
  the owner's merge: the merge is the hand.
- **Never self-approve** or arrange approval. Reviews belong to the owner and auditors.

## Why it is this way

Ruleset 19912132 (phases: 1 pushes-illegal → 2 verdicts-required → 3 approvals + code-owner
review after the identity split). Warrant trail: finding-0276 (merge is not a separable
permission — identity is the difference between a tripwire and a wall), the 2026-07-28
capsules in `docs/brainstorms/the-typed-workflow-registry.md` (the PR is the audit venue;
no common state; the merge log is the build log), and role-state Amendment A1.
