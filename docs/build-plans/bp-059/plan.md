---
type: build-plan
id: bp-059
alias: sigma-star-mst
status: ready
design_ref:
  - docs/design-notes/connectivity-instruments.md   # RATIFIED — CN-1 (the (σ,t,cut) index discipline) + CN-2 (σ*/MST, the keystone)
contract: builder
write_scope:
  - eval/harness/connectivity.py
  - tests/unit/test_connectivity.py
  - tests/quality/test_connectivity_sigma_star.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/global-event-clock.md                       # GC-3 certified cuts (the cut index)
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md      # the FibersEvidence pinning discipline this family copies
  - docs/findings/finding-0096.md                                  # golden_recall saturation — DO NOT assume a σ-signal in a recall objective
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CN-2: σ*, the abstraction ultrametric, via one maximum spanning tree per cut

## 0. Mode & provenance
Graduated from RATIFIED `dn-connectivity-instruments` CN-1 + CN-2 (the keystone of the tranche;
no upstream item dependency). Investigation & planning produced this from a single context holding
the whole note + the six built substrate modules; implementation proceeds item-by-item on owner
approval. Separate authority-to-act (owner: "build out what we have already designed", 2026-07-17)
from the readiness blessing (owner-only `proposed → ready`; no agent flips it). **This plan also
lays the shared CN-1 scaffolding (the ConnIndex object + the graph-at-cut builder + the evidence
pin) that bp-060/061/062 import** — get its surface right; it is load-bearing for the family.

## 1. Objective
`eval/harness/connectivity.py`: build one **maximum spanning tree** over the σ-graph at the latest
certified cut and read off, for any pair, `σ*(A,B) = sup{σ : A ∼ B in G_σ}` (the maximin-cosine
path value) **and** its realizing MST chain — grid-relative, cut-indexed, model-free, writing only
keyed eval readings.

## 2. Context manifest (read in order)
1. `docs/design-notes/connectivity-instruments.md` — WHOLE. CN-1 (§2.1: the (σ,t,cut) index
   signature discipline — σ* declares `(σ-grid, cut)`, no t), CN-2 (§2.2: σ* def, MST equivalence,
   grid-relativity, "not connected within grid", the two falsifiers), §3 item-1 laws, §4 parked
   (conductance grain / cut lattice), §Cross-references (the code map).
2. `core/dreaming/graph.py:22-75` — `MirrorGraph` (frozen: `notes`, `sim`, `sigma`, `_adj`);
   `build(cls, view, *, sigma)` (**no cut arg** — see §3 Q1); `sim` is the full cosine matrix;
   `neighbors`/`degree`/`digest`/`title`. The σ-graph builder this instrument sweeps.
3. `core/dreaming/cluster.py:22-80` — `NoteVector` (`digest`,`title`,`vector`), `note_centroids`,
   `similarity_matrix` (pairwise cosine over L2-normed centroids; the edge weights are `sim[i,j]`).
4. `core/mirror.py:66-105` — `MirrorView` (Invariant-6 firewall; `project(source)`, `rows()`);
   **has no cut-restriction surface** (the grounding gap resolved in §3/§4).
5. `core/temporal/spine.py:216-229, 585-870` — `CertifiedCut` (frozen, hashable: `frontier`,
   `certificates`, `evidence`); `Spine.derive`, `cut_at(*, strata)` (raises `CutCertificateError`
   if uncertified), `downset(cut)`, `crossing_edges(cut)` (must be `[]`). The cut index source.
6. `eval/harness/fibers.py:95-133, 178-189` — `FibersEvidence` (`grid`, `base_fingerprint`,
   `lever_registry_hash`; `as_ref()`), `fibers_spec_hash`, `_grid_descriptor`. **Copy this
   evidence-pinning pattern verbatim** — grid + fingerprints in every reading, fail-closed on drift.
7. `eval/harness/store.py:47-100` — `EvalKey`, `Reading`, `EvalResultsStore.put` (idempotent-by-key,
   never overwrites). The write target.

