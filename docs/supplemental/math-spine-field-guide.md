# Math Spine Field Guide

A working reference for every mathematical construct in the Mind Palace reasoning complex. Each entry answers three questions: what it measures, what assumptions make it valid, and what observable result would show it is not earning its place. The third clause is the load-bearing one. A construct with no failing condition is decoration by definition.

The stance this document supports: you do not need proof-level fluency in any of these. You need to be able to state each entry's three clauses without looking, and you need the Track L harness running so the falsifiers are actually checkable. Empirical accountability substitutes for derivation; nothing substitutes for empirical accountability.

---

## 0. Shared assumptions (read first)

Every instrument below inherits two assumptions from the complex itself, and most failures will trace back to these rather than to any individual construct.

**Weight comparability across typed layers.** The generalized Laplacian aggregates edges of different types (citation, semantic similarity, temporal adjacency, contradiction) into one operator. This silently assumes a weight of 0.7 on a citation edge is commensurable with 0.7 on a similarity edge. If the layer weightings are arbitrary, every downstream spectrum, curvature, and cluster is arbitrary in the same proportion. Falsifier: rerun the instruments under perturbed layer weights (±50%); if cluster assignments or bridge rankings reshuffle substantially, the outputs reflect your weighting choices, not the corpus.

**Edge semantics are honest.** An edge must mean what its type says it means. If "similarity" edges come from embedding cosine above a threshold, they mean "the embedding model thinks these are similar," which is weaker. Falsifier: sample edges of each type and hand-verify; if more than a small fraction of a type's edges are semantically wrong, instruments consuming that layer are consuming noise.

---

## 1. Coboundary operator / generalized Laplacian (the spine itself)

**Measures:** how local disagreement aggregates globally. The coboundary δ takes values on nodes to differences on edges; L = δ*δ turns "how much does each node disagree with its neighborhood" into a single operator whose spectrum encodes the corpus's global structure. Everything else derives from this.

**Valid when:** the incidence structure of the complex reflects real relations (see §0), and the derivation of each specialized instrument from the shared operator is actual derivation, not parallel implementation with a shared name.

**Not earning its place if:** instruments derived from the generalized operator do not outperform the same instruments computed on a flat, untyped, single-layer graph of the same notes. This is the master ablation. If typed multilayer structure buys nothing on verdicts, the generalization is architecture theater and a plain graph Laplacian would do.

---

## 2. Ordinary graph Laplacian

**Measures:** smoothness of functions over the graph. Low eigenvalues correspond to functions that vary slowly across edges; the associated eigenvectors partition the graph into weakly connected regions (clusters). λ₂ measures overall connectivity — how hard the graph is to cut in two.

**Valid when:** edges mean affinity ("these belong together"), edge weights are on a comparable scale, and the graph is connected or you handle components explicitly. Spectral clustering additionally assumes clusters are roughly balanced in size; it is known to shred small clusters to balance a cut.

**Not earning its place if:** Laplacian-derived clusters do not beat the TF-IDF BaselineDreamer on your verdict stream. This is the single most important falsifier in the project and it is already wired: the baseline exists precisely so this comparison is one command, not a research project.

---

## 3. Signed Laplacian

**Measures:** structural balance in a graph with positive (agreement/support) and negative (contradiction/opposition) edges. Its smallest eigenvalue measures total frustration — how far the corpus is from being cleanly partitionable into internally-agreeing, mutually-opposing camps.

**Valid when:** negative edges genuinely mean opposition, not merely "dissimilar" or "unrelated." This is the strictest edge-semantics requirement in the system. A negative edge asserting contradiction between two notes that are just about different topics poisons the frustration signal.

**Not earning its place if:** the global frustration number never moves in response to you actually writing contradictory notes, or moves in response to things that aren't contradictions. A cheap test: author a deliberate three-note contradiction, confirm frustration rises; delete it, confirm it falls.

---

## 4. Frustrated triangle enumeration

**Measures:** the local units of imbalance — triads whose sign product is negative (e.g., A supports B, B supports C, A contradicts C). These are the specific places where "something has to give" in your beliefs.

