"""Zone A — theme clustering / synthesis (cron, mirror-not-oracle). BUILD-SPEC §9.

The dreaming agent clusters the AUTHORED corpus into themes (deterministic, model-free) and
reflects each back to the owner as a lens on their own notes — never external truth. Output
is INTERPRETED + regenerable, self-checked before it is kept, and only runs in troughs.
"""

from core.dreaming.cluster import (
    Cluster,
    NoteVector,
    cluster_notes,
    near_duplicate_pairs,
    note_centroids,
    note_snippets,
)
from core.dreaming.dreamer import Dreamer, Synthesizer, Theme, build_dreamer

__all__ = [
    "Cluster",
    "Dreamer",
    "NoteVector",
    "Synthesizer",
    "Theme",
    "build_dreamer",
    "cluster_notes",
    "near_duplicate_pairs",
    "note_centroids",
    "note_snippets",
]