## 3. Investigation & grounding
- **Q1 — Can we build the σ-graph *at a certified cut*?** No — not from the built path.
  `MirrorGraph.build(view, *, sigma)` (`core/dreaming/graph.py:32-40`) takes **no cut**; it builds
  over whatever rows the `MirrorView` holds. `MirrorView.project(source)` (`core/mirror.py:96-101`)
  reads the source's **current** state; `rows()` (`:103-105`) returns all authored rows. There is
  **no `at_cut` / downset filter** on `MirrorView`. *Code does not settle historical restriction.*
  What would: a `MirrorView` downset filter (each row carries a spine event_id `<store>:<chain>:<pos>`
  filterable against `spine.downset(cut)`) — a `core/` change, out of this eval-side plan's scope.
  **Resolution (§4):** v1 pins to the **latest cut**. The graph is built over the current
  `MirrorView`; the reading records the `CertifiedCut` from `spine.cut_at(strata=frozenset({"mirror"}))`
  as its cut index. Historical/cut-restricted sweeps are PARKED (§11) with the named prerequisite.
- **Q2 — Does σ* need the spine at all for v1, or only the cut certificate?** Only the certificate.
  σ*'s index is `(σ-grid, cut)` — a single cut per reading. The MST/union-find run needs only the
  cosine matrix + the σ-grid; the cut rides in evidence for legality (CN-1 falsifier: a reading at an
  uncertified cut refuses). `spine.cut_at` raising `CutCertificateError` IS the refusal mechanism —
  do not catch-and-continue; let it propagate (fail-closed).
- **Q3 — MST edge weights.** `MirrorGraph.sim[i,j]` (`graph.py:24`) is the cosine; the maximum
  spanning tree maximizes total similarity. `σ*(A,B)` = the **minimum edge cosine on the A–B MST
  path** (the bottleneck = maximin value; single-linkage ultrametric). The realizing chain is the
  MST path itself.
- **Q4 — grid-relativity.** The grid is the declared σ-grid (fibers discipline). The MST is built
  on the **loosest-grid graph** (lowest σ = densest edges); a pair unconnected there is "not
  connected within grid" (its component split at grid-min). σ* is then the largest grid σ ≤ the
  path-bottleneck cosine (grid-snapped), NOT the raw bottleneck (honest bounded answer).
- **Q5 — the objective is NOT recall (finding-0096).** This instrument reports σ* + chains; it does
  **not** feed golden_recall or claim a σ-discriminating recall signal. finding-0096 established
  golden_recall saturates at this corpus scale — the σ* falsifiers (§2.2) are ultrametric-inequality
  and MST≡union-find agreement, both scale-free structural checks, NOT a recall improvement. Keep it so.

**Additional risks surfaced:** (a) n=0 / n=1 corpora — `_adj` is empty-safe (`graph.py`), MST is
trivial/empty; guard the "no pairs" path (emit no readings, note it). (b) disconnected graph at
grid-min → a spanning **forest**; σ* across components = "not connected within grid" (not −∞, not 0).

## 4. Reconciliation
- `core/dreaming/graph.py` `MirrorGraph.build` — the built σ-graph carries **no cut**; CN-1 says
  "the graph at a moment exists only at a certified cut". → **cross-reference-on-extension** (not a
  correction — the dreamer never needed a cut): a module docstring in `connectivity.py` states that
  this family *supplies* the cut index externally (via `spine.cut_at`), pins v1 to the latest cut,
  and links CN-1 §2.1 + this plan's §11 parked historical-restriction re-entry. No edit to
  `graph.py`. If a future item needs cut-restricted graphs, that is a `core/` plan with its own warrant.

## 5. Write scope
The three files in frontmatter: the new `eval/harness/connectivity.py` (the shared CN-1 scaffolding +
σ*), its unit tests, its quality battery. **OUT:** `core/**` (graph.py/mirror.py/spine.py are
read-only substrate — the cut gap is cross-referenced, never patched here), `ops/levers.py`
(no levers this plan), `eval/harness/fibers.py`/`gate.py`/`store.py` (imported, not modified),
`eval/golden/**` + `CONSTITUTION.md` + `docs/design-notes/**` (foundation denylist), the mirror
surfacing/report wiring (a later E6 tenant plan).

