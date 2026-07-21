---
type: finding
id: finding-0149
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/findings/finding-0147.md                  # the deep audit of dn-code-ingest-pipeline (16 corrections)
  - docs/findings/finding-0148.md                  # the M2/K1 un-minted follow-through (owner-flagged)
ftype: discovery
route: orchestrator
resolution: null
---

# Audit rollup — the 2026-07-18→21 design corpus + its build plans, audited at fable (main loop)

## Why

The fable→opus worker-downgrade bug (confirmed on the dn-code-ingest-pipeline pass, whose
banner falsely self-reported "Composed at fable") put every recent "fable pass" banner under
suspicion. Owner directed: audit every design document of the last few days and the build
plans they produced — ratified/blessed included — for mistakes that slipped through. All
audits ran in the fable main loop (never delegated); ratified notes were read-only (A8).

## Verdicts, per artifact

| artifact | status | verdict |
|---|---|---|
| dn-code-ingest-pipeline (07-21) | draft | **16 defects, corrected in place** (finding-0147); zero hallucinated citations; banner provenance was false |
| dn-agentic-loop (07-21) | ratified | **CLEAN** — ~20 spot-checks: all wiring-state claims verified (flags off, launcher lines, census X_cite-only confirms Correction 1); exact live counts (37 agent_observations, 210 dream_runs); AL-1/AL-3 builds landed as licensed |
| dn-fiber-geometry (07-21) | ratified | **CLEAN** — all code cites exact (conductance weight law, shipped-zero magnitudes, PROVEN_WEIGHT, {F,D}→{F,D,C} chain); math sound (block-diagonal sheaf, ML-d monoid-vs-group); [FROM MEMORY] flags honest |
| dn-synchronic-diachronic-dreamer (07-20) | ratified | **CLEAN** — objects all exist (CertifiedCut, factory ceiling, RowSource:54, dreamer_scope:143, eager build:33-40 exact); Rayleigh monotonicity correctly applied; validated by 4 sealed builds |
| dn-inner-outer-core (07-20) | ratified | **CLEAN as a note; one program-level gap** — M0/S1 faithful; the M2/K1 physical `core/kernel/` migration was never minted (finding-0148; entry gates opened at ratification `fbea48d`; K1 now mintable) |
| dn-plane-principals (07-20) | ratified | **CLEAN** — finding-0116:35-44 exact; launcher gui/$UID + cockpit + config cites verified (some line-drift from later builds — objects all exist; `palace` group live on disk) |
| dn-exhaust-lane (07-19) | ratified | **CLEAN** — config pin :46 exact, [exhaust] block, invariant test + writer built and live |
| dn-session-handoff-gate (07-19) | ratified | **CLEAN** — clause (e) live in `_lib.py`; session-brief.sh:46-47/:52 exact |
| dn-headless-daemon-secret-bootstrap (07-20) | draft | **CLEAN** — every grounded cite exact (unseal read :31, both plist labels, UserName, env dict, no backup UserName); the keychain-ACL-has-no-uid-axis analysis is technically correct |
| dn-agent-taxonomy (07-18) | ratified | **CLEAN via cross-validation** — its load-bearing clauses (§2.3 strata carving + forest quote, §2.4 fiber-vs-edge criterion, §2.5 witness law/C fiber) verified verbatim during the other audits; diamond builds sealed against it |
| dn-ouroboros-principal (07-19) | ratified→superseding | not deep-audited (superseded by dn-plane-principals; its surviving content re-verified through that note's §2 retention list) |
| bp-079..082, bp-083, bp-085..089 | complete | **FAITHFUL** — 1:1 with their notes' licensed items; none exceeds its license; bp-084's defect was self-caught (finding-0144 → bp-089 re-mint); S1's +7→37 vs the note's "36" correctly handled by F6 (recompute at HEAD) |

## What slipped through the cracks (the owner's question, answered)

1. **The dn-code-ingest-pipeline defects** — now fixed (finding-0147). The worst were two
   false present-tense claims (temporal wiring; per-row embedder stamp) and the false banner.
2. **The M2/K1 physical migration** — not a build error but an orchestration gap plus a
   misleading "wave complete" frame (finding-0148). Re-entry: /graduate K1.
3. **Nothing else.** No hallucinated citation was found in any ratified note; the ratified
   corpus's ground-citations were correct at their stated verification trees (line-drift
   since is dating, not error). The blessing gate held: everything blessed was sound.

## Systemic note

The one real forgery vector was the **banner self-report** ("Composed at fable"). Tier
verification by completion `<usage>` + main-loop audit caught it. Standing rule already in
memory: never trust worker self-reports for tier; the banners of pre-wave notes remain
unverifiable in principle but their content audited clean, which is the property that matters.
