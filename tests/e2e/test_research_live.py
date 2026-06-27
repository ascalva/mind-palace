"""Live gate: public literature ranked against a real corpus, inside the walls (§16).

The cloud path (fetcher/bridge → S3) is cold-tested with fakes per the build's operational
boundary (no live AWS). This exercises the *core* side end to end with the real embedder over
the golden fixture corpus: emit de-identified criteria, then rank a candidate paper set by
private-corpus relevance — proving the personalization runs locally, corpus never leaving.
Gated on the embedding model being pulled. Run: pytest -m live.
"""

import pytest

from config.loader import get_config
from core.ingest.embed import build_embedder
from core.ingest.index import index_records
from core.ingest.pipeline import ingest_vault
from core.models.ollama_client import OllamaClient
from core.research.criteria import Paper, deidentify
from core.research.rank import rank_literature
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from eval.golden import CORPUS_DIR

pytestmark = pytest.mark.live


def _embedder_present() -> bool:
    try:
        cfg = get_config()
        return cfg.embedding.model in set(OllamaClient(cfg.ollama).list_models())
    except Exception:
        return False


@pytest.mark.skipif(not _embedder_present(), reason="embedding model not pulled")
def test_literature_is_ranked_by_corpus_relevance(tmp_path):
    cfg = get_config()
    raw = RawStore(tmp_path / "raw")
    store = VectorStore(tmp_path / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    # A de-identified request derived from a (would-be personal) question.
    criteria = deidentify("anxiety and sleep", ["anxiety", "sleep", "insomnia"])

    # A clearly on-topic paper vs an off-topic one; the corpus relevance must order them.
    on_topic = Paper(source="openalex", id="A", title="Anxiety and sleep disturbance: a review",
                     abstract="Insomnia and anxiety interact; cognitive behavioral therapy "
                              "improves sleep.", year=2020, venue="J", type="review",
                     doi="10.1/a", url="https://doi.org/10.1/a", is_preprint=False)
    off_topic = Paper(source="openalex", id="B", title="Advances in semiconductor lithography",
                      abstract="Extreme ultraviolet photolithography for chip fabrication.",
                      year=2020, venue="J", type="review", doi="10.1/b",
                      url="https://doi.org/10.1/b", is_preprint=False)

    ranked = rank_literature([off_topic, on_topic], criteria, embedder, store)
    assert ranked[0].paper.id == "A"               # on-topic ranks first via corpus relevance
    assert ranked[0].relevance > ranked[-1].relevance
