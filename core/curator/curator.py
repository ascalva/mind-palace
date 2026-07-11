"""The curator (BUILD-SPEC §9) — Zone A, cron/trough tier.

Background compaction that **DETECTS and FLAGS — it never rewrites the owner's authored
ground truth** (§8: "the curator operates on the interpreted layer and must never silently
rewrite the explicit layer"). It only *reads* the authored corpus; everything it produces is
an `INTERPRETED` finding in the derived store (regenerable). Authored near-duplicates are
flagged as merge *candidates*, never auto-merged — applying a merge or prune to authored
content is a corpus mutation that belongs to the gated self-modification loop (Phase 10,
propose → approve → execute → validate → rollback), not an unattended cron.

Findings produced (all `kind=FINDING`, `subkind` is the finding type):
  - near_duplicate : distinct authored notes whose embeddings are near-identical. Deterministic.
  - prune_candidate: derived vector rows orphaned from the raw store — *dead derived weight*,
                     safe to regenerate away (not authored loss). Deterministic.
  - contradiction  : within-theme contradictions. This is a model JUDGMENT, so it is an
                     injectable seam, *deferred* (produces nothing) until a detector is
                     supplied — exactly like the §4 judge seam, never faked with heuristics.

Trough-only: a `curate` job routes to the synthesis tier (`scheduler.router`), gated off while
the owner is present by the supervisor's foreground check (`HEAVY_TIERS`, Phase 3) — §13.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from config.loader import Config
from core.attestation import Attestor
from core.dreaming.cluster import (
    Cluster,
    cluster_notes,
    near_duplicate_pairs,
    note_centroids,
    note_snippets,
)
from core.mirror import MirrorView
from core.stores.derived import FINDING, DerivedStore, artifact_id
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore

NEAR_DUPLICATE = "near_duplicate"
PRUNE_CANDIDATE = "prune_candidate"
CONTRADICTION = "contradiction"

_SNIPPET_CHARS = 600

# A contradiction detector judges a theme cluster (with its grounding text) and returns a
# description per contradiction it finds. The real one is the synthesis model; absent one,
# contradiction detection is deferred (never approximated by keyword matching).
ContradictionDetector = Callable[[Cluster, str], "list[str]"]


@dataclass(frozen=True)
class CurationFinding:
    subkind: str
    subjects: tuple[str, ...]
    detail: str
    data: dict[str, Any]
    digests: tuple[str, ...] = ()   # authored note digests this finding is derived FROM (G2)


@dataclass(frozen=True)
class CurationReport:
    findings: tuple[CurationFinding, ...]
    contradiction_detection_deferred: bool   # True when no detector was wired (honest)

    def of(self, subkind: str) -> tuple[CurationFinding, ...]:
        return tuple(f for f in self.findings if f.subkind == subkind)


@dataclass
class Curator:
    store: VectorStore
    derived: DerivedStore
    raw: RawStore | None = None
    near_dup_threshold: float = 0.93       # cosine >= this => near-duplicate candidate
    cluster_threshold: float = 0.62        # theme grouping for contradiction scan
    min_cluster_size: int = 2
    max_clusters: int = 8
    contradiction_detector: ContradictionDetector | None = None
    # Optional runtime proof layer: when present, each finding emits an attestation (inputs =
    # the authored note digests the finding concerns, output = the finding record). None = off.
    attestor: Attestor | None = None
    _snippets: dict[str, str] = field(default_factory=dict)

    def near_duplicates(self) -> list[CurationFinding]:
        """Authored notes with near-identical embeddings — read-only over the mirror.

        Reads through a `MirrorView` (Invariant 6, structural): a non-authored note can never
        reach this scan, because a MirrorView holding one is unrepresentable."""
        notes = note_centroids(MirrorView.project(self.store).rows())
        return [
            CurationFinding(
                subkind=NEAR_DUPLICATE,
                subjects=(a.title, b.title),
                detail=(f"near-identical embeddings (cosine {sim:.3f}); review as a merge "
                        "candidate — not auto-merged (authored notes are immutable, §8)"),
                data={"similarity": round(sim, 4), "digests": [a.digest, b.digest]},
                digests=(a.digest, b.digest),
            )
            for a, b, sim in near_duplicate_pairs(notes, threshold=self.near_dup_threshold)
        ]

    def prune_candidates(self) -> list[CurationFinding]:
        """Derived vector rows orphaned from the raw store (dead derived weight). Requires a
        raw store to compare against; without one this check is simply skipped."""
        if self.raw is None:
            return []
        orphans: dict[str, str] = {}
        for r in self.store.all_rows():       # all provenances — dead derived weight is dead
            d = r["digest"]
            if d not in orphans and not self.raw.exists(d):
                orphans[d] = r.get("title", "")
        return [
            CurationFinding(
                subkind=PRUNE_CANDIDATE,
                subjects=(title,),
                detail="derived vector rows orphaned from the raw corpus (regenerable dead weight)",
                data={"digest": digest},
                digests=(digest,),
            )
            for digest, title in orphans.items()
        ]

    def contradictions(self) -> list[CurationFinding]:
        """Within-theme contradictions — a model judgment. Deferred (returns nothing) until a
        detector is injected; never faked (cf. the §4 judge seam)."""
        if self.contradiction_detector is None:
            return []
        rows = MirrorView.project(self.store).rows()   # Invariant 6 (structural): authored-only
        self._snippets = note_snippets(rows, limit=_SNIPPET_CHARS)
        clusters = cluster_notes(note_centroids(rows), threshold=self.cluster_threshold,
                                 min_size=self.min_cluster_size)[: self.max_clusters]
        findings: list[CurationFinding] = []
        for cluster in clusters:
            block = self._format_cluster(cluster)
            for desc in self.contradiction_detector(cluster, block):
                findings.append(CurationFinding(
                    subkind=CONTRADICTION,
                    subjects=cluster.titles,
                    detail=desc,
                    data={"cluster_size": cluster.size},
                    digests=cluster.digests,
                ))
        return findings

    def _format_cluster(self, cluster: Cluster) -> str:
        blocks = [
            f"[[{m.title}]]\n{self._snippets.get(m.digest, '')[:_SNIPPET_CHARS]}"
            for m in cluster.members
        ]
        return "Notes in this theme:\n\n" + "\n\n---\n\n".join(blocks)

    def curate(self) -> CurationReport:
        """Run a full curation pass and persist every finding as an INTERPRETED artifact.
        Reads the authored corpus; writes ONLY to the derived store (§8 firewall)."""
        findings = self.near_duplicates() + self.prune_candidates() + self.contradictions()
        for f in findings:
            # Emit the finding's attestation BEFORE writing it so the record links back; the
            # attestor auto-chains to the ingest attestations for these authored digests.
            attestation_id = None
            if self.attestor is not None:
                att = self.attestor.emit(
                    agent_role="curator", action="curate_finding",
                    input_hashes=f.digests,
                    output_hashes=[artifact_id(FINDING, f.subkind, f.subjects)],
                )
                attestation_id = att.id
            # A finding is derived FROM the authored notes it concerns — its leaves (G2).
            self.derived.add(kind=FINDING, subkind=f.subkind, summary=f.detail,
                             subjects=f.subjects, data=f.data, derived_from=f.digests,
                             attestation_id=attestation_id)
        return CurationReport(
            findings=tuple(findings),
            contradiction_detection_deferred=self.contradiction_detector is None,
        )


def build_curator(config: Config | None = None) -> Curator:
    """Wire a Curator against the real configured stores. Contradiction detection stays
    deferred unless a detector is supplied (e.g. one backed by the synthesis model)."""
    from config.loader import get_config
    from core.attestation import build_attestor
    from core.stores.derived import open_derived_store
    from core.stores.vectorstore import open_vector_store

    cfg = config or get_config()
    dcfg = cfg.dreaming
    return Curator(
        store=open_vector_store(cfg),
        derived=open_derived_store(cfg),
        raw=RawStore(cfg.paths.raw_store),
        near_dup_threshold=dcfg.near_dup_threshold,
        cluster_threshold=dcfg.similarity_threshold,
        min_cluster_size=dcfg.min_cluster_size,
        max_clusters=dcfg.max_clusters,
        attestor=build_attestor(cfg),
    )
