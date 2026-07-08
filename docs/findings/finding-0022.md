---
type: finding
id: finding-0022
status: promoted
ftype: discovery
origin_plan: null            # owner-approved outcome of the archive-recommendation pass
route: orchestrator
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/audits/archive-recommendation.md                    # the evidence (signal table, per-pair rationale)
  - docs/audits/corpus-state-audit-2026-07-verification.md   # code-reality corroboration
  - docs/findings/finding-0021.md                            # sibling meta-finding (the episode; ground-truth set)
resolution: promoted — both supersessions applied by owner hand-edit at the blessing gate, 2026-07-06
---

# finding-0022 — Two design-note supersessions, per audit evidence

## What

The archive-recommendation pass (2026-07-06), grounded in both corpus audits and
creation chronology, identified two design notes as superseded-in-place. The owner
reviewed the evidence and approved both. This finding is the warrant those two
supersession records cite.

1. **`dn-ambassador-interpretation-and-flow` → superseded by
   `dn-ambassador-as-reasoning-agent`.** All three signals: older (06-28 vs 06-29),
   subject overlap, and the successor is the authoritative note for what is built.
   Partial — the note's own banner records the scope (§1–§4 remain valid; the
   "thin dispatcher" framing is corrected by the successor).

2. **`dn-secrets-management-evolution` → superseded by `dn-vault-runtime-auth`.**
   Two signals (chronology unavailable — same commit batch): subject overlap with
   the successor's own declaration ("correct but incomplete"), and the audit shows
   the successor's design is the one actually built (`cloud/terraform/vault_engine.tf`,
   dynamic secrets engine). Partial — residual value retained (§1 tipping-point
   analysis, §5 taxonomy, §6 what-not-to-do).

## Disposition

Both applied by owner hand-edit (front-matter `status: superseded`,
`superseded_by`, `warrant: finding-0022`) — the certification act at the blessing
gate. Full evidence lives in `archive-recommendation.md`; this finding is the
accountable record the supersessions ground on. These two edges are the positive
cases of the ground-truth set in finding-0021 / `supersession-recovery-evaluation.md`.
