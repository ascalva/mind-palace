---
name: commit
description: How and when to commit in this repo — the CONVENTIONS §Commits header format, one-logical-change discipline, the uv-run test gate, main-branch ingestion awareness, and the blessing fences an agent commit must never cross.
---

# commit — when and how

## When to commit

- **At a semantic boundary**: one logical change, complete, verified. The same trigger
  family as the journal checkpoint (§9) — if the moment deserves a checkpoint entry, the
  work probably deserves a commit; the two usually travel together.
- **The gate before any commit**: `uv run pytest -q -m 'not live and not podman'` (the
  fast ratchet) green, plus `uv run ruff check .` on touched code. If the change touches
  a model tier or the sandbox, the matching live axis (`-m live` / `-m podman`) is part
  of verifying it — see runbook §Verifying a change.
- **Never commit**: a broken intermediate state; unrelated changes mixed into one commit;
  writes to the foundation denylist; or any blessing flip — `status: ratified` on a note,
  `proposed → ready` on a plan — those are owner-only by hand (§10); `gate-guard` denies
  them pre-hoc and the Stop-gate audits the diff post-hoc. If a commit would carry one,
  stop and route a finding instead.
- **Branch awareness**: `main` is the ingestion branch (CONVENTIONS §Commits). The
  post-commit hook runs the code sensor on `main` only; builder worktrees commit on their
  branch and the ledger ingests the work at merge. Write merge/squash messages to the
  header rule — that message becomes the ledger row.

## How to write it

- **Header**: `type(scope): subject`. Types: `feat fix docs test refactor perf ops chore`.
  Scope = the tree area or artifact id the change lives in (`core`, `ops`, `hooks`,
  `bp-005`, `triage`). Subject: imperative, ≤ 72 chars, no trailing period, states the
  *change* ("add X"), never the activity ("worked on X").
- **One logical change per commit** — if the subject needs "and" twice, split the commit.
- **Body**: the *why*, plus what the diff can't say — the constraint honored, the
  invariant touched, the alternative rejected. Agent-authored commits carry the
  `Co-Authored-By` trailer the harness supplies.
- **The machine consumers are real**: semantic-release versions from `type`; the
  code-sensor ledger (`data/code_snapshots.sqlite`) parses the header into
  `ctype`/`scope`/`subject` lookup columns beside the commit's structural snapshot.
  A malformed header degrades lookup, not just style. Merge commits are exempt.
- **Never push** unless the owner asks; never amend or rebase published history.
- **After a main commit**, the hook prints `code-sensor sync: ingested=1 …`. If it
  didn't, the sensor missed — `uv run scripts/snapshot_code.py` heals idempotently.
