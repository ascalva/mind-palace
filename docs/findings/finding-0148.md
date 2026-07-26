---
type: finding
id: finding-0148
status: resolved
created: 2026-07-21
updated: 2026-07-26
links:
  - docs/design-notes/inner-outer-core.md          # the note whose M2 stage is at issue
  - docs/build-plans/bp-083/plan.md                # M0 — rings enforced in place (sealed)
  - docs/build-plans/bp-089/plan.md                # S1 — temporal math splits, INNER 30→37 (sealed)
ftype: direction
route: orchestrator          # owner-flagged; the re-entry is a /graduate pass minting K1
resolution: resolved — bp-090 (K1) + bp-091 (K3) complete; core/kernel/ exists, rings recomputed at build HEAD
---

# The physical inner/outer reorganization (M2/K1) was never minted — owner-flagged; entry gates opened only this morning

> **Triage 2026-07-26 (session-52) — RESOLVED.** The re-entry condition (a `/graduate` pass minting
> K1) is satisfied and the work is built: `core/kernel/` exists with the full subtree, and
> `core/kernel/rings.py:21-24` records `INNER` as "recomputed at build HEAD after the K1 (bp-090) and
> K3 (bp-091) physical relocations", enumerating 29 born + 7 S1 kernel members plus the five
> split-package outer residues. **bp-090 and bp-091 are both `complete`**, each carrying this finding
> as `warrant`.
> **Its §3 caveat materialized** — the CI-1↔K1 `chunk_text` sequencing collision it warned about
> became finding-0156 (bp-092's write_scope/pins drifted under the relocation), already `resolved`.
> That is the caveat working, not a miss.
> **For the deskcheck:** the Inner/outer-core queue row still reads "bp-083/089, M0+S1" and should
> name K1/K3 when demoed.

## What the owner observed (2026-07-21)

"The inner/outer work was supposed to have re-organized the core package to reflect the split
between the inner and outer core; it does not look like that was ever completed." Verified on
disk: **correct** — `core/` has no `kernel/` subtree; the 37 INNER modules (`core/rings.py`)
still live at their original flat paths. No physical separation exists.

## Disposition — not build-infidelity; an un-minted follow-through

The ratified note stages the program in four (`dn-inner-outer-core` §2.7): **M0** enforce rings
in place (no moves) → **M1** membership grows via remedies → **M2** physical migration to
`core/kernel/**`, per-wave plans → **M3** the flip. §3 is explicit: *"Licenses exactly two
build plans now"* — **M0 and S1 only**; the M2 wave plans are licensed *"upon ratification +
the §2.7 entry gates; each wave graduates as its own small plan with computed manifests."*

- M0 (bp-083) and S1 (bp-089) delivered exactly what they licensed — both sealed; the builds
  are faithful. Nothing ever claimed M2 was done.
- **The M2 entry gate opened only this morning**: ratification landed at `fbea48d`
  (2026-07-21, owner hand-bless). Before that, minting a K-wave plan was structurally
  premature by the note's own sequencing.
- **But no K1 plan was minted after ratification** — the graduation wave (6/6) contained only
  M0 + S1 from this program, and "GRADUATION WAVE COMPLETE" reads as if the ring program
  finished when its physical half had not yet begun. That perception gap is the real defect.

## K1 mintability check (the §2.7 entry conditions, evaluated today)

1. **Note ratified** ✓ (`fbea48d`).
2. **Per-wave stability** — K1 = the born set (the ~30 pre-S1 members): unchanged across two
   sealed plans (bp-083, bp-089; S1 only *added* 7) ✓ arguably satisfied.
3. **No open plan names any wave module** ✓ — no active plans at audit time. Caveat: when
   `dn-code-ingest-pipeline` ratifies, CI-1 will *import* the ingest text machinery
   (`chunk_text`) that K1 moves — either order works (each move commit repoints repo-wide),
   but the orchestrator should sequence them consciously.

## Re-entry / next step

A `/graduate` pass on `dn-inner-outer-core` minting **K1** (status `proposed`; computed
manifest at graduation per §2.7 — the born set as one or two plans; `git mv` + repo-wide
repoint + map rename + outer-count-unchanged + inner test green + full local CI, per move
commit). K3 (the S1 seven) follows as its own wave. Owner blesses `proposed→ready` by hand.

## Routing

`direction` → orchestrator (self). Owner already engaged — this finding records the
disposition and the mintability evaluation for the artifact chain.
