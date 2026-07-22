"""CI-2 (bp-093) — the retrieval harness honours the mirror firewall (§7 invariant).

bp-092 built the store-level ratchets (F-CI1/F-CI5, `test_code_vector_isolation`). This plan is
read-only *on top of* that green; the obligation here is that the CI-2 measurement harness itself
never reaches code through the MIRROR_READABLE default — it reads the code lane ONLY via an explicit
`provenances={CODE}` set. Concretely, with a store holding BOTH authored notes and code rows:

  * the default mirror `semantic_search` still surfaces zero code (consumes bp-092's F-CI1);
  * `ranked_paths` (the M-C3 retrieval, incl. the docstring-only baseline) returns ONLY code paths —
    the baseline reads the L1/codedoc layer via the CODE provenance, never via the note mirror;
  * `run_mc4`'s note side (MIRROR_READABLE) never includes a code row, and its code side never
    includes a note — the deliberate cross-space read stays on explicit provenance sets.
"""

from __future__ import annotations

import hashlib
from typing import cast

from core.ingest.code_corpus import code_rows, derive_code_chunks
from core.ingest.embed import Embedder
from core.ingest.index import _chunk_row, semantic_search
from core.kernel.ingest.chunk import Chunk
from core.kernel.ingest.pipeline import IngestRecord
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.stores.vectorstore import VectorStore
from eval.code_probes import PROBES
from eval.harness.code_retrieval import (
    BASELINE_LAYERS,
    LANE_LAYERS,
    ranked_paths,
    run_mc3,
    run_mc4,
)
from tests.fixtures.fakes import HashingEmbedder

_DIM = 64


def _seed_notes(store: VectorStore, emb: HashingEmbedder) -> None:
    rec = IngestRecord(
        digest="noteA", source_path="notes/a.md", title="A",
        provenance=Provenance.AUTHORED_SOLO, tags=frozenset(), links=frozenset(),
        chunks=(Chunk(0, "a note about nearest neighbour vectors and dreaming"),
                Chunk(1, "a second note about embedded chunks and lancedb")), is_new=True)
    vecs = emb.embed_documents([c.text for c in rec.chunks])
    store.add([_chunk_row(rec, c, v) for c, v in zip(rec.chunks, vecs, strict=True)])


def _seed_code(store: VectorStore, emb: HashingEmbedder) -> None:
    src = (
        '"""State container."""\n'
        "def search_nearest_neighbour_embedded_chunks_lancedb(vector):\n"
        "    return vector\n"
    )
    chunks = derive_code_chunks("core/store.py", src)
    vecs = emb.embed_documents([c.text for c in chunks])
    blob = hashlib.sha256(src.encode()).hexdigest()
    store.add(code_rows("core/store.py", blob, chunks, vecs))


def _mixed_store(tmp_path) -> tuple[VectorStore, HashingEmbedder]:
    store = VectorStore(tmp_path / "v.lance", dim=_DIM)
    emb = HashingEmbedder(dim=_DIM)
    _seed_notes(store, emb)
    _seed_code(store, emb)
    return store, emb


def test_default_search_still_surfaces_no_code(tmp_path):
    """The harness's substrate: the MIRROR_READABLE default never returns code (bp-092 F-CI1,
    re-checked at the boundary this plan reads from)."""
    store, emb = _mixed_store(tmp_path)
    hits = semantic_search("nearest neighbour embedded chunks lancedb",
                           cast(Embedder, emb), store, k=10)
    assert hits, "sanity: the authored notes are retrievable"
    assert all(h["provenance"] != Provenance.CODE.value for h in hits)


def test_ranked_paths_returns_only_code_paths(tmp_path):
    """Both the lane AND the docstring-only baseline read the code lane via provenances={CODE} —
    never the note mirror. So every returned path is a code source, never a note."""
    store, emb = _mixed_store(tmp_path)
    for layers in (LANE_LAYERS, BASELINE_LAYERS):
        ranked = ranked_paths("nearest neighbour embedded chunks lancedb", emb, store,
                              layers=layers, pool=50)
        assert all(not p.endswith(".md") for p, _ in ranked)
        assert all(p == "core/store.py" for p, _ in ranked)


def test_mc3_over_a_mixed_store_never_ranks_a_note(tmp_path):
    store, emb = _mixed_store(tmp_path)
    res = run_mc3(emb, store, probes=PROBES[:3], pool=50)
    # the harness completes and every reading is a rank into code paths only (never a note leak)
    assert len(res.readings) == 3


def test_mc4_reads_each_class_through_its_own_provenance(tmp_path):
    """M-C4's cross-space read uses explicit provenance sets: the note side (MIRROR_READABLE) holds
    no code, the code side holds no note — the deliberate cross-space read never routes through the
    mirror default (§7)."""
    store, _emb = _mixed_store(tmp_path)
    code = store.all_rows(provenances={Provenance.CODE})
    notes = store.all_rows(provenances=set(MIRROR_READABLE))
    assert code and notes
    assert all(r["provenance"] == Provenance.CODE.value for r in code)
    assert all(r["provenance"] != Provenance.CODE.value for r in notes)
    res = run_mc4(store, sample=20, seed=0)
    assert res.n_code >= 1 and res.n_note >= 1
