# Mind Palace

[![CI](https://github.com/ascalva/Mind-Palace/actions/workflows/ci.yml/badge.svg)](https://github.com/ascalva/Mind-Palace/actions/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-1000%2B-brightgreen)](docs/runbook.md)
[![coverage](https://img.shields.io/badge/coverage-88%25-green)](pyproject.toml)
[![mypy](https://img.shields.io/badge/mypy-0_errors-brightgreen)](pyproject.toml)
[![type coverage](https://img.shields.io/badge/type_coverage-gate--enforced-brightgreen)](ops/type_gate.py)
[![sealed core](https://img.shields.io/badge/sealed_core-zero_egress-6f42c1)](scripts/check_imports.py)
[![python](https://img.shields.io/badge/python-3.13%2B-blue)](pyproject.toml)
[![license](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)

> A knowledge system built around a single question: what does it mean for a system to know _why_ it believes something?

It's deliberately limited in scope — it trades breadth of action for provability — with a formal structure that lets it reason about how its own knowledge holds together. Runs locally, core sealed. Built with the thing it's trying to understand.

Two names, deliberately: **mind-palace** is the framework — this repository. **Ouroboros** is the live instance — the always-on daemon dreaming over one person's corpus, named by its own founding note ("is that the name i would give this study on process? ouroboros"). The framework is public; the corpus never is.

## Why it exists

Before it is a tool, this is a **living thought experiment** — one person seeing how far physics and mathematical intuition can be pushed into running code without losing rigor on the way. The method is the project: an intuition (conductance between two thoughts; a helix of revisitation; proper time inside a corpus; memory as a graph at a past cut) is admitted only if it can be **bounded by mathematics** — an ultrametric, a circuit law, a gain graph, a certified snapshot — **made representable and constructable** in typed code, and **validated by the system itself**: every design decision ships with a named falsifier, every instrument carries the observable that would prove it wrong, and the numeric checks run before the prose is committed. The guardrails are not bureaucracy around the creativity; they are the kiln. A metaphor that survives formalization becomes an instrument; one that doesn't is recorded, with the reason it failed, in the same ledger.

Utility is a side effect and is treated as one. What the project optimizes for is the loop itself: conversation → capture → design note → build plan → code → findings → back into design — with the system increasingly able to observe that loop running through it.

## What it is

Mind Palace takes private notes and writing and represents them as a typed, layered graph rather than a pile of documents. On top of that graph sits an operator — one mathematical object in several guises — that turns the relationships between pieces of knowledge into things the system can compute over, test, and revise, instead of leaving them implicit.

The point isn't to produce answers. It's to produce answers that carry their reasons: where a belief came from, what it's allowed to affect, and whether it still holds.

## Design principles

A few ideas do most of the load-bearing work:

- **Make the wrong state unrepresentable, not merely discouraged.** Provenance labels, capability ceilings, and the de-identification airlock are the same pattern — typed constraints on flow, enforced by making the illegal flow impossible to express rather than by asking components to behave. Where a runtime guarantee can be promoted to a static one, it is: the import firewall proves the sealed core can't *name* the network; the type plane makes accidental promotion of derived content a compile-time error.
- **Read and write are separated by construction.** A read-only view into memory and a write-only view into the world are distinct objects; nothing that reflects can also act, by type.
- **Every consequential act is attested.** Ingests, dreams, verdicts, CI results, credential rotations, deployments — each lands in an append-only, hash-chained, signed record. "The system did X" is a queryable claim, not a memory.
- **Formalize only what earns it.** A type exists to delete an illegal state; a formalism must constrain, not decorate. Otherwise a docstring. Otherwise nothing.
- **The core is preserved; everything else is expendable.** The system is designed around what has to survive, not around what happens to be running.

## Architecture at a glance

- **Ambassador** — the reasoning layer you interact with. Computationally light, reaches for deterministic tools when exactness matters, and is plain about how much effort a given answer took.
- **Dreamer** — the offline layer that works over the structure of what's stored. Deterministic clustering feeds model synthesis; outputs are content-addressed proposals that can never silently become beliefs.
- **Store, and its typed views** — memory, a read-only reflection of it (`MirrorView`: authored words only, enforced at construction), and a write-only path to external effect. The asymmetry is deliberate and enforced.
- **Provenance and scope** — every item carries its origin class and what it may affect; the self-model reads only what the owner actually wrote. Code itself enters as a *sensed stream* — the repo is an instrument, never a voice in the mirror.
- **Airlock and the curated stratum** — a one-way path for outside research: de-identified on the way out, unable to reach back in. What returns is ranked against the private corpus locally; a clearly open-access source can be embedded into a *separate* curated store — a second bedrock of ground truth _about the world_, held structurally apart from the mirror of what the owner wrote, and never merged into it.

## Status — stated honestly

The base build (Phases 0–10) is complete; the live instance runs always-on under launchd with a graceful, gated deployment path. "Complete" is not "wired": this repo distinguishes **built** (code + tests exist), **deployed** (present in the running system), and **wired** (active in the live loop) — and its own audit found the summaries were the least honest surface, so this one names the gaps.

Wired and live today: ingestion (notes within seconds, code per commit), dreaming on a six-hour cadence with content-addressed idempotency, the provenance firewall, the attestation chain, strict-typed core (mypy zero, enforced), CI on every push, deploy-gated releases, and the research airlock driven live — a de-identified query goes out, a reading list ranked against the private corpus comes back. Built but deliberately dormant, awaiting their design gates: retrieval demotion for superseded content, the supersession certification layer, the curated stratum's full-text embedding (built and licence-gated, waiting on a deployed fetcher before any source is ingested), effectors (the "hands" — flag-off at every tier), recursive dreaming (parked on an adoption criterion it hasn't earned yet).

The current frontier is the temporal-connectivity layer: over a substrate of certified cuts, per-stratum clocks, and a cross-clock atlas (built), a ratified instrument family is entering build — σ\*, the abstraction ultrametric with its realizing chain; (σ,t) conductance profiles whose reconnection events are attributed, never guessed; type-checked bridges where an argument is a path whose capability scopes still compose; and a helix detector resting on a proved theorem that revisitation across time cannot close flat. Behind it, drafted: the palace's memory of itself — the graph as it stood at any past cut, and the conversations that design the system becoming a stratum it can study. The entanglement between the corpus and the code that implements it deepens by design.

An honest note on scope: the engineering rigor here governs _how_ outputs are produced — their provenance, their limits, whether they still hold. Whether the outputs are actually insightful is a separate question the reasoning layer has to earn against real use, not against provability alone. That gap is named on purpose.

## How it's built

By a human and AI agents in a gated loop, in the open. The human owns direction and every blessing; agents propose, implement, and verify — and structurally *cannot* perform the acts reserved for the owner. The workflow is itself a typed artifact chain: brainstorm → design note (ratified only by hand) → build plan (blessed only by hand) → build → findings, which re-enter design through the same gate. Enforcement is hooks, not etiquette: write-scopes are capabilities, blessing transitions are denied to agents pre-hoc and audited post-hoc against committed history, and the guards carry regression harnesses proven to fail against the code that preceded them.

Builds run as supervised parallel agents in isolated worktrees; merges are scrutinized diffs, never trust. Code reaches the live system through exactly one gate — `deploy`: clean tree, tests green locally, pipeline green remotely *and attested*, graceful cycle, successor verified, release cut. The build's own history is a first-class dataset: every commit's structure (symbols, signatures, imports, typed headers) is snapshotted into a queryable ledger by a model-less sensor agent — the system tracks its own construction.

The recursion is the point. It's a system for reasoning carefully about AI, built with AI, whose corpus opens with its owner thinking about what it means to build it. It has already bent back on itself: a literature pass grounding the system's own math notes caught a misattribution in a ratified design — a kernel result credited to Mercer that is properly Moore–Aronszajn — and the correction became the curated layer's first resident. The next turn is drafted: the design conversations themselves — the place where intuition gets its formal helping hand — becoming a sensed stratum, so the distance between an idea's first utterance and its formalization is something the system can one day measure.

## Rigor, verifiable

Claims above are checkable, not vibes:

```sh
uv sync --extra dev
uv run pytest -q -m 'not live and not podman'   # the deterministic tier: 1000+ tests
uv run pytest -m 'not live and not podman and not needs_vault and not needs_restic' --cov  # line+branch coverage: 88%
uv run mypy                                      # core/ strict: 0 errors, enforced
uv run python scripts/check_imports.py           # the sealed core names no network module
bash docs/build-plans/bp-010/acceptance/run.sh   # the write-guard harness, 11 cases
sqlite3 data/attestations.sqlite 'select agent_role, action, count(*) from attestations group by 1,2'
```

Structural invariants carry structural tests — e.g. the balance mathematics is proven bit-identical under injection of dispositional edges, and the blessing gates' harnesses include the laundering, comment-evasion, and deletion paths. The suite is tiered by intent — unit, integration, property, metamorphic, adversarial, integrity, longitudinal, and emergent — so an invariant regression reads differently from a flaky assertion. Live axes (`-m live`, `-m podman`, a dev-Vault CI service) verify against the real substrates, honestly skipped when absent. Line+branch coverage over the deterministic tier is **88%** (reported, not gated — code reachable only through the live/podman/vault axes reads as uncovered here, by design); the stance is that a structural test deleting an illegal state matters more than a line touched, so coverage informs rather than commands, and the type-gate separately enforces that every core-reaching package is type-checked at all.

## Running it

Local by design. Your hardware, a local model server, notes in a plain markdown vault, the core backed up encrypted. Nothing about it depends on a service staying up. `docs/runbook.md` is the operational manual — from `uv sync` to the always-on launchd lifecycle.

## Repository

- `CLAUDE.md` — operating rules loaded every agent session. Start here.
- `CONSTITUTION.md` — the fixed directives every agent inherits.
- `CONVENTIONS.md` — engineering and security practice, including the commit and deploy rules.
- `docs/BUILD-SPEC.md` — the full master specification.
- `docs/design-notes/` — the ratified design record (status-guarded: drafts are working material, ratified notes are immutable to agents).
- `docs/PROGRESS.md` — the build log, maintained across sessions.
- `docs/runbook.md` — how to run, verify, and operate it.

## License

AGPL-3.0. You're free to use, study, and build on it; derivatives — including anything run as a hosted service — stay open under the same terms. Lineage preserved.
