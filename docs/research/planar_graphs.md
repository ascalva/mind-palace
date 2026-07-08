---
type: research
id: rn-planar_graphs
status: draft
created: 2026-07-03
updated: 2026-07-03
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Executive Summary  

Planar graphs – graphs drawable in the plane without edge crossings – have a rich theory (e.g. Kuratowski’s and Wagner’s theorems) and many special properties.  Equivalently, a graph is planar if it can be *embedded* on a 2D surface (sphere) so edges meet only at common endpoints.  Extending this, any graph can be embedded without crossings in 3D (or higher) space.  In practice one can **project** a 3D (or higher-D) embedding to 2D to attempt a crossing-free drawing: if the graph is truly nonplanar, some crossings will appear.  Graph drawing research therefore studies *planarization* and crossing minimization: one finds a large planar subgraph, draws it, and then re-inserts the remaining edges (often via dummy vertices).  

For knowledge graphs (KGs) – typically directed, labeled graphs (RDF triples or property graphs) – the planar viewpoint can aid **visualization** but rarely without sacrifice.  Real-world KGs are usually nonplanar and dense, so forcing planarity often loses edges or clusters nodes, obscuring semantics.  In KG visualization, hybrid layouts (hierarchical for ontologies, force-directed with edge-bundling for instance data) are more common.  Planar layouts *do* preserve basic graph properties (adjacency, connectivity, cycles) exactly, but forcing planarity (e.g. by dropping edges) can break semantic relationships.  On the other hand, planar (or low-genus) embeddings allow specialized algorithms (graph separators, linear-time shortest-path, flow, etc.), which outperform general-graph algorithms. 

**In summary:** any planar graph can be seen as a projection of a 3D embedding, but simply “lifting” a nonplanar KG to 3D rarely yields a clean 2D view without crossings.  Practical KG visualization therefore uses mixed techniques: planar embeddings where natural (e.g. tree hierarchies), plus force-directed/spectral layouts, edge bundling, and subgraph filtering for larger, cyclic parts.  We recommend using planar methods for small or schema-level subgraphs (e.g. ontologies) and layered or clustered layouts for large KGs, leveraging specialized tools (e.g. yEd, Gephi, GraphViz) and possibly user-driven filtering rather than forcing global planarity.  

# Definitions and Theory  

- **Planar graph:** A graph is *planar* if its vertices can be placed in the Euclidean plane and its edges drawn as curves meeting only at common endpoints.  Equivalently, it admits a drawing with **no edge crossings**.  Fáry’s theorem guarantees straight-line edges suffice for a planar drawing of any planar graph.  Planar graphs satisfy Euler’s formula $V - E + F = 2$ (for a connected embedding) and have at most $3V-6$ edges (simple graphs).  **Kuratowski’s theorem** states that a finite graph is planar iff it contains no subgraph that is a subdivision of $K_5$ or $K_{3,3}$.  Equivalently (Wagner’s theorem), no minor is $K_5$ or $K_{3,3}$.  These are the only minimal “obstructions” to planarity.  

- **Graph embedding:** More generally, embedding a graph on a *surface* means drawing it so edges intersect only at shared endpoints.  A *topological embedding* fixes only intersection constraints (edges as arcs); a *geometric embedding* typically means vertices at fixed positions and straight edges.  Planarity is embedding on a sphere or plane (genus 0).  A graph’s **(orientable) genus** is the minimum genus $g$ of a surface on which it can embed; planar graphs have genus 0.  For instance, *toroidal* graphs embed on a torus ($g=1$) without crossings.  

- **Higher dimensions:** In $3$-D ($\mathbb R^3$), *any* finite graph can be embedded without crossings.  Thus one can always “lift” a graph to 3D to avoid crossings, but some crossings will reappear under projection back to 2D.  (No simple criterion like Kuratowski’s distinguishes “3D-planar” graphs, since all graphs qualify.)  Conversely, viewing a planar graph as the intersection of 3D cell complexes (3-sphere triangulations or CW-complexes) is conceptually possible but rarely used in practice.  

- **Graph minors:** A graph $H$ is a *minor* of $G$ if $H$ can be obtained by deleting and contracting edges.  Since planarity is minor-closed, Robertson–Seymour tells us exactly two forbidden minors ($K_5,K_{3,3}$) characterize planarity.  **Topological minors** allow subdividing edges instead of contracting.  In graph drawing, the notion of an *immersion minor* arises: planarization of a nonplanar drawing (replace each crossing by a dummy vertex) yields an immersion of the original graph.  For example, after planarizing, we get a planar graph that is an immersion minor of the original.  

