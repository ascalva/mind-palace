"""Live gate: the dreaming agent synthesizes a theme over a real corpus (BUILD-SPEC §9).

End to end through the real embedder + the synthesis model over the golden fixture corpus:
deterministic clustering groups related notes, the model reflects a theme back, the result is
stored as an INTERPRETED dream, and the grounding self-check runs (mirror, not oracle). Gated
on the synthesis-tier model being pulled (it is large — `ollama pull` it to exercise this).
Run: pytest -m live.
"""

import pytest

from config.loader import get_config
from core.dreaming import Dreamer
from core.ingest.embed import build_embedder
from core.ingest.index import index_records
from core.ingest.pipeline import ingest_vault
from core.models import build_model_server
from core.models.ollama_client import OllamaClient
from core.stores.derived import DREAM, DerivedStore
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from eval.golden import CORPUS_DIR

pytestmark = pytest.mark.live


def _models_present() -> bool:
    try:
        cfg = get_config()
        have = set(OllamaClient(cfg.ollama).list_models())
        return {cfg.embedding.model, cfg.model_for_tier("synthesis").name} <= have
    except Exception:
        return False


@pytest.mark.skipif(not _models_present(), reason="synthesis-tier model not pulled")
def test_dreaming_synthesizes_a_grounded_theme(tmp_path):
    cfg = get_config()
    raw = RawStore(tmp_path / "raw")
    store = VectorStore(tmp_path / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    server = build_model_server(cfg)
    dreamer = Dreamer(
        store=store,
        synthesize=lambda messages: server.chat("synthesis", messages),
        derived=DerivedStore(tmp_path / "derived.sqlite"),
        threshold=0.45,            # the small fixture corpus must form at least one theme
        min_cluster_size=2,
    )
    if not dreamer.clusters():
        pytest.skip("fixture corpus did not cluster at the test threshold")

    themes = dreamer.dream()
    assert themes                                            # a theme was synthesized
    assert themes[0].summary.strip()
    # The grounding mechanism fired end to end (PASS/FAIL depends on the live generation's
    # citation discipline, asserted deterministically in test_dreamer — not here).
    assert any(f.directive == "grounded-citations" for f in themes[0].check.findings)
    assert dreamer.derived.count(kind=DREAM) == len(themes)  # persisted as INTERPRETED dreams
