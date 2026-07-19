---
type: build-plan
id: bp-073
alias: connectivity-re-measure
status: proposed
design_ref:
  - docs/design-notes/agent-taxonomy.md            # §2.2 grounding law + §3 Phase Δ (the charter)
  - docs/design-notes/connectivity-instruments.md  # RATIFIED — the σ*/conductance consumers of E_proven
  - docs/findings/finding-0096.md                  # the oq-0031 saturation (golden_recall flat at 1.0)
contract: builder
write_scope:
  - eval/harness/re_measure.py
  - eval/harness/connectivity.py
  - eval/harness/fibers.py
  - tests/unit/test_re_measure.py
  - tests/unit/test_connectivity.py
session_budget: 2
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: [bp-069, bp-070, bp-071]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/design-notes/agent-taxonomy.md
created: 2026-07-19
updated: 2026-07-19
re_entry: null
---

# Build Plan — Phase Δ: connectivity re-measure (does E_proven break the oq-0031 saturation?)

## 0. Mode & provenance
Graduates `dn-agent-taxonomy` §3 Phase Δ — the **payoff measurement** of the Β→Γ→Δ arc. Β (bp-069)
added the dialogue nodes; Γ (bp-071) added the proven C-edges; Δ feeds BOTH into D3's `ComposedGraph`
(`core/graph/composed.py`, landed bp-070) and runs the *existing, unchanged* σ*/conductance
instruments over the enlarged graph to answer oq-0031: **was the 13-doc connectivity saturation
input starvation (fixable by a second, proven edge class + more nodes), or a real ceiling?**
⚠️ **MINTED with genuine open design (like bp-071): §3/§6 carry default leans; the FIRST build act is
Item 0 — pin the C-edge→node-pair mapping and the dialogue-node set against landed reality.**

