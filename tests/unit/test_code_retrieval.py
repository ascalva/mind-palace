"""CI-2 (bp-093) — the golden probe fixture + the M-C3/M-C4/M-C5 harness mechanics.

The REAL numeric verdicts (M-C3/M-C4 over the seeded qwen3 corpus) park for the owner-visible seed
run — no Ollama in a worktree. These tests prove the *machinery* is correct and reproducible with a
deterministic fake embedder + hand-built vectors: the probe fixture is well-formed and pinned to
real HEAD paths, M-C3 ranks the lane vs the docstring-only baseline and verdicts the majority-beat
(F-CI3), M-C4's non-degeneracy statistic separates an informative geometry from a degenerate one
(F-CI4), and M-C5 measures the reader-scale posture.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from core.ingest.code_corpus import code_rows, derive_code_chunks
from core.kernel.provenance import Provenance
from core.stores.vectorstore import VectorStore
from eval.code_probes import PROBES, CodeProbe, probe_set_hash
from eval.harness.code_retrieval import (
    BASELINE_LAYERS,
    LANE_LAYERS,
    MC3Verdict,
    MC4Verdict,
    cosine,
    ranked_paths,
    run_mc3,
    run_mc4,
    run_mc5,
)
from tests.fixtures.fakes import HashingEmbedder

_DIM = 64
_REPO_ROOT = Path(__file__).resolve().parents[2]


# ── the golden probe fixture ──────────────────────────────────────────────────────────────

def test_probe_set_is_well_formed():
    assert len(PROBES) >= 15
    ids = [p.probe_id for p in PROBES]
    assert len(ids) == len(set(ids)), "probe ids must be unique"
    for p in PROBES:
        assert p.query.strip(), f"{p.probe_id}: empty query"
        assert p.answer_paths, f"{p.probe_id}: no answer paths"


def test_every_answer_path_exists_at_head():
    """The known-answer paths are real files — a rename that orphans a probe fails HERE, so the
    fixture never silently rots into a meaningless future reading."""
    for p in PROBES:
        for rel in p.answer_paths:
            assert (_REPO_ROOT / rel).is_file(), f"{p.probe_id}: missing answer path {rel}"


def test_probe_set_hash_is_stable_and_order_independent():
    reordered = tuple(reversed(PROBES))
    assert probe_set_hash(PROBES) == probe_set_hash(reordered)
    mutated = (*PROBES[1:], CodeProbe(PROBES[0].probe_id, PROBES[0].query + " X",
                                      PROBES[0].answer_paths))
    assert probe_set_hash(mutated) != probe_set_hash(PROBES)


# ── M-C3: retrieval — code lane vs docstring-only baseline ────────────────────────────────

def _seed_code(store: VectorStore, sources: dict[str, str], embedder: HashingEmbedder) -> None:
    for path, src in sources.items():
        chunks = derive_code_chunks(path, src)
        vecs = embedder.embed_documents([c.text for c in chunks])
        blob = hashlib.sha256(src.encode()).hexdigest()
        store.add(code_rows(path, blob, chunks, vecs))


# The query terms live ONLY in identifiers/bodies (not docstrings/comments), so the
# docstring-only baseline (codedoc) cannot see them while the code lane (L0a/L0b) can.
_SOURCES = {
    "core/store.py": (
        '"""State container."""\n'
        "def search_nearest_neighbour_embedded_chunks_lancedb(vector):\n"
        "    return vector\n"
    ),
    "core/parser.py": (
        '"""A helper."""\n'
        "def tokenize_split_overlapping_character_windows(raw):\n"
        "    return raw\n"
    ),
    "core/misc.py": (
        '"""Assorted unrelated utilities for configuration and logging."""\n'
        "def configure(level):\n"
        "    return level\n"
    ),
}
_PROBES3 = (
    CodeProbe("nn", "nearest neighbour embedded chunks lancedb", frozenset({"core/store.py"})),
    CodeProbe("win", "tokenize split overlapping character windows",
              frozenset({"core/parser.py"})),
    CodeProbe("cfg", "configuration and logging utilities", frozenset({"core/misc.py"})),
)


class _DictEmbedder:
    """A fully controlled embedder: `embed_query` maps a probe query to an exact fixed vector, so a
    ranking is deterministic and a lane-beats-baseline ORDERING (not a fragile lexical accident) can
    be asserted. `embed_documents` is unused here — rows are inserted with hand-built vectors."""

    def __init__(self, queries: dict[str, list[float]]):
        self._q = queries

    def embed_query(self, text: str) -> list[float]:
        return self._q[text]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._q.get(t, [0.0] * _DIM) for t in texts]


def _code_row(path: str, layer: str, vec: list[float], idx: int) -> dict[str, object]:
    return {"id": f"{path}:{layer}:{idx}", "digest": path, "title": path,
            "source_path": path, "chunk_index": idx, "provenance": Provenance.CODE.value,
            "text": f"{path} {layer}", "layer": layer, "qualname": "",
            "line_start": 0, "line_end": 0, "vector": vec}


def _e(i: int) -> list[float]:
    v = [0.0] * _DIM
    v[i] = 1.0
    return v


def test_mc3_lane_beats_docstring_only_baseline(tmp_path):
    """A controlled ORDERING signal: the answer's terms live in its CODE (a code_text chunk matching
    the query), a decoy's terms live in its DOCSTRING (a codedoc chunk matching the query). The lane
    (all layers) ranks the answer above the decoy; the docstring-only baseline ranks the decoy above
    the answer — so the lane strictly beats the baseline (F-CI3's bar, met)."""
    from core.stores.vectorstore import LAYER_CODE_TEXT, LAYER_CODEDOC
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    # probe P1 queries dim 0; P2 queries dim 2. mix vector is close-but-not-equal to the axis.
    mix0 = [0.9, 0.1, 0.0, 0.0] + [0.0] * (_DIM - 4)
    mix2 = [0.0, 0.0, 0.9, 0.1] + [0.0] * (_DIM - 4)
    store.add([
        # answer a.py: code MATCHES the query axis, docstring is orthogonal
        _code_row("a.py", LAYER_CODE_TEXT, _e(0), 0),
        _code_row("a.py", LAYER_CODEDOC, _e(1), 1),
        # decoy da.py: docstring matches the query axis, code is orthogonal
        _code_row("da.py", LAYER_CODEDOC, mix0, 0),
        _code_row("da.py", LAYER_CODE_TEXT, _e(1), 1),
        _code_row("b.py", LAYER_CODE_TEXT, _e(2), 0),
        _code_row("b.py", LAYER_CODEDOC, _e(3), 1),
        _code_row("db.py", LAYER_CODEDOC, mix2, 0),
        _code_row("db.py", LAYER_CODE_TEXT, _e(3), 1),
    ])
    emb = _DictEmbedder({"q1": _e(0), "q2": _e(2)})
    probes = (CodeProbe("p1", "q1", frozenset({"a.py"})),
              CodeProbe("p2", "q2", frozenset({"b.py"})))

    res = run_mc3(emb, store, probes=probes, pool=50)
    by_id = {r.probe_id: r for r in res.readings}
    # the lane ranks the answer #1; the docstring-only baseline ranks the decoy above it (rank > 1).
    for pid in ("p1", "p2"):
        assert by_id[pid].lane_rank == 1
        base_rank = by_id[pid].baseline_rank
        assert base_rank is not None and base_rank > 1
    assert res.lane_wins == 2 and res.baseline_wins == 0
    assert res.catastrophic_regressions == 0
    assert res.lane_mrr > res.baseline_mrr
    assert res.verdict is MC3Verdict.LANE_BEATS_BASELINE
    # reproducible: a second run over the same store gives byte-identical readings
    assert run_mc3(emb, store, probes=probes, pool=50).readings == res.readings
    assert "verdict=lane-beats-baseline" in res.table()


def test_mc3_no_signal_when_lane_equals_baseline(tmp_path):
    """F-CI3 path: with the lane restricted to the baseline layers every probe ties, so the
    majority-beat fails and the verdict is NO_SIGNAL — a result, not a crash (still seals)."""
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    emb = HashingEmbedder(dim=_DIM)
    _seed_code(store, _SOURCES, emb)
    res = run_mc3(emb, store, probes=_PROBES3, pool=50,
                  lane_layers=BASELINE_LAYERS, baseline_layers=BASELINE_LAYERS)
    assert res.lane_wins == 0 and res.baseline_wins == 0
    assert res.verdict is MC3Verdict.NO_SIGNAL


def test_ranked_paths_dedupes_by_source_and_filters_layer(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    emb = HashingEmbedder(dim=_DIM)
    _seed_code(store, _SOURCES, emb)
    lane = ranked_paths("nearest neighbour embedded chunks lancedb", emb, store,
                        layers=LANE_LAYERS, pool=50)
    paths = [p for p, _ in lane]
    assert paths[0] == "core/store.py"
    assert len(paths) == len(set(paths)), "one entry per source path"


# ── M-C4: cross-space geometry — informative vs degenerate ────────────────────────────────

def _rand_vec(seed: int, dims: range) -> list[float]:
    v = [0.0] * _DIM
    for d in dims:
        h = int(hashlib.sha256(f"{seed}:{d}".encode()).hexdigest(), 16)
        v[d] = (h % 1000) / 1000.0 + 0.1
    return v


def _add_raw(store: VectorStore, prov: Provenance, vectors: list[list[float]], tag: str) -> None:
    rows = []
    for i, vec in enumerate(vectors):
        rows.append({
            "id": f"{tag}:{i}", "digest": f"{tag}{i}", "title": tag,
            "source_path": f"{tag}/{i}", "chunk_index": i,
            "provenance": prov.value, "text": f"{tag} {i}", "vector": vec,
        })
    store.add(rows)


def test_mc4_informative_when_classes_share_the_space(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    full = range(_DIM)
    _add_raw(store, Provenance.CODE, [_rand_vec(s, full) for s in range(30)], "code")
    _add_raw(store, Provenance.AUTHORED_SOLO,
             [_rand_vec(s, full) for s in range(100, 130)], "note")
    res = run_mc4(store, sample=30, seed=0)
    assert res.n_code == 30 and res.n_note == 30
    assert res.verdict is MC4Verdict.INFORMATIVE
    assert res.overlap >= res.threshold


def test_mc4_degenerate_when_classes_occupy_orthogonal_subspaces(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    lo, hi = range(0, _DIM // 2), range(_DIM // 2, _DIM)
    # code lives in the low half, notes in the high half → cross cosine ≈ 0, within-class high
    _add_raw(store, Provenance.CODE, [_rand_vec(s, lo) for s in range(30)], "code")
    _add_raw(store, Provenance.AUTHORED_SOLO,
             [_rand_vec(s, hi) for s in range(100, 130)], "note")
    res = run_mc4(store, sample=30, seed=0)
    assert res.cross_median < 0.05
    assert res.verdict is MC4Verdict.DEGENERATE


def test_cosine_basic():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


# ── M-C5: reader-scale posture (mechanics; the 7k reading parks/one-off) ──────────────────

def test_mc5_measures_the_posture(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    emb = HashingEmbedder(dim=_DIM)
    _add_raw(store, Provenance.CODE, [_rand_vec(s, range(_DIM)) for s in range(80)], "code")
    res = run_mc5(emb, store)
    assert res.n_code_rows == 80
    assert res.all_rows_s >= 0.0 and res.search_s >= 0.0
    assert res.viable  # trivially under the loose ceiling at this scale
    assert "M-C5 code_rows=80" in res.summary()