- **Graph analogues:** Graph theory also studies **simplicial complexes** (higher-dimensional generalizations of graphs) and **hypergraphs** (edges connecting >2 vertices).  A graph is a 1-dimensional simplicial complex; one could consider embedding these in space.  Hypergraphs can sometimes be drawn by replacing each hyperedge with a region or introducing a node per hyperedge.  These do not in general correspond directly to planar-graph embeddings.  There is no simple “planarity” analog for hypergraphs, except by converting them to bipartite incidence graphs and then embedding that graph (often nonplanar).  

# Algorithms and Methods  

- **Planarity testing and embedding:**  There are linear-time algorithms to test planarity and, if planar, compute an embedding (e.g. Hopcroft–Tarjan, Boyer–Myrvold).  These yield a cyclic rotation system of edges at each vertex.  From that, one can draw the graph without crossings (e.g. using Tutte’s barycentric method for straight-line drawings).  Many libraries implement this (OGDF’s `Planarity` module, LEDA, Boost Graph, etc.).  

- **Planar subgraph / Planarization:**  For nonplanar graphs, **planarization heuristics** are used.  A common approach (the *planarization method*) is:  
  1. **Extract a large planar subgraph** (preferably maximal).  Since finding a maximum planar subgraph is NP-hard, heuristics or greedy algorithms are used (e.g. repeatedly remove or avoid the edge that causes a crossing).  
  2. **Draw the planar subgraph** with a planar layout algorithm.  
  3. **Re-insert removed edges** one by one.  When adding each edge, replace any crossings by introducing a “dummy” vertex (thus maintaining planarity). After inserting all edges, one has a planarized (auxiliary) graph.  
  4. **Remove dummy vertices** or highlight crossing points as needed (edge rerouting may be done in final layout).  

  This planarization yields a drawing with relatively few crossings.  In practice, graph-drawing systems (e.g. OGDF, GraphViz’s “neato” with edge-cross minimization) use variations of this method.  The planar subgraph step dominates: exact solution is hard, but greedy or iterative improvement can handle medium-sized graphs (up to thousands of nodes) reasonably.  

- **Graph drawing algorithms:** Beyond pure planarity, many generic layout methods exist.  **Force-directed** algorithms (Fruchterman–Reingold, Barnes–Hut, ForceAtlas2) treat edges as springs and nodes as repelling masses, converging to low-energy layouts. These are $O(n^2)$ or $O(n\log n)$ per iteration but can handle large graphs with approximation. They do *not* guarantee planarity; crossings remain if the graph is nonplanar. **Spectral methods** project the graph using eigenvectors of Laplacians (O($n^3$) eigen-computation or faster approximations). These aim to preserve distances or connectivity in the layout. **Layered/hierarchical** layouts (Sugiyama) impose a direction (e.g. ontologies) and order nodes in ranks, minimizing crossings via heuristic layer-by-layer refinement. **Orthogonal** layouts route edges with horizontal/vertical segments (common in ER diagrams). **Circular and radial** layouts place nodes on concentric circles or around a center (often used for ego networks). Graph drawing libraries (yFiles, GraphViz, Tulip, Gephi) implement these. For example, yFiles offers *hierarchical* (for trees/ontologies), *organic* (force-based) and edge-bundling.  

- **Edge bundling and routing:** To reduce visual clutter from many edges, **edge bundling** clusters edges (especially those with similar routes) into curved bundles.  Bundling can create the illusion of planarity by hiding individual crossings inside bundles. It preserves connectivity but not individual adjacency. **Edge routing** (polyline routing around nodes) can also avoid visual overlap but is usually orthogonal to planarity: it may still cross edges or nodes.  

- **Dimensionality reduction:** Sometimes graph drawing is done by embedding nodes in low-dimensional space (via multidimensional scaling, t-SNE, node embeddings etc.) and then plotting in 2D. These methods (often used in ML for KGs) preserve proximity metrics but ignore graph topology explicitly; they do not ensure planarity and may distort connectivity.  