**Valid when:** the sign semantics are roughly transitive at triad scale, and triangles are meaningful units (dense-enough graph that triads exist; sparse-enough that they aren't ubiquitous).

**Not earning its place if:** when surfaced for review, flagged triangles are judged "not a real tension" at a high rate. This should be a verdict category in Track L. If precision on flagged tensions is near chance, the instrument is generating review fatigue, which your own design notes identify as the primary failure mode of the whole harness.

---

## 5. Sheaf Laplacian

**Measures:** consistency of local data under context-dependent translation. Where the ordinary Laplacian asks "do neighbors agree," the sheaf Laplacian asks "do neighbors agree *after* each one's data is mapped through the restriction map into the shared edge context." It detects inconsistencies that only appear once you account for the fact that the same concept means slightly different things in different notes.

**Valid when:** the restriction maps are principled — learned or specified from actual context relationships, not defaulted to identity. This is the highest-risk construct in the spine. Identity restriction maps make the sheaf Laplacian collapse to the ordinary Laplacian with extra bookkeeping, which is the canonical form of decorative formalism.

**Not earning its place if:** (a) an audit of the restriction maps shows they are identity or near-identity in the bulk of cases, or (b) inconsistencies detected by the sheaf machinery are the same set detected by plain contradiction edges. Either result means the sheaf layer should be cut until there is a principled source of restriction maps.

---

## 6. Hypergraph Laplacian

**Measures:** higher-order structure that pairwise edges cannot express — a note that cites three sources *jointly*, where the joint relation is not the sum of three pairwise relations.

**Valid when:** hyperedges encode genuinely non-decomposable group relations. Most "groups" in a notes corpus decompose fine.

**Not earning its place if:** clique expansion (projecting every hyperedge to its pairwise complete graph) yields the same clusters and rankings. This is a standard, cheap ablation in the hypergraph literature and it frequently wins. If it wins here, the pairwise complex suffices and the hypergraph machinery should go.

---

## 7. Ollivier-Ricci curvature

**Measures:** local transport cost — how expensive it is to move the neighborhood of one node onto the neighborhood of its neighbor. Positive curvature: overlapping neighborhoods, community interior. Negative curvature: disjoint neighborhoods, a bridge or bottleneck. In Mind Palace terms, strongly negative edges are candidate "connecting ideas" between otherwise separate regions of thought.

**Valid when:** the probability measure placed on neighborhoods is defensible (uniform vs. weight-proportional changes results), and edge weights function as meaningful distances. Also computationally honest only at your corpus scale — optimal transport per edge is expensive, fine on an M2 Max at personal-corpus size.

**Not earning its place if:** edges ranked most-negative do not receive "surprising but grounded" verdicts at a higher rate than random cross-cluster edges, or the ranking is unstable under small graph perturbations (add five notes, top-ten bridge list reshuffles completely). Bridge-surfacing is a Dreamer output category, so this falsifier runs through the normal verdict flow.

---

## 8. Forman-Ricci curvature

**Measures:** the same qualitative signal as Ollivier — bridge vs. interior — via a purely combinatorial formula (degrees and weights, no optimal transport). It is a cheap proxy, useful as a pre-filter or at scales where Ollivier is too slow.

**Valid when:** used as a ranking heuristic, not as a quantity with geometric meaning. Its absolute values mean little; its ordering correlates with Ollivier's on most graphs.

**Not earning its place if:** its ranking disagrees substantially with Ollivier's on your corpus *and* the disagreement propagates downstream. Then carrying both creates confusion rather than robustness — keep Ollivier (the principled one) at your scale and drop Forman, since the only argument for Forman is compute you don't need to save.

---

## 9. Persistent homology

**Measures:** multiscale topological features — connected components (H₀) and loops (H₁) — that survive across a filtration, typically thresholding edges by weight. A persistent H₁ feature is a circuit of ideas that keeps reappearing across resolution scales: a cycle of notes each related to the next with no chord collapsing it.

**Valid when:** the filtration parameter is meaningful — sweeping an edge-weight threshold must correspond to something interpretable like "confidence in the relation." Also assumes long persistence implies significance, which is contested even within the TDA field.

**Not earning its place if:** (a) persistent loops, when surfaced, do not correspond to circuits of ideas you can name and recognize, or (b) the persistence diagram of your corpus is statistically indistinguishable from diagrams of degree-matched random graphs. The second test is the sharper one and is easy to run: generate configuration-model nulls, compare diagrams via bottleneck distance. If your corpus's topology isn't distinguishable from noise, homology is measuring the null model, not your mind.

---

## 10. Stochastic block models

**Measures:** latent community structure under a generative story: nodes belong to blocks, edge probability depends only on block membership. Unlike spectral clustering, SBM gives you model selection — a principled answer to "how many communities" — and can find non-assortative structure (e.g., a hub block) that spectral methods miss.

**Valid when:** edges are conditionally independent given block assignments (violated by transitivity, which real note graphs have in abundance — mitigated but not eliminated by degree-corrected variants), and you use degree correction, since raw SBM on heterogeneous-degree graphs mostly recovers degree, not community.

**Not earning its place if:** inferred blocks do not beat Laplacian clusters on verdicts (two clusterers must fight for the slot; keep the winner), or model selection persistently returns trivial answers (one block, or n blocks) on your corpus, indicating the generative assumptions don't fit.

---

## 11. Noisy-OR message passing

**Measures:** belief propagation through a causal structure where multiple independent causes each suffice, unreliably, to produce an effect. It gives the Dreamer calibrated-in-principle posteriors: "given these supporting notes, belief in this synthesized claim is p."

**Valid when:** causes are genuinely independent (the noisy-OR factorization assumes no interaction between causes — two notes derived from the same source violate this and inflate confidence), and the graph is tree-like enough for loopy BP to converge to something meaningful.

**Not earning its place if:** (a) BP fails to converge on real corpus subgraphs, or (b) the posteriors are uncalibrated against outcomes — among claims scored ~0.8, materially more or fewer than ~80% earn positive verdicts. Calibration is checkable directly from the Track L verdict store once it accumulates; a reliability diagram is one plot. Uncalibrated confidence is worse than no confidence, because it is confidence theater on top of a system whose whole thesis is provable belief.

---

## 12. Diffusion clustering

**Measures:** community structure via heat flow — nodes that heat reaches together at diffusion time *t* belong together. The scale parameter *t* is the point: small *t* sees fine structure, large *t* sees coarse structure.

**Valid when:** the choice of *t* (or the range swept) is justified rather than defaulted, and the same affinity assumptions as §2 hold, since diffusion runs on the same Laplacian.

**Not earning its place if:** cluster assignments are unstable across the reasonable range of *t* — if adjacent scales give unrelated partitions, the corpus has no diffusion-scale structure and the clusterer is reporting parameter choice. Stability across a *t*-window is the standard sanity check and is cheap.

---

## 13. Spectral bridging

**Measures:** nodes or edges positioned between clusters in the spectral embedding — items whose eigenvector coordinates sit near cluster boundaries. Candidate "connective tissue" notes, complementary to curvature-based bridge detection (§7): spectral bridging is a global-embedding view, curvature is a local-transport view.

**Valid when:** the embedding dimensions used are the informative ones (eigengap-justified), and boundary position in embedding space actually reflects semantic betweenness rather than noise in low eigenvectors.

**Not earning its place if:** its bridge candidates and Ollivier-Ricci's bridge candidates are (a) nearly identical — then one is redundant, keep one — or (b) completely disjoint with no verdict-rate difference from random — then neither view is finding real bridges and both need scrutiny. The interesting outcome is partial overlap where each method's exclusive finds still earn good verdicts; that is the result that justifies keeping both.

---

## How to use this document

Once Track L is live, each falsifier above maps to one of three mechanisms, all of which already exist or are specified:

1. **Verdict-rate comparisons** (§2, §4, §7, §10, §13) — the instrument's outputs are Dreamer outputs; the verdict store measures them against the baseline for free.
2. **Ablations and nulls** (§1, §6, §9, plus the §0 perturbation tests) — one-off scripted experiments against the frozen control corpus, each an afternoon of work, run once and recorded.
3. **Internal consistency checks** (§3, §5, §8, §11, §12) — convergence, stability, calibration, degeneracy audits; candidates for the weekly digest so drift is caught rather than discovered.

The honest end state is not "all thirteen survive." Some of these should die. A version of this document a year from now with three entries struck through and the ablation results linked is stronger evidence of load-bearing formalism than all thirteen surviving unexamined.
