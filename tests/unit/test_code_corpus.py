"""core/ingest/code_corpus.py — the code embed lane (bp-092 Items 2–3).

Pure derivation (L0a byte-cover + bit-identical re-derivability = F-CI2; L0b window reuse; L1
prose), the STRUCTURAL CODE mint (F-CI1: no provenance parameter anywhere), and blob-sha-keyed
incremental sync (the falsifier: an unchanged file must re-embed NOTHING). No Ollama — a
deterministic fake embedder.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from core.ingest import code_corpus
from core.ingest.code_corpus import (
    CodeChunk,
    CodeCorpusSync,
    code_rows,
    derive_code_chunks,
)
from core.kernel.ingest.chunk import chunk_text
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.stores.vectorstore import (
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    LAYER_CODEDOC,
    VectorStore,
)
from tests.fixtures.embedding import DIM, FakeEmbedder

_SRC = (
    '"""Module doc."""\n'                        # 1
    "import json\n"                              # 2
    "\n"                                         # 3
    "# a module-grain comment\n"                 # 4
    "TOP = 1\n"                                  # 5
    "\n"                                         # 6
    "class Thing:\n"                             # 7
    '    """Class doc."""\n'                     # 8
    "    def method(self, x):\n"                 # 9
    '        """Method doc."""\n'                # 10
    "        # inner comment\n"                  # 11
    "        return x + TOP\n"                   # 12
    "\n"                                         # 13
    "def top_level():\n"                         # 14
    "    return Thing()\n"                       # 15
)


# ── L0a: byte-cover (F-CI2) + re-derivability + headers ─────────────────────────────────

def _l0a(src: str) -> list[CodeChunk]:
    return [c for c in derive_code_chunks("m.py", src) if c.layer == LAYER_CODE_AST]


def test_l0a_slices_byte_cover_every_source_line_once():
    lines = _SRC.splitlines()
    bodies: list[str] = []
    for c in _l0a(_SRC):
        # each L0a chunk is "header\nbody"; drop the deterministic header line, keep source lines
        _header, _, body = c.text.partition("\n")
        bodies.extend(body.split("\n"))
    assert sorted(bodies) == sorted(lines)      # every source line appears exactly once (F-CI2)


def test_l0a_is_bit_identically_rederivable():
    assert derive_code_chunks("m.py", _SRC) == derive_code_chunks("m.py", _SRC)


def test_l0a_headers_name_the_symbol():
    by_qual = {c.qualname: c for c in _l0a(_SRC)}
    assert by_qual["Thing.method"].text.startswith("# m.py:Thing.method(self, x)")
    assert by_qual["top_level"].text.startswith("# m.py:top_level()")
    assert by_qual[""].text.startswith("# m.py\n")   # the module shell
    # the shell owns the imports/module preamble; the method owns its body incl. its inner comment
    assert "import json" in by_qual[""].text
    assert "# inner comment" in by_qual["Thing.method"].text
    # fiber coordinates carried on the chunk
    assert (by_qual["Thing.method"].line_start, by_qual["Thing.method"].line_end) == (9, 12)


def test_l0a_oversized_slice_hard_splits_via_chunk_text():
    big = "def huge():\n" + "\n".join(f"    x{i} = {i}" for i in range(400))
    chunks = _l0a(big)
    assert len(chunks) > 1                        # a >max_chars symbol splits into several chunks
    assert all(c.qualname == "huge" for c in chunks)


# ── L0b: reuses the ONE window machinery over raw source ────────────────────────────────

def test_l0b_windows_equal_chunk_text_over_raw_source():
    l0b = [c.text for c in derive_code_chunks("m.py", _SRC) if c.layer == LAYER_CODE_TEXT]
    assert l0b == [c.text for c in chunk_text(_SRC)]   # DRY: the note chunker, unmodified


# ── L1: docstrings + comments as prose, source order ────────────────────────────────────

def test_l1_prose_carries_docstrings_and_comments():
    l1 = " ".join(c.text for c in derive_code_chunks("m.py", _SRC) if c.layer == LAYER_CODEDOC)
    assert "Module doc." in l1 and "Method doc." in l1 and "Class doc." in l1
    assert "a module-grain comment" in l1 and "inner comment" in l1


def test_parse_error_file_still_embeds_as_text_plus_shell():
    chunks = derive_code_chunks("bad.py", "def broken(:\n  pass\n")
    layers = {c.layer for c in chunks}
    assert LAYER_CODE_TEXT in layers                 # L0b windows always land
    assert LAYER_CODE_AST in layers                  # a module-shell L0a covers the whole file


# ── the STRUCTURAL CODE mint (F-CI1: no provenance parameter anywhere) ──────────────────

def test_code_rows_hardcode_code_provenance():
    chunks = derive_code_chunks("m.py", _SRC)
    rows = code_rows("m.py", "blobsha", chunks, [[0.0] * DIM for _ in chunks])
    assert {r["provenance"] for r in rows} == {Provenance.CODE.value}
    assert Provenance.CODE not in MIRROR_READABLE    # ∉ the mirror set
    assert all(r["digest"] == "blobsha" for r in rows)
    # ids are (path, layer, content)-scoped so identical text in two layers stays distinct
    assert len({r["id"] for r in rows}) == len(rows)


def test_no_public_api_accepts_a_provenance_parameter():
    """F-CI1, structural: a code-lane API with a provenance argument is a laundering surface."""
    for name, obj in vars(code_corpus).items():
        if name.startswith("_") or not callable(obj):
            continue
        try:
            params = inspect.signature(obj).parameters
        except (ValueError, TypeError):
            continue
        assert "provenance" not in params and "provenances" not in params, name


# ── incremental sync: the seed + the "unchanged file = zero embeds" falsifier ───────────

class _CountingEmbedder(FakeEmbedder):
    def __init__(self) -> None:
        self.embedded_texts = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts += len(texts)
        return super().embed_documents(texts)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "a.py").write_text("def a():\n    return 1\n")
    (r / "b.py").write_text("def b():\n    return 2\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "one")
    return r


def test_seed_then_unchanged_resync_embeds_nothing(repo, tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    emb = _CountingEmbedder()
    sync = CodeCorpusSync(repo=repo, store=store, embedder=emb)

    seeded = sync.seed()
    assert seeded.changed_files == 2 and seeded.embedded_rows > 0
    after_seed = emb.embedded_texts
    code_count = len(store.all_rows(provenances={Provenance.CODE}))
    assert code_count == store.count()               # only code rows in this store

    # a second sync with NO change: zero new embeds, store unchanged (the incremental claim)
    again = sync.sync()
    assert again.changed_files == 0 and again.embedded_rows == 0
    assert emb.embedded_texts == after_seed
    assert len(store.all_rows(provenances={Provenance.CODE})) == code_count


def test_changed_blob_reembeds_only_that_file(repo, tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    emb = _CountingEmbedder()
    sync = CodeCorpusSync(repo=repo, store=store, embedder=emb)
    sync.seed()
    baseline = emb.embedded_texts

    (repo / "a.py").write_text("def a():\n    return 1 + 1  # changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")

    report = sync.sync()
    assert report.changed_files == 1 and report.unchanged_files == 1
    assert emb.embedded_texts > baseline             # a.py re-embedded
    a_rows = [r for r in store.all_rows(provenances={Provenance.CODE})
              if r["source_path"] == "a.py"]
    assert any("changed" in str(r["text"]) for r in a_rows)


def test_vanished_file_is_retained_but_marked_superseded(repo, tmp_path):
    """Keep-and-link (dn-temporal-code-corpus D2, bp-099 — reverses the old delete): a vanished
    file's rows are RETAINED (never deleted) but flipped current=false, so the current-view no
    longer surfaces them while history is preserved."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = CodeCorpusSync(repo=repo, store=store, embedder=FakeEmbedder())
    sync.seed()
    (repo / "b.py").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "drop b")
    report = sync.sync()
    assert report.deleted_files == 1
    assert report.superseded_rows > 0                # b.py's rows flipped, not deleted
    all_code = store.all_rows(provenances={Provenance.CODE})
    # b.py is RETAINED (the falsifier: a superseded row must never be deleted)
    assert {r["source_path"] for r in all_code} == {"a.py", "b.py"}
    b_rows = [r for r in all_code if r["source_path"] == "b.py"]
    assert b_rows and all(r["current"] is False for r in b_rows)
    a_rows = [r for r in all_code if r["source_path"] == "a.py"]
    assert all(r["current"] is True for r in a_rows)