- **Graph genus algorithms:** More advanced algorithms determine the exact genus embedding (NP-hard in general).  Fixed-parameter tractable algorithms exist for small genus, but these are seldom needed for visualization.  If one permits embedding on a torus or double-torus (genus $g>0$ surface), some nonplanar graphs become “planar” on that surface.  For instance, $K_{3,3}$ embeds on a torus without crossing, making it *genus-1*.  However, projecting a toroidal embedding into 2D introduces crossings (e.g. cut the torus).  

- **Graph minor and planarization theory:** The Robertson–Seymour Graph Minors theory implies that any minor-closed family (like planar graphs) is characterized by forbidden minors.  In graph drawing, one approach is to identify Kuratowski subgraphs (forbidden minors) to guide edge removal or planarity testing.  Indeed, OGDF’s *ExtractKuratowskis* class can find many Kuratowski subdivisions.  Once small obstructions are removed, the graph becomes planar.  

- **Complexity:** Planarity testing is $O(n)$.  Finding largest planar subgraph is NP-hard; heuristics are fast in practice (often $O(n\log n)$ or $O(m\log n)$ for $n$ nodes, $m$ edges). Force-directed layouts typically cost $O(n^2)$ per iteration (can be improved to $O(n \log n)$ with Barnes-Hut). Spectral layouts cost $O(n^3)$ in worst case.  Overall, drawing a graph with many nodes (e.g. $>10^4$) is challenging; one often uses multilevel or sampling techniques.  

- **Tools & Libraries:** Many tools implement these methods.  **OGDF** (Open Graph Drawing Framework) provides planarity testing, planar embedding, planar subgraph extraction, crossing minimization, and various layout algorithms.  **GraphViz** offers layouts (dot/hierarchical, neato/spring, sfdp/large-spring). **yFiles/yEd** (commercial) and **Gephi** (open) provide rich GUI layout (hierarchical, force, circular).  For KGs specifically, tools like **Cytoscape** and **GraphDB Workbench** offer built-in drawing (mostly force-directed).  Graph databases (Neo4j, Virtuoso, etc.) often rely on such libraries for visual exploration.  For hypergraphs or RDF triple visualization, tools may introduce intermediate nodes for predicates or use custom schemes (e.g. reification nodes), but that is outside pure planar embedding theory.  

```mermaid
graph LR
    A[Input Graph (KG)] --> B{Is graph planar?}
    B -->|Yes| C[Planar embed & draw]
    B -->|No| D[Extract large planar subgraph]
    D --> E[Insert remaining edges as dummy vertices]
    C --> F[Apply planar drawing algorithm]
    E --> F
    F --> G[Final layout (remove dummies)]
```

# Applications to Knowledge Graphs  

Knowledge graphs (KGs) are graphs of entities and relations (often RDF triples or property graphs with labels and directions).  They are rarely planar due to high connectivity, multi-relations, and cycles. Nevertheless, planarization concepts can inform their study:

- **Graph structure and semantics:** KGs often encode ontologies (class hierarchies, taxonomies) plus instance data.  Class hierarchies ($rdfs:subClassOf$, part-of hierarchies) are typically trees or DAGs, which *are* planar.  Ontology editors use tree or layered layouts for these (e.g. Protégé’s class hierarchy view).  Instance graphs (entities linked by many predicates) are usually nonplanar.  Also, RDF allows parallel edges (multiple predicates between same two entities) and hyper-relations (n-ary facts), which break the simple graph model.  In practice, one often represent multi-edges as separate labeled edges or by reification (introducing nodes for complex relations), further complicating embedding.  

- **Visualization:** Planar layouts (straight or curved) give clutter-free views if applicable.  For KGs, schema graphs (ontology) can use planar hierarchical layouts (Preserving tree structure exactly).  For large instance graphs, strict planarity is unachievable; instead, visualization tools use force-directed or *organic* layouts with **edge bundling** or filtering to manage crossings.  For example, yFiles recommends: *hierarchic layout for ontology (schema)*, and *organic layout with edge bundling for entity-relation exploration*.  Figure layouts in the literature on KG viz often show dense meshes with many crossings; there’s no known effective way to make a complex KG fully planar without hiding much information.  

- **Querying and reasoning:** If a KG happened to be planar (or near-planar), some graph algorithms could be faster.  For example, planar graphs admit small separators ($O(\sqrt{n})$) and some linear or near-linear time solutions for shortest-paths, max-flow, etc..  However, SPARQL engines and KG reasoners do not exploit planarity; they use general graph/triple-store indexing.  Query performance typically depends on index structures, distribution of predicates, and join algorithms, not on global planarity.  Some specialized RDF benchmarks (e.g. geo-data) use near-planar graphs (road networks), where query planning can exploit locality.  In general, though, KGs do not assume planarity, so the theoretical benefits (like [58]) remain unused.  

