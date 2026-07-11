"""F9 — the real DreamerAdapter binding for the output-quality suite.

`tests/quality/test_dreamer_quality.py` defines a `DreamerAdapter` protocol and ships a
`RefDreamer` reference fake so the suite runs green out of the box. THIS module is the other
half: it binds that protocol to the **live** dreaming machinery so the apophenia / signal-vs-
noise suite actually exercises the system, not a stand-in. (Roadmap Track F, item F9;
design-notes/dreamer-quality-suite-evaluation.md.)

What is genuinely the real system here
--------------------------------------
The thing the quality suite tests is the dreamer's *signal-finding*: does it invent themes in
noise, does it recover planted structure, is its grounding load-bearing, is its confidence
calibrated. That machinery is the live, deterministic, model-free path:

  * `core.dreaming.dreamer.Dreamer.clusters()` — the real clustering over a `MirrorView`
    (Invariant 6: authored-only is structural, not a flag);
  * `core.dreaming.cluster.{note_centroids,cluster_notes,similarity_matrix}` — the real
    single-linkage clustering and cosine math;
  * `core.selfcheck.grounding_score` + `core.recursion` — the real grounding/confidence law;
  * `core.stores.derived.DerivedStore` — the real interpreted-only store (exercised end to
    end by `persist_dreams`, used by `tests/quality/test_real_dreamer_binding.py`).

Only two inputs are deterministic CI substitutes, for the same reason the existing dreamer
tests substitute them (see tests/integration/test_dreamer.py): the **embedder** (the real one
is Ollama-backed → network + a pulled model) and the **synthesizer** (the synthesis-tier
model). Neither is what the quality suite measures. The owner can later point the binding at
the real Ollama embedder for a `needs_models` full-fidelity run — that is the "tune THRESH on
known corpora via the harness" step in the design note; the THRESH table is the tuning
surface, not this code.

The confidence definition — resolving the open `g` question (review note 2 / §4)
---------------------------------------------------------------------------------
The live `Dreamer` (Phase 7) produces grounded *Themes* but no scalar confidence; the
confidence law lives in the R&D adjudicator (flag-OFF):

    c(κ) = γ^{d(κ)} · g(κ) · (1 + λ(|Agr(κ)| − 1))         [core.dreaming.adjudicator]

and its `g(κ)` is today `grounding_score(evidence, authored)` — pure **resolvability** (1.0 for
any cluster whose citations are authored leaves, which is every live cluster). That makes `c`
*flat* across clusters of every size and cohesion. The evaluation predicted exactly this:

    "does g scale with the NUMBER of authored supports or only their similarity? If
     similarity-only, this suite will (correctly) flag it."  (§4)

It would: a flat confidence fails `test_confidence_is_calibrated`. So binding the suite *forces*
the resolution the design note asked for. We resolve `g` here, in the binding layer (where the
note says to — "Resolve g's definition when binding"), as:

    g(κ) = g_resolve(κ) · support_strength(κ)

  * g_resolve = grounding_score(members, authored) ∈ [0,1] — the UNCHANGED resolvability gate.
    Structural: g_resolve = 0 ⇒ g = 0 ⇒ c = 0, so agreement/cohesion can never manufacture
    confidence from un-anchored citations. (Identical to the live `grounding_score`.)
  * support_strength = cohesion · size_factor ∈ [0,1] — the NEW factor (review note 2):
      - cohesion   = mean pairwise cosine of the cluster's note centroids (real similarity);
      - size_factor = min(1, (|κ| − 1) / SIZE_SATURATION) — folds in support COUNT, so a
        two-note cosine-1.0 *coincidence* scores weak (size_factor small), which is the
        apophenia failure in miniature and the whole point of the guard.

We report the **base confidence** c₀(κ) = g·(1 + λ(|Agr|−1)) (named as such in
`core.recursion`): the live run is depth-uniform (every claim grounds directly in authored
leaves, d = 1 — `adjudicator.AUTHORED_LEAF_DEPTH`), so the γ^d cross-depth decay is a single
constant that changes no ranking and only differentiates depths — which is the recursion /
drift suite's job, not this one (binding-seam review note 3). There is one clustering "method",
so |Agr| = 1 and the corroboration term is 1.0; the seam is kept so a future multi-interpreter
binding folds in naturally.

WHAT THIS SURFACES FOR THE REAL ADJUDICATOR (record, do not silently change): the flag-OFF
`core.dreaming.adjudicator` still defines `g = grounding_score` only. When that R&D path is
made live it must fold support count into `g` the same way, or its confidence will be
un-calibrated for the same reason. This binding does NOT modify the adjudicator (flag-OFF R&D;
flipping/altering it is a separate deliberate step) — it resolves `g` for the quality suite and
flags the adjudicator change as owner-deferred. See docs/PROGRESS.md F9 entry.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.complex.spectral import diffusion_cluster_notes
from core.dreaming.adjudicator import AUTHORED_LEAF_DEPTH
from core.dreaming.cluster import Cluster, cluster_notes, similarity_matrix
from core.dreaming.dreamer import Clusterer, Dreamer
from core.provenance import Provenance
from core.recursion import DEFAULT_LAMBDA
from core.selfcheck import grounding_score
from core.stores.derived import DREAM, DerivedStore


# The suite imports its `Dream` dataclass from the test module; to avoid a fixture→test-module
# import cycle the adapter is duck-typed against it and returns objects of the same shape (the
# suite only reads `.theme` / `.confidence` / `.grounding_node_ids`). This local mirror keeps
# the module self-contained.
@dataclass(frozen=True)
class _Dream:
    theme: str
    confidence: float
    grounding_node_ids: tuple[str, ...]
    id: str = ""


# Clustering + confidence tuning for the deterministic *lexical* embedder below. These are the
# adapter's own knobs (matched to the lexical embedder's cosine statistics); they are NOT the
# suite's THRESH (that is the quality bar). The real Ollama embedder would instead use the
# configured `[dreaming] similarity_threshold` (~0.62) — cosine statistics differ by embedder.
LEXICAL_THRESHOLD = 0.50       # cosine to join two notes (presence-vector statistics)
SIZE_SATURATION = 4.0          # support count at which size_factor saturates to 1.0
MAX_CLUSTERS = 256             # do not truncate: the calibration test needs many clusters
MIN_CLUSTER_SIZE = 2           # matches the suite's RefDreamer (clusters of >= 2)

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the of to and or in on for with is are was were be been this that these those it "
    "its as at by from into over under i you he she they we my your".split()
)


def _tokens(text: str) -> list[str]:
    return [w for w in _TOKEN.findall(text.lower()) if len(w) > 2 and w not in _STOP]


class LexicalEmbedder:
    """Deterministic, similarity-PRESERVING, offline embedder for the quality suite.

    The shipped `tests/fixtures/embedding.FakeEmbedder` hashes whole strings (identical text →
    identical vector) — correct for idempotency/retrieval tests but USELESS for clustering: two
    paraphrases of the same theme hash to unrelated vectors. The quality suite needs the
    opposite property — notes that share content must embed *close* — so it can recover planted
    structure. This embedder gives exactly that, with no model: an L2-normalised binary
    bag-of-tokens over a per-batch vocabulary. Cosine(a,b) = |tokens(a) ∩ tokens(b)| /
    sqrt(|a|·|b|), so lexical overlap (which is what the synthetic corpora encode, and a decent
    proxy for what a real semantic embedder finds on keyword-bag notes) becomes geometric
    proximity. Vocabulary is built from the batch, so it is exact (no hash collisions) and
    deterministic; cross-batch dimension differences are irrelevant (each run clusters its own
    batch).
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        toksets = [set(_tokens(t)) for t in texts]
        vocab: dict[str, int] = {}
        for ts in toksets:
            for tok in ts:
                vocab.setdefault(tok, len(vocab))
        dim = max(1, len(vocab))
        out: list[list[float]] = []
        for ts in toksets:
            vec = [0.0] * dim
            for tok in ts:
                vec[vocab[tok]] = 1.0
            norm = (sum(v * v for v in vec)) ** 0.5
            if norm:
                vec = [v / norm for v in vec]
            out.append(vec)
        return out


