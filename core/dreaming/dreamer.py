"""The dreaming agent (BUILD-SPEC §9) — Zone A, cron/trough tier.

Clusters the AUTHORED corpus into themes, then asks the synthesis-tier model to reflect each
theme back to the owner as a *lens on their own notes* — **mirror, not oracle** (Constitution
§III.2): grounded in the clustered notes, citing them, never presented as external truth.

Firewall: it reads `MIRROR_READABLE` (AUTHORED only), so third-party observed exhaust can
never seed a dream and dreams never enter the behavioral baselines (§15). Output is stored as
`INTERPRETED` artifacts in the derived store (regenerable), and each synthesis runs the
Constitution pre-return check (`core.selfcheck`) before it is kept — a dream that fabricates a
citation is flagged exactly like a librarian answer that does.

Trough-only: a `dream` job routes to the synthesis tier (`scheduler.router`), which the
supervisor's foreground gate (`HEAVY_TIERS`, Phase 3) blocks while the owner is present — so
dreaming is never concurrent with foreground use (§13). The synthesizer is injected so this
module is testable without the (large, possibly unpulled) synthesis model.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from core.constitution import Message, frame_context
from core.dreaming.cluster import Cluster, cluster_notes, note_centroids, note_snippets
from core.mirror import MirrorView
from core.selfcheck import SelfCheck, Source, SubjectiveJudge, self_evaluate
from core.stores.derived import DREAM, Artifact, DerivedStore
from core.stores.vectorstore import VectorStore

# A synthesizer maps an assembled (Constitution-first) context -> the reflection text. The
# real one is ModelServer.chat at the synthesis tier; tests inject a fake. (Model advises;
# code assembles the context and decides when to run — Invariant 3.)
Synthesizer = Callable[[list[Message]], str]

DREAMER_ROLE = (
    "You are the dreaming agent of a sealed personal mind-palace. You are shown a cluster of "
    "the owner's OWN notes that group together by theme. Reflect that theme back to the owner "
    "as a lens on their own thinking — a mirror, never an oracle.\n\n"
    "Ground every observation in the notes shown and cite them by title in double brackets, "
    "e.g. [[note title]]. Do not introduce facts that are not in these notes, do not invent "
    "notes or quotes, and do not present anything as external truth. Surface the recurring "
    "patterns, tensions, and open questions you see across these notes, and leave the "
    "conclusions to the owner. If the notes do not actually cohere into a theme, say so."
)

_DREAM_TASK = (
    "Reflect on the theme these notes share. What recurring patterns, tensions, or open "
    "questions run through them? Keep it brief and grounded; cite the notes you draw on."
)

# Per-note text budget in a cluster block — keep the dream context lean (the Constitution
# loads into every window; §13), enough to ground the synthesis without dumping whole notes.
_SNIPPET_CHARS = 600


@dataclass(frozen=True)
class Theme:
    titles: tuple[str, ...]
    summary: str
    check: SelfCheck
    artifact: Artifact


@dataclass
class Dreamer:
    store: VectorStore
    synthesize: Synthesizer
    derived: DerivedStore
    threshold: float = 0.62        # cosine similarity to join two notes into a theme
    min_cluster_size: int = 2
    max_clusters: int = 8          # cap the number of syntheses per run (scarce slot, §5)
    judge: SubjectiveJudge | None = None
    _snippets: dict[str, str] = field(default_factory=dict)

    def clusters(self) -> list[Cluster]:
        """Deterministic note-level clustering over the AUTHORED mirror (model-free, §9).

        The rows come from a `MirrorView` (Invariant 6, structural): its only constructor is
        the MIRROR_READABLE projection and it cannot hold a non-authored row, so observed
        exhaust reaching this clustering is unrepresentable — not merely filtered out."""
        rows = MirrorView.project(self.store).rows()
        self._snippets = note_snippets(rows, limit=_SNIPPET_CHARS)   # grounding text per note
        notes = note_centroids(rows)
        return cluster_notes(notes, threshold=self.threshold,
                             min_size=self.min_cluster_size)[: self.max_clusters]

    def _format_cluster(self, cluster: Cluster) -> str:
        blocks = [
            f"[[{m.title}]]\n{self._snippets.get(m.digest, '')[:_SNIPPET_CHARS]}"
            for m in cluster.members
        ]
        return (
            "Notes in this theme (the ONLY evidence you may cite):\n\n"
            + "\n\n---\n\n".join(blocks)
        )

    def dream(self) -> list[Theme]:
        """Run a full dreaming pass: cluster -> synthesize each theme -> self-check -> store.
        Returns the themes produced (also persisted as INTERPRETED dreams)."""
        themes: list[Theme] = []
        for cluster in self.clusters():
            messages = frame_context(DREAMER_ROLE, _DREAM_TASK,
                                     context_blocks=[self._format_cluster(cluster)])
            output = self.synthesize(messages)
            # The clustered notes are the only legitimate citation targets; resolve by stable
            # digest so the grounding check is well-posed under shared titles (G1).
            sources = [Source(title=m.title, digest=m.digest) for m in cluster.members]
            check = self_evaluate(output, sources=sources, judge=self.judge)
            artifact = self.derived.add(
                kind=DREAM,
                summary=output,
                subjects=cluster.titles,
                data={"grounded": check.passed, "check": list(check.notes),
                      "cluster_size": cluster.size},
                # The dream is derived FROM the clustered AUTHORED notes — its leaves (G2).
                # Today every dream is depth 1 over authored ground; recursive dreaming (a
                # flag-OFF R&D path) would add interpreted parents, which the acyclic insert
                # and the decay bound c ≤ γ^d·g are already built to handle.
                derived_from=[m.digest for m in cluster.members],
            )
            themes.append(Theme(titles=cluster.titles, summary=output,
                                check=check, artifact=artifact))
        return themes


def build_dreamer(config: object | None = None, *, tier: str = "synthesis") -> Dreamer:
    """Wire a Dreamer against the real configured stores + synthesis model. Pulling the
    synthesis-tier model is required only to actually run it (the unit path injects a fake)."""
    from config.loader import get_config
    from core.models import build_model_server
    from core.stores.derived import open_derived_store
    from core.stores.vectorstore import open_vector_store

    cfg = config or get_config()
    server = build_model_server(cfg)
    dcfg = cfg.dreaming
    return Dreamer(
        store=open_vector_store(cfg),
        synthesize=lambda messages: server.chat(tier, messages),
        derived=open_derived_store(cfg),
        threshold=dcfg.similarity_threshold,
        min_cluster_size=dcfg.min_cluster_size,
        max_clusters=dcfg.max_clusters,
    )