- **Preserving properties:** A planar embedding preserves graph theoretic properties: adjacency, connectivity, cycles, distances (as graph), etc., are all exactly the same in the abstract graph, just laid out without crossings.  But any **projection** or dimensionality-reduction embedding (e.g. spectral) may distort distances (shortest paths may not look short geometrically) and do not preserve labels/semantics.  Planarization (removing edges) or bundling clusters edges, which can break semantics: two entities might appear adjacent only via a bundle rather than a direct edge, obscuring which predicate linked them.  Moreover, many KG semantics rely on edge labels and directions: planar drawing algorithms ignore labels and directionality, so one often needs to visually annotate or color edges by predicate, as yFiles suggests.  

- **Practical KG graph layout:** Current best practices for KGs avoid enforcing planarity.  Instead, they **segment** the graph: show a backbone (ontology tree) with one layout, and allow user-driven expansion of subgraphs (ego-networks, predicate clusters).  Tools like Neo4j Browser and GraphDB Visualizer do this via BFS expansions.  Edge types (predicate namespaces) may be color-coded or handled as separate views.  This multi-view approach acknowledges that a global planar embedding of the full KG is both impossible and not necessary for insight.  

# Pros and Cons  

**Advantages of planar/low-dimensional view:** 
- *Readability:* Planar drawings (or drawings with few crossings) are aesthetically clearer.  Humans find it easier to follow edges without crossing confusions.  
- *Preserves graph properties:* A true planar embedding (with no removed edges) fully preserves adjacency, connectivity, cycles, etc.  Thus shortest-path distance in the graph equals geodesic distance in the drawn graph (ignoring coordinate scaling).  
- *Algorithmic benefits (in theory):* As noted, planar graphs allow faster graph algorithms (shortest path, flows, matching) in $O(n\log n)$ or even linear time.  Also, planar graphs have small separators and bounded treewidth, enabling efficient divide-and-conquer.  In theory, if a KG or query graph were planar, one could exploit these for faster inference or query planning.  

**Drawbacks and limitations:** 
- *Loss of information:* Enforcing planarity usually requires dropping edges or merging them.  For KGs, every edge carries meaning (a predicate). Removing or bundling edges destroys the explicit semantics.  
- *Computational hardness:* Finding an optimal planarization (minimizing crossings) is NP-hard.  Heuristics may still leave many crossings if the graph is dense.  Large KGs (millions of nodes/edges) are beyond current graph-drawing scales anyway, so planarity methods apply only to small subgraphs.  
- *Nonplanar realities:* Many KGs are inherently nonplanar (complete subgraphs among related entities, multi-relations).  Analogies like “embedding in higher dimensions” don’t alleviate this: while any graph is 3D-planar, the 2D projection will usually show crossings except by careful viewpoint selection.  And viewpoint-dependent 3D rendering has its own issues (perspective distortion, occlusion).  
- *Edge crossings vs bundling:* Some modern graph-drawing research suggests allowing controlled crossings (beyond-planar graph classes, RAC drawings with right-angle crossings) or bundling multiple edges into meta-edges to reduce clutter.  These techniques accept some crossings but make them uniform or hidden.  However, theoretical results for these are limited, and standard KG tools do not yet exploit beyond-planar constraints.  

**Impact on semantics:** Planarity methods treat the KG as an abstract graph, ignoring labels/directions.  So while geometric properties may be nice, logical semantics (RDF schema, inference rules) are not preserved in the geometry.  For instance, inferencing (transitive closure) has no equivalent in the planar layout – it is purely combinatorial.  A planar drawing might spatially cluster nodes but won’t show, say, that one path implies another fact unless annotated.  

# Recommendations  

- **Use planar embeddings for small, tree-like subgraphs:**  If the KG or a subgraph is known to be (almost) planar – for example, a class hierarchy or a carefully filtered ego-network – using a planar or hierarchical layout yields very clean visuals.  For tree/DAG (acyclic) portions, hierarchical/orthogonal drawings (which are planar by design) work well.  Tools: GraphViz `dot`, yEd’s hierarchical layout, or specialized ontology viewers.  