def test_changed_blob_keeps_and_links_old_version(repo, tmp_path):
    """D2: on a changed blob the OLD version survives current=false (same ids, vectors intact) and
    the NEW version lands current=true. The falsifier: any superseded row deleted."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = CodeCorpusSync(repo=repo, store=store, embedder=FakeEmbedder())
    sync.seed()
    before = {(r["id"], r["digest"], tuple(r["vector"]))
              for r in store.all_rows(provenances={Provenance.CODE})
              if r["source_path"] == "a.py"}

    (repo / "a.py").write_text("def a():\n    return 1 + 1  # changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")
    report = sync.sync()
    assert report.superseded_rows > 0

    a_rows = [r for r in store.all_rows(provenances={Provenance.CODE})
              if r["source_path"] == "a.py"]
    old = [r for r in a_rows if r["current"] is False]
    new = [r for r in a_rows if r["current"] is True]
    assert old and new                                     # BOTH versions retained
    assert any("changed" in str(r["text"]) for r in new)   # the new version is current
    assert not any("changed" in str(r["text"]) for r in old)
    # the old rows survive with the SAME ids/digest/vectors (vectors carried through the flip)
    after_old = {(r["id"], r["digest"], tuple(r["vector"])) for r in old}
    assert before <= after_old


def test_default_search_is_current_view_history_is_opt_in(repo, tmp_path):
    """D3: a superseded version never surfaces on the default search; include_superseded=True
    returns it. A deterministic fake embedder + a real temp lance store (no Ollama)."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    emb = FakeEmbedder()
    sync = CodeCorpusSync(repo=repo, store=store, embedder=emb)
    sync.seed()
    (repo / "a.py").write_text("def a():\n    return 42  # newtoken\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")
    sync.sync()

    q = emb.embed_documents(["def a"])[0]
    current_only = store.search(q, k=50, provenances={Provenance.CODE})
    assert current_only and all(r["current"] is True for r in current_only)
    with_history = store.search(q, k=50, provenances={Provenance.CODE},
                                include_superseded=True)
    assert any(r["current"] is False for r in with_history)


