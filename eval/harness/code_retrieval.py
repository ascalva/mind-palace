# ── Family 1 boundary (eval readings over the code lane) · symbols in docs/NOTATION.md ──
# OBJECT:    the CI-2 retrieval/geometry/scale battery (dn-code-ingest-pipeline §2.8 M-C3/M-C4/M-C5,
#            bp-093). Read-only measurements over a store the code lane seeded (bp-092/CI-1).
# INVARIANT: this module NEVER writes the store and NEVER reaches code through the MIRROR_READABLE
#            default — the code lane is read only via an EXPLICIT `provenances={CODE}` set (§7).
# ENFORCED:  reads go through `semantic_search`/`store.all_rows` with provenances passed explicitly;
#            no `add`/`delete` call exists here. `test_code_mirror` re-checks the firewall boundary.
"""The CI-2 measure-first battery: does the code lane earn its keep? (bp-093, read-only, eval-side).

Three measurements over a store the CI-1 lane already seeded — the honest proofs the note names:

  * **M-C3 — retrieval quality.** Per golden probe (`eval/code_probes.py`), the rank of the
    known-answer path in the **code lane** (all code layers) vs the **docstring-only baseline**
    (the `codedoc`/L1 layer alone) — same k, same embedder. Verdict: the lane must beat the
    baseline on the majority with no catastrophic regressions (F-CI3; a null is a *result*).
  * **M-C4 — cross-space geometry.** Code↔note cosine distribution vs within-class. Verdict
    "informative" iff the cross-class mass is non-degenerate — it overlaps the within-class mass
    rather than being bimodally separated toward orthogonality (F-CI4; gates CI-4 and PD-C).
  * **M-C5 — reader scale.** `all_rows`/search latency at the seeded scale — the Python-side-filter
    posture (`core/stores/vectorstore.py`) re-checked. Embedder-independent (row count + payload).

Every reading carries a **CN-1 index** (`reading_index`): the embedder pin, the corpus ref, the
seed, k, the layer partition, and the probe-set hash — so a number always knows what it measured.
Verdicts are graded here; the numeric verdicts on the REAL corpus land at the owner-visible seed run
(bp-092 parked it — no Ollama in a worktree/CI). This module holds the machinery; the numbers park.

Imports a core read path (`core.ingest.index`) — permitted: the eval-isolation firewall (§2.10)
seeds only `eval.harness.{store,registry,__init__}`, and this module is imported by none of them.
"""

from __future__ import annotations

import math
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, cast

from core.ingest.embed import Embedder
from core.ingest.index import semantic_search
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.stores.vectorstore import (
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    LAYER_CODEDOC,
    VectorStore,
)
from eval.code_probes import PROBES, CodeProbe, probe_set_hash

# The layer partition the M-C3 comparator uses (note §2.8/§3 Q2). The "lane" is the full code
# corpus; the "baseline" is the docstring/comment prose alone — the honest comparator: does
# embedding the CODE (L0a structural + L0b textual) beat embedding only the DOCS?
LANE_LAYERS: frozenset[str] = frozenset({LAYER_CODE_AST, LAYER_CODE_TEXT, LAYER_CODEDOC})
BASELINE_LAYERS: frozenset[str] = frozenset({LAYER_CODEDOC})

_DEFAULT_POOL = 400  # flat-chunk budget pulled before the Python-side layer filter + path dedup
_DEFAULT_K = 10      # the retrieval depth a "catastrophic regression" is judged against


class _QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


# ── shared geometry ──────────────────────────────────────────────────────────────────────

def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors (0.0 when either is a zero vector)."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ── M-C3: retrieval quality — code lane vs docstring-only baseline ─────────────────────────

