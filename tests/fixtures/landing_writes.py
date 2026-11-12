"""The catalog's six writing methods, each as one write on the catalog `ready` leaves, with the
method of the landing log it calls after the catalog's own statement. The landing log's tests kill
the process, or fail the write, between the two (tests/property/test_landing_log.py); a killed
process imports this module, so it stays small."""

from __future__ import annotations

from collections.abc import Callable

from core.kernel.provenance import Provenance
from core.stores.authored_supersession import owner_declaration
from core.stores.catalog import VaultCatalog


def ready(cat: VaultCatalog) -> None:
    """A catalog on which each write below changes a row of the catalog and the log with it."""
    cat.record("a.md", "d1", "A")
    cat.record("b.md", "d2", "B", provenance=Provenance.CURATED)
    cat.record("gone.md", "dg", "G")
    cat.tombstone("gone.md")


# name: (the landing log's method the write calls after its catalog statement, the write)
WRITES: dict[str, tuple[str, Callable[[VaultCatalog], object]]] = {
    "record": ("store", lambda cat: cat.record("a.md", "d9", "A")),
    "tombstone": ("tombstone", lambda cat: cat.tombstone("a.md")),
    "relabel_provenance": ("relabel", lambda cat: cat.relabel_provenance("curated", "observed")),
    "migrate_rekey_doc_id": ("rekey", lambda cat: cat.migrate_rekey_doc_id(
        "a.md", "id-new", declaration=owner_declaration())),
    "remove": ("empty_path", lambda cat: cat.remove("gone.md")),
    "remove_digest": ("empty_digest", lambda cat: cat.remove_digest("dg")),
}