def test_current_column_additive_migration_preserves_rows(tmp_path):
    """The `current` migration mirrors the `layer` migration precedent: a store written under the
    old (pre-`current`) schema is migrated in place on the next add — every row preserved
    bit-identically, stamped current=true (correct while the store is HEAD-only), vectors/ids
    untouched. The legacy table is built with raw lancedb (no `current` column)."""
    import lancedb  # type: ignore[import-untyped]

    from core.stores.vectorstore import TABLE
    path = tmp_path / "v.lance"
    chunks = derive_code_chunks("m.py", _SRC)
    landed = code_rows("m.py", "blob0", chunks, [[0.1] * DIM for _ in chunks])
    legacy = [{k: v for k, v in r.items() if k != "current"} for r in landed]   # strip current

    raw = lancedb.connect(str(path))
    raw.create_table(TABLE, data=legacy)                       # a pre-bp-099 (no-current) table

    store = VectorStore(path, dim=DIM)                         # opens the legacy table
    store.add(code_rows("n.py", "blob1", derive_code_chunks("n.py", _SRC),
                        [[0.2] * DIM for _ in derive_code_chunks("n.py", _SRC)]))
    rows = store.all_rows(provenances={Provenance.CODE})
    assert all("current" in r for r in rows)
    m_rows = [r for r in rows if r["source_path"] == "m.py"]
    assert m_rows and all(r["current"] is True for r in m_rows)   # migrated rows stamped true
    # vectors/ids preserved bit-identically for the migrated rows (the falsifier: migration
    # must not touch vectors/ids)
    by_id = {r["id"]: r for r in m_rows}
    for r in legacy:
        assert r["id"] in by_id
        assert list(by_id[r["id"]]["vector"]) == pytest.approx(list(r["vector"]))
