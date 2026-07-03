# Documentation index

Canonical map of every doc in the repo: what it is, whether it's current, and how it
cross-references. For the reading protocol (what to actually read for a given task), start at
[`ORIENTATION.md`](ORIENTATION.md) instead — this file is the index, not the entry point.

## Authority order

When docs conflict, higher wins:

**`CONSTITUTION.md` > `BUILD-SPEC.md` > `CONVENTIONS.md` > `design-notes/` > `research/`**

`PROGRESS.md` is state-of-the-world (a build log), never a spec — it records what happened, not
what should happen. `schema.md` and `runbook.md` are code-adjacent operational references, not
design authorities.

## Status legend

| Status | Meaning |
|---|---|
| current | live and accurate |
| realized | the parked design was built; note kept as rationale, not a build target |
| parked | not built; re-entry conditions stated in the note itself |
| draft | research-in-progress, not ratified |
| point-in-time | an audit/snapshot honestly dated, not meant to stay current |
| mostly-consumed | a builder prompt whose steps are mostly done; remaining steps still live |
| historical | superseded or complete; kept in `archive/` for the record |

---

## Root

| Doc | Category | Status |
|---|---|---|
| [`CLAUDE.md`](../CLAUDE.md) | authoritative-spec | current — operating rules, loaded every session |
| [`CONSTITUTION.md`](../CONSTITUTION.md) | authoritative-spec | current — **read-only fixed point, never edited** |
| [`CONVENTIONS.md`](../CONVENTIONS.md) | authoritative-spec | current — engineering & security practice |
| [`README.md`](../README.md) | index | current — public-facing overview |

## Core spec, state, and reference

| Doc | Category | Status |
|---|---|---|
| [`ORIENTATION.md`](ORIENTATION.md) | index / builder-facing | current — top-of-session card; the map and reading protocol |
| [`BUILD-SPEC.md`](BUILD-SPEC.md) | authoritative-spec | current — the full master specification |
| [`PROGRESS.md`](PROGRESS.md) | live-state | current — append-only build log, resume source. Phases 0–10 rotated to `archive/PROGRESS-phases-0-10.md`; this file now starts at the Forward layer |
| [`schema.md`](schema.md) | authoritative-spec | current — live data schema |
| [`runbook.md`](runbook.md) | authoritative-spec | current — operational procedures |
| [`ROADMAP-V1.md`](ROADMAP-V1.md) | live-state / builder-facing | current — forward-layer track sequencing and dependencies |
| [`MIND-PALACE-V1.md`](MIND-PALACE-V1.md) | authoritative-spec | current — v1.0 technical map (issued at the 10-phase completion) |

## The whitepaper / mathematics companion series

A deliberate numbered set — companions I–IV plus a shared glossary. Keep-separate: each is a
distinct layer (prose, formal models, invariant catalog, unified reframing), not redundant
copies. `NOTATION.md` is load-bearing — cited by ~15 code file headers as the symbol↔code join.

| Doc | Companion | Category | Status |
|---|---|---|---|
| [`WHITEPAPER.md`](WHITEPAPER.md) | I — prose | authoritative-spec | current, living document |
| [`WHITEPAPER-TECHNICAL.md`](WHITEPAPER-TECHNICAL.md) | formal models & figures | authoritative-spec | current |
| [`WHITEPAPER-FORMAL-PROPERTIES.md`](WHITEPAPER-FORMAL-PROPERTIES.md) | II — invariant catalog | authoritative-spec | current |
| [`REASONING-COMPLEX-MATHEMATICS.md`](REASONING-COMPLEX-MATHEMATICS.md) | III v0.2 — Dreamer math | authoritative-spec | current — supersedes `archive/WHITEPAPER-DREAMER-MATHEMATICS.md` (0.1) |
| [`REASONING-COMPLEX-BUILD.md`](REASONING-COMPLEX-BUILD.md) | III build spec | builder-facing | current — Track H (H1–H9) mostly built against this |
| [`MATHEMATICAL-REFRAMING.md`](MATHEMATICAL-REFRAMING.md) | IV — the five families | authoritative-spec | current — unified account, most of it since integrated |
| [`NOTATION.md`](NOTATION.md) | glossary | authoritative-spec | current — **load-bearing**, referenced from code headers |
| [`supplemental/math-spine-field-guide.md`](supplemental/math-spine-field-guide.md) | reference | draft-research | current — per-construct falsifiability guide, ties to Track L |

## Builder prompts & wiring

| Doc | Category | Status |
|---|---|---|
| [`BUILDER-PROMPT-FORWARD.md`](BUILDER-PROMPT-FORWARD.md) | builder-facing | current — **the canonical forward-layer prompt**, `CLAUDE.md` points here |
| [`BUILDER-PROMPTS-INTEGRATION.md`](BUILDER-PROMPTS-INTEGRATION.md) | builder-facing | mostly-consumed — R0–G3 executed; G4–G6 prompts still live |
| [`INTEGRATION-AND-WIRING.md`](INTEGRATION-AND-WIRING.md) | builder-facing | mostly-consumed — companion to the above; same live G4–G6 tail |
| [`WIRING-AUDIT.md`](WIRING-AUDIT.md) | historical / audit | point-in-time (2026-06-29) — a dated WIRED/DANGLING/FLAG-OFF snapshot; some DANGLING items closed since. Don't treat as current state, don't archive — an audit is inherently dated |

## Design notes (`design-notes/`)

Parked or realized designs, each written with re-entry conditions. "Realized" = built; the note
stays as rationale, not a live build target.