def ranked_paths(query: str, embedder: _QueryEmbedder, store: VectorStore, *,
                 layers: Iterable[str], pool: int = _DEFAULT_POOL) -> list[tuple[str, float]]:
    """The ranked, path-deduplicated retrieval for one query restricted to `layers`. Pulls `pool`
    flat code chunks via an EXPLICIT `provenances={CODE}` search (never the mirror default — §7),
    filters to the requested layers, and collapses to one entry per source path at its best
    (lowest-distance) hit, preserving rank. Returns `[(path, distance)]` best-first.

    The Python-side layer filter + path dedup mirrors the store's single-user-scale posture
    (`all_rows`/`rows_for_source`): pull a generous pool, refine in Python."""
    allowed = set(layers)
    hits = semantic_search(query, cast(Embedder, embedder), store, k=pool,
                           provenances={Provenance.CODE})
    best: dict[str, float] = {}
    order: list[str] = []
    for h in hits:
        if h.get("layer") not in allowed:
            continue
        path = str(h["source_path"])
        dist = float(h.get("_distance", 0.0))
        if path not in best:
            best[path] = dist
            order.append(path)
        elif dist < best[path]:
            best[path] = dist
    return [(p, best[p]) for p in order]


def _rank_of(paths: Sequence[tuple[str, float]], answers: frozenset[str]) -> int | None:
    """1-based rank of the first answer path in the ranking, or None (a miss)."""
    for i, (path, _dist) in enumerate(paths, start=1):
        if path in answers:
            return i
    return None


class MC3Verdict(StrEnum):
    LANE_BEATS_BASELINE = "lane-beats-baseline"
    NO_SIGNAL = "no-signal"            # F-CI3 — record, re-open grain (PD-D); the plan still seals


@dataclass(frozen=True)
class ProbeReading:
    probe_id: str
    lane_rank: int | None
    baseline_rank: int | None

    @property
    def lane_wins(self) -> bool:
        """The lane strictly beats the baseline on this probe (finds it; better or equal-rank-and-
        baseline-missed)."""
        if self.lane_rank is None:
            return False
        return self.baseline_rank is None or self.lane_rank < self.baseline_rank

    @property
    def baseline_wins(self) -> bool:
        if self.baseline_rank is None:
            return False
        return self.lane_rank is None or self.baseline_rank < self.lane_rank


def _mrr(ranks: Iterable[int | None]) -> float:
    """Mean reciprocal rank — 1/rank per probe, 0 for a miss. The single-scalar summary."""
    vals = [(1.0 / r if r is not None else 0.0) for r in ranks]
    return sum(vals) / len(vals) if vals else 0.0


@dataclass(frozen=True)
class MC3Result:
    readings: tuple[ProbeReading, ...]
    k: int
    lane_mrr: float
    baseline_mrr: float
    lane_wins: int
    baseline_wins: int
    ties: int
    catastrophic_regressions: int  # baseline found it in top-k, the lane missed it entirely
    verdict: MC3Verdict

    def table(self) -> str:
        """A fixed-width per-probe table (lane rank | baseline rank | winner) for the journal."""
        rows = ["probe                lane  base  winner",
                "-------------------- ----  ----  ------"]
        for r in self.readings:
            lane = "miss" if r.lane_rank is None else f"{r.lane_rank:>4}"
            base = "miss" if r.baseline_rank is None else f"{r.baseline_rank:>4}"
            win = "lane" if r.lane_wins else ("base" if r.baseline_wins else "tie")
            rows.append(f"{r.probe_id:<20} {lane}  {base}  {win}")
        rows.append(f"MRR lane={self.lane_mrr:.3f} baseline={self.baseline_mrr:.3f} "
                    f"| wins lane={self.lane_wins} base={self.baseline_wins} tie={self.ties} "
                    f"| catastrophic={self.catastrophic_regressions}"
                    f" | verdict={self.verdict.value}")
        return "\n".join(rows)


