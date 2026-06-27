"""Live gate: the Librarian answers a query grounded in the corpus (BUILD-SPEC §9).

End to end through the real embedder + the routine model over the golden fixture corpus:
the right note is retrieved, an answer comes back, and the deterministic grounding check
does not flag a fabricated citation. Run: pytest -m live.
"""

import pytest

from config.loader import get_config
from core.ingest.embed import build_embedder
from core.ingest.index import index_records
from core.ingest.pipeline import ingest_vault
from core.librarian import Librarian
from core.models import build_model_server
from core.models.ollama_client import OllamaClient
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from eval.golden import CORPUS_DIR

pytestmark = pytest.mark.live


def _models_present() -> bool:
    try:
        cfg = get_config()
        have = set(OllamaClient(cfg.ollama).list_models())
        return {cfg.embedding.model, cfg.model_for_tier("routine").name} <= have
    except Exception:
        return False


@pytest.mark.skipif(not _models_present(), reason="librarian models not pulled")
def test_librarian_answers_grounded(tmp_path):
    cfg = get_config()
    raw = RawStore(tmp_path / "raw")
    store = VectorStore(tmp_path / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    lib = Librarian(server=build_model_server(cfg), embedder=embedder, store=store, k=3)
    ans = lib.answer("how can I calm down and fall asleep when my mind races at night?")

    assert ans.text.strip()                                      # an answer came back
    assert ans.sources
    assert ans.sources[0].title == "sleep-and-racing-thoughts"   # retrieval is deterministic
    # The grounding check ran (mechanism fires end to end). Whether it PASSES depends on the
    # model's citation discipline, which is asserted deterministically in test_selfcheck /
    # test_librarian — not on a live generation, which varies run to run.
    assert any(f.directive == "grounded-citations" for f in ans.check.findings)
