---
type: finding
id: finding-0100
status: resolved
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/brainstorms/graph-at-a-past-cut.md         # the full design pass (D2/D3/D4/D6/D8)
  - docs/build-plans/bp-059/plan.md                 # §11 parked re-entry — the prerequisite this corrects
  - docs/design-notes/connectivity-instruments.md   # CN-1 — the cut index this extends to past cuts
  - core/mirror.py                                  # the RowSource Protocol seam
  - core/stores/rawstore.py                         # the retention that makes retro a pure function
ftype: design
origin_plan: graph-at-a-past-cut design pass (Fable/xhigh, 2026-07-17)
route: orchestrator
resolution: RESOLVED by finding-0113 (bp-073 Δ, owner-blessed 2026-07-19). The claim that the measurement is EVAL-SIDE constructible (the substrate already retains everything) is CONFIRMED — Δ built the whole re-measure eval-side over `MirrorGraph`-surface graphs and the live read-only stores, with NO core edit (ratchet held 19). The retro/eval-side constructibility this finding asserted is demonstrated in `eval/harness/re_measure.py`.
---

# Graph-at-a-past-cut is EVAL-SIDE constructible — the substrate already retains everything; bp-059 §11's "core/ plan" prerequisite is over-stated, and note-grain identity across cuts is already solved

## What
bp-059 §11 parks historical/cut-restricted graphs with re-entry prerequisite "a `core/` plan adding
downset restriction" to `MirrorView`. A rigorous grounding pass (capture, D2/D3) shows the accurate
prerequisite is smaller:
1. **Retention is already constitutional.** `CertifiedCut.frontier` pins (chain-key, position) per
   doc; the append-only versions store maps (doc_id, version_seq) → digest; the immutable
   content-addressed rawstore maps digest → verbatim bytes ("raw is sacred"); the re-embed path is
   anticipated by design (`core/ingest/embed.py:6`). Content-as-of-any-cut is a **pure function of
   retained data** — no new retention, no git archaeology.
2. **The seam already exists.** `RowSource` is a Protocol (`core/mirror.py:54-60`);
   `MirrorView.project(source)` accepts any implementor, and the Invariant-6 firewall check runs
   unchanged. A `HistoricalRowSource` adapter is therefore an **eval-side** build; the only
   genuinely new mechanism is deriving the frontier at a past commit (capture O1: digest-join
   against the versions chains — zero writes — or a small additive ingest-ledger column).
3. **Note-grain identity transport is already built.** `doc_id` is constant along version chains
   (append-only; rename-adoption and the owner-gated rekey both preserve it), so cross-cut pair
   queries at note grain are well-typed **today**. uuid-identity gates only claim/idea grain
   (CN-6's π) — not the memory-curve family at note grain.
4. **Wall-clock enters as bookmarks only** (owner question, 2026-07-17): the substrate already
   annotates (versions.at; run-ledger started_at; committer dates on COMMIT cuts). The missing
   piece is a **resolver** — wall-range → cut *interval*, ambiguity-widening, never an ordering
   key or an index coordinate (Law C4 intact; readings stay (σ,t,cut)-indexed).

## Why it matters
The "study the past like a memory" family — the memory curve σ*(A,B;c), the event-impact query,
reconnection-as-jump-points — is materially closer than the parked decision implies: the **anchored
gauge** (today's vectors, membership-at-c from the versions chains alone) needs no rawstore reads
and no re-embedding, and composes directly with bp-059's σ*/MST module as a small follow-on plan.
Leaving the over-stated "core/ plan" prerequisite on record would deter exactly the cheap build
that is actually available.

## Disposition
- **No change to bp-059** (blessed `ready`; its items and latest-cut v1 posture are unaffected —
  the parked decision's *default* stands; only the re-entry's named prerequisite is corrected, and
  this finding is the greppable correction of record).
- After the tranche builds: graduate `docs/brainstorms/graph-at-a-past-cut.md` into a design note
  (the three gauges, the resolver contract, the event-impact query, O1–O4); candidate first plan =
  memory curve v1 (anchored, note grain).
- Registers no new uuid-identity consumer (contra the session's first guess): note grain needs
  none; claim grain was already registered via CN-6/Track D/SF-a.
