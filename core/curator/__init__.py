"""Zone A — background graph compaction / contradiction flagging (cron). BUILD-SPEC §9.

The curator DETECTS and FLAGS; it never rewrites authored ground truth (§8). It reads the
corpus and writes only INTERPRETED findings (near-duplicate / prune / contradiction
candidates) to the derived store; applying any change to authored content is the gated
self-modification loop's job (Phase 10). Runs only in troughs.
"""

from core.curator.curator import (
    CONTRADICTION,
    NEAR_DUPLICATE,
    PRUNE_CANDIDATE,
    ContradictionDetector,
    CurationFinding,
    CurationReport,
    Curator,
    build_curator,
)

__all__ = [
    "CONTRADICTION",
    "ContradictionDetector",
    "CurationFinding",
    "CurationReport",
    "Curator",
    "NEAR_DUPLICATE",
    "PRUNE_CANDIDATE",
    "build_curator",
]