- **For general graphs, focus on clustering and bundling:**  Recognize that large KGs won’t be planar.  Instead, cluster nodes by type, use force-directed layout for global structure, and apply edge bundling or filtering to reduce perceived crossings.  For example, color edges by predicate and bundle edges of the same predicate or direction to highlight patterns.  

- **Exploit multiple views:**  Split the KG into views: a schema view (classes and their relations) which is small and planar, and an instance view (data), which is large and cyclic.  Show schemas with planar/tree layouts; show instances with organic or radial layouts.  Allow interactive expansion: start from one or few nodes and reveal neighbors (ego-centric layout).  

- **Leverage planar subgraph methods for readability:**  In static diagrams (e.g. figure in a paper), one can apply planarization: remove some less important edges or draw them curved to the side to reduce crossings.  Algorithms: use planar subgraph extraction heuristics (implemented in libraries like OGDF or LEDA) to get a crossing-free backbone, then add other edges with minimal crossings.  This sacrifices some edges but retains the main structure.  

- **Preserve semantics with labeling and coloring:**  Whenever using a graph layout, always encode semantics (node and edge types) with shapes, colors, or icons.  Many KG tools will render RDF predicates as colored edges or separate shapes – do not rely on spatial layout alone to convey meaning.  

- **Choose the right tools:**  For prototype and research, use open libraries like OGDF (C++), GraphViz, or networkx+Matplotlib.  For interactive KG exploration, use graph-DB specific tools: Neo4j Bloom, GraphDB’s workbench, yEd Live, or Cytoscape.  These are not planar-specific but offer good defaults.  Some specialized tools allow plugin of planarization: e.g. Gephi has a Planar Layout plugin.  

- **Don’t force global planarity:**  Unless the KG is small, do not attempt to draw the entire graph without crossings; it will be unreadable or misleading.  Instead, rely on search, navigation, and filtering.  If an application *requires* a planar representation (e.g. mapping data to a planar embedding for a specific algorithm), be aware you will need to add artificial constraints (dummy nodes, multiple layers, etc.) and lose direct interpretability.  

Below is a comparison of common methods and tools:

| **Method / Algorithm**      | **Type**      | **Complexity**               | **Best for**                 | **Preserves**             | **Notes**                          |
|-----------------------------|---------------|------------------------------|------------------------------|---------------------------|------------------------------------|
| Planarity test (Hopcroft–Tarjan)  | Testing      | $O(n)$                    | Any graph planar check       | N/A (just decision)      | Builds embedding if planar.        |
| Planar embedding (Straight-line) | Drawing      | $O(n)$                    | Planar graphs (≤10^5 nodes)   | Graph structure, adjacencies | Uses Fáry’s theorem.              |
| Maximal planar subgraph (heuristic) | Planarization | NP-hard (heuristic $O(m\log n)$) | Sparse subgraph (100–1000 nodes) | Subgraph edges, partial adj. | Removes some edges to planarize.  |
| Planarization + reinsertion | Crossing minimization | Heuristic (depends on layout) | Medium graphs (<10k nodes) | Original nodes; some adjacency lost | Best crossing reduction method.    |
| Force-directed (e.g. Fruchterman-Reingold) | Layout        | $O(n^2)$ per iteration (or $n\log n$) | Any graph (up to ~10^4 nodes) | Adjacency (~distance) | Preserves connectivity well, many crossings.  |
| Spectral layout (Laplacian eigenvectors) | Layout | $O(n^3)$ (dense) or sparse solvers | Medium graphs (few thousand) | Global distances (approx) | May cluster by connectivity, edges can cross. |
| Hierarchical/Sugiyama       | Layout        | $O(n+m)$ (layers) + $O(k)$ crossing heuristics | DAGs, trees (planar)         | Hierarchy, directed edges | Minimizes crossings in layered view. |
| Radial / Circular           | Layout        | $O(n+m)$                     | Ego-nets, cycles             | Highlight central node connectivity | Cycles appear circular, edges cross inward. |
| Edge bundling              | Post-processing | $O(m \log m)$ (clustering)  | Dense networks visualization | Connectivity (clustered)  | Reduces visual clutter, merges adjacency. |
| Dimensionality reduction (t-SNE, PCA) | Embedding      | $O(n^2)$ (t-SNE) or $O(n^3)$ (PCA) | Feature embedding of nodes   | Distances in embedding    | No guarantee on graph adjacency.   |
| **Tool / Library**         | **Type**      | **Inputs**                   | **Features**                 | **Planarity support**     | **Notes**                         |
| OGDF (C++ library)         | Library       | Graph (adjacency list)       | Planarity test/embed, planar subgraph, force layout | Yes (planarity module)    | Extensive algorithms, high-performance. |
| GraphViz (dot, neato, sfdp)| Layout tool   | Graph in DOT format          | Hierarchic (dot), spring (neato, fdp), multi-scale (sfdp) | No explicit planar mode    | Widely used for graphs; dot enforces DAG layering. |
| yFiles / yEd (desktop)     | GUI toolkit   | Graph (nodes/edges)         | Hierarchic, organic, circular + edge bundling | User-selectable          | Commercial but free yEd; rich interactivity. |
| Gephi (desktop)            | GUI tool      | Graph (CSV/GraphML etc)      | ForceAtlas2, hierarchical, circular | No (but has plug-ins)    | Good for large networks, clustering analysis. |
| Cytoscape / Linkurious     | GUI (networks) | Graph data                  | Force-directed, edge bundling plugin | No (focus on biology/graphs) | Often used in semantic web visualization. |
| Neo4j Browser / Bloom      | DB viewer     | Property graph (Cypher)      | Force layouts, schema view   | No                       | Built-in for exploring KG, not custom layout. |
| GraphDB Visualiser         | SPARQL UI     | RDF triples                  | Force-directed view of RDF   | No                       | Limited scale, basic. |

 >*Table: Comparison of graph-planarization and drawing methods, and tools. "Preserves semantics?" is understood as preserving connectivity/graph structure (not RDF logic).*

