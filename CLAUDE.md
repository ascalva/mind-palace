# CLAUDE.md — Agent-Workflow Constitution

Loaded every session; the operational layer. Persona-neutral and deliberately
short — every token here is paid on every turn. Depth lives in skills and loads
only when invoked. Spec: `docs/design-notes/agent-workflow.md`.

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
  `docs/inbox/owner-questions.md` and `docs/PROGRESS.md`; flips plan status on
  completion. Single-writer of those files.
- **Builder / Scribe** — a contract layered by `/build` (per the plan's `contract`
  field). Writable surfaces are exactly three: the plan's `write_scope`, its own
  `journal.md`, and new files in `docs/findings/`. Everything else is denied.

## Rules that bind every session
- **Routing.** Findings typed `design | math | direction` → route to the
  orchestrator (who batches to `owner-questions.md` if the owner is needed).
  Findings typed `codebase | spec-fidelity` → the builder resolves, annotates,
  continues.
- **Note-taking obligation.** Checkpoint the journal at every semantic boundary
  (criterion closed, commit made, finding filed) — §9, the **checkpoint** skill.
  The bar is the fresh-agent test: a new session with only plan + journal +
  write-scope files must continue without re-asking. Resume beats compaction.
- **Never block on the owner.** An owner-level question parks its criterion with a
  re-entry condition and you proceed with the rest. Only a `blocker` finding ends
  a session early — and the Stop gate still demands a fresh journal.
- **Two blessing gates are owner-only, by hand.** `draft→ratified` (a design note)
  and `proposed→ready` (a plan split) are never done in a session. `gate-guard`
  denies them pre-hoc and the Stop-gate audit blocks any Bash-mediated flip.
- **Write discipline is a capability, not a suggestion.** `scope-guard` enforces
  the active plan's `write_scope` pre-hoc; the `journal-gate` diff audit catches
  Bash writes post-hoc. A foundation denylist (`CONSTITUTION.md`,
  `docs/design-notes/**`, `eval/golden/**`) is never writable, orchestrator
  included. A denial means narrow the scope or file a finding — never route around.

## Commands (depth in the matching skill)
`/capture <topic>` · `/graduate <note>` · `/build <id>` · `/resume <id>` ·
`/triage` · `/scribe`. Skills: **graduate**, **build-plan**, **finding**,
**checkpoint**, **commit**, **book**. Templates: `docs/templates/`.
Run commands via `uv run` (CONVENTIONS §Language) — never `./.venv/bin/...` paths.

If a hook prints `HOOK-FAILURE …`, enforcement did not apply: rerun the named
script standalone (`bash .claude/hooks/<name>.sh --standalone …`), reconcile, then
proceed.
