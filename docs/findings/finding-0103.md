---
type: finding
id: finding-0103
status: open
created: 2026-07-17
updated: 2026-07-17
links:
  - CONVENTIONS.md                                 # where the self-containment + DRY rules will be stated
  - docs/findings/finding-0101.md                  # the graph-instruments instance (resolved by bp-065)
  - docs/findings/finding-0102.md                  # shadow.py eval-LOGIC — SUBSUMED by this wider audit
  - core/dreaming/shadow.py                         # the worst offender (eval.drift/golden + ops.levers)
re_entry: RULED (owner 2026-07-17) config IS in-scope — strict, no wiggle room; enforcement test red at 106; cleanup = DI program + 16 inversions
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# core is not self-contained: 106 imports from sibling packages (full audit)

## What
Owner principle (2026-07-17): **`core/` is the processing unit; it must import nothing from the
project outside `core/`, period — everything else (eval, ops, agents, edge, scheduler, config) is
machinery to test, study, calibrate, run, and enforce around it.** A full AST scan of `core/**`
finds the invariant violated **106 times across 49 files**:

- **`config` — 90 imports** (`from config.loader import get_config, Config`, and
  `config.secrets_backend`): pervasive — nearly every `core/stores/*` `open_*` helper and most
  modules reach for global config at call time.
- **`ops` — 8**: `shadow.py→ops.levers`, `effect_proposal.py→ops.{effect_catalog,effect_gate,
  effects}`, `sensing.py→ops.effects`, `factory.py→ops.gate`, `ops_view.py→ops.ledger`,
  `reference_view.py→ops.lifecycle.runs`.
- **`eval` — 7**: `shadow.py→eval.{drift,golden,harness,harness.store}`, `ops_view.py→eval.drift`,
  `spine.py→eval.harness.store` (finding-0102's set — now subsumed here).
- **`agents` — 1**: `interface.py→agents.ambassador`.

The 16 non-config imports are core reaching **UP** into machinery that should depend on core, not
the reverse — the true inversion (drift/golden logic, effector catalog/gate, levers, the ambassador,
the runs ledger, the readings store). The 90 config imports are a different shape: core reaching for
declarative settings, a dependency-injection question rather than a logic inversion.

## Why it matters
The graph-instruments fix (bp-065/finding-0101) closed one family; this audit shows it was the tip.
Two open questions the owner must rule on before enforcement scope is fixed:
1. **Is `config.loader` in-scope?** By the owner's taxonomy config is "run" machinery (strict ⇒ in;
   90 violations ⇒ dependency-inject config/paths into core, a large refactor). Or config is
   declarative settings, not behavioral machinery (⇒ the one sanctioned inward import; 16 violations
   remain — the genuine "reach for machinery" set).
2. The 16 non-config reaches each need inversion (core returns data; the machinery calls core) or
   relocation — a program of work, not one edit.

## Progress (2026-07-18)
- **Enforcement: DONE** (bp-066) — the red test at 106 + the CONVENTIONS DRY/self-containment rules +
  the manifest-audit skill step.
- **Config leg: DONE** (bp-067) — the loader moved to `core.config`; ratchet **106 → 19**. The config
  remediation was a **SPLIT** (loader into core, tomls stay in `config/`, outside becomes a facade),
  NOT the DI first sketched. `get_secret` split at the trust boundary (core env-only; token in the
  facade). Note bp-067 fixed 87 (not 90) config imports — factory's token `get_secret` + 2
  `secrets_backend` imports are network-entangled and DEFERRED to the secrets inversion (see below).
- **Remaining red = 19:** (a) the **3 factory secrets/Vault reaches** (`config.secrets_backend` ×2 +
  the token `get_secret`) — a SECURITY-focused inversion (inject/relocate the network Vault wiring out
  of core; `ops/effect_exec.py` shares the pattern), **bp-068 candidate**; (b) the **16 machinery
  reaches** (shadow/effect_proposal/sensing/factory→gate/interface/ops_view/reference_view/spine) —
  each its own inversion plan. Zero ⇒ suite fully green.

## Re-entry condition
**RULED (owner, 2026-07-17): config IS in-scope — strict, no wiggle room.** The forbidden set is
EVERY first-party sibling of core (`config`, `eval`, `ops`, `agents`, `edge`, `scheduler`, …). The
enforcement test lands **red at 106 by design** (owner directive: a loud failure now, never a silent
allowlist — the red suite is the forcing function). bp-066 delivers the enforcement (the red test +
the CONVENTIONS rules + the manifest-audit skill step). Cleanup is a SEPARATE program, the red test ratcheting
toward zero:
- **config (90) — SPLIT, not DI** (owner ruling 2026-07-17): split `config/` into a **core-scoped
  config that lives INSIDE `core/`** (`core.config` — core owns its own settings/paths) and an
  **outside-scoped config** for the machinery. Core imports `core.config` (self-contained ✓); the
  outside config may import `core.config` for anything shared (the `eval/ops → core` direction is
  ALLOWED), plus its own outside-only settings. A ~45-file import repoint + a definitions move — its
  own plan (bp-067 candidate). Cleaner than threading paths through every `open_*` constructor.
- **the 16 machinery reaches — INVERT**: each of eval/ops/agents reaches (shadow→eval/ops,
  effect_proposal→ops, factory→ops.gate, interface→agents.ambassador, spine→eval.store, …) becomes
  "the machinery calls core," not the reverse — its own plan(s).
finding-0102 folds into this one.

## Routing
`design` discovery → orchestrator → owner (the config ruling + the cleanup program). Surfaced by the
orchestrator's full self-containment audit, session-26, at the owner's direction to enforce the
principle immediately.
