"""An in-memory `AtomTable` for the shared plane (core/stores/plane.py).

The same contract the vector store's LanceDB table meets, held in a dict, so the plane's logic —
landing, currency, the supersession log, purge, the cleared join — can be driven thousands of
times by Hypothesis in milliseconds. `nearest` is exact (brute force, ties broken by atom id), which
is what makes noninterference an exact property here rather than an approximate one.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from core.stores.plane import AtomRecord, Candidate


def cosine_distance(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return 1.0 - dot / (na * nb)


@dataclass
class MemoryAtoms:
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)

    def present(self, atom_ids: Sequence[str]) -> set[str]:
        return {a for a in atom_ids if a in self.rows}

    def insert(self, atoms: Sequence[AtomRecord]) -> int:
        for a in atoms:
            self.rows[a.atom_id] = {"layer": a.layer, "text": a.text, "vector": list(a.vector),
                                    "held": frozenset(), "held_ever": frozenset()}
        return len(atoms)

    def payload(self, atom_ids: Sequence[str]) -> dict[str, tuple[str, Sequence[float]]]:
        return {a: (self.rows[a]["text"], self.rows[a]["vector"])
                for a in atom_ids if a in self.rows}

    def nearest(self, vector: Sequence[float], *, classes: Sequence[str], superseded: bool,
                limit: int) -> list[Candidate]:
        col = "held_ever" if superseded else "held"
        wanted = set(classes)
        ranked = sorted(((cosine_distance(vector, r["vector"]), a, r)
                         for a, r in self.rows.items() if r[col] & wanted),
                        key=lambda t: (t[0], t[1]))
        return [Candidate(atom_id=a, text=r["text"], vector=r["vector"], distance=d)
                for d, a, r in ranked[:limit]]

    def held(self, atom_ids: Sequence[str]) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
        return {a: (self.rows[a]["held"], self.rows[a]["held_ever"])
                for a in atom_ids if a in self.rows}

    def set_held(self, updates: Mapping[str, tuple[frozenset[str], frozenset[str]]]) -> int:
        for a, (h, e) in updates.items():
            self.rows[a]["held"], self.rows[a]["held_ever"] = frozenset(h), frozenset(e)
        return len(updates)

    def delete(self, atom_ids: Sequence[str]) -> int:
        n = 0
        for a in atom_ids:
            n += self.rows.pop(a, None) is not None
        return n

    def ids(self) -> set[str]:
        return set(self.rows)