---

## Review addendum — 2026-07-03

Reviewer: Claude (design-partner session). Scope: errata for the compiled text above, framing corrections, instrument candidates in field-guide clause form, parked decisions with re-entry conditions. Compiled text retained unmodified above this line.

### Errata

1. **Immersion direction is reversed.** Planarizing a drawing (replacing crossings with dummy vertices) produces a planar graph P that *contains* the original G as an immersion: each edge of G becomes an edge-disjoint path through dummy vertices of P. G is the immersion minor of P, not the reverse.
2. **"No Kuratowski-style criterion in 3D" is misleading.** Mere embeddability in R³ is trivial: place vertices on the moment curve (t, t², t³); no four points are coplanar, so straight edges never cross. The nontrivial 3D notions do have exact characterizations: linkless embeddability is characterized by the seven forbidden minors of the Petersen family (Robertson–Seymour–Thomas); knotless embeddability has a finite but currently unknown obstruction set (K₇ is intrinsically knotted, Conway–Gordon).
3. **Spectral cost overstated for the sparse regime.** O(n³) applies to dense full eigendecomposition. Lanczos-type iteration returns the k extreme eigenpairs in ≈ O(k·m) on sparse graphs; that is the regime any spine computation runs in.
4. **Mermaid block will not parse.** Parenthesized node labels (`A[Input Graph (KG)]`) are a syntax error; quote the labels or drop the parentheses.

### Framing corrections

- **Dimension is a property of a realization, not of a graph.** A graph is combinatorial. ρ: V → R^d is a choice; "projecting a graph" means post-composing a realization with linear M: R^d → R^(d−n). Consequently |E|/|V| is invariant under any projection — density claims about projections are category errors. What degrades is metric fidelity and injectivity of the drawing, never the combinatorics.
- **Planarity is the existence direction, not the lifting direction.** Lifting to R³ is free and contentless (moment curve). G is planar iff *some* 3D realization admits *some* projection direction whose image is crossing-free. Generic projections of generic realizations create crossings; planarity is the escape hatch, not the starting point.
- **Ingestion embeddings are not projections.** The encoder maps a discrete domain (token sequences) carrying no canonical metric into a fixed R^n; it *manufactures* the geometry rather than distorting a pre-existing one. The loss model is therefore not (1±ε) metric distortion but: (a) non-injectivity — pigeonhole over an unbounded discrete domain into a bounded-precision fixed codomain; (b) selectivity — the training objective decides which distinctions survive (surface form mostly does not; negation notoriously often does not). Consequence for the store: cosine similarity is a retrieval prior, not a semantic judgment; truth-functional content lives in typed edges and provenance, never in vector proximity. Keep the two loss stages in separate accounting: encoder loss (task-relative; quantifiable only against a chosen reference relation) and post-hoc compression loss (metric; JL-governed; quantifiable).

