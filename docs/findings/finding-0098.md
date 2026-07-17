---
type: finding
id: finding-0098
status: open
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/experiments/sigma-sweep-run-1.md          # the run that surfaced it (SE-3)
  - docs/design-notes/sigma-sweep-experiment.md    # FROZEN @ d932670 — SE-3 bars + "any bar fails ⇒ finding + owner decision"
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md   # §2.5 the gate whose real-data calibration this is
ftype: design
origin_plan: dn-sigma-sweep-experiment run 1 (SE-3)
route: orchestrator
---

# SE-3 bar (1) fails on real data: SETTLED-tier claims are NOT rated more real than RETAINED — persistence-tiering does not yet discriminate owner-perceived realness at 13-doc scale (apophenia guard DOES hold: bars 2 & 3 pass)

## What
Run 1's SE-3 blind judgment (owner rated 14 dream_v2 claims — 2 SETTLED / 8 HUNCH / 4 RETAINED —
before unblinding; legend 0=noise, 1=real connection, 2=plausible). Mapped to a semantic quality
scale (real > plausible > noise), the three FROZEN bars resolve:
- **(1) SETTLED median > RETAINED median — FAIL.** Both SETTLED claims rated `plausible` (median
  quality 1.0); RETAINED rated 3×plausible + 1×`real connection` (median 1.0). Not strictly greater —
  in fact a RETAINED claim was the only one rated `real connection`.
- **(2) ≥70% SETTLED ≥ plausible — PASS** (2/2 = 100%).
- **(3) >2 SETTLED rated noise — PASS** (0 SETTLED rated noise).

## Why it matters
Per the frozen note, **any bar failing ⇒ finding + owner decision; θ moves only as a subsequent lever
act, never inside the run.** The honest reading: the gate's **apophenia guard holds** (SETTLED tiers
are never noise — the thing that would discredit the gate did NOT happen), but persistence-tier does
**not yet track the owner's sense of a real connection** at this corpus scale. Two compounding causes:
1. **Corpus scale (13 docs).** With so few notes, "persists across the whole σ-range" and "is a real
   connection" need not coincide — a claim can survive every σ simply because the graph is tiny.
2. **Rater uncertainty compressed the scale.** The owner rated 10/14 `plausible` explicitly because
   "I don't remember all of the notes." A blind judgment where the rater cannot recall the referents
   collapses toward the middle rating, gutting the discrimination bar's signal. This is single-subject
   calibration evidence, NOT inferential statistics (as the note pre-labels it).

## Recommendation (re-entry — owner decision)
This is a PARK, not a gate failure: the gate stays un-shipped for surfacing (its `surfaced` API was
already closed pending F9 validation), and its real-data calibration rung is recorded as "apophenia
guard holds; discrimination unproven at 13-doc scale." Re-entry: **a larger corpus** (the owner can
actually judge realness) is the primary lever; a re-run's blind judgment should also present enough
claim CONTEXT that the rater isn't defaulting to `plausible`. **θ does NOT move in run 1** (frozen).
Whether to retune θ later is a separate owner-visible lever act informed by this record. Non-blocking.

## Non-goals
Not shipping or un-shipping the gate here (its API stays closed). Not moving θ (frozen in-run). Not a
correctness defect — the tiering + bars computed exactly as specified; the finding is that the real
data + rater conditions don't yet validate discrimination.