## 6. Interfaces pinned inline
```python
# --- CONSUMED, verbatim current signatures (do not re-derive) ---
# core/dreaming/graph.py
@dataclass(frozen=True)
class MirrorGraph:
    notes: tuple[NoteVector, ...]; sim: np.ndarray; sigma: float; _adj: np.ndarray
    @classmethod
    def build(cls, view: MirrorView, *, sigma: float) -> MirrorGraph: ...   # NO cut arg
    @property
    def n(self) -> int: ...
    def digest(self, i: int) -> str: ...
    def title(self, i: int) -> str: ...
# core/dreaming/cluster.py
@dataclass(frozen=True)
class NoteVector: digest: str; title: str; vector: tuple[float, ...]
def similarity_matrix(notes: list[NoteVector]) -> np.ndarray: ...   # pairwise cosine, L2-normed

# core/temporal/spine.py
@dataclass(frozen=True)
class CertifiedCut:
    frontier: tuple[tuple[str, int], ...]; certificates: frozenset[Certificate]; evidence: tuple[str, ...]
class Spine:
    @classmethod
    def derive(cls, sources, coarsening_ticks=None, cut_sources=None) -> Spine: ...
    def cut_at(self, *, strata: frozenset[str]) -> CertifiedCut: ...   # raises CutCertificateError if uncertified
    def downset(self, cut: CertifiedCut) -> frozenset[str]: ...
    def crossing_edges(self, cut: CertifiedCut) -> list[tuple[str, str]]: ...

# eval/harness/fibers.py — the evidence-pinning pattern to COPY
@dataclass(frozen=True)
class FibersEvidence:
    grid: tuple[float, ...]; base_fingerprint: str; lever_registry_hash: str
    def as_ref(self) -> str: ...   # JSON, sort_keys: {instrument, grid, base_fingerprint, lever_registry_hash}

# eval/harness/store.py — the write target
@dataclass(frozen=True)
class EvalKey: spec_hash: str; corpus_ref: str; config_fingerprint: str; seed: int
@dataclass(frozen=True)
class Reading:
    key: EvalKey; metric_name: str; value: float; type_tag: str
    interval_lo: float | None = None; interval_hi: float | None = None; evidence_ref: str | None = None
class EvalResultsStore:
    def put(self, r: Reading) -> bool: ...   # idempotent-by-key; False on skip; never overwrites

# --- TO BUILD in eval/harness/connectivity.py ---
_INSTRUMENT = "connectivity/v1"
_TYPE_TAG = "SigmaStar"

@dataclass(frozen=True)
class ConnIndex:                       # the CN-1 index object — shared by the family
    grid: tuple[float, ...]            # the declared σ-grid
    cut: CertifiedCut                  # the corpus-history coordinate (latest cut, v1)
    # each instrument declares WHICH of (σ-grid, t, cut) it uses; σ* uses (grid, cut) — no t

@dataclass(frozen=True)
class ConnEvidence:                    # the family's evidence pin (mirrors FibersEvidence)
    grid: tuple[float, ...]; base_fingerprint: str; cut_fingerprint: str
    def as_ref(self) -> str: ...       # JSON sort_keys {instrument, grid, base_fingerprint, cut_fingerprint}

@dataclass(frozen=True)
class SigmaStar:
    a: str; b: str                     # note digests (the pair)
    sigma_star: float | None           # grid-snapped bottleneck cosine; None ⇒ "not connected within grid"
    chain: tuple[str, ...]             # the realizing MST path (digests), () when unconnected

def build_max_spanning_tree(graph: MirrorGraph) -> ...     # MST over sim on the loosest-grid graph
def sigma_star(mst, a: str, b: str, *, grid: Sequence[float]) -> SigmaStar
def run_connectivity(*, view: MirrorView, spine: Spine, grid: Sequence[float],
                     eval_store: EvalResultsStore, base_fingerprint: str) -> ...   # entry point (cf. run_fibers)
```

