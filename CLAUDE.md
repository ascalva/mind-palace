# CLAUDE.md — Mind-Palace Operating Rules

This file is loaded every session. It is the operational layer. The full design lives in `docs/BUILD-SPEC.md`; the inviolable directives every agent inherits live in `CONSTITUTION.md`; engineering and security practice lives in `CONVENTIONS.md`. Read all three before writing code.

## What this project is
A single-user, offline-first, privacy-sealed personal AI — a "mind palace" that indexes the owner's private notes and reflects patterns back, plus a gated agent layer, a dynamic agent factory, a pluggable messaging interface, and a one-way research airlock. Built to be **extended over time**, not shipped as a fixed product. Owner is a security-focused DevOps/AWS engineer with strong Python — write to that level.

## Non-negotiables (full list in BUILD-SPEC §3; never violate)
1. **Sealed core has zero network egress.** Enforce structurally, not by convention.
2. **Network and private data never share a component.** Only `edge/` (bridge + interface gateway) touches the network; neither reads the vault.
3. **The model advises; code acts.** No model holds a shell, raw secrets, or direct infra mutation.
4. **Executed code is powerless.** Runs sandboxed: no creds, no network (unless explicit scoped grant), no vault. Returns data, never actions.
5. **Self-modification is gated → validated → reversible.** Propose → human-approve → execute → validate → auto-rollback. No step skipped.
6. **Every agent inherits `CONSTITUTION.md`** as its outermost frame. Task instructions nest inside, never override. Minted agents can't exceed their template's scope or a pre-declared max.
7. **Consequential advice (health/financial/legal) defers but isn't withheld** — substantive + honest about uncertainty + refuses dangerous specifics + final decision to owner & a professional.
8. **Respect the memory ceiling** (§5): ≤2 resident models, ~20–24 GB usable. Scheduler refuses breaching work.
9. **The fixed points are sacred** — the frozen golden set and `CONSTITUTION.md` are never auto-modified. Human-only, deliberate, logged.
10. **Secrets outside code** — Keychain/env only; never commit, read-by-model, or log.
11. **The interface may transit a third party; the corpus never does.** WhatsApp-style adapters leak interactions, not the corpus — opt-in only; private default is local/Tailscale.
12. **Voice/telephony is bounded.** Speech synth/recognition run locally in core; only audio crosses the carrier. The adapter dials **only the owner's pre-registered number**; the LLM never supplies a number; calls are owner-initiated; a passphrase/callback authenticates the human before personalized content is spoken.

## How to work
- **Build phase by phase** (BUILD-SPEC §18). Verify each phase against its gate, then **stop and checkpoint with the human** before advancing. Do not jump ahead.
- **Ask, don't guess** on the decisions in BUILD-SPEC §20. For everything else, pick a sensible default and state it inline.
- **Write tests as you build**, not after. Small, verifiable steps.
- If a feature can't be built without violating §3 or the Constitution, **stop and surface it**.

## Build-session budget (you, the building agent)
This is a large system — build it without exhausting your own context. (Distinct from the runtime context budgeter in BUILD-SPEC §13, which manages the *local* models at run time.)
- **One phase per session.** Build a single phase, verify, hand off; the human starts a fresh session (or `/clear`) for the next. Don't carry the whole history.
- **Resume from `docs/PROGRESS.md`, not from chat history.** At each checkpoint append a terse entry there (built / verified / next / decisions). A fresh session re-grounds from that file + this one + the current phase's spec section.
- **Update the Current phase marker** below as phases complete.
- **Reference, don't echo.** Don't paste large file contents back; cite paths and work incrementally.

## Conventions (full detail in CONVENTIONS.md)
- **Python** for orchestration/agents. Thin custom code over heavy frameworks — **no LangGraph/CrewAI/AutoGen**; own the loop.
- **Stores:** LanceDB (vectors), DuckDB (telemetry), SQLite (queue/state/gate). Scoped access per agent — enforce in an access layer.
- **Model serving:** Ollama (HTTP). Keep it abstract so a future GPU node can join.
- **AWS = Terraform only.** No click-ops. Least-privilege IAM.
- **Sandbox:** rootless Podman (network-off, no-mount, limited) + warm pool; WASM for pure compute.
- **Comment the *why* at trust boundaries** (airlock asymmetry, propose/execute split, scope ceiling).

## Repo map
```
core/    Zone A — sealed, no network (librarian, curator, dreaming, ingest, matching, factory, sandbox, stores)
edge/    Zone B — networked, containerized (bridge, interface)
cloud/   Zone C — Terraform + fetcher
agents/  persistent role definitions      scheduler/  supervisor + queue + context budgeter
ops/     gate, levers, rollback           eval/  golden sets, metrics, baselines
docs/    BUILD-SPEC.md, PROGRESS.md (build log)
```
Keep `core/` free of any import that can reach the network.

## Current phase
> Phase: 7 COMPLETE (2026-06-26) — verified against gate (152 logic passed; 6 live + 6 live-synthesis/podman skipped). Curator + dreaming on the **INTERPRETED** layer, trough-only. `core/stores/derived.py` `DerivedStore` (SQLite) writes `interpreted` provenance ONLY (no `provenance` param — §8 firewall, structural); idempotent content-ids + `reset()` = regenerable. `VectorStore.all_rows(provenances=…)` for clustering. `core/dreaming/` deterministic NumPy clustering (note centroids → cosine single-linkage) + `Dreamer` (clusters the AUTHORED mirror, **mirror-not-oracle**, injectable synthesizer, grounding self-check → INTERPRETED dreams). `core/curator/` `Curator` **flags, never rewrites authored** (§8): near-dup candidates + orphan-prune candidates (deterministic) + contradiction (injectable judge seam, **deferred** without a detector). `scheduler/cron.py` wires `dream`/`curate` → synthesis tier; the Phase-3 foreground gate (`HEAVY_TIERS`) makes trough-only structural. `[dreaming]` config + `numpy` dep. ⚠️ Live synthesis (`qwen3.6:27b`) NOT pulled → `test_dreaming_live` skips. ⚠️ Phase 4 empirical `-m podman` still pending — podman machine won't boot here; see `docs/runbook.md` → "Sandbox runtime". **Hardening pass (2026-06-26, NOT a phase — main build NOT advanced, dream R&D flag OFF):** worked the invariant catalog (`docs/WHITEPAPER-FORMAL-PROPERTIES.md`) — promoted I6 structural (`core/mirror.py` `MirrorView`), I2 static (`ops/import_lint.py` + CI), I9 decidable (digest `Source`), I10 acyclic (`derived_from` + cycle-refused insert, `core/recursion.py`); FSM-checked I8 (loader) + I12 (gate, honest G_now); G6 aging (`scheduler/queue.py`); G7 bounds declared; G8 preorder retired; Hypothesis property tests. **183 logic pass (+31)**; runtime behavior unchanged. Gaps: CLOSED G1/G2/G3/G6, OPEN G4 + new G9/G10/G11 — see `docs/PROGRESS.md`. Next: Phase 8 (the airlock, AWS Zone C) — needs §20.7 (AWS acct/region/TF state) + §20.9 (Lambda vs Fargate) from owner. Phase 6b voice optional (§20.11). Update this line as phases complete.
```

