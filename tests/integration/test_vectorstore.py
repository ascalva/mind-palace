"""LanceDB vector store: nearest-neighbour search, the provenance firewall, dim guard.

Deterministic — hand-built vectors, no Ollama needed.
"""

import pytest

from core.provenance import Provenance
from core.stores.vectorstore import VectorStore


def _row(rid, vec, prov, title="t"):
    return {
        "id": rid, "digest": rid, "title": title, "source_path": "p",
        "chunk_index": 0, "provenance": prov.value, "text": "x", "vector": vec,
    }


def test_search_returns_nearest(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("a", [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("b", [0.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("c", [0.0, 0.0, 1.0], Provenance.AUTHORED_SOLO),
    ])
    assert vs.count() == 3
    res = vs.search([0.9, 0.1, 0.0], k=1)
    assert res[0]["id"] == "a"


def test_provenance_filter_is_the_mirror_firewall(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("auth", [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("obs", [1.0, 0.0, 0.0], Provenance.OBSERVED),  # identical vector, observed
    ])
    res = vs.search([1.0, 0.0, 0.0], k=5, provenances={Provenance.AUTHORED_SOLO})
    assert {r["id"] for r in res} == {"auth"}  # observed excluded from the mirror


def test_all_rows_scans_everything_and_filters_by_provenance(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("auth", [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("interp", [0.0, 1.0, 0.0], Provenance.INTERPRETED),
    ])
    assert {r["id"] for r in vs.all_rows()} == {"auth", "interp"}
    # The dreaming agent clusters over the AUTHORED mirror only (the firewall).
    mirror = vs.all_rows(provenances={Provenance.AUTHORED_SOLO})
    assert {r["id"] for r in mirror} == {"auth"}
    assert mirror[0]["vector"] == [1.0, 0.0, 0.0]      # vectors come back as plain lists


def test_all_rows_is_empty_before_any_write(tmp_path):
    assert VectorStore(tmp_path / "v.lance", dim=3).all_rows() == []


def test_dim_mismatch_raises(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    with pytest.raises(ValueError):
        vs.add([_row("x", [1.0, 0.0], Provenance.AUTHORED_SOLO)])