## 7. Items
### Item 1 — the CN-1 scaffolding: ConnIndex, ConnEvidence, the latest-cut gate
- **Objective:** the shared index object + evidence pin + cut acquisition (`spine.cut_at`) the whole
  family reuses; a graph built at an uncertified cut refuses.
- **Files:** `eval/harness/connectivity.py`, `tests/unit/test_connectivity.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_connectivity.py -q` green — `ConnEvidence.as_ref()`
  round-trips (stable JSON, sort_keys); acquiring the cut calls `spine.cut_at(strata=frozenset({"mirror"}))`
  and lets `CutCertificateError` propagate (a stubbed uncertified spine ⇒ the run raises, emits no
  reading); `crossing_edges(cut) == []` asserted on the acquired cut (the CN-1 legality tooth).
- **Falsifier:** a reading emitted at an uncertified cut (the certificate error swallowed); a
  wall-clock value used anywhere as an index key (Law C4 — grep the module for time/now/datetime).
- **Invariant(s):** CN-1 index discipline (every reading carries its declared tuple); no store write
  beyond eval readings; model-free (no LLM call).
- **Touches stored data?** No (reads MirrorView + spine; writes only keyed eval Readings).
- **Parallelizable?** No (foundation for item 2).  **Depends on:** none.

### Item 2 — the MST and σ* with the realizing chain
- **Objective:** one maximum spanning tree on the loosest-grid graph; `sigma_star(a,b)` returns the
  grid-snapped bottleneck + MST path; unconnected pairs report "not connected within grid".
- **Files:** `eval/harness/connectivity.py`, `tests/unit/test_connectivity.py`.
- **Acceptance test:** unit tests green — (a) **ultrametric inequality** `σ*(A,C) ≥ min(σ*(A,B),σ*(B,C))`
  on sampled real triples (skip pairs where either is None); (b) **MST≡union-find**: σ* from the MST
  equals a direct union-find sweep over the grid (two independent computations agree on every pair);
  (c) an unconnected-at-grid-min pair returns `sigma_star=None, chain=()`; (d) the realizing chain is
  a real MST path whose min-cosine edge equals the reported (pre-snap) bottleneck.
- **Falsifier:** the ultrametric inequality violated on a real triple (σ* is not single-linkage — the
  MST is wrong); MST-σ* disagreeing with the union-find sweep (one computation is buggy); a σ* reported
  above grid-min for a pair the union-find sweep splits at grid-min (grid-relativity broken).
- **Invariant(s):** grid-relativity (σ* snapped to the declared grid, never extrapolated); O(E log V)
  single-MST (no per-pair re-search); no mutation of `MirrorGraph`/`sim`.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** item 1.

### Item 3 — the entry point + the quality battery + readings
- **Objective:** `run_connectivity(...)` builds the graph over the current MirrorView, acquires the
  cut, computes the pairwise σ* summary, and writes keyed readings with the ConnEvidence ref.
- **Files:** `eval/harness/connectivity.py`, `tests/quality/test_connectivity_sigma_star.py`.
- **Acceptance test:** `uv run pytest tests/quality/test_connectivity_sigma_star.py -q` green — on a
  planted two-cluster fixture (known cosines, cf. bp-057's fixture philosophy: bounds & relationships,
  never exact floats) the within-cluster σ* exceeds the cross-cluster σ*; the cross-cluster pair at a
  loose grid connects and at a tight grid reports "not connected within grid" (grid-relativity
  observable); every emitted `Reading.evidence_ref` decodes to a `ConnEvidence` carrying the grid +
  cut fingerprint; `put()` is idempotent (a second run writes 0 new readings). n=0/n=1 corpora emit no
  readings and note it.
