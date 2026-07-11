"""Synthetic, deterministic corpus generators — no model, no I/O of their own.

`vector_rows` produces the ``{digest, title, text, vector}`` dicts the deterministic
clustering path (`core.dreaming.cluster`) consumes. `write_vault` lays synthetic notes on
disk for the ingest pipeline. Both are reproducible: same args -> same bytes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def vector_rows(specs: list[tuple[str, str, list[float]]]) -> list[dict[str, Any]]:
    """Build chunk rows from ``(digest, title, vector)`` triples.

    A single text per row is enough for clustering (it averages vectors per digest).
    """
    return [
        {"digest": digest, "title": title, "text": title, "vector": list(vec)}
        for digest, title, vec in specs
    ]


def write_vault(root: Path, notes: dict[str, str]) -> Path:
    """Write ``{filename: markdown}`` notes into ``root`` and return it."""
    root.mkdir(parents=True, exist_ok=True)
    for name, body in notes.items():
        (root / name).write_text(body)
    return root