## 1. Objective
Assemble the REAL composed graph — `{mirror ∪ dialogue nodes} × {E_sim ∪ E_proven}` — from the live
stores (MirrorView for E_sim + authored nodes; bp-069's dialogue layers for dialogue nodes; bp-071's
`causal_edges.sqlite` for E_proven), run the ratified connectivity instruments (`sigma_star`,
`sigma_t_profile`) over it via `compose()`, and **attribute connectivity to E_sim vs E_proven**
(`ComposedGraph.classes_of` — the falsifier the note names). Produce the oq-0031 re-measure report:
does discriminating power return once the graph is fed proven edges + dialogue nodes? Resolve or
honestly re-state findings 0096–0100. Model-free, eval-side (finding-0100: the measurement is
eval-side constructible; the substrate already retains everything). NO new instruments — feed the
existing ones unchanged (the note's discipline: "assembly, not new instruments").

## 2. Context manifest (PROVISIONAL — re-verify at Item 0)
1. `dn-agent-taxonomy` §2.2 (the grounding law — E_proven ∪ E_sim is the answer, not a better σ) +
   §3 Phase Δ + §2.5 (the witness law — every E_proven edge carries its witness).
2. `core/graph/composed.py` — `compose(nodes, sim_edges, proven_edges)` → `ComposedGraph`; the
   `MirrorGraph` surface (`.n/.digest/.neighbors/.sim`) + `classes_of(a,b)` (per-class attribution).
   Proven edges default weight 1.0 (present at every grid σ → can bridge σ-components).
3. `core/graph/sigma_star.py` (`build_max_spanning_tree`, `sigma_star`, `pairwise_sigma_star`) +
   `core/graph/conductance.py` (`sigma_t_profile`) — the consumers, fed a `MirrorGraph`-surface graph
   UNCHANGED (a localized `cast` bridges the static type, per composed.py's docstring).
4. `core/stores/causal_edges.py` (bp-071) — the E_proven source: `CausalEdge(session_id, event_order,
   kind, dst_type, dst, witness_digest, witness_turn, pair_cut_sha)`; `all_edges()`. Endpoints are
   (event → commit sha | file path | doc artifact-id) — NOT yet node-PAIRS (see §3 Q2).
5. `core/mirror.py` (MirrorView) + `core/dreaming/graph.py` (`MirrorGraph.build`) — the E_sim source +
   the authored (mirror) node set + how digests/embeddings/cosine edges are produced today.
6. bp-069's dialogue layers — `core/stores/chat_events.py` (L1) + `core/stores/chatlog.py` (L0) — the
   dialogue-node candidates; and the dialogue_artifact digests (design-notes/findings/brainstorms)
   already in the corpus.
7. `eval/harness/connectivity.py` + `eval/harness/fibers.py` + `eval/harness/sweep.py` — the current
   σ-sweep experiment (the oq-0031 run-1 that saturated); the extend-vs-new-module decision (§11).
8. findings 0096–0100 (the saturation cluster) + oq-0031 (owner-questions.md) — what "resolved" means.

## 3. Investigation & grounding (to COMPLETE at Item 0; charter-level answers recorded)
- **Q1 — what ARE the dialogue nodes (as graph nodes)?** *Lean:* the corpus digests that carry
  embeddings — authored mirror notes (E_sim as today) PLUS **dialogue_artifact** nodes (design-notes/
  findings/brainstorms — already embeddable corpus). Chat-session/L1-event nodes are proven-only
  (no embedding) — they enter as E_proven endpoints, not E_sim participants. Confirm the mirror/embed
  seam admits dialogue_artifact digests.
- **Q2 — how do C-edges become node-PAIRS?** The integrator's C-edges are (dialogue-event → endpoint),
  not (node → node). *Lean:* project to node-pairs by COMPOSITION over a shared witness — an
  `action→commit` edge composed with the existing `commit→file`/`commit→doc` relations (reference_edges
  / code_observations) yields `doc↔doc` / `doc↔code` node-pairs, **carrying the concatenated witness
  tuple** (finding-0111 / the owner's composition note: paths compose, the witness must ride along, the
  fiber label only composes within-fiber). A pure `action→doc` C-edge (a direct file/doc write) is
  already a node-pair if the endpoint is a graph node. STOP-and-raise if the mapping needs a design
  decision beyond the note (→ `design` finding, owner).
- **Q3 — E_sim for dialogue nodes?** *Lean:* reuse the mirror's cosine machinery over dialogue_artifact
  embeddings (same σ-grid); do NOT invent a new similarity. Proven-only nodes have no E_sim.
- **Q4 — the oq-0031 success criterion (what "discrimination returned" MEANS).** *Lean:* pin it BEFORE
  measuring (no moving goalposts): e.g. `golden_recall` no longer flat across the σ-grid (0096), and/or
  a cross-component pair whose `sigma_star` flips None→reading *because* of an E_proven bridge
  (`classes_of` attributes the bottleneck edge to E_proven). Report honestly if it still saturates —
  that is a real finding (the taxonomy's answer was necessary-but-insufficient), NOT a failure to force
  green.

## 4. Reconciliation
Additive + eval-side. NO change to the ratified instruments (`core/graph/**` is consumed, not edited).
NO change to bp-069/bp-071 modules (their stores are READ). The measurement is a new eval-harness lane
(or an extension of `connectivity.py`/`fibers.py` — Item 0 decides) that assembles real edge sets and
drives `compose()` + the instruments. Ratchet stays 19 (no core edit). Corpus-side stores are read-only.

## 5. Write scope
As front-matter (eval-harness measurement + its tests). **OUT:** `core/graph/**` (the instruments +
composed.py — consumed, never edited); bp-069/bp-071 core modules + their stores (read-only);
the sweep engine's decision rules (SE-1/SE-3 — 0097/0098 are separate; Δ re-measures, it does not
re-tune). If Item 0 finds a core-side helper is genuinely needed, STOP → scope-amendment finding.

## 6. Interfaces pinned inline (PROVISIONAL until Item 0)
```python
# eval/harness/re_measure.py (NEW — the Δ measurement; eval-side, model-free):
def assemble_composed_graph(*, mirror, causal_edges, ...) -> ComposedGraph:
    # nodes = mirror digests ∪ dialogue_artifact digests (Q1); sim_edges = mirror cosine (Q3);
    # proven_edges = C-edges projected to node-pairs by witnessed composition (Q2), weight 1.0.
    ...
def re_measure_oq0031(graph: ComposedGraph, *, sigma_grid, t_grid) -> ReMeasureReport:
    # cast(MirrorGraph, graph); build_max_spanning_tree; pairwise_sigma_star; sigma_t_profile;
    # attribute each connecting bottleneck edge to E_sim | E_proven via graph.classes_of.
    ...
@dataclass
class ReMeasureReport:
    n_nodes: int; n_sim: int; n_proven: int
    golden_recall_by_sigma: dict[float, float]     # the 0096 saturation gauge — flat ⇒ still starved
    proven_bridges: list[tuple[str, str]]          # pairs connected ONLY via an E_proven bottleneck
    discriminates: bool                            # the Q4 criterion, pinned at Item 0
```

## 7. Items
### Item 0 — GROUND the mapping + node set  (blast: none — reading + plan amendment)
- **Acceptance:** Q1–Q4 answered against landed reality (MirrorView/MirrorGraph embed seam; the
  reference_edges/code_observations commit→file relations for the Q2 composition; the causal_edges
  shape; the sweep's `golden_recall`). The C-edge→node-pair projection + the dialogue-node set are
  pinned in this plan (journal-logged). Extend-vs-new eval module decided. STOP-and-raise (`design`
  finding, owner) if the mapping needs a decision beyond the note.
### Item 1 — assemble the real composed graph  (blast: new eval module, reads only)
- **Acceptance:** `uv run pytest tests/unit/test_re_measure.py -q` green — `assemble_composed_graph`
  builds a `ComposedGraph` from real stores (fixtured): mirror nodes + dialogue_artifact nodes; E_sim
  cosine edges; E_proven node-pairs from composed C-edges, each carrying its witness tuple; weight 1.0
  on proven edges. A proven bridge joins two σ-components a fixture keeps sim-disconnected.
- **Falsifier:** a proven edge minted without a witness; a node-pair from an uncomposed (endpoint-less)
  C-edge; E_sim and E_proven silently merged (attribution lost).
### Item 2 — re-measure + the oq-0031 verdict  (blast: measurement + report)
- **Acceptance:** `uv run pytest tests/unit/test_re_measure.py tests/unit/test_connectivity.py -q`
  green; the real instruments (`sigma_star`/`sigma_t_profile`) run over the composed graph via `cast`;
  `ReMeasureReport` attributes connectivity to E_sim vs E_proven; the Q4 criterion is computed. LIVE
  run over the real corpus: report `n_proven > 0`, and a HONEST verdict on `discriminates` (either
  discrimination returned — annotate/resolve 0096–0100 — or it still saturates → a `math` finding
  stating the taxonomy's answer was necessary-but-insufficient). Full suite green-except-the-ratchet.
- **Falsifier:** a forced-green verdict; the instruments edited to discriminate; a proven bridge not
  attributed to E_proven; `golden_recall` improvement claimed without the σ-grid evidence.

### Item 2b — READ-ONLY by construction (operational safety; blast: none)
- **Acceptance:** the live measurement opens EVERY corpus store read-only (sqlite
  `file:…?mode=ro` URI / `open(..., "r")`), so it holds NO writable handle to any store the live
  daemon owns. A test asserts this (a write attempt through the measurement's handles raises
  `sqlite3.OperationalError: attempt to write a readonly database`). Consequence: Δ can run WHILE
  Ouroboros is live with zero write-contention and zero possibility of corrupting a store or the run
  ledger — the daemon's recovery path (unclean-exit-only) is structurally unreachable from here.
- **Falsifier:** any measurement code path holding a writable handle to a corpus/ledger store; a run
  that requires stopping the daemon (Δ must be safe to run against the live corpus).

## 8. Math carried explicitly
The grounding law (§2.2): connectivity is measured over `E_proven ∪ E_sim`; a proven edge has weight
1.0 ≥ any cosine, so it is present at EVERY grid σ and can bridge two similarity components — the
mechanism by which a second edge class breaks saturation (composed.py's max-weight flatten). The
witness law rides through composition: a projected `doc↔code` node-pair carries the concatenated
witness tuple of its `action→commit→file` path (finding-0111) — the composite is re-derivable, so it
stays in E_proven; a pair-cut anchors each commit hop. No inference; the dreamer's E_interp is NOT here.

## 9. Non-goals
NO new instruments (feed the ratified σ*/conductance UNCHANGED). NO edit to `core/graph/**` or to
bp-069/bp-071 modules. NO model. NO E_interp / dreamer edges (Law 2's interpretive class is later).
NO re-tuning of the sweep decision rules (0097/0098 are a separate concern). NO forcing a green verdict.

## 10. Stop-and-raise conditions
- Item 0 finds the C-edge→node-pair mapping needs a design decision beyond the note → STOP, `design`
  finding (owner). The composition (Q2) requires the commit→file relation — if `reference_edges`/
  `code_observations` cannot supply it for the corpus, STOP, `codebase` finding.
- The enlarged graph STILL saturates → NOT a stop; report it honestly as a `math` finding (the
  answer was necessary-but-insufficient), resolving the oq-0031 cluster with a truthful verdict.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| dialogue nodes = which digests | authored mirror ∪ dialogue_artifact (embeddable); events proven-only | Item 0 |
| C-edge → node-pair projection | witnessed composition (action→commit→file/doc), witness carried | Item 0 |
| new eval module vs extend connectivity.py | new `eval/harness/re_measure.py` | Item 0 |
| oq-0031 success criterion | golden_recall un-flattens AND/OR an E_proven bottleneck bridge | Item 0 (pin before measuring) |

## 12. Dependency & ordering summary
`depends_on: [bp-069, bp-070, bp-071]` — Phase Δ, the arc's payoff. Item 0 (ground) → 1 (assemble) →
2 (measure + verdict). **Upstream landed:** D3 `ComposedGraph` (bp-070), dialogue nodes (bp-069),
E_proven (bp-071). **Downstream:** the dreamer's grounding law (Law 2) consumes E_proven; resolving
oq-0031 unblocks the connectivity/sweep track's validation (0096–0100).
