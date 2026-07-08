---
type: finding
id: finding-0019
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/BUILD-SPEC.md
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md
  - docs/design-notes/vault-runtime-auth.md
  - docs/audits/corpus-state-audit-2026-07-verification.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0019 — The research airlock is a fully-built, AWS-deployed subsystem with no design note and no live driver — missed entirely by the prior audit's scope

## What
The **research airlock** (BUILD-SPEC §16) is a substantial built + tested +
AWS-deployed subsystem that the corpus audit never inventoried (its cloud tier was
outside the audit's search scope — finding-0018). It spans four tiers:

- **Core (Zone A):** `core/research/airlock.py` (`ResearchAirlock.emit/collect`,
  `build_airlock`), `core/research/criteria.py` (`deidentify`, `assert_clean`,
  `to_request` — the de-identification firewall), `core/research/rank.py`
  (`rank_literature`); the emitter `core/librarian/librarian.py:186-203`
  (`research_criteria`).
- **Bridge (Zone B):** `edge/bridge/bridge.py` (`ResearchBridge.push_requests/
  pull_results/sync_once`, `build_bridge`), `edge/bridge/protocol.py`.
- **Cloud (Zone C):** `cloud/fetcher/{handler,sources,aggregate}.py` — a real Lambda
  aggregating OpenAlex / Europe PMC / arXiv, evidence-ranked, de-dup'd.
- **IaC:** `cloud/terraform/{bootstrap,airlock,backups}` — S3, Lambda, least-privilege
  IAM, `vault_engine.tf` (Vault AWS dynamic secrets engine), `backups/kms.tf`.

TESTED: `tests/integration/{test_research_airlock,test_bridge,test_fetcher,
test_research_criteria}.py`, `tests/adversarial/test_pii_scrubber.py`.

**WIRED: no.** `build_bridge` requires `[airlock] s3_bucket`, which is empty in
`config/defaults.toml` and unset in this machine's `config/local.toml` → it raises.
`librarian.research_criteria()` exists but **nothing on the live path calls
`emit`/`collect`/`rank_literature`** (the `ambassador_task` handler does RAG answers,
not airlock emits); the `"research"` router-kind (`scheduler/router.py:31`) has no
handler and no enqueuer. `docs/PROGRESS.md:267` concedes "the research airlock has no
live driver"; CHANGELOG "Phase 8 Complete" means built/deployed, not wired.

**Related — IaC-ahead-of-code:** `ops/vault/policies/correlator.hcl` (+ `dreamer.hcl`)
provision a Vault `correlator` role reading `oura-daily-aggregates` for a
correlator/biometric pipeline that **has no implementation** (the observed-iot
correlator is Track-D forward work). The deployment provisions access for code that
does not exist yet.

## Why it matters
A major deployed subsystem with (a) no design record in `docs/design-notes/`, (b) live
AWS infra (S3/Lambda/IAM applied), and (c) no code driving it end-to-end is exactly
what an audit must surface — the prior pass omitted it entirely. The IaC-ahead-of-code
provisioning grants Vault/cloud access for pipelines that cannot yet use it, a latent
surface worth a conscious owner decision.

## Re-entry condition
Owner rules on: (a) give the airlock a design note, or an explicit BUILD-SPEC §16
cross-reference in the corpus index, so it is not invisible to future audits; (b) wire
the live driver (`research_criteria → emit → bridge → collect → rank_literature`) or
explicitly defer it with a re-entry marker; (c) whether the correlator/biometric Vault
provisioning should precede its implementation.

## Routing
`discovery` (direction) → orchestrator. A design-record + wiring gap on a deployed
subsystem; owner sequences the driver/deferral.
