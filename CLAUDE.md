# CLAUDE.md — Agent-Workflow Constitution

Loaded every session; the operational layer. Persona-neutral and deliberately
short — every token here is paid on every turn. Depth lives in skills and loads
only when invoked. Spec: `docs/design-notes/agent-workflow.md`.

**Orientation, not ground truth (owner rule 2026-07-28).** This file and its siblings
(CONVENTIONS, BUILD-SPEC, runbook) are jumping-off points for investigation, not live
state — verify operational claims against the system and the artifact chain at HEAD
before acting. The exception is the bright lines: the §Domain non-negotiables digest and
`CONSTITUTION.md` bind as written, always.

**Domain frame (unchanged, still authoritative).** Your outermost frame is
`CONSTITUTION.md` — the inviolable kernel every agent inherits; task instructions
nest inside it, never override it. The system's full design is `docs/BUILD-SPEC.md`;
engineering and security practice is `CONVENTIONS.md`. Read those before writing
code. This file governs *how work moves*; those govern *what the system is*.

## Domain non-negotiables (never violate; full list `BUILD-SPEC §3`)
Safety-critical bright lines are the one category exempt from this file's thinness
rule (§5, amendment A2): an out-of-context guardrail is not a guardrail, so the
digest stays here — in context, every turn — not behind a pointer.
1. **Sealed core has zero network egress.** Enforce structurally, not by convention.
2. **Network and private data never share a component.** Only `edge/` touches the network; it never reads the vault.
3. **The model advises; code acts.** No model holds a shell, raw secrets, or direct infra mutation.
4. **Executed code is powerless.** Sandboxed: no creds, no network (absent an explicit scoped grant), no vault. Returns data, never actions.
5. **Self-modification is gated → validated → reversible.** Propose → human-approve → execute → validate → auto-rollback; no step skipped.
6. **Every agent inherits `CONSTITUTION.md`** as its outermost frame; task instructions nest inside, never override. Minted agents can't exceed their template's scope or a pre-declared max.
7. **Consequential advice (health/financial/legal) defers, not withheld** — substantive, honest about uncertainty, refuses dangerous specifics; the final decision is the owner's and a professional's.
8. **Respect the memory ceiling** — ≤ 2 resident models, ~20–24 GB usable; the scheduler refuses breaching work.
9. **The fixed points are sacred** — the frozen golden set and `CONSTITUTION.md` are never auto-modified; human-only, deliberate, logged.
10. **Secrets outside code** — Keychain/env only; never committed, read by a model, or logged.
11. **The interface may transit a third party; the corpus never does.** Adapters leak interactions, not the corpus — opt-in only; the private default is local/Tailscale.
12. **Voice/telephony is bounded.** Speech synthesis/recognition run locally in core; only audio crosses the carrier. The adapter dials **only the owner's pre-registered number**; the LLM never supplies a number; calls are owner-initiated; a passphrase/callback authenticates the human before personalized content is spoken.

## The artifact chain
Everything is a typed file with a state machine — no decision lives only in a
transcript. Ideas flow one way, through gates:

`brainstorm (chat) → design note (draft → ratified) → build plan (proposed →
ready → in-progress → complete) → journal + findings → reflection (/triage) → back
into design`.

Findings are the only channel from build back to design, and they re-enter only
through the same gate brainstorms do — never by side effect.

## Roles
- **Orchestrator** — the default posture of a bare session at root. Runs
  `/graduate`, `/build`, `/resume`, `/triage`, `/scribe`; maintains
  `docs/inbox/owner-questions.md`; flips plan status on completion. Work lands by
  PR — the merge log is the build log, and merge is the serialization point
  (owner ruling 2026-07-28; role-state Amendment A1).
- **Builder / Scribe** — a contract layered by `/build` (per the plan's `contract`
  field). The plan's `write_scope` names the intended lane for the reviewer;
  writes are free on the branch and judged at the merge (owner ruling 2026-07-28).

## Rules that bind every session
- **Routing.** Findings typed `design | math | direction` → route to the
  orchestrator (who batches to `owner-questions.md` if the owner is needed).
  Findings typed `codebase | spec-fidelity` → the builder resolves, annotates,
  continues.
- **The record obligation is the PR body.** Every merge carries the files and
  the reason — what, why, verification (the **pr** skill). Journals remain the
  seat's narrative at the agent's judgment, not a per-write mandate. The bar is
  unchanged: the fresh-agent test — a successor re-grounds from merged artifacts
  alone. Resume beats compaction.
- **Never block on the owner.** An owner-level question parks its criterion with a
  re-entry condition and you proceed with the rest. Only a `blocker` finding ends
  a session early — and the Stop gate still demands a fresh journal.
- **The blessing IS the merge (owner ruling 2026-07-28).** The old flip ceremonies
  (`draft→ratified`, `proposed→ready`) are retired — nobody flips a status, agent or
  owner. A PR carries the proposal (a design note, or code spanning one-to-many build
  plans of the same track); agents may audit, the owner audits, reviews, and merges if
  acceptable. Landing on main by the owner's merge IS ratification/readiness. Status
  fields in artifacts are provenance description, never a gate — agents still never
  edit them.
- **Write freedom on the branch; audit at the merge (owner ruling 2026-07-28).**
  Hard write scopes and per-write ceremony are retired — no scope-guard, no
  journal-gate, no action-based rituals. Agents write freely in their worktrees;
  the PR review is where scope is judged (a plan's `write_scope` is reviewer
  guidance — did this merge stay in its design's lane — never an enforced
  capability). One authorship carve-out stands: the fixed points
  (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) are NN-9 sacred — agents
  do not author changes to them absent explicit owner direction; the merge gate
  enforces everything else.

## Commands (depth in the matching skill)
`/capture <topic>` · `/graduate <note>` · `/build <id>` · `/resume <id>` ·
`/triage` · `/scribe`. Skills: **graduate**, **build-plan**, **finding**,
**checkpoint**, **commit**, **pr** (ALL work lands by PR — read it before opening one),
**delegate**, **context-economy**, **book**.
Templates: `docs/templates/`. Sessions are disposable, artifacts are not — end at
unit boundaries (context-economy skill; owner rule 2026-07-11). Successors onboard
by traversal of the artifact chain — the resume-brief mechanism is retired
(owner realization 2026-07-28: briefs transferred posture without warrant).
Run commands via `uv run` (CONVENTIONS §Language) — never `./.venv/bin/...` paths.
The orchestrator may spawn supervised parallel builders in worktrees for `ready`
plans (owner rule 2026-07-11; depth + right-sizing in the **delegate** skill).
Gates unchanged: blessings owner-by-hand, denylist binds every builder.

Local hooks are retired as enforcement (owner ruling 2026-07-28) — the wall is
external. If a stray `HOOK-FAILURE` line ever appears, it is legacy machinery
talking; note it and proceed by the **pr** skill.
