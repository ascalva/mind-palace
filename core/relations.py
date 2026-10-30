"""Signed relation edges — the typed/signed edge ingest (REASONING-COMPLEX-BUILD §5 H1; the
`edges` store's own docstring: "explicit contradictions/links a detector or the owner asserts").

`core/stores/edges.py` holds the edges the cosine graph cannot carry — supports (+1), contradicts
(−1), contextualizes (+1, weaker) — and `core/kernel/complex/balance.py` reads them for the signed
Laplacian and frustrated triangles (H3: "contradiction, rigorously"). Until now nothing wrote one.
Two producers, kept apart by provenance:

* **Authored** — a note's own column-0 properties, `supports:: [[Other note]]`,
  `contradicts:: [[…]]`, `contextualizes:: [[…]]`, resolved by title through the catalog. These are
  the owner's assertions: provenance `authored-solo`, weight 1.
* **Interpreted** — a model-mediated detector. Candidates come from the σ-backbone: note pairs
  similar enough to be about the same thing (cosine ≥ σ) but under the near-duplicate line, most
  similar first. The synthesis tier labels each pair; `unrelated` writes nothing, anything else is
  an edge with provenance `interpreted` and w = the pair's cosine. Nothing here can mint an
  authored edge from model output — provenance is fixed by the producer, not by the label.

Edges point from the earlier note to the later one (t(u) < t(v)), the orientation the
supersession-candidate score `s(C, D) = sim · 1[contradiction] · 1[t(D) > t(C)]` reads. The detector
wakes a model, so it runs on demand only (`palace relate`).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from core.kernel.clearance import MIRROR_READ, Clearance
from core.kernel.complex_types import EdgeSign
from core.kernel.config import Config, get_config
from core.kernel.constitution import Message
from core.kernel.ingest.logseq import _LINK, parse_note
from core.kernel.provenance import Provenance
from core.stores.vectorstore import open_vector_store

RELATIONS: dict[str, tuple[EdgeSign, float]] = {  # label -> (sign, weight factor)
    "supports": (EdgeSign.SUPPORT, 1.0),
    "contradicts": (EdgeSign.CONTRADICT, 1.0),
    "contextualizes": (EdgeSign.SUPPORT, 0.5),
}
LABELS = (*RELATIONS, "unrelated")
NOTE_CHARS = 1500

_SYSTEM = (
    "You compare two notes written by the same person. Answer with exactly one word:\n"
    "supports — note B agrees with or reinforces note A\n"
    "contradicts — note B disagrees with or is in tension with note A\n"
    "contextualizes — note B gives background or context for note A without taking a side\n"
    "unrelated — there is no meaningful relation"
)


@dataclass(frozen=True)
class Note:
    source_path: str
    title: str
    digest: str
    updated_at: str


@dataclass
class RelateReport:
    authored: int = 0
    judged: int = 0
    written: dict[str, int] = field(default_factory=dict)
    skipped_existing: int = 0

    def __str__(self) -> str:
        made = ", ".join(f"{k}={v}" for k, v in sorted(self.written.items())) or "none"
        return (
            f"authored={self.authored} judged={self.judged} interpreted: {made} "
            f"(skipped {self.skipped_existing} pairs already related)"
        )


def parse_label(text: str) -> str:
    """The first allowed label in the model's answer; anything else counts as `unrelated`."""
    for word in text.lower().replace("—", " ").split():
        word = word.strip(".,:;*\"'`")
        if word in LABELS:
            return word
    return "unrelated"


class EdgeSink(Protocol):
    def add(
        self,
        u: str,
        v: str,
        *,
        sign: EdgeSign,
        rel_type: str,
        w: float = 1.0,
        provenance: str = "interpreted",
        created_at: str | None = None,
    ) -> Any: ...
    def all(self, *, rel_type: str | None = None) -> list[Any]: ...


class Catalog(Protocol):
    def active_entries(self) -> list[Any]: ...


class Rows(Protocol):
    def all_rows(self, *, clearance: Clearance[Provenance]) -> Sequence[Mapping[str, Any]]: ...