def _theme_string(cluster: Cluster, snippets: dict[str, str]) -> str:
    """A deterministic, content-based theme label: the cluster's most common content tokens.

    This is the model-free stand-in for the synthesis prose (which the quality suite does not
    measure — it tokenizes `Dream.theme`). Built from the SAME grounding text the real
    synthesizer would see (`note_snippets`), so it is stable under meaning-preserving paraphrase
    (the embedder is order-invariant) — which is what `test_paraphrase_invariance` checks.
    """
    df: Counter[str] = Counter()   # document frequency within the cluster (robust to one loud note)
    tf: Counter[str] = Counter()
    for m in cluster.members:
        toks = _tokens(snippets.get(m.digest, "") or m.title)
        tf.update(toks)
        df.update(set(toks))
    if not df:
        return "misc"
    ranked = sorted(df, key=lambda w: (-df[w], -tf[w], w))
    return " ".join(ranked[:4])


def _cohesion(cluster: Cluster) -> float:
    """Mean pairwise cosine over the cluster's note centroids — the real similarity signal."""
    n = cluster.size
    if n < 2:
        return 0.0
    sim = similarity_matrix(list(cluster.members))
    total = sum(float(sim[i, j]) for i in range(n) for j in range(i + 1, n))
    return total / (n * (n - 1) / 2)


