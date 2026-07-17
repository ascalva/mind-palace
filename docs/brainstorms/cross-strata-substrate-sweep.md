# Cross-strata substrate sweep — the "proper test" over the whole substrate

Brainstorm seed for the design arc that widens the σ-sweep / dreaming experiment from the authored
mirror (13 docs) to the whole substrate: authored notes + docs + code + code comments + chats +
observed. Motivated by σ-sweep RUN 1's findings (the mirror is too small + too homogeneous to test
the theories). The instruments to re-read such a run are already ratified (`dn-connectivity-instruments`,
deferred tranche); the capability to dream over non-authored strata is already ratified in generalized
form (`dn-cross-strata-dreamer`).

## 2026-07-17T16:38:31Z

```capsule
decisions:
  - The "more proper test" of the σ-hierarchy / multiscale-dreaming theories is a sweep across the
    WHOLE substrate, not the authored mirror alone. Owner direction 2026-07-17, immediately after
    σ-sweep run 1 sealed.
  - Run 1 is the evidence FOR this: golden_recall saturated at 1.0 across all 21 σ-cells
    (finding-0096 — the 13-doc authored corpus gives the objective zero dynamic range); phase7 fell
    below the n_claims≥10 floor; SE-3 discrimination was unprovable because the owner couldn't judge
    realness on so few, un-recalled notes (finding-0098). SE-2 was the positive: the fibers instrument
    WORKS (dream_v2 non-degenerate even at 13 docs) — give it real substrate and it should shine.
  - ARCHITECTURE (non-negotiable, stated so no one wires a firewall breach): the current sweep is the
    MIRROR dreamer — authored-only by Invariant 6 (a non-authored node is structurally unrepresentable
    upstream). "Across the whole strata" is NOT a config flag on that sweep; it is the CROSS-STRATA
    CORRELATOR (Track D family) — a scoped dreamer with an owner-declared read-exemption from ι_MR,
    output interpreted-tier only, MIRROR_READABLE untouched, the mirror dreamer still authored-only.
    This is exactly what dn-cross-strata-dreamer ratified (oq-0027: "dreamers should be allowed to be
    scoped to use non-authored seeds; we can test it all").
  - Substrate splits into two bands by privacy:
      * PUBLIC / firewall-safe — docs, code, code comments. A correlator over these grows the corpus
        WITHOUT touching private data (they are repo content, not vault data) — the nearer-term fix
        for finding-0096's saturation. (code-sensor already runs — `code-sensor sync` every commit.)
      * PRIVATE / gated — chats (the NEW chat sensor under discussion), observed (ObservedView, Track
        D's declared seam; self-sensor already runs). These need the scoped correlator + owner grant.
  - This is the owner's self-map thesis made literal ([[owner-background-self-mapping]]): chats + code
    + docs + notes + observations as ONE connected graph — "mining my own brain."

parked:
  - The full cross-strata run vs the public-band-first run. Default: sequence public-band first
    (docs/code/comments — firewall-safe, addresses saturation soonest), layer the private band
    (chats/observed) once the chat sensor + scoped grant land. Re-entry: the design note chooses the
    band scope; a private-band run is gated on the scoped-correlator capability + owner read-exemption.
  - The non-saturated objective. Default: golden_recall stays the guardrail, but a σ-sweep needs a
    metric with dynamic range — finding-0096's own re-entry names f9_composite / per-cell F9 wiring
    (dn-evaluation-harness E5/E7). Re-entry: the cross-strata note picks the objective (a bigger,
    heterogeneous corpus may also un-saturate golden_recall on its own — to be measured).
  - The chat sensor. Parked as a build: the new sensor projecting conversations into the substrate.
    Re-entry: a sensor design (mirrors code-sensor/self-sensor) + its View + the privacy handling
    (chats are sensitive → scoped-read, interpreted-only).

open_questions:
  - Which Views exist vs must be built? (MirrorView ✓ authored; code-sensor ✓ → a CodeView?;
    self-sensor ✓ → ObservedView is the Track D seam; chats = new; docs = a DocsView.) Inventory
    needed before scoping.
  - Does the cross-strata correlator reuse MirrorGraph's σ-adjacency over composed note-centroids, or
    need a typed multi-stratum graph (Res(π) over a composed substrate)? (The connectivity-instruments
    σ*/MST/conductance machinery assumes a per-cell graph — check it generalizes.)
  - uuid-identity: the gating prerequisite (connectivity-tranche item 4; SF-a claim identity across a
    bigger, changing, cross-stratum corpus). How much of the cross-strata run needs it up front?

next_steps:
  - This graduates into a NEW design note — a cross-strata σ-sweep pre-registration (its own SE-*/V-*),
    NOT a silent run-2 (different substrate AND instrument). Sequenced WITH the ratified
    dn-connectivity-instruments tranche (the phase-B re-analysis is literally designed for a run like
    this) and gated on uuid-identity + the chat sensor.
  - Immediate build-out (owner direction 2026-07-17): graduate + build the ALREADY-RATIFIED
    dn-connectivity-instruments tranche (items 1–3; item 4 gated on uuid-identity) — the analysis
    instruments that will read the cross-strata run when it exists.

references:
  - docs/experiments/sigma-sweep-run-1.md            # the run + findings that motivate this
  - docs/findings/finding-0096.md                    # golden_recall saturation at 13-doc scale
  - docs/findings/finding-0098.md                    # SE-3 discrimination needs a larger, judgeable corpus
  - docs/design-notes/connectivity-instruments.md    # RATIFIED — the phase-B re-analysis tranche (deferred)
  - docs/design-notes/cross-strata-dreamer.md        # RATIFIED (generalized) — the scoped-dreamer capability
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md   # the fibers/gate this widens
```