@dataclass
class RelationDetector:
    config: Config
    edges: EdgeSink
    catalog: Catalog | None
    vectors: Rows
    chat: Callable[[list[Message]], str] | None = None  # None = authored edges only
    max_pairs: int = 24

    def notes(self) -> list[Note]:
        """Active authored-solo notes that exist on disk, oldest first."""
        if self.catalog is None:
            return []
        out = [
            Note(e.source_path, e.title, e.digest, _when(Path(e.source_path)))
            for e in self.catalog.active_entries()
            if e.provenance == Provenance.AUTHORED_SOLO.value and Path(e.source_path).exists()
        ]
        return sorted(out, key=lambda n: (n.updated_at, n.source_path))

    # authored ---------------------------------------------------------------------------------
    def authored(self, notes: list[Note]) -> int:
        by_title = {n.title.lower(): n for n in notes}
        vault = self.config.ingestion.vault.path
        count = 0
        for n in notes:
            path = Path(n.source_path)
            if not path.exists():
                continue
            props = parse_note(path, vault).properties
            for rel, (sign, factor) in RELATIONS.items():
                for target in _LINK.findall(props.get(rel, "")) or (
                    [props[rel]] if props.get(rel) else []
                ):
                    other = by_title.get(target.strip().lower())
                    if other is None or other.digest == n.digest:
                        continue
                    self.edges.add(
                        n.digest,
                        other.digest,
                        sign=sign,
                        rel_type=rel,
                        w=factor,
                        provenance=Provenance.AUTHORED_SOLO.value,
                    )
                    count += 1
        return count

    # interpreted ------------------------------------------------------------------------------
    def candidates(self, notes: list[Note]) -> list[tuple[Note, Note, float]]:
        rows = self.vectors.all_rows(clearance=MIRROR_READ)
        by_src: dict[str, list[np.ndarray]] = {}
        for r in rows:
            by_src.setdefault(str(r["source_path"]), []).append(
                np.asarray(r["vector"], dtype=np.float64)
            )
        ordered = [n for n in notes if n.source_path in by_src]
        if len(ordered) < 2:
            return []
        mat = np.asarray([np.mean(by_src[n.source_path], axis=0) for n in ordered])
        mat /= np.linalg.norm(mat, axis=1, keepdims=True)
        sims = mat @ mat.T
        lo, hi = self.config.dreaming.similarity_threshold, self.config.dreaming.near_dup_threshold
        pairs = [
            (ordered[i], ordered[j], float(sims[i, j]))
            for i in range(len(ordered))
            for j in range(i + 1, len(ordered))
            if lo <= sims[i, j] < hi
        ]
        return sorted(pairs, key=lambda p: -p[2])

    def run(self) -> RelateReport:
        report = RelateReport()
        notes = self.notes()
        report.authored = self.authored(notes)
        if self.chat is None:
            return report
        related = {frozenset((e.u, e.v)) for e in self.edges.all()}
        for a, b, cos in self.candidates(notes):
            if report.judged >= self.max_pairs:
                break
            if frozenset((a.digest, b.digest)) in related:
                report.skipped_existing += 1
                continue
            label = parse_label(self.chat(self._messages(a, b)))
            report.judged += 1
            if label in RELATIONS:
                sign, factor = RELATIONS[label]
                self.edges.add(
                    a.digest,
                    b.digest,
                    sign=sign,
                    rel_type=label,
                    w=round(cos * factor, 4),
                    provenance=Provenance.INTERPRETED.value,
                )
                report.written[label] = report.written.get(label, 0) + 1
        return report

    def _messages(self, a: Note, b: Note) -> list[Message]:
        return [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": f"Note A ({a.title}):\n{_text(a)}\n\nNote B ({b.title}):\n{_text(b)}",
            },
        ]


_STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})-(\d{6})")


def _when(path: Path) -> str:
    """When a note was written: the `note-YYYY-MM-DD-HHMMSS` stamp the capture app puts in the
    name, else the file's mtime. Orders edges earlier → later."""
    m = _STAMP.search(path.name)
    if m:
        return f"{m.group(1)}T{m.group(2)}"
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).strftime("%Y-%m-%dT%H%M%S")


def _text(n: Note) -> str:
    path = Path(n.source_path)
    return path.read_text(encoding="utf-8", errors="replace")[:NOTE_CHARS] if path.exists() else ""


def build_relation_detector(
    config: Config | None = None, *, with_model: bool = True, max_pairs: int = 24
) -> RelationDetector:
    from core.stores.catalog import VaultCatalog
    from core.stores.edges import open_edge_store

    cfg = config or get_config()
    chat = None
    if with_model:
        from core.models import build_model_server

        server = build_model_server(cfg)
        chat = lambda messages: server.chat("synthesis", messages, think=False, temperature=0.0)  # noqa: E731
    return RelationDetector(
        config=cfg,
        edges=open_edge_store(cfg),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        vectors=open_vector_store(cfg),
        chat=chat,
        max_pairs=max_pairs,
    )
