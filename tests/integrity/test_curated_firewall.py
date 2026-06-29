"""The curated self-knowledge graph stays OUT of the mirror (Track B / B4) — integrity tier.

B4 ingests the system's own docs as `CURATED` so the Ambassador can explain its architecture.
The load-bearing property: curated material is in its OWN graph and never the authored mirror
(curated ∉ MIRROR_READABLE). A mirror-scoped retrieval cannot surface it; the deliberate,
non-default `provenances={CURATED}` retrieval can — and vice versa. Same firewall as book dreaming.
"""

from pathlib import Path

from core.ingest.curated import curated_sources, ingest_curated
from core.librarian import Librarian
from core.mirror import MirrorView
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.fakes import HashingEmbedder, ReplyServer

DIM = 32


def _ingest_curated_doc(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "CONSTITUTION.md").write_text(
        "# Constitution\nThe model advises; code acts. The sealed core never reaches the network."
    )
    (repo / "docs" / "design.md").write_text(
        "# Design\nThe Ambassador is a reasoning agent that is computationally light."
    )
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    embedder = HashingEmbedder(DIM)
    ingest_curated(
        curated_sources(repo),
        raw=RawStore(tmp_path / "raw"),
        store=store,
        embedder=embedder,
        catalog=VaultCatalog(tmp_path / "c.sqlite"),
        repo_root=repo,
    )
    return store, embedder


def test_curated_docs_are_tagged_curated_and_excluded_from_the_mirror(tmp_path):
    store, _ = _ingest_curated_doc(tmp_path)
    curated = store.all_rows(provenances={Provenance.CURATED})
    assert curated and all(r["provenance"] == "curated" for r in curated)
    # the firewall: a mirror-scoped scan sees NONE of it
    assert store.all_rows(provenances=MIRROR_READABLE) == []
    # and a MirrorView cannot hold it (projection drops every curated row)
    assert len(MirrorView.project(store)) == 0


def test_explain_path_retrieves_curated_only_via_explicit_provenance(tmp_path):
    store, embedder = _ingest_curated_doc(tmp_path)
    lib = Librarian(server=ReplyServer(), embedder=embedder, store=store, k=5)

    # The "explain yourself" path: deliberate, non-default provenances={CURATED}.
    explained = lib.retrieve("how does the Ambassador work", provenances={Provenance.CURATED})
    assert explained and all(r.provenance == "curated" for r in explained)

    # The DEFAULT (mirror) retrieval never surfaces curated material.
    mirror = lib.retrieve("how does the Ambassador work")     # default = MIRROR_READABLE
    assert mirror == []


def test_curated_sources_finds_the_real_self_knowledge_corpus():
    # Smoke: against the real repo, the corpus includes the Constitution + design notes.
    repo_root = Path(__file__).resolve().parents[2]
    sources = curated_sources(repo_root)
    names = {p.name for p in sources}
    assert "CONSTITUTION.md" in names and "CONVENTIONS.md" in names
    assert any("ambassador" in p.name for p in sources)        # the design notes are in scope
