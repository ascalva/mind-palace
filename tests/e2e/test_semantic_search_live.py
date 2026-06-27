"""Live gate: semantic search is sane (requires the embedding model). Run: pytest -m live."""

import pytest

from config.loader import get_config
from core.ingest.embed import build_embedder
from core.ingest.index import index_records, semantic_search
from core.ingest.pipeline import ingest_vault
from core.models.ollama_client import OllamaClient
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore

pytestmark = pytest.mark.live


def _embed_model_present() -> bool:
    try:
        cfg = get_config()
        return cfg.embedding.model in OllamaClient(cfg.ollama).list_models()
    except Exception:
        return False


@pytest.mark.skipif(not _embed_model_present(), reason="embedding model not pulled")
def test_semantic_search_ranks_relevant_first(tmp_path):
    cfg = get_config()
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Cooking.md").write_text("Risotto needs constant stirring and warm stock.")
    (vault / "Anxiety.md").write_text(
        "Racing thoughts at 3am again; slow breathing and naming the fear help me calm down."
    )
    (vault / "Cycling.md").write_text("Long climbs in the hills — cadence, gearing, and pacing.")

    raw = RawStore(tmp_path / "raw")
    store = VectorStore(tmp_path / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)

    added = index_records(ingest_vault(vault, raw), embedder, store)
    assert added >= 3

    res = semantic_search("how do I cope with panic and sleeplessness?", embedder, store, k=3)
    assert res
    assert res[0]["title"] == "Anxiety"  # nearest by meaning, not keyword overlap
