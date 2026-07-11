"""Note-version history store — build plan Item 6 (ingest-identity-and-amendment.md §4A).

Version-supersession is keyed on version identity `(doc_id, version_seq)`, NOT content digest, so a
revert stays a LINEAR chain (no cycle, no node merge — Constraint 1); and it lives in a store the
balance math cannot reach — VaultSync no longer holds any edge handle, so nothing leaks a `sign`
into the signed graph (Constraint 2 / Q8). Append-only. Deterministic; no model, no network.
"""

from __future__ import annotations

from core.stores.versions import VersionStore


def test_records_a_monotonic_version_chain(tmp_path):
    vs = VersionStore(tmp_path / "versions.sqlite")
    assert vs.current("a.md") is None
    v1 = vs.record("a.md", "digA")
    v2 = vs.record("a.md", "digB")
    assert (v1.version_seq, v2.version_seq) == (1, 2)
    assert vs.current("a.md") == v2
    assert [v.version_seq for v in vs.history("a.md")] == [1, 2]
    assert vs.supersessions("a.md") == [(1, 2)]


def test_revert_stays_linear_no_cycle(tmp_path):
    # Constraint 1: v1 → v2 → back to v1's exact bytes is v3 (seq 3), distinct from v1, SAME digest.
    vs = VersionStore(tmp_path / "versions.sqlite")
    vs.record("a.md", "digA")            # v1
    vs.record("a.md", "digB")            # v2
    v3 = vs.record("a.md", "digA")       # revert to v1's bytes
    assert v3.version_seq == 3 and v3.digest == "digA"
    assert [v.version_seq for v in vs.history("a.md")] == [1, 2, 3]   # linear, not a 2-cycle
    assert vs.supersessions("a.md") == [(1, 2), (2, 3)]


def test_versions_are_per_document(tmp_path):
    vs = VersionStore(tmp_path / "versions.sqlite")
    vs.record("a.md", "d1")
    vs.record("b.md", "d1")              # same content, different doc → each its own seq-1 chain
    a_current, b_current = vs.current("a.md"), vs.current("b.md")
    assert a_current is not None and b_current is not None   # just recorded, for these exact ids
    assert a_current.version_seq == 1
    assert b_current.version_seq == 1


def test_store_is_append_only(tmp_path):
    vs = VersionStore(tmp_path / "versions.sqlite")
    assert not any(hasattr(vs, m) for m in ("delete", "update", "remove", "reset"))


def test_amendment_records_a_version_and_no_edge_handle_exists(tmp_path):
    # The Item-6 fix end to end: an amendment records a VERSION, and VaultSync has NO edge-store
    # handle at all — so a version relation cannot reach the balance-fed graph (Q8 hazard removed by
    # construction, not by a rel-type-filter discipline).
    from core.ingest.sync import VaultSync
    from core.stores.catalog import VaultCatalog
    from core.stores.rawstore import RawStore
    from core.stores.vectorstore import VectorStore
    from tests.fixtures.embedding import DIM, FakeEmbedder

    vault = tmp_path / "vault"
    vault.mkdir()
    versions = VersionStore(tmp_path / "versions.sqlite")
    catalog = VaultCatalog(tmp_path / "cat.sqlite")
    sync = VaultSync(vault=vault, raw=RawStore(tmp_path / "raw"),
                     store=VectorStore(tmp_path / "v.lance", dim=DIM),
                     catalog=catalog, embedder=FakeEmbedder(), version_store=versions)
    note = vault / "n.md"
    note.write_text("alpha content", encoding="utf-8")
    sync.rescan()
    note.write_text("beta content", encoding="utf-8")
    sync.rescan()

    src = catalog.active_entries()[0].source_path
    assert [v.version_seq for v in versions.history(src)] == [1, 2]   # v1 (ingest) + v2 (amendment)
    assert not hasattr(sync, "edge_store")           # no handle into the signed graph


def test_delete_rel_type_retires_stray_supersedes(tmp_path):
    # The Item-6 migration: any `supersedes` rows a prior build wrote into the EdgeStore can be
    # retired (they must not sit in the balance-fed store); a real semantic edge is untouched.
    from core.complex_types import EdgeSign
    from core.stores.edges import CONTRADICTS, EdgeStore

    edges = EdgeStore(tmp_path / "edges.sqlite")
    edges.add("u", "v", sign=EdgeSign.SUPPORT, rel_type="supersedes")     # a stray legacy row
    edges.add("x", "y", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS)   # a real semantic edge
    assert edges.delete_rel_type("supersedes") == 1
    assert edges.count() == 1 and edges.all(rel_type="supersedes") == []  # contradiction survives
