---
type: finding
id: finding-0016
status: routed
created: 2026-07-06
updated: 2026-07-08
links:
  - docs/design-notes/wasm-sandbox-runtime.md
  - docs/design-notes/skills-and-scope.md
  - docs/design-notes/vault-runtime-auth.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0016 — The execution / agency substrate is present and tested but nothing in the live system drives it

> **Triage 2026-07-08 (/triage):** routed → orchestrator. **Parked pending the forward build (Track D correlator / sandbox-driver** — the live path that mints an agent and executes through the broker) — normal roadmap sequencing. Its accuracy facet folds into `owner-questions.md` **oq-0007**. Re-entry per §Re-entry condition below.

## What
Several capability substrates exist and are tested, but have no live driver — the
long-standing "sandbox-driver / factory undriven" dangling frontier
(`docs/PROGRESS.md:265-266,367`):

- **Sandbox.** `core/sandbox/*` (WASM/Podman) executes only via the manual
  `scripts/sandbox.py` CLI (`:53`); `ops/lifecycle/launcher.py build_components`
  constructs no `ExecutionBroker`.
- **Agent factory.** `core/factory/build_factory` / `MintedAgent.mint` are never
  called outside tests; neither `core/runtime.py bootstrap()` nor `build_components`
  construct a factory.
- **Instructional-skill half is a dead field.** `RoleTemplate.skills`
  (`core/factory/roles.py:27`) has zero consumers, and `MintedAgent.build_context`
  (`core/factory/factory.py:56-59`) never loads skill frames — the "composer loads
  relevant skills" seam of `skills-and-scope.md` is unbuilt.
- **WASM execution path untested.** The real wasmtime path
  (`core/sandbox/runner.py:154-210` `_run_wasi`) has no test exercising it (only
  structural/fake-runner tests) and is inert by config (`[sandbox] runtime = "podman"`,
  `wasm_module = ""`, `config/defaults.toml:274,276`).
- **Dead documented entrypoint.** `core/runtime.py bootstrap()` — the documented
  sealed-core entrypoint that "installs the guard then wires services" — has no live
  caller (only `tests/e2e/test_ollama_live.py`); the live seal comes from per-script
  `seal()` calls. (Invariant 1 still holds.)

## Why it matters
Invariant 4 ("executed code is powerless") has a real substrate, but nothing in the
live system executes through it — so the safety machinery is present yet unexercised
end-to-end *in situ*, and a reader could over-credit the system's current agency.
Several notes in this cohort read as if the whole model is pending when in fact the
capability half is built and only the *driver* is missing.

## Re-entry condition
Track D / the sandbox-driver lands a live path that mints an agent and executes
through the broker; add a `needs_wasm` e2e that exercises `_run_wasi` with an
owner-placed `python.wasm`.

## Routing
`direction` → orchestrator. The built-but-undriven frontier; owner sequences the
Track-D correlator / sandbox-driver that would give it a live caller.
