"""Live gate: the frozen golden set passes against the real embedder (BUILD-SPEC §15).

Ingests the synthetic fixture corpus into a throwaway store and scores the blessed
queries; asserts every query finds its note and nothing regresses vs the baseline.
Run: pytest -m live.
"""

import pytest

from config.loader import get_config
from core.ingest.embed import build_embedder
from core.ingest.index import index_records, semantic_search
from core.ingest.pipeline import ingest_vault
from core.models.ollama_client import OllamaClient
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from eval.golden import CORPUS_DIR, evaluate, load_baseline, load_golden_set, regressions

pytestmark = pytest.mark.live


def _embed_present() -> bool:
    try:
        cfg = get_config()
        return cfg.embedding.model in OllamaClient(cfg.ollama).list_models()
    except Exception:
        return False


@pytest.mark.skipif(not _embed_present(), reason="embedding model not pulled")
def test_golden_set_meets_baseline(tmp_path):
    cfg = get_config()
    raw = RawStore(tmp_path / "raw")
    store = VectorStore(tmp_path / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    def retrieve(query, k):
        return semantic_search(query, embedder, store, k=k)

    report = evaluate(load_golden_set(), retrieve)
    assert report.recall_at_k == 1.0                      # every blessed query finds its note
    assert regressions(report, load_baseline()) == []    # no capability drift vs the anchor
