---
type: finding
id: finding-0190
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/import_lint.py
  - core/factory/factory.py
  - core/sealing.py
  - ops/network/ouroboros-egress.pf.conf
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# `hvac` is reachable from core in two hops the direct-only import lint cannot see

## What
`ops/import_lint.py::scan_core` performs one AST walk per file and tests only the
top-level root of each DIRECT import. There is no graph traversal. The computed
first-party transitive closure from `core/**` (173 modules, 20 non-core reachable)
contains an off-host HTTP client:

```
core/factory/factory.py:182 -> config.secrets_backend -> hvac.Client(url=self.addr)
```

`hvac` is explicitly listed in `ops/import_lint.py::NETWORK_MODULES` with the comment
"Vault HTTP client ... config/scheduler only, never core". Core reaches it in two hops the
lint cannot see, and the acceptance test never will.

What actually stands between a `[secrets]`-enabled core process and off-host egress:
(1) `hvac` is an uninstalled optional extra — a packaging accident, not a boundary;
(2) `core/sealing.py::seal()`'s socket monkeypatch, whose own docstring admits a native
extension bypasses it; (3) the `pf` anchor, which is INERT — committed but owner-loaded,
`scripts/verify_planes.py:171` reports PENDING.

## Why it matters
This is the concrete live instance of Chapter 2's abstract (*) conditional, and neither
the chapter nor `SYNC.md`'s open block names it. Naming the live instance is what turns a
conditional proposition into an actionable one. `core/factory/factory.py:178-182` already
documents the intent ("it belongs OUT of core (Invariant 1) ... left RED on purpose"), so
this is known-and-deferred rather than unnoticed — but the guard is configuration
accident, not structure, which non-negotiable #1 forbids ("enforce structurally, not by
convention").
