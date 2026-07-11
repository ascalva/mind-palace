"""ops/supersede.py — owner CLI resolve + declare (hermetic stores)."""

import pytest

from core.stores.authored_supersession import AuthoredSupersessionStore
from core.stores.catalog import VaultCatalog
from ops.supersede import AmbiguousRef, declare, resolve


@pytest.fixture
def catalog(tmp_path):
    c = VaultCatalog(tmp_path / "cat.sqlite")
    c.record("/vault/janus_notes/note-2026-07-11-000843.md", "d" * 64, "Ouroboros")
    c.record("/vault/janus_notes/note-2026-07-12-091500.md", "e" * 64, "Ouroboros, fixed")
    return c


def test_resolve_by_suffix_and_ambiguity(catalog):
    path, digest = resolve(catalog, "note-2026-07-11-000843.md")
    assert path.endswith("000843.md") and digest == "d" * 64
    with pytest.raises(AmbiguousRef):
        resolve(catalog, ".md")                      # matches both — refuse, never guess
    with pytest.raises(AmbiguousRef):
        resolve(catalog, "no-such-note.md")          # matches none


def test_declare_records_owner_edge(catalog, tmp_path):
    store = AuthoredSupersessionStore(tmp_path / "sup.sqlite")
    old, new = declare(catalog, store, "note-2026-07-11-000843.md",
                       "note-2026-07-12-091500.md", note="typo fix thread")
    rows = list(store._conn.execute(
        "SELECT superseded, superseding, note FROM authored_supersessions"))
    assert [(r[0], r[1]) for r in rows] == [(old, new)]
    assert rows[0][2] == "typo fix thread"


def test_declare_refuses_selfsame_content(catalog, tmp_path):
    catalog.record("/vault/janus_notes/dup.md", "d" * 64, "same bytes")
    store = AuthoredSupersessionStore(tmp_path / "sup.sqlite")
    with pytest.raises(AmbiguousRef):
        declare(catalog, store, "note-2026-07-11-000843.md", "dup.md")