| Doc | Status |
|---|---|
| [`attestation-layer.md`](design-notes/attestation-layer.md) | realized — security & attestation track |
| [`secrets-management-evolution.md`](design-notes/secrets-management-evolution.md) | realized — Vault |
| [`vault-runtime-auth.md`](design-notes/vault-runtime-auth.md) | realized — Vault |
| [`vault-sync-and-capture.md`](design-notes/vault-sync-and-capture.md) | realized — sync |
| [`wasm-sandbox-runtime.md`](design-notes/wasm-sandbox-runtime.md) | realized — WASM sandbox |
| [`test-organization.md`](design-notes/test-organization.md) | realized — test reorg |
| [`dreamer-quality-suite-evaluation.md`](design-notes/dreamer-quality-suite-evaluation.md) | realized — F9 |
| [`ambassador-as-reasoning-agent.md`](design-notes/ambassador-as-reasoning-agent.md) | realized — Track B |
| [`ambassador-interpretation-and-flow.md`](design-notes/ambassador-interpretation-and-flow.md) | realized — Track B |
| [`dreaming-v2-interpreter-panel.md`](design-notes/dreaming-v2-interpreter-panel.md) | realized — R0/R1 |
| [`hands-and-the-effector-layer.md`](design-notes/hands-and-the-effector-layer.md) | parked / in-progress — Track G; G1–G3 built (types, gate, read-only sensing), G4–G6 not yet |
| [`skills-and-scope.md`](design-notes/skills-and-scope.md) | parked — referenced from `core/factory/__init__.py` |
| [`dream-phase-rnd-charter.md`](design-notes/dream-phase-rnd-charter.md) | parked — flag OFF, referenced from `config/defaults.toml` |
| [`recursive-strata.md`](design-notes/recursive-strata.md) | parked — cross-linked with `research/security-planes.md` and `stability-adjudication.md`; blocking on a foundation file-set verification pass |
| [`stability-adjudication.md`](design-notes/stability-adjudication.md) | parked — cross-linked with `research/security-planes.md` and `recursive-strata.md` |
| [`live-adoption-and-longitudinal-harness.md`](design-notes/live-adoption-and-longitudinal-harness.md) | parked — Track L, forward-looking from the Track-H core |
| [`observed-data-and-the-assistant-tier.md`](design-notes/observed-data-and-the-assistant-tier.md) | parked — Track D |
| [`observed-iot-and-cross-source-synthesis.md`](design-notes/observed-iot-and-cross-source-synthesis.md) | parked — Track D |
| [`dreaming-on-curated-graphs.md`](design-notes/dreaming-on-curated-graphs.md) | parked — R5 |
| [`recursive-dreaming-bounded-by-grounding.md`](design-notes/recursive-dreaming-bounded-by-grounding.md) | parked |
| [`alignment-subsystem.md`](design-notes/alignment-subsystem.md) | parked — Phase-10 expansion |
| [`nervous-system-and-ambassador.md`](design-notes/nervous-system-and-ambassador.md) | parked |
| [`roadmap-and-future-directions.md`](design-notes/roadmap-and-future-directions.md) | parked — post-Phase-10 areas of interest |
| [`holistic-testing.md`](design-notes/holistic-testing.md) | parked — Track F |

## Research (`research/`) & audits (`audits/`)

| Doc | Category | Status |
|---|---|---|
| [`research/security-planes.md`](research/security-planes.md) | draft-research | draft, pending ratification (2026-07-03) — cross-linked with `recursive-strata.md`, `stability-adjudication.md`, `audits/prompt-integrity-audit.md` |
| [`research/un-represent-ability.md`](research/un-represent-ability.md) | draft-research | draft — external-survey style |
| [`audits/prompt-integrity-audit.md`](audits/prompt-integrity-audit.md) | historical / audit | current (2026-07-02) — cross-linked with `research/security-planes.md` |

## Planned but not yet written

Referenced from `ROADMAP-V1.md`, `MIND-PALACE-V1.md`, and `BUILDER-PROMPT-FORWARD.md` as forward
pointers for Track F (F1–F8); intentional, not dangling:
- `simulation-harness-and-reasoning-probes.md`
- `literary-interpretation-probes.md`

## Archive (`archive/`)

Superseded or historically-complete; moved here, never deleted.

| Doc | Superseded by / reason |
|---|---|
| [`HANDOFF.md`](archive/HANDOFF.md) | the security & attestation track it scoped is complete (`PROGRESS.md`, 2026-06-27) |
| [`PROGRESS-phases-0-10.md`](archive/PROGRESS-phases-0-10.md) | rotated out of the live `PROGRESS.md` (2026-07-03 docs cleanup) — the numbered-phase build log, verbatim |
| [`CLAUDE-current-phase-2026-07-03.md`](archive/CLAUDE-current-phase-2026-07-03.md) | verbatim snapshot of `CLAUDE.md`'s "Current phase" marker before it was trimmed to a 3-line pointer (2026-07-03 docs cleanup) |
| [`WHITEPAPER-DREAMER-MATHEMATICS.md`](archive/WHITEPAPER-DREAMER-MATHEMATICS.md) | superseded by `REASONING-COMPLEX-MATHEMATICS.md` (companion III v0.2) |
| [`math_proposals/gem_chats.md`](archive/math_proposals/gem_chats.md), [`math_proposals/gpt_chats.md`](archive/math_proposals/gpt_chats.md) | raw source-chat logs behind the mathematics companions |