- **Falsifier:** within-cluster σ* ≤ cross-cluster σ* on the planted fixture (the instrument does not
  measure abstraction proximity); a reading whose evidence_ref omits grid or cut; a re-run overwriting
  a prior reading (`put` returning True on an identical key — the store contract broke).
- **Invariant(s):** FibersEvidence pinning discipline (grid + fingerprints reconstructable from every
  reading); idempotent-by-key writes; certified-cut-only.
- **Touches stored data?** Yes — writes eval Readings. Dry-run: item 3 first runs with an in-memory
  `EvalResultsStore` in the test before any persistent path; the entry point never writes to core stores.
- **Parallelizable?** No.  **Depends on:** items 1–2.

## 8. Math carried explicitly
- **σ\* — the abstraction ultrametric** — *measures:* the strictest abstraction threshold at which two
  thoughts still share a component (single-linkage / maximin-cosine). *valid when:* computed against a
  declared σ-grid on a certified cut; edge weights are the L2-normed centroid cosines; the MST is the
  maximum spanning tree on the loosest-grid graph. *fails its keep if:* the ultrametric inequality is
  violated on sampled real triples, or the MST value disagrees with a direct union-find sweep.
- **The realizing MST chain** — *measures:* the strongest single chain of association (path of least
  resistance) between two thoughts. *valid when:* it is an actual MST path and its bottleneck edge
  equals σ*(A,B). *fails its keep if:* the reported chain's min-cosine edge ≠ the reported σ*.

## 9. Non-goals
No conductance / diffusion / walk-time (t axis — that is bp-060; σ* declares no t). No bridges or
arc search (bp-061). No helix (bp-062). No writes beyond eval readings; no `core/` change (the cut gap
is cross-referenced, not patched); no `MirrorView` downset filter (parked). No golden_recall coupling
(finding-0096). No mirror surfacing wiring. No new `ops/levers.py` lever. No claim matching (SF-a).

## 10. Stop-and-raise conditions
- The corpus is n≤1 → emit no readings, note it, complete (a sanctioned empty outcome, not a failure).
- `spine.cut_at` raises `CutCertificateError` on the live spine → the substrate has no certified mirror
  cut; STOP, journal it, file a `codebase` finding (a substrate gap, builder-owned per routing) — do
  not fabricate a cut.
- Building a cut-restricted historical graph turns out to be needed for acceptance → STOP; that is the
  parked `core/` prerequisite (§11), a re-graduation trigger, not a mid-build core edit.
- Any pressure to couple σ* to golden_recall to "show a signal" → STOP (finding-0096 — the objective,
  not σ, was the problem; σ* is a structural instrument, not a recall booster).
- Any blessing (`proposed→ready`, `draft→ratified`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| historical / cut-restricted graphs | latest cut only (cut in evidence) | add a `MirrorView` downset filter now (a `core/` change — sprawls the write_scope across zones, violates session-sizing) | an instrument needs σ* *at a past cut* → a `core/` plan adding downset restriction (its own warrant) |
| conductance grain (chunk vs note) | note-centroid grain (`MirrorGraph`'s built grain) | chunk-grain σ* now (heavier; the source-set relation supplies the group-by later) | item-2 design review shows chunk/claim-grain queries dominate |
| certified-cut arithmetic (meets/joins) | cut *sampling* at the latest cut | build cut lattice closure now (unneeded by σ*) | an instrument needs cut meets/joins, not samples |

## 12. Dependency & ordering summary
No upstream plan dependency — **the keystone; build first.** Items are strictly serial:
1 (CN-1 scaffolding: ConnIndex/ConnEvidence/latest-cut gate) → 2 (MST + σ* + chain) → 3 (entry point +
readings + quality battery). Blast radius: read-only sensing throughout; the only stored-data touch is
additive keyed eval Readings in item 3 (idempotent, dry-run in-memory first). **Downstream:** bp-060
(conductance) imports this module's `ConnIndex`/`ConnEvidence` and the graph-at-cut acquisition;
bp-061 (bridges) and bp-062 (helix) depend transitively. Not parallelizable with any sibling (they
consume its surface).
