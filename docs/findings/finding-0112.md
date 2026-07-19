---
type: finding
id: finding-0112
status: resolved
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/build-plans/bp-073/plan.md                # §1/§3 Q1–Q4 grounded here (Item 0)
  - core/stores/vectorstore.py                      # the mirror embed store — holds ONLY 17 authored janus_notes
  - core/mirror.py                                  # MIRROR_READABLE={authored} firewall REFUSES repo docs by construction
  - core/stores/causal_edges.py                     # E_proven source: 941 doc + 2681 file + 78 commit endpoints (3700 edges)
  - core/graph/composed.py                          # compose()/classes_of — the Δ falsifier surface
re_entry: RESOLVED — owner ruled A (2026-07-19, session-32): embed the dialogue-artifact corpus eval-side.
ftype: spec-fidelity
origin_plan: bp-073
route: orchestrator
resolution: owner ruled OPTION A (2026-07-19, session-32) — the Δ measurement embeds the dialogue-artifact doc corpus eval-side (ephemeral, read-only, never persisted). Node set = the docs carrying C-edges; E_sim = cosine over eval-side doc embeddings (reuse the ingest embedder, the model-free substrate); E_proven = C-edge shared-witness co-production. Accepts the deterministic embedder in the eval loop over the doc corpus. Q2 builder-resolved (co-production, no §10 stop). Items 1–2 unparked; plan §1/§3/§6/§11 pinned in the bp-073 journal (session-32).
---

# bp-073 Item 0 grounding: the dialogue-artifact corpus is UNEMBEDDED, so the Δ measurement cannot ride the existing MirrorView — it must embed the doc corpus eval-side (owner ruling on node set + embedder)

## What
Item 0 (ground the C-edge→node-pair mapping + the dialogue-node set against landed reality)
found two things — one builder-resolved, one owner-level.

**A. Q2 (C-edge → node-PAIR) — RESOLVED in-plan (builder, spec-fidelity).** The C-edges are
(dialogue-action → endpoint), not (node → node). The robust, inference-free projection is
**shared-witness co-production**: two direct `action→{doc,file}` C-edges in the SAME session are
causally co-produced → an endpoint↔endpoint E_proven pair carrying the concatenated witness
(session `transcript_digest`, both event turns). Live grounding: **53 sessions co-produce ≥2
distinct docs** (208 distinct doc endpoints over 941 doc-edges), so doc↔doc pairs are abundant.
This needs NO `commit→file` relation → the plan §10 codebase-STOP does **not** trigger
(finding-0111 already established a commit's changed-file set is unresolvable from any store;
co-production sidesteps it — the pair comes from the two proven writes directly, not from fanning
a commit's tree). Reference-composition (`action→commit ∘ reference_edges@commit`) is an optional
bonus where reference_edges carries rows at a C-edge's commit sha. Alberto pre-confirmed the
composition lean at mint; grounding confirms it is concretely supplied.

**B. Q1/Q3 (dialogue nodes + their E_sim) — a DIVERGENCE that forces an owner decision.** Plan §1
assumes "MirrorView for E_sim + authored nodes." But the LIVE mirror vectorstore
(`data/vectors.lance`) holds **only 17 authored janus_notes** (`authored-solo`) — zero repo docs;
the mirror firewall (`MIRROR_READABLE={authored}`) structurally refuses dialogue_artifacts. The 208
docs that carry C-edges (of 266 on disk: 64 design-notes + 72 build-plans + 97 findings + 33
brainstorms) are a **disjoint, unembedded corpus**.

**The load-bearing consequence:** over the mirror node set, **E_proven is empty** — the janus_notes
carry no C-edges — so adding E_proven to the mirror graph changes nothing and cannot break the
oq-0031 saturation. The measurement is only non-trivial over the **dialogue-artifact** node set (the
docs that HAVE C-edges), and for E_proven to be shown *bridging* E_sim-gaps there, those docs must
carry E_sim. So the faithful measurement must **embed the dialogue-artifact corpus eval-side** (Q3
lean: "reuse the mirror's cosine machinery over dialogue_artifact embeddings").

## Why it matters
This is bigger and different-shaped than "feed the existing MirrorView + causal_edges into
`compose()`." It (a) requires eval-side embedding of ~208–266 docs via the ingest embedder, and (b)
brushes the §9 "NO model" non-goal — though embeddings are the deterministic substrate the note
already treats as model-free (`MirrorGraph` is "model-free (NumPy cosine only)"; the vectors are the
upstream floor). It also determines **what corpus oq-0031 is answered over** — a measurement-design
choice with interpretive weight, hence owner-routed, not silently builder-resolved.

## Decision (owner)
What node set + E_sim source does the Δ payoff measure over?
- **A (recommended) — embed the dialogue-artifact doc corpus eval-side.** Nodes = the docs carrying
  C-edges; E_sim = cosine over eval-side doc embeddings (ephemeral/read-only, never persisted to any
  daemon store — consistent with Item 2b); E_proven = C-edge co-production. The only faithful
  measurement: E_proven can genuinely be shown to bridge E_sim-gaps. Cost: embedder in the eval loop.
- **B — proven-only doc nodes (no doc E_sim).** Nodes = mirror (E_sim) ∪ docs (E_proven-only). But
  the two edge classes then live on DISJOINT node sets → E_proven cannot bridge an E_sim-component;
  degenerate for the "breaks saturation" question. Not recommended.
- **C — reference_edges as the doc structural edge class instead of embedding.** Uses an existing
  proven-ish relation, but it is not *similarity*, so it does not answer "does E_proven bridge the
  E_SIM gaps." Off the note's intent.

Recommendation: **A** — it is the only measurement that can actually answer oq-0031, and it sits
inside the note (§3 "{mirror ∪ dialogue nodes} × {E_sim ∪ E_proven}") + the Q3 lean. The owner call
is really "accept the deterministic embedder in the eval measurement, over the doc corpus."