### What earns instrument status (field-guide clauses)

1. **Spectral incompressibility.**
   - *Measures:* per-stratum lower bound on Euclidean embedding distortion via λ₂ (Linial–London–Rabinovich: constant-degree expanders require Ω(log n) distortion in any Euclidean embedding); JL dimension budget k = O(log n / ε²) once tolerance ε is fixed (Larsen–Nelson: optimal, independent of source dimension and of graph structure).
   - *Valid when:* the consumer reads pairwise distances (retrieval plane). Note the ANN index's product quantization is already a lossy projection spending the same distortion budget.
   - *Falsified by:* recall@k vs. target-dimension curves failing to stratify by spectral gap — if large-gap strata compress as gracefully as small-gap ones, the certificate is decoration.

2. **Curvature-matched embedding targets.**
   - *Measures:* fit between a stratum's Gromov δ-hyperbolicity / Ricci profile and target-space curvature. Prediction: hyperbolic target (Sarkar: trees embed in H² with distortion 1+ε) beats Euclidean (Bourgain: trees need Ω(√log log n) in ℓ₂) at matched dimension on tree-like strata; mixed-curvature products for heterogeneous strata.
   - *Valid when:* δ is small relative to diameter and the curvature statistics survive the perturbation-stability filter.
   - *Falsified by:* no distortion or retrieval advantage for the curvature-matched target on strata the instrument classified as tree-like.

3. **Constrained shortest hyperpath ("train of thought").**
   - *Measures:* minimum-cost derivation from premise set to conclusion. Semiring choices: −log(confidence) weights turn multiplicative chain plausibility into (min,+) — plain Dijkstra recovers the maximum-likelihood chain; (max,min) recovers weakest-link. Type admissibility via automaton–graph product (regular-language-constrained shortest path; PRA lineage in KG reasoning). Conjunctive premises (A ∧ B ⟹ C) are B-hyperedges: shortest B-hyperpath via Gallo–Longo–Pallottino's SBT procedure, polynomial for monotone costs. k diverse chains for owner review via Yen; bidirectional search since the conclusion node is known.
   - *Valid when:* edge confidences are approximately independent along a chain — the exact assumption the noisy-OR machinery exists to repair; a validity clause, not a footnote — and cost functions are monotone.
   - *Falsified by:* Track L verdicts rating surfaced chains no better than length-matched random type-valid chains.

### Parked, with re-entry conditions

- **Crossing number / genus / planar-separator algorithms.** Re-enter only if some stratum measures near-planar (m ≤ 3n − 6 on its skeleton and Boyer–Myrvold passes). Not expected to fire on this corpus.
- **van Kampen–Flores / simplicial-complex embeddability.** (Any k-complex embeds in R^(2k+1); the k-skeleton of the (2k+2)-simplex does not embed in R^(2k); K₅ non-planarity is the k = 1 case.) No consumer. Aesthetic only.
- **Four-color theorem.** No consumer; the complex is not planar. Adjacent live idea if ever needed: general graph coloring as conflict scheduling for ingest/trough parallelism. Cultural footnote only: Appel–Haken → Gonthier is the origin story of attested machine-checked computation.
- **Ollivier–Ricci unearthing.** Status: the curvature instrument is specified but dormant; do not implement ahead of the stream that can falsify it. *Re-entry condition:* Track L shadow runner live and verdict taxonomy ratified. *Re-entry experiment:* surface stability-filtered top-k most-negative-curvature edges as a candidate stream beside the Dreamer's existing candidates; blind adjudication; compare verdict hit rate against degree- and length-matched random bridges. No advantage over matched controls → record "no signal at this scale," keep modular. *Design knobs to fix at build time:* α (walk laziness); treatment of direction and edge types in the neighbor measures (symmetrization vs. directed W₁). *Cost note:* exact per-edge W₁ is an LP in the local degrees, ≈ O(d³) per edge, Sinkhorn if needed; feasible at corpus scale on local hardware — compute is not the blocker, validation is. *Interim option:* Forman–Ricci (combinatorial, ≈ O(1) per edge given degree and triangle counts) as a smoke-test baseline and descriptive input to the target-geometry question; pay the optimal-transport cost only where the cheap signal warrants.
  

