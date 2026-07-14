"""The curated literature store (bp-029 Item 28) — a SEPARATE LanceDB, gitignored, curated-only.

Deterministic: hand-built vectors, no Ollama. Proves `open_curated_store` aims the proven
`VectorStore` at `cfg.paths.curated_store` (never the mirror `vector_store`), that a
`provenance="curated"` row round-trips, that the mirror firewall excludes it structurally
(curated ∉ MIRROR_READABLE), and that the default path is under `data/` → git-ignored (Inv 11:
the embedded full text never enters git).
"""

import dataclasses
import subprocess

from config.loader import REPO_ROOT, load_config
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.curated_store import open_curated_store


def _curated_row(rid: str, vec: list[float]) -> dict[str, object]:
    return {
        "id": rid, "digest": rid, "title": "t", "source_path": f"reference:{rid}",
        "chunk_index": 0, "provenance": Provenance.CURATED.value, "text": "x", "vector": vec,
    }


def _cfg_with(tmp_path, dim=3):
    cfg = load_config()
    return dataclasses.replace(
        cfg,
        paths=dataclasses.replace(cfg.paths, curated_store=tmp_path / "curated.lance"),
        embedding=dataclasses.replace(cfg.embedding, dim=dim),
    )


def test_open_curated_store_is_separate_and_roundtrips(tmp_path):
    cfg = _cfg_with(tmp_path)
    store = open_curated_store(cfg)
    assert store.path == cfg.paths.curated_store       # aimed at the curated path
    assert store.path != cfg.paths.vector_store        # NOT the mirror store — a distinct file
    assert store.dim == 3                              # shares the embedder dimension

    store.add([_curated_row("a", [1.0, 0.0, 0.0])])
    assert store.count() == 1
    rows = store.all_rows()
    assert rows[0]["provenance"] == "curated"
    assert rows[0]["source_path"] == "reference:a"     # curated marker, never a mirror path


def test_curated_rows_are_excluded_from_the_mirror_firewall(tmp_path):
    # Structural, not by convention: CURATED is not in MIRROR_READABLE, so a mirror-scoped
    # read (all_rows / search with provenances=MIRROR_READABLE) cannot surface curated text.
    assert Provenance.CURATED not in MIRROR_READABLE
    store = open_curated_store(_cfg_with(tmp_path))
    store.add([_curated_row("a", [1.0, 0.0, 0.0])])
    assert store.all_rows(provenances=MIRROR_READABLE) == []
    assert store.search([1.0, 0.0, 0.0], k=5, provenances=MIRROR_READABLE) == []
    assert {r["id"] for r in store.search([1.0, 0.0, 0.0], k=5,
                                          provenances={Provenance.CURATED})} == {"a"}


def test_default_curated_path_is_under_data_and_gitignored():
    cfg = load_config()
    assert "data" in cfg.paths.curated_store.parts      # lives under data/ (never the repo tree)
    r = subprocess.run(
        ["git", "check-ignore", str(cfg.paths.curated_store)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert r.returncode == 0, f"curated_store is NOT gitignored (Inv 11 breach): {r.stdout!r}"
