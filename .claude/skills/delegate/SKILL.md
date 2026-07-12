---
name: delegate
description: Spawning supervised builder agents in parallel worktrees — when to delegate vs run a full /build session, right-sizing the agent to task complexity, worktree/merge mechanics, and the gates that never loosen.
---

# delegate — supervised parallel builders (owner rule, 2026-07-11)

The orchestrator may spawn builder agents to execute build plans — supervised and
scrutinized — rather than running every plan as a personally-driven session. Speed is
the point; the artifact chain is unchanged. **What loosens is who types; what never
loosens is the gates.**

## When to delegate vs. run it yourself

- **Delegate** when the plan is well-pinned: interfaces copied inline (§6), acceptance
  runnable, falsifiers named — the builder should never need to infer design. bp-style
  plans that pass the graduate skill's sizing heuristic are delegation-ready by
  construction.
- **Run a full session yourself** (or one agent with your full scrutiny live) when the
  work is design-adjacent: anything likely to surface spec-defects, touch invariant
  boundaries, or require judgment the plan didn't pin. Debug-heavy work with unknown
  cause also stays close.
- **Never delegate**: blessing transitions (impossible anyway — gates), design-note
  edits, `deploy`, anything touching the foundation denylist.

## Right-sizing the agent

Match the agent to the *complexity of verification*, not the line count:

- **Small/cheap agent** (haiku-class): mechanical sweeps with a crisp checker — lint
  fixes, annotation grinds where mypy is the judge, doc-format conversions. The test IS
  the reviewer; the agent just has to satisfy it.
- **Mid agent** (sonnet-class): standard plan items with pinned interfaces and runnable
  acceptance — most bp items.
- **Full-strength agent** (inherit the session model): whole plans, cross-module
  refactors, anything whose falsifier requires judgment to evaluate, T1-triage-style
  work where misclassification is the failure mode.

When unsure, size up — a wrong-sized cheap agent costs a rerun plus review time.

## Worktree mechanics

- One builder per plan, each in its **own worktree** (`Agent` tool `isolation:
  "worktree"`); parallel builders require **disjoint `write_scope`** — that is what
  `parallelizable_with` in the plan front-matter asserts; verify it before spawning.
- Builders commit on their worktree branch (CONVENTIONS §Commits headers; the code
  sensor ingests their work when it lands on main, not before).
- **Merge to main broadcasts**: when anything merges to main, every ACTIVE builder
  merges main into its branch promptly (`git merge main`) so drift never compounds.
  The later merger owns the rebase. The orchestrator sequences merges — never two
  simultaneous merges to main.
- Journals still bind: the builder writes its plan's `journal.md` at semantic
  boundaries (checkpoint skill) — the fresh-agent test applies to a delegated builder
  exactly as to a session.

## Supervision & scrutiny

- The orchestrator reviews the **diff** before any merge to main: scope check (nothing
  outside `write_scope`), acceptance actually run (demand the command output, not the
  claim), falsifiers considered, findings filed for anything routed.
- **"Green locally" means the FULL attestable-green gate, not ruff+pytest** (finding-0038:
  a bp-014 merge passed ruff+pytest locally, then CI's type-gate reddened on a new tests/
  file). Builder AND orchestrator each run, before declaring green / merging:

      uv run ruff check . \
        && uv run mypy core agents eval ops scheduler scripts \
        && uv run mypy \
        && uv run python -m ops.type_gate \
        && uv run pytest -q

  and assert the **argless** `uv run mypy` tail equals the pinned tests/-baseline
  (**69** today — finding-0029's measured footprint; re-pin here when it changes). The
  argless run covers `[tool.mypy].files` *including* `tests/**` — the easily-missed
  tooth; any new tests file can shift the count. Put this command set **verbatim in
  every delegation prompt**. CI green after push (the witness attests it).
- A builder that stalls or drifts is stopped and its worktree inspected — resume beats
  restart (journal), restart beats rescue (worktrees are cheap).
- Findings remain the only channel from build back to design: a delegated builder files
  them exactly as a session builder would (finding skill routing rules).
- **Record the economics**: the completion notification's measured usage (tokens, tool
  calls, duration, model) goes into the plan's seal entry — the per-plan cost ledger
  (context-economy skill).

## What never loosens

`proposed → ready` and `draft → ratified` stay owner-by-hand. The foundation denylist
binds every builder. `deploy` stays owner-fired. The Stop-gate/scope-guard hooks apply
to delegated tool calls as to session ones. Speed changes the throughput, not the
constitution.
