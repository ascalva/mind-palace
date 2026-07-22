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

## Right-sizing the AUDIT (risk-proportional, design-note D2)

The audit that stands behind a track's deskcheck is sized to *who built it and at
what tier*, not to line count — and it is **recorded** so the board's
"audit: present/owed" flag (fed by the track/deskcheck `audit_refs`) has a basis:

- **Delegated build, or a build at a lower tier than the reviewer** ⇒ an
  **independent audit pass at the reviewer's tier** (typically Opus): a fresh read
  of the diff against the plan's falsifiers, filed as a finding (or an explicit
  "audit clean" note the deskcheck cites). The builder's own green gate is not the
  audit.
- **Supervised same-tier merge** (the orchestrator drove or watched the work live)
  ⇒ the **merge scrutiny IS the audit** — the pre-merge diff review (scope,
  acceptance actually run, falsifiers considered) is the audit of record. Record it
  as such (name it in the seal / the deskcheck `audit_refs`); do not double-pay a
  redundant second pass.

Either way the audit is a *named artifact*, not a vibe: the deskcheck (the third
owner-only gate) evaluates the track against its DoD **and** its audit, so an
un-recorded audit reads as "audit: owed" on the board.

## Delegating UP to fable — precision + tier-verification (field-tested 2026-07-13)

The mirror of sizing down: some work genuinely needs the top tier — open math/formalism, a
taxonomy or cross-plane design ruling, a falsifier only judgment can evaluate. Fable is **scarce**
(a hard token budget), so spend it only where reasoning *depth* changes the answer, and squeeze
every token:

- **Scope surgically.** One precise question (or an ordered priority set), with EXACTLY the
  context it needs pinned inline — name the files, the prior state, the exact deliverable. Do the
  cheap scouting yourself (grep, read, frame the options) so fable spends only on the reasoning,
  never on rediscovery. A wandering fable agent burns the scarcest tokens.
- **Verify the tier was actually delivered** — a silent downgrade wastes the budget on non-fable
  work wearing the fable label. **The agent's own self-declaration is NOT a valid check**
  (field-proven 2026-07-13: two spawns both printed "claude-fable-5 — fable tier, confirmed" on
  line 1 while the Claude Code UI showed **opus** — the agent echoes the model named in its
  injected system prompt, it does not introspect the model actually executing it). Trust only the
  two OBJECTIVE signals:
  1. **The live UI model indicator** (the harness's actual routing) — check it in the first
     moments of the run, before the worker gets deep. If it shows a lower tier than requested,
     STOP the worker immediately (`TaskStop`); a downgraded worker burns budget on non-fable work.
     The owner sees this indicator; ask them to read it for a background spawn.
  2. **The completion notification's `<usage>`** (the harness's own accounting): the actual model
     + token count. Implausibly low tokens for the depth, or a mismatched model, is the tell.
  Keep the honesty mandate in the prompt anyway (flag interruption/resume/degradation, stop clean
  if low) — it is a useful *secondary* signal, but it is defeated by a silent downgrade, so it
  NEVER substitutes for the UI/usage check.
  - **Fable availability is a WEEKLY time-throttle, not a spendable balance** (learned 2026-07-13):
    once the weekly Fable cap is hit it resets on a fixed date (does not lift by buying extra-usage
    credits — those fund opus/sonnet instead), and until then every `model: fable` spawn silently
    falls back to the session model. When fable is capped, do the non-fable-dependent work now
    (e.g. web literature checks, grounding) and PARK the reasoning-depth items for the reset — do
    NOT run a fable-grade design/invariant vet at opus, which is usually the same tier that drafted
    the artifact (no added depth).
- **Make the agent self-bound + trust-calibrated:** it returns the deliverable and STOPS on
  completion (not burn budget), and labels every claim (`[GROUNDED]` cite path:line / `[DERIVED]`
  / `[INFERENCE]` / `[ANALOGY]`) so you can trust-weight without re-deriving.
- **Preserve the output.** Fable output is the most expensive artifact in the system; the
  orchestrator (single-writer) captures it faithfully into the durable artifact (brainstorm /
  finding / design note), not just the transcript. A fable pass that lives only in chat is
  paid-for reasoning thrown away.

Complements context-economy's tier rubric (which decides *which* tier); this is how to reach the
scarce top tier without waste.

## Pre-flight budget gate (owner rule, 2026-07-13)

Before spawning **any** delegated worker, gate the spawn against the remaining budget. The
fable/subscription token pool is scarce and has **no query API** — the owner reads it (`/usage`
or `/cost`; the agent cannot run slash commands) and relays the number. The gate prevents the
failure this repo has logged repeatedly: a worker that dies at the usage limit mid-run, burning
the tokens it already spent for nothing.

- **Get `available`** from the owner (exact, or an estimate with headroom).
- **Pad the estimate by the measured overrun margin — estimates run OVER.** This wave's builders
  came in at ~1.5–1.6× their graduation estimate (bp-020 1.50×, bp-026 1.56×). Gate on
  `estimate × ~1.6`, not the raw estimate — or quote a pre-padded estimate and compare directly.
  Refine the margin from the ledger's estimate/actual pairs as it grows.
- **Spawn only if `padded_estimate ≲ available`.** Otherwise: downsize the tier, split the task
  into budget-sized units, or defer — never start a worker that can't finish.
- **Close the loop:** the worker self-reports actual usage on completion (the honesty mandate
  above); record it in the seal; the estimate/actual ratio sharpens the next margin. Managing a
  scarce budget becomes a checklist instead of vigilance.

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
  file). Builder AND orchestrator each run, before declaring green / merging — run each
  leg SEPARATELY and read its result, do NOT `&&`-chain them:

      uv run ruff check .
      uv run mypy core agents eval ops scheduler scripts
      uv run mypy                 # ARGLESS — exits 1 at the tests/-baseline (69);
                                   # this is why the legs must not be &&-chained (leg 3
                                   # would short-circuit legs 4-5).
      uv run python -m ops.type_gate
      uv run pytest -q

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
