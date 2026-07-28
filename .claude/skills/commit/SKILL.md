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
- ⚑ **ALWAYS pass the message via `git commit -F -` with a QUOTED heredoc (`<<'EOF'`). Never
  `-m "…"`.** In zsh, backticks inside double quotes are command-substituted, so a message
  citing `` `code refs` `` — which this repo's style demands constantly — is silently
  mutilated *before git sees it*: the backticked words are deleted and replaced with the
  (empty) output of running them as commands. You get `command not found: …` on stderr,
  amid normal hook output, and a commit whose body has holes. A quoted heredoc delimiter
  makes the body literal; that is the whole fix.
  This happened **twice in session-53**, the second time hours after the lesson was written
  into a journal — which is why the rule lives here, in the file that loads when you commit,
  rather than in a journal nobody re-reads. It is also finding-0222's thesis in miniature:
  a convention you wrote down is not enforcement.
  Damage is **not** repairable by amending: the code-sensor ingests the body at commit time,
  so `code_snapshots.sqlite` keeps the mutilated text either way. Record a correction instead
  (precedent: `docs/build-plans/bp-095/journal.md`, `cffe515`).
- ⚑⚑ **`git add -A` and `git add .` are BANNED. Stage every path by name.** Owner rule,
  2026-07-26, after `cffe515` absorbed two of his blessings into a commit about something
  else. Unconditional on purpose: the earlier version of this rule said "whenever the owner
  might be editing in parallel", and a rule you must first decide whether to apply is the
  kind that failed twice in one session (finding-0222).
  **Before staging, run `git status --short`. A file you did not touch appearing there means
  STOP** — it is probably an owner hand-edit, and if it is a blessing it needs its own
  `bless(...)` commit after you verify the diff is the status line alone.
  Why naming paths is sufficient: you cannot absorb a file you never named, so the hazard is
  closed by construction rather than by vigilance. It also preserves grouping — a fix and the
  test that proves it stay in ONE bisectable commit, which strict one-file-per-commit would
  break (the fix would land without its test, or the test would land red), and which merge
  commits cannot honour at all.
  ⚑ Note `git merge` does **not** accept `-F -`: write the message to the scratchpad and pass
  `git merge -F <file>`.
- **Body**: the *why*, plus what the diff can't say — the constraint honored, the
  invariant touched, the alternative rejected.
- **Co-Authored-By trailer** (owner preference, 2026-07-11): include it ONLY on commits
  that are substantially agent-authored CODE (feat/fix/refactor touching source). Omit it
  on routine orchestration commits — triage sweeps, seals, captures, inbox deliveries,
  journal updates. Attribution where it informs; silence where it's ceremony.
  (The attestation chain and the run ledger carry machine provenance regardless.)
- **The machine consumers are real**: semantic-release versions from `type`; the
  code-sensor ledger (`data/code_snapshots.sqlite`) parses the header into
  `ctype`/`scope`/`subject` lookup columns beside the commit's structural snapshot.
  A malformed header degrades lookup, not just style. Merge commits are exempt.
- **Push to origin is routine** (owner standing rule, 2026-07-11: the remote mirrors the
  current state; `mind-palace deploy` is the one gate that needs the owner in the loop).
  Never amend or rebase published history; never run `deploy` yourself — the owner fires it.
- **Push at boundaries, not per commit** — CI minutes are free-tier shared runners. Each
  code push runs the `ratchet` job (ruff + import-firewall + model-free pytest, uv-cached);
  docs-only pushes skip it via `rules:changes`. Batch related commits, then push once.
  After a code push, verify the pipeline if `glab` is available
  (`glab ci status --repo ascalva-projects/mind-palace`); live/podman/vault axes never run
  in CI — they are local verification (runbook §Verifying a change).
- **After a main commit**, the hook prints `code-sensor sync: ingested=1 …`. If it
  didn't, the sensor missed — `uv run scripts/snapshot_code.py` heals idempotently.
