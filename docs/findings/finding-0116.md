---
type: finding
id: finding-0116
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/design-notes/exhaust-lane.md              # the writer is workflow-plane (orchestrator + scripts/, ascalva)
  - docs/design-notes/ouroboros-principal.md       # §3.4: exhaust is ouroboros-WRITE-ONLY
  - docs/build-plans/bp-076/plan.md                # the migration that would enforce the conflict
  - docs/brainstorms/exhaust-and-ingest-sync.md
re_entry: null
ftype: spec-defect
origin_plan: bp-076
route: owner
resolution: null
---

# The exhaust WRITE-owner contradicts the report writer's plane — two ratified notes disagree on who writes `exhaust/reports/`

## What
Surfaced by the owner (2026-07-20): "as a workflow agent, will I have write scope to
`exhaust/reports/`?" Two RATIFIED notes give incompatible answers:

- **`dn-exhaust-lane`**: build reports are **composed by the orchestrator** (a workflow-plane
  act, single-writer judgment) and **placed by `scripts/exhaust_report.py`** (repo-workflow
  tooling). Both run as **`ascalva`** — the development/workflow plane.
- **`dn-ouroboros-principal` §3.4**: `~/.mind-palace/exhaust` is `ouroboros`-owned, mode `0755`,
  **writes = `ouroboros` only**; others read.

After the ouroboros migration (bp-076), `ascalva` — the orchestrator AND the writer script —
**cannot write `exhaust/reports/`**. The delivery path breaks at exactly the migration meant to
harden the system.

## Root cause — exhaust has TWO producer planes, and §3.4 assumed one
The `dn-ouroboros-principal` "exhaust = system-emitted, ouroboros-writes" model implicitly
assumed the *system* (ouroboros: dreams, digests) is the only producer. But **build reports are a
workflow-plane artifact** — they describe delegated *development*, composed by the orchestrator
(`ascalva`), not emitted by the reasoning core. So exhaust actually has two writers:
- **workflow plane (`ascalva`)** — build reports (`exhaust/reports/`);
- **system plane (`ouroboros`)** — future self-emissions (dream digests, weekly summaries).

A uniform `ouroboros`-write rule cannot hold. This is the same plane-mapping the owner drew in
§3.3 ("the uid separates planes") — applied to *producers* of exhaust, it forces a split.

## Why it matters
- **A bp-076 (migration) blocker, NOT a bp-075 blocker.** bp-075 works TODAY: pre-migration,
  exhaust is `ascalva`-owned, the writer writes fine. The conflict bites only when bp-076's
  migration flips exhaust to `ouroboros`-write-only. So bp-076 MUST carry the resolution before
  its runbook chowns exhaust — else the owner migrates and silently loses report delivery.
- It touches a **ratified note** (`dn-ouroboros-principal` §3.4), so the resolution is an
  owner-hand amendment (A8) or is carried in bp-076's plan §3 grounding (bp-076 is `ready`, not
  yet built — cheapest to fix there).

## Options (owner decision)
- **A — `exhaust/reports/` is workflow-plane-owned (RECOMMENDED).** `exhaust/` stays
  `ouroboros`-owned/traversable, but `exhaust/reports/` is owned by `ascalva` (or a shared group)
  and workflow-writable; system-emission subdirs (`exhaust/dreams/` etc.) stay `ouroboros`-write.
  Honors the plane mapping exactly: build reports ARE workflow output. `dn-ouroboros-principal`
  §3.4's exhaust row gets an amendment carving out `reports/`.
- **B — a shared `ouroboros` group, exhaust group-writable.** Both planes write via the group.
  Simplest perms, but softens isolation — acceptable because exhaust is the OUTBOUND, owner-read
  lane (low sensitivity vs the corpus), yet weaker than A's clean plane split.
- **C — reports become a system-plane emission.** The daemon (ouroboros) writes reports; the
  orchestrator hands it the composed HTML over a boundary. Awkward cross-plane handoff for a
  fundamentally workflow artifact; rejected unless reports are re-conceived as system output.

## Recommendation
**A.** It keeps the plane mapping honest (workflow writes reports, system writes emissions), needs
only a `reports/` ownership carve-out, and requires no cross-plane handoff. Carry it in bp-076's
plan §3 (ground the exhaust ownership against the report writer) + an owner-hand amendment to
`dn-ouroboros-principal` §3.4 at the same time the migration lands.
