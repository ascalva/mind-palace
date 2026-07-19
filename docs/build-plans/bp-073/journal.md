# Journal — bp-073 (Phase Δ: connectivity re-measure — does E_proven break oq-0031 saturation?)

## 2026-07-19 (session-31, OPUS) — minted (proposed) at the Γ-seal; Item 0 = ground the mapping
Graduates dn-agent-taxonomy §3 Phase Δ, the payoff measurement of the Β→Γ→Δ arc. Minted immediately
after bp-071 sealed (Γ), grounded against the LANDED upstream: D3 `core/graph/composed.py`
(`compose` + `ComposedGraph.classes_of` — the per-class attribution the oq-0031 falsifier needs),
the ratified σ*/conductance consumers (`core/graph/sigma_star.py`, `conductance.py`), bp-071's
`causal_edges.sqlite` (E_proven source), MirrorView/MirrorGraph (E_sim + authored nodes), and the
saturation cluster (findings 0096–0100 / oq-0031: golden_recall flat at 1.0 on the 13-doc corpus).

**Deliberately minted with genuine open design (the bp-071 pattern):** §3 carries four lean-defaulted
questions the build's Item 0 must pin against reality —
- Q1 what the dialogue nodes ARE (lean: authored mirror ∪ dialogue_artifact digests; events proven-only);
- Q2 how C-edges (event→endpoint) become node-PAIRS (lean: witnessed COMPOSITION action→commit→file/doc,
  carrying the concatenated witness tuple — finding-0111 + the owner's session-31 composition note);
- Q3 E_sim for dialogue nodes (lean: reuse mirror cosine over dialogue_artifact embeddings);
- Q4 the oq-0031 success criterion, PINNED before measuring (lean: golden_recall un-flattens AND/OR an
  E_proven bottleneck bridges a σ-component) — no moving goalposts, and an honest "still saturates"
  verdict is a `math` finding, never a forced green.

Eval-side (finding-0100: the measurement is eval-side constructible; the substrate retains everything).
NO new instruments (feed the ratified ones unchanged — the note's "assembly, not new instruments").
`depends_on: [bp-069, bp-070, bp-071]` — all landed. write_scope = eval/harness measurement + tests.

**Operational safety (owner raised, session-31): Δ cannot push Ouroboros into recovery.** Recovery is
an UNCLEAN-EXIT fail-safe read off `runs.sqlite`; Δ is eval-side, touches neither the daemon process
nor the run ledger. Added **Item 2b — READ-ONLY by construction:** the live measurement opens every
corpus store with sqlite `mode=ro` (a test asserts no writable handle), so Δ runs safely WHILE the
daemon is live — zero write-contention, recovery structurally unreachable. Made the property STRUCTURAL,
not conventional (the owner's enforcement principle).
**Next:** owner blesses proposed→ready (by hand); then a fresh OPUS /build session, Item 0 first.