def _confidence(cluster: Cluster, authored: set[str], *, agreement: int = 1) -> float:
    """The resolved confidence c₀(κ) = g·(1 + λ(|Agr|−1)) with g = g_resolve · support_strength.

    See the module docstring for why this — and not the live adjudicator's flat
    `g = grounding_score` — is the calibrated definition the suite forces.
    """
    g_resolve = grounding_score(cluster.digests, authored)              # resolvability gate (1.0)
    cohesion = _cohesion(cluster)
    size_factor = min(1.0, (cluster.size - 1) / SIZE_SATURATION)        # support COUNT folds in
    g = g_resolve * cohesion * size_factor
    corroboration = 1.0 + DEFAULT_LAMBDA * (agreement - 1)              # |Agr|=1 here ⇒ 1.0
    # depth is uniform (AUTHORED_LEAF_DEPTH) for every live cluster, so the γ^d decay is a
    # constant and we report the base confidence c₀ (see docstring + binding-seam note 3).
    assert AUTHORED_LEAF_DEPTH == 1                       # guards the depth-uniform claim above
    return max(0.0, min(1.0, g * corroboration))


class _RowSource:
    """The minimal RowSource the dreamer clusters over (mirror of tests/integration's FakeStore):
    authored rows, filtered by provenance exactly like the real VectorStore. The dreamer reaches
    it only through `MirrorView.project`, which re-validates that every row is authored."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances=None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _grounded_synth(messages: list[dict]) -> str:
    """A deterministic synthesizer that grounds correctly for ANY cluster: it echoes the exact
    [[note titles]] the dreamer placed in the cluster block, so `core.selfcheck` sees every
    citation resolve. Stands in for the synthesis-tier model — the quality suite does not grade
    prose, and the end-to-end binding test only needs a grounded, self-check-passing reflection.
    """
    content = messages[-1]["content"] if messages else ""
    titles = re.findall(r"\[\[([^\]]+)\]\]", content)
    cites = " ".join(f"[[{t}]]" for t in titles)
    return f"A recurring theme runs through {cites}." if cites else "No coherent theme."


@dataclass
class MindPalaceDreamerAdapter:
    """Binds the quality suite's `DreamerAdapter` protocol to the live `Dreamer`/`DerivedStore`.

    `run` exercises the real clustering + grounding + the resolved confidence law (the fast,
    deterministic, signal-finding path the suite measures). `persist_dreams` runs the FULL real
    `Dreamer.dream()` against a real `DerivedStore` (synthesis → self-check → interpreted-only
    persist with `derived_from` = authored leaves), used by the end-to-end binding test.
    """

    embedder: Any = field(default_factory=LexicalEmbedder)
    threshold: float = LEXICAL_THRESHOLD
    min_cluster_size: int = MIN_CLUSTER_SIZE
    max_clusters: int = MAX_CLUSTERS
    # The clustering strategy behind the seam. Default = the Phase-7 single-linkage (the existing
    # F9 baseline). `build_diffusion_dreamer_adapter()` swaps in the reasoning complex's diffusion
    # clusterer (H2) so F9 can be run against the adopted subset without touching the default.
    clusterer: Clusterer = cluster_notes

    # ---- row construction (the corpus → authored mirror rows) ----------------------------
    def _rows(self, notes: Sequence[Any]) -> list[dict[str, Any]]:
        vectors = self.embedder.embed_documents([n.text for n in notes])
        # digest == the suite's Note.id: grounding_node_ids must come back as note ids (the
        # suite checks `set(grounding) & signal_ids`), and the digest IS the citation identity.
        return [
            {"id": f"{n.id}:0", "digest": n.id, "title": n.id, "source_path": "",
             "chunk_index": 0, "provenance": Provenance.AUTHORED_SOLO.value,
             "text": n.text, "vector": vec}
            for n, vec in zip(notes, vectors, strict=True)   # one vector per note, by construction
        ]

    def _dreamer(self, rows: list[dict[str, Any]], *,
                 derived: DerivedStore | None = None) -> Dreamer:
        return Dreamer(
            store=_RowSource(rows),
            synthesize=_grounded_synth,
            derived=derived if derived is not None else DerivedStore(Path(":memory:")),
            threshold=self.threshold,
            min_cluster_size=self.min_cluster_size,
            max_clusters=self.max_clusters,
            clusterer=self.clusterer,
        )

    def _clusters(self, notes: Sequence[Any]) -> tuple[list[Cluster], Dreamer, set[str]]:
        rows = self._rows(notes)
        dreamer = self._dreamer(rows)
        clusters = dreamer.clusters()                      # real, deterministic, model-free
        authored = {r["digest"] for r in rows}
        return clusters, dreamer, authored

    # ---- the DreamerAdapter protocol -----------------------------------------------------
    def run(self, notes: Sequence[Any], *, seed: int = 0) -> list[_Dream]:
        """Real clustering → Dreams. Deterministic, so `seed` is honored vacuously (no RNG)."""
        clusters, dreamer, authored = self._clusters(notes)
        dreams: list[_Dream] = []
        for c in clusters:
            theme = _theme_string(c, dreamer._snippets)
            dreams.append(_Dream(
                theme=theme,
                confidence=_confidence(c, authored),
                grounding_node_ids=c.digests,              # authored leaves (flattened; note 3)
                id=f"d:{theme[:12]}",
            ))
        return dreams

    def run_without_grounding(self, notes: Sequence[Any], *, seed: int = 0) -> list[_Dream]:
        """Negative control (review note 3): same clustering, but the citations are DECORATIVE —
        they do not point at the cluster that produced the theme. Ablating them therefore does
        NOT collapse the theme, so dreams made *without* the grounding discipline survive
        citation-ablation, which is what `test_grounding_discipline_improves_faithfulness`
        contrasts against the real (grounded) run. Deterministic: cite the two lowest note ids
        that are NOT in the cluster.
        """
        clusters, dreamer, _authored = self._clusters(notes)
        all_ids = sorted(n.id for n in notes)
        dreams: list[_Dream] = []
        for c in clusters:
            members = set(c.digests)
            decoy = tuple(i for i in all_ids if i not in members)[:2] or tuple(all_ids[:2])
            theme = _theme_string(c, dreamer._snippets)
            dreams.append(_Dream(
                theme=theme,
                confidence=_confidence(c, set(all_ids)),
                grounding_node_ids=decoy,                  # decorative — not the real support
                id=f"d:{theme[:12]}",
            ))
        return dreams

    # NOTE: rate_blind is deliberately NOT implemented. Whether a real dream beats Barnum-bait
    # is irreducibly a human question (review note 1); the suite's
    # `test_real_dreams_beat_decoys_under_blind_rating` SKIPS until the owner wires a periodic
    # blind-rating ritual (docs/runbook.md). A passing proxy is not a validated value-claim.

    # ---- end-to-end real-DerivedStore exercise (binding test) ----------------------------
    def persist_dreams(self, notes: Sequence[Any], derived: DerivedStore) -> list:
        """Run the FULL live `Dreamer.dream()` against a REAL `DerivedStore`: real clustering →
        grounded synthesis → Constitution self-check → interpreted-only persist with
        `derived_from` = authored leaf digests. Returns the Themes; the store now holds the
        DREAM artifacts. Proves the binding reaches the real Dreamer AND DerivedStore."""
        rows = self._rows(notes)
        return self._dreamer(rows, derived=derived).dream()


def build_real_dreamer_adapter() -> MindPalaceDreamerAdapter:
    """Zero-arg factory — the `MIND_PALACE_DREAMER_ADAPTER` entry point and the value the
    quality suite's parametrized `adapter` fixture loads for the "real" variant."""
    return MindPalaceDreamerAdapter()


def build_diffusion_dreamer_adapter() -> MindPalaceDreamerAdapter:
    """Same binding, but the clustering runs through the reasoning complex's diffusion clusterer
    (H2) instead of the single-linkage floor — the adopted-subset path F9 non-regression is run
    against. Everything else (embedder, grounding, confidence) is identical, so a comparison
    isolates the clusterer."""
    return MindPalaceDreamerAdapter(clusterer=diffusion_cluster_notes)


# Re-export the artifact kind so the binding test can assert on persisted DREAM rows without
# reaching into core directly.
__all__ = ["MindPalaceDreamerAdapter", "LexicalEmbedder", "build_real_dreamer_adapter",
           "build_diffusion_dreamer_adapter", "DREAM"]
