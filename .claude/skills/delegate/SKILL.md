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

Before spawning **any** delegated worker, gate the spawn against the remaining budget. The gate
prevents the failure this repo has logged repeatedly: a worker that dies at the usage limit
mid-run, burning the tokens it already spent for nothing.

- **Probe it yourself — the gate is SELF-SERVE** (verified 2026-07-19; corrected here by bp-125,
  which found the stale claim below still in this file). `claude -p "/usage"` as a one-shot
  renders the figures, so the agent does **not** need the owner in the loop to read a budget.
  Owner-relay (`/usage` or `/cost` read off their screen) is the **fail-closed fallback** for when
  the probe itself fails — not the primary path.
  ⚑ The superseded claim, recorded so it is not re-derived: this file previously said the pool
  "has **no query API** — the owner reads it … the agent cannot run slash commands." The second
  half is true of an *interactive* slash command and false of the one-shot form, and the
  difference had already been established in practice while this file still said otherwise.
- **Re-probe before EVERY spawn, not once per session.** A figure read before the previous
  worker ran is not a budget; a wave that spawns three builders probes three times.
- **Get `available`** (exact, or an estimate with headroom).
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
- ⚑ **A blessing removes the WAIT, not the ORDERING.** Several plans reaching `ready` together is
  permission for each to *start*, never permission to fan them out: `depends_on` still binds, and
  plans sharing a `write_scope` glob are still mutually exclusive whatever their status says. A
  blessed wave whose members all hold one glob is **strictly serial**, and its own
  `parallelizable_with: []` says so. Read the two fields, not the green lights.
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

- ⚑ **A bare `pytest -q` has TWO expected failures — report the count exactly, never round it.**
  The finding-0103 core-self-containment ratchet and `tests/e2e/test_dream_v2_live.py`
  (finding-0226) both fail by design on a full local run. **Both carry `pytest.mark.live` and are
  therefore absent from CI and the deploy gate**, which run
  `-m "not live and not podman and not needs_vault and not needs_restic"` — which is why the local
  full run and the pipeline disagree, and why the disagreement is not a regression. A *third*,
  `tests/e2e/test_scheduler_live.py`, is a known flake (finding-0219). **Anything beyond these is a
  regression.** Two seals reported "1 failed" and were wrong; a miscounted gate is a false green,
  so state the numbers as observed rather than as remembered.

- ⚑ **Never pipe a gate leg to `tail` — `pytest -q | tail` returns TAIL's exit code**, so a red
  suite reports success, and the pipe buffers everything until the run completes so you watch
  nothing for the whole run. **Redirect to a file** (`> /tmp/…/pytest.txt 2>&1`) and read it after.
  This cost two 18-minute runs. The same trap applies to any leg whose exit code you intend to
  believe.
- A builder that stalls or drifts is stopped and its worktree inspected — resume beats
  restart (journal), restart beats rescue (worktrees are cheap).
- Findings remain the only channel from build back to design: a delegated builder files
  them exactly as a session builder would (finding skill routing rules).
- **Record the economics**: the completion notification's measured usage (tokens, tool
  calls, duration, model) goes into the plan's seal entry — the per-plan cost ledger
  (context-economy skill).

## A sub-orchestrator that owns a wave owns its merges (owner ruling, 2026-07-26)

An orchestrator may delegate a whole *wave* — not just its builders — to a **sub-orchestrator**,
which then owns the wave end to end. Owner ruling, verbatim: *"sub-orchestrator will handle the
merge and stand up its own auditor to review before merging, **it manages the merge, not you**."*

- **What transfers:** spawning the wave's builders, standing up **its own auditor** for the
  pre-merge review, and performing the merges to main, in the wave's dependency order.
- **What the root seat does instead:** nothing to that wave. The instinct of a fresh orchestrator
  is to audit and merge whatever it finds `ready`-and-built; against a delegated wave that instinct
  is **wrong**, and acting on it races the owner of the wave for the merge — the one operation this
  repo already serializes on purpose ("never two simultaneous merges to main," above).
- **If the sub-orchestrator dies mid-wave, do NOT silently take over.** Inspect the worktrees, say
  plainly what state the wave is in, and **ask the owner** whether to re-spawn it or drive the rest
  directly. A half-merged wave is the bad outcome; a takeover that guesses at which halves landed
  makes it worse. Resume beats restart here as everywhere, but the *decision* is the owner's
  because the failure is mid-flight and its blast radius is main.
- **Write it down, in the artifact, not in the session.** This rule reached the point of being
  obeyed from an agent's working memory alone, recorded in no artifact anywhere — which is exactly
  the failure mode the rules-live-in-skills discipline exists to end (a rule loads at the moment of
  use or it does not hold). It is recorded here by `bp-125`; whether the delegation *contract*
  wants a formal amendment beyond this is an open owner-level question.

## What never loosens

`proposed → ready` and `draft → ratified` stay owner-by-hand. The foundation denylist
binds every builder. `deploy` stays owner-fired. The Stop-gate/scope-guard hooks apply
to delegated tool calls as to session ones. Speed changes the throughput, not the
constitution.
