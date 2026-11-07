"""The plane's vector read goes through Arrow and NumPy and returns, bit for bit, the lists of
floats the row-by-row `to_list` read returned, in a half and a single precision store."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.kernel.clearance import MIRROR_READ
from core.stores import vectorstore as V
from core.stores.vectorstore import VectorStore

DIM = 24


def _old_payload(atoms: V._LanceAtoms, ids: list[str]) -> dict[str, tuple[str, Any]]:
    """The read this replaced, verbatim."""
    out: dict[str, tuple[str, Any]] = {}
    for batch in V._batched(ids):
        for r in atoms._scan(f"{V._id_in(batch)} AND {V._PROSE_ATOM}", ["id", "text", "vector"]):
            out[str(r["id"])] = (str(r["text"]), cast(list[float], r["vector"]))
    return out


@pytest.mark.parametrize("precision", ["float16", "float32"])
def test_payload_vectors_are_bitwise_the_old_reads(tmp_path: Path, precision: str) -> None:
    store = VectorStore(path=tmp_path / "v.lance", dim=DIM, precision=cast(Any, precision))
    rng = np.random.default_rng(3)
    rows = [{"id": f"n{i}.md:{i}", "digest": f"d{i}", "title": f"t{i}", "source_path": f"n{i}.md",
             "chunk_index": 0, "provenance": "authored-solo", "text": f"text {i}",
             "vector": rng.standard_normal(DIM).astype(np.float32).tolist()} for i in range(40)]
    store.add(rows)
    atoms = V._LanceAtoms(store)
    ids = sorted(atoms.ids())
    assert len(ids) == 40
    new, old = atoms.payload(ids), _old_payload(atoms, ids)
    assert new.keys() == old.keys()
    for k in new:
        assert new[k][0] == old[k][0]
        assert isinstance(new[k][1], list) and all(type(x) is float for x in new[k][1])
        assert np.array_equal(np.asarray(new[k][1]), np.asarray(old[k][1]))
        assert [x.hex() for x in new[k][1]] == [x.hex() for x in old[k][1]]    # bit for bit
    # and what a reader sees: the rows' vectors, so every score computed from them
    by_text = {t: v for t, v in old.values()}
    got = {r["text"]: r["vector"] for r in store.all_rows(clearance=MIRROR_READ)}
    assert got.keys() == by_text.keys() and all(got[t] == by_text[t] for t in got)
    assert atoms.payload([]) == {}
