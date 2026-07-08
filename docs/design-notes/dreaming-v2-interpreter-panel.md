---
type: design-note
id: dn-dreaming-v2-interpreter-panel
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-06-26
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Dreaming v2: a panel of interpreters with evidence-based adjudication

*Family tag → family 5 (the reasoning complex): a panel of interpreters over the complex with evidence-based adjudication (c = γ^d·g·(1 + λ(|Agr|−1))). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only; an **expansion of the already-built Phase 7 dreamer**. Not
committed; does not change Phases 0–10 scope. Honor as a post-Phase-7 enhancement. Builds
directly on `core/dreaming/cluster.py`, `core/dreaming/dreamer.py`, `core/selfcheck.py`,
`core/stores/derived.py`.

## What exists (Phase 7) — already the single-worker version
One deterministic interpreter (cosine single-linkage connected components, `cluster.py`)
→ per-theme grounded synthesis (`dreamer.py`, Constitution-first, cluster notes as the only
citable evidence) → stored as an INTERPRETED `dream` in the `DerivedStore`, reading the
AUTHORED mirror only (`MIRROR_READABLE`), grounding-checked before storage. This note
generalizes that single lens into a panel, and adds adjudication.

## The expansion — two moves
1. **A panel of deterministic interpreters (the "workers").** Each is a different lens on
   the same authored graph; each emits candidate pattern-claims **plus the graph evidence
   that supports them**. Beyond today's single-linkage clustering:
   - community detection (Leiden/Louvain) — thematic clusters
   - centrality (degree/eigenvector/betweenness) — which themes are load-bearing
   - temporal trend / change-point — what is rising or fading over time
   - structural-hole / bridge detection — what connects otherwise-separate clusters
   - density-based clustering (HDBSCAN) — clusters + explicit noise
   Cheap, parallel, **model-free** — the §9 deterministic floor, just more eyes. The model
   is still earned only for narration/synthesis, never for the pattern-finding itself.
2. **An adjudicator (the "leader/judge").** Ranks the competing candidate interpretations and
   logs a **confidence-ordered list** as the dream's outcome, each entry carrying its
   evidence. Agreement *across* lenses is a confidence signal; disagreement is information,
   not noise.

## The load-bearing caveat — evidence, not persuasion
**Adversarial-by-persuasion is a self-deception engine; adversarial-by-evidence is honest.**
LLMs are persuasive independent of correctness. If the judge scores argument quality, the
most eloquent interpretation wins — a sophisticated way to fool yourself about your own mind,
the mirror-not-oracle (§4) failure in a debate costume. Therefore:
- The judge's **currency is resolvable evidence**: does the cluster exist in the graph; do
  the cited notes actually support the claim. Reuse and extend `core/selfcheck.py`'s
  "every cited identifier must resolve" grounding — it is exactly the right judge.
- Optional LLM **advocates** may *narrate* a candidate (make its meaning legible) but
  **cannot win on eloquence — only on evidence**. They are presenters, not deciders.

## "Cryptographically sound", done right
Log each interpretation with **content-addressed evidence references** (the raw store is
already sha256-addressed): a dream becomes **tamper-evident and reproducible**, auditable on
the Phase-11 dashboard. This is integrity + reproducibility, not zero-knowledge proofs.

## Provenance & alignment guardrails (reaffirmed)
- Outputs are `INTERPRETED` — `DerivedStore.add()` has no provenance parameter, so dreams
  **structurally cannot masquerade as authored** ground truth.
- Inputs are AUTHORED-only (`MIRROR_READABLE`): observed exhaust can never seed a dream, nor
  reach the §15 baselines.
- Confidence ranking ranks **hypotheses for the owner to weigh, never verdicts**. A
  high-confidence dream is still a hypothesis. Nothing a dream concludes acts on the system
  except through the Phase-10 gate.

## Build order (do not over-build)
The **deterministic panel + grounded adjudicator** captures most of the value cheaply and
safely — build that first. **LLM advocates / full debate are a later, optional elaboration
and the riskiest part** (the persuasion failure mode); gate them behind the panel proving
insufficient. The per-cluster checkpoint seam already noted (`queue.checkpoint`) lets the
panel run as resumable trough work.

## Open questions
- Which interpreters, and how many, before it is noise rather than signal.
- Confidence calibration: cross-lens agreement as the primary signal; how to surface
  disagreement as information.
- How the owner reviews a confidence-ranked dream (the Phase-11 dashboard view).
- Whether any high-confidence interpretation ever does more than display (default: no —
  only via the gate).