def run_mc3(embedder: _QueryEmbedder, store: VectorStore, *,
            probes: tuple[CodeProbe, ...] = PROBES,
            lane_layers: Iterable[str] = LANE_LAYERS,
            baseline_layers: Iterable[str] = BASELINE_LAYERS,
            k: int = _DEFAULT_K, pool: int = _DEFAULT_POOL) -> MC3Result:
    """M-C3: per-probe rank in the code lane vs the docstring-only baseline; the majority-beat
    verdict (F-CI3). Reproducible: deterministic given (probes, embedder, store, k, pool). A
    *catastrophic regression* is a probe the baseline finds within top-k but the lane misses
    entirely — its presence blocks a LANE_BEATS_BASELINE verdict even on a favourable win count."""
    readings: list[ProbeReading] = []
    catastrophic = 0
    for p in probes:
        lane = ranked_paths(p.query, embedder, store, layers=lane_layers, pool=pool)
        base = ranked_paths(p.query, embedder, store, layers=baseline_layers, pool=pool)
        lr, br = _rank_of(lane, p.answer_paths), _rank_of(base, p.answer_paths)
        readings.append(ProbeReading(p.probe_id, lr, br))
        if br is not None and br <= k and lr is None:
            catastrophic += 1
    lane_wins = sum(1 for r in readings if r.lane_wins)
    baseline_wins = sum(1 for r in readings if r.baseline_wins)
    ties = len(readings) - lane_wins - baseline_wins
    verdict = (MC3Verdict.LANE_BEATS_BASELINE
               if lane_wins > baseline_wins and catastrophic == 0
               else MC3Verdict.NO_SIGNAL)
    return MC3Result(
        readings=tuple(readings), k=k,
        lane_mrr=_mrr(r.lane_rank for r in readings),
        baseline_mrr=_mrr(r.baseline_rank for r in readings),
        lane_wins=lane_wins, baseline_wins=baseline_wins, ties=ties,
        catastrophic_regressions=catastrophic, verdict=verdict,
    )


# ── M-C4: cross-space geometry — code↔note cosine distribution vs within-class ────────────

class MC4Verdict(StrEnum):
    INFORMATIVE = "informative"   # cross-class mass overlaps within-class — the §2.4 bridge lives
    DEGENERATE = "degenerate"        # F-CI4 — near-total class separation; PD-C re-enters


def _vectors(store: VectorStore, provenances: Iterable[Provenance]) -> list[list[float]]:
    return [[float(x) for x in r["vector"]]
            for r in store.all_rows(provenances=set(provenances))]


def _sample(items: list[list[float]], n: int, seed: int) -> list[list[float]]:
    """A deterministic sub-sample (seeded stride) — bounds the O(n²) pairwise cost without numpy."""
    if len(items) <= n:
        return items
    step = len(items) / n
    idx = sorted({int((i * step + seed) % len(items)) for i in range(n)})
    return [items[i] for i in idx]


def _pairwise(a: list[list[float]], b: list[list[float]], *, within: bool) -> list[float]:
    out: list[float] = []
    if within:
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                out.append(cosine(a[i], a[j]))
    else:
        for va in a:
            for vb in b:
                out.append(cosine(va, vb))
    return out


def _overlap_coefficient(x: Sequence[float], y: Sequence[float], *, bins: int = 20) -> float:
    """Histogram-overlap of two cosine distributions on [-1, 1] — Σ min(pₓ, p_y) over shared bins.
    1.0 = identical distributions, 0.0 = disjoint support. The non-degeneracy statistic: a
    bimodally separated cross-class mass (all near 0 while within-class sits high) yields ≈ 0."""
    if not x or not y:
        return 0.0

    def hist(vals: Sequence[float]) -> list[float]:
        counts = [0] * bins
        for v in vals:
            b = min(bins - 1, max(0, int((v + 1.0) / 2.0 * bins)))
            counts[b] += 1
        total = len(vals)
        return [c / total for c in counts]

    px, py = hist(x), hist(y)
    return sum(min(a, b) for a, b in zip(px, py, strict=True))


