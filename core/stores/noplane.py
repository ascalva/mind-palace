"""The plane of an instance that keeps none (dn-palace-lite).

An instance with `[embedding] enabled = false` embeds nothing, so it opens no vector store: no
LanceDB directory is made, no table is read. The readers that would ask the plane (the writer's
UNCHANGED check, the drain's pending set, the query engine's universe, the MCP surface's counts)
are handed this object instead, whose every read answers what an empty plane answers, so a reader
built for the plane needs no second code path, and whose every write refuses. Nothing is ever
landed into it, and nothing an instance holds is ever read from it.

`EmbeddingOff` is the refusal, raised by the factories that would build an embedder or open a
plane for such an instance (`build_embedder`, `open_vector_store`, `open_curated_store`), so a code
path the lite profile did not anticipate fails by name instead of reaching for a server or a
directory, and by any method of this object beyond the reads below.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class EmbeddingOff(RuntimeError):
    """The instance embeds nothing (`[embedding] enabled = false`): it has no embedder and no
    plane, and the operation asked for one."""


def refuse(what: str) -> EmbeddingOff:
    return EmbeddingOff(f"{what}: this instance embeds nothing ([embedding] enabled = false), so "
                        f"it has no embedder and no vector plane")


class NoPlane:
    """An empty plane that never fills. The reads are the plane's (`VectorStore`) with an empty
    answer; a write, or any other method, raises `EmbeddingOff`."""

    def count(self) -> int:
        return 0

    def all_rows(self, *, clearance: Any = None, include_atom_rows: bool = False
                 ) -> list[Mapping[str, Any]]:
        return []

    def search(self, vector: Sequence[float], *, k: int = 5, clearance: Any = None,
               **_: Any) -> list[Mapping[str, Any]]:
        return []

    def rows_for_source(self, source_path: str, *, clearance: Any = None
                        ) -> list[Mapping[str, Any]]:
        return []

    def holds_current(self, source_path: str, digest: str, *, clearance: Any = None) -> bool:
        return False

    def has_digest(self, digest: str, *, clearance: Any = None) -> bool:
        return False

    def current_versions(self, *, clearance: Any = None) -> set[tuple[str, str]]:
        return set()

    def known_atoms(self, atom_ids: Sequence[str]) -> set[str]:
        return set()

    def known_atoms_in(self, atom_ids: Sequence[str], classes: Iterable[Any]) -> set[str]:
        return set()

    def delete_source(self, source_path: str) -> None:
        """A retire's plane step: the plane holds nothing at any path, so there is nothing to
        take out, and the retire goes on to its key."""
        return None

    def add(self, rows: Iterable[Mapping[str, Any]]) -> int:
        raise refuse("adding rows to the vector plane")

    def __getattr__(self, name: str) -> Any:
        raise refuse(f"the vector plane's {name!r}")
