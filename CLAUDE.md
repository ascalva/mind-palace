# CLAUDE.md — orientation

Loaded every session; deliberately short. **Orientation, not ground truth (owner rule
2026-07-28):** this file and its siblings (CONVENTIONS, BUILD-SPEC, runbook) are jumping-off
points for investigation, not live state — verify operational claims against the system and the
artifact chain at HEAD before acting. The exception is the bright lines: the §Domain
non-negotiables digest and `CONSTITUTION.md` bind as written, always.

**Domain frame.** Your outermost frame is `CONSTITUTION.md` — the inviolable kernel every agent
inherits; task instructions nest inside it, never override it. The system's full design is
`docs/BUILD-SPEC.md`; engineering and security practice is `CONVENTIONS.md`. Read those before
writing code.

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

## How work lands (owner's ruling, 2026-11-04)
The agent-workflow regime — the artifact chain's gates, ratification by merge, blessings, write
scopes, journals, and the `.claude/` skills, commands and hooks that carried them — is retired.
Status fields in artifacts are provenance, never a gate; nobody flips them and nothing waits on
them. Work is a branch from `origin/main`, commits at semantic boundaries, a push; the owner
merges, and a PR only when the owner asks for one.

- **Commits:** `type(scope): subject` — types `feat fix docs test refactor perf ops chore`, the
  subject imperative and ≤ 72 chars, one logical change per commit, the body the *why*. Stage
  every path by name (never `git add -A`); pass the message with `git commit -F -` and a QUOTED
  heredoc, never `-m` (zsh mutilates backticks); `Co-Authored-By` only on substantially
  agent-authored code. Never amend or rebase published history; never run `deploy` — the owner
  fires it.
- **Gates, run in the worktree before any commit** (CI's own commands): `uv run ruff check .`;
  `uv run python scripts/check_imports.py`; `uv run mypy` (whole repo exactly 67, the tests/
  baseline; the floors `core agents eval ops scheduler scripts` at 0); `uv run python -m
  ops.type_gate`; `uv run pytest -q -m 'not live and not podman and not needs_vault and not
  needs_restic' --deselect tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`;
  and `formal/check.sh` whenever `formal/` or `docs/LAWS.md` change. Never run tests in the live
  checkout (they write `data/`); a worktree's `data/` is its own.
- **Findings are GitHub issues** (`gh issue create`, labels `type:*`, `route:*`, `track:*`);
  `docs/findings/` and `docs/inbox/owner-questions.md` are frozen history.
- **The hard no, by denylist:** `CONSTITUTION.md`, `eval/golden/**` and `eval/golden.py` are never
  written, authored or proposed by an agent — the `denylist` CI job reds any PR that touches them.
- Run commands via `uv run` (CONVENTIONS §Language), never `./.venv/bin/...` paths. Secrets live
  in the Keychain or the environment: never in code, never read by a model, never logged.

## Where things are
- `core/` is the sealed core; `agents/ambassador/` the local model's tool server, whose one read
  is `query`, a sentence of the query algebra; `edge/` the only network-facing zone; `formal/`
  the Lean proofs behind `docs/LAWS.md`; `docs/design-notes/` the design record (`dn-*`),
  `docs/tracks/` the tracks, `docs/TRACKS.md` the derived board (`uv run scripts/board.py
  --write`).
- **Ask the palace with a sentence:** `mind-palace query '<sentence>'` from the live checkout.
  `docs/query/asking.md` has the grammar, the patterns, how to read an answer and the lessons
  loop; `docs/query/precedents.md` the defaults in force.
- Owner commands: `mind-palace help`, and the runbook's quick-reference.