def _median(vals: Sequence[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


@dataclass(frozen=True)
class MC4Result:
    n_code: int
    n_note: int
    within_median: float
    cross_median: float
    overlap: float             # histogram overlap of the cross vs within cosine distributions
    threshold: float
    verdict: MC4Verdict

    def summary(self) -> str:
        return (f"M-C4 code={self.n_code} note={self.n_note} | within={self.within_median:.3f}"
                f" cross_median={self.cross_median:.3f} overlap={self.overlap:.3f}"
                f" (>= {self.threshold:.2f} ⇒ informative) | verdict={self.verdict.value}")


def run_mc4(store: VectorStore, *,
            note_provenances: Iterable[Provenance] = MIRROR_READABLE,
            sample: int = 60, seed: int = 0, overlap_threshold: float = 0.10) -> MC4Result:
    """M-C4: is the code↔note cross-space geometry informative or bimodally degenerate?
    Samples ≤ `sample` code vectors and ≤ `sample` note vectors (seeded, deterministic), compares
    the cross-class cosine distribution to the pooled within-class one via a histogram overlap, and
    verdicts INFORMATIVE iff the overlap clears `overlap_threshold` — the cross mass not pushed to
    orthogonality (F-CI4). Gates CI-4 (bp-095) and PD-C. A degenerate verdict is a FINDING, never a
    silent embedder tune (§3)."""
    code = _sample(_vectors(store, {Provenance.CODE}), sample, seed)
    note = _sample(_vectors(store, note_provenances), sample, seed)
    within = _pairwise(code, [], within=True) + _pairwise(note, [], within=True)
    cross = _pairwise(code, note, within=False)
    overlap = _overlap_coefficient(cross, within)
    verdict = MC4Verdict.INFORMATIVE if overlap >= overlap_threshold else MC4Verdict.DEGENERATE
    return MC4Result(
        n_code=len(code), n_note=len(note),
        within_median=_median(within), cross_median=_median(cross),
        overlap=overlap, threshold=overlap_threshold, verdict=verdict,
    )


# ── M-C5: reader-scale check — the Python-side-filter posture at the seeded scale ─────────

@dataclass(frozen=True)
class MC5Result:
    n_code_rows: int
    all_rows_s: float          # wall time of a CODE-filtered full scan (the Python-side filter)
    search_s: float            # wall time of one nearest-neighbour search over CODE
    ceiling_s: float
    viable: bool               # both operations under the (loose, machine-relative) ceiling

    def summary(self) -> str:
        return (f"M-C5 code_rows={self.n_code_rows} | all_rows={self.all_rows_s * 1e3:.1f}ms "
                f"search={self.search_s * 1e3:.1f}ms (ceiling {self.ceiling_s:.1f}s) "
                f"| viable={self.viable}")


def run_mc5(embedder: _QueryEmbedder, store: VectorStore, *,
            probe_query: str = "the vector store", ceiling_s: float = 5.0) -> MC5Result:
    """M-C5: re-check the single-user Python-side-filter posture at the seeded scale. Times a
    CODE-filtered `all_rows` scan and one `search`, and flags viability against a loose,
    machine-relative ceiling. Embedder-independent (dominated by row count + vector payload), so a
    synthetic-scale store measures the posture faithfully — not a semantic verdict."""
    t0 = time.perf_counter()
    rows = store.all_rows(provenances={Provenance.CODE})
    all_rows_s = time.perf_counter() - t0

    qv = embedder.embed_query(probe_query)
    t1 = time.perf_counter()
    store.search(qv, k=10, provenances={Provenance.CODE})
    search_s = time.perf_counter() - t1

    return MC5Result(
        n_code_rows=len(rows), all_rows_s=all_rows_s, search_s=search_s,
        ceiling_s=ceiling_s, viable=(all_rows_s < ceiling_s and search_s < ceiling_s),
    )


# ── CN-1: the reproducibility index — a reading knows what it measured ────────────────────

@dataclass(frozen=True)
class ReadingIndex:
    """The CN-1 index recorded beside every CI-2 reading (dn-code-ingest-pipeline §3; the harness
    unified-key discipline). Content-addresses the fixture + pins the measurement conditions so a
    number is reproducible and never confounded with another corpus/config."""

    embedder_model: str
    embedder_dim: int
    corpus_ref: str            # HEAD sha of the seeded corpus, or "fixture:<n>" for a fake store
    seed: int
    k: int
    pool: int
    lane_layers: tuple[str, ...]
    baseline_layers: tuple[str, ...]
    probe_set: str = field(default_factory=probe_set_hash)

    def as_dict(self) -> dict[str, Any]:
        return {
            "embedder_model": self.embedder_model, "embedder_dim": self.embedder_dim,
            "corpus_ref": self.corpus_ref, "seed": self.seed, "k": self.k, "pool": self.pool,
            "lane_layers": list(self.lane_layers), "baseline_layers": list(self.baseline_layers),
            "probe_set": self.probe_set,
        }


__all__ = [
    "BASELINE_LAYERS", "LANE_LAYERS",
    "MC3Result", "MC3Verdict", "MC4Result", "MC4Verdict", "MC5Result",
    "ProbeReading", "ReadingIndex",
    "cosine", "ranked_paths", "run_mc3", "run_mc4", "run_mc5",
]
