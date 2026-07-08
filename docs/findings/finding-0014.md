---
type: finding
id: finding-0014
status: routed
created: 2026-07-06
updated: 2026-07-08
links:
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/research/security-planes.md
  - ops/import_lint.py
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0014 — Invariant-2 import-firewall is asymmetric and is not enforced by the GitLab CI

> **Triage 2026-07-08 (/triage):** routed → orchestrator. Touches a domain non-negotiable (Invariant 2); the `scan_edge` lint + CI-topology decision is batched to `owner-questions.md` **oq-0006** (may graduate to a small builder task once ruled). Re-entry per §Re-entry condition below.

## What
Invariant 2 (network and private data never share a component; only `edge/` touches
the network, never the vault) is enforced structurally by `ops/import_lint.py`, but
asymmetrically:

- **core → edge/networking is comprehensively linted.** `ops/import_lint.py:96-98`
  (`scan_core`) bars core from importing `edge`/`cloud` and from networking modules
  outside a 2-file allowlist (`:54-57` = `core/sealing.py`,
  `core/models/ollama_client.py`). Enforced as a test
  (`tests/integrity/test_import_firewall.py:24-28`) **and** a dedicated GitHub CI job
  (`.github/workflows/ci.yml:15-25`).
- **edge → core/vault has no blanket static lint.** Only `edge/effectors/**` is
  narrowly barred from importing `core/ops/scheduler`
  (`tests/integrity/test_sensing_firewall.py:111-121`). Nothing stops
  `edge/interface`, `edge/monitor`, or `edge/bridge` from importing `core`;
  `scripts/monitor.py:9` only *documents* (does not lint) that the monitor never
  imports core.
- **The GitLab CI does not run the lint.** `.gitlab-ci.yml:1-26` runs only
  SAST / secret-detection / semantic-release — no `import-firewall` job. If GitLab is
  the authoritative CI host, structural enforcement of this non-negotiable rides
  solely on the pytest integrity gate, not a dedicated lint.

## Why it matters
Invariant 2 is a domain bright line the constitution requires to be enforced
"structurally, not by convention." A one-directional lint plus a CI host that does
not run it weakens that guarantee: an `edge/` component could import `core`/vault and
only a passing pytest run (if that host runs it) would catch it. The core→edge
direction is well covered; the private-data-leak direction (edge reaching into the
vault) is the one with the thinner net.

## Re-entry condition
Owner rules on: (a) adding an `edge → core/vault` blanket lint rule (a `scan_edge`
mirror of `scan_core`), and (b) ensuring the `import-firewall` job runs on whichever
CI host is authoritative (add it to `.gitlab-ci.yml`, or confirm GitHub Actions is
canonical). May graduate to a small builder task once ruled on.

## Routing
`discovery` → orchestrator. Touches a domain non-negotiable (Invariant 2); the fix is
a scoped code/CI change pending an owner decision on CI topology.
