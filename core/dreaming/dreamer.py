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

from config.loader import Config
from core.attestation import Attestor
from core.complex.support import grounding_with_support
from core.complex.temporal import SnapshotStore, compute_snapshot
from core.constitution import Message, frame_context
from core.dreaming.cluster import Cluster, cluster_notes, note_centroids, note_snippets
from core.dreaming.graph import MirrorGraph
from core.dreaming.interpreters import build_structural_context, collect_claims
from core.dreaming.rnd import require_rnd_enabled
from core.mirror import MirrorView
from core.selfcheck import SelfCheck, Source, SubjectiveJudge, self_evaluate
from core.stores.derived import DREAM, Artifact, DerivedStore, artifact_id
from core.stores.edges import EdgeStore
from core.stores.vectorstore import VectorStore

# A synthesizer maps an assembled (Constitution-first) context -> the reflection text. The
# real one is ModelServer.chat at the synthesis tier; tests inject a fake. (Model advises;
# code assembles the context and decides when to run — Invariant 3.)
Synthesizer = Callable[[list[Message]], str]

# A clusterer groups note centroids into themes: (notes, *, threshold, min_size) -> [Cluster].
# The default is the deterministic cosine single-linkage (`cluster.cluster_notes`); the reasoning
# complex's diffusion clusterer (`core.complex.spectral.diffusion_cluster_notes`) is a drop-in
# selected behind the DreamerAdapter seam — it dissolves single-linkage chaining (companion III
# §2.2). Both are model-free and deterministic; the live default is unchanged.
Clusterer = Callable[..., list[Cluster]]

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
    # The clustering strategy (the DreamerAdapter seam). Default = the Phase-7 cosine
    # single-linkage; inject `core.complex.spectral.diffusion_cluster_notes` to use the reasoning
    # complex's principled clusterer instead. Behavior is unchanged unless a clusterer is injected.
    clusterer: Clusterer = cluster_notes
    judge: SubjectiveJudge | None = None
    # Optional runtime proof layer: when present, each dream emits a signed-later attestation
    # (inputs = the authored cluster digests, output = the dream record) and the record links
    # back to it. None = no attestation (existing behavior unchanged).
    attestor: Attestor | None = None
    # Loop-v2 seams (H8/H9; both optional — the v1 path never touches them): persisted
    # typed/signed edges overlaid on the signed adjacency (the tension lens's input), and the
    # structural-snapshot store the v2 pass appends to (§5.4). None = no edges / no snapshot.
    edge_store: EdgeStore | None = None
    snapshots: SnapshotStore | None = None
    _snippets: dict[str, str] = field(default_factory=dict)

    def clusters(self) -> list[Cluster]:
        """Deterministic note-level clustering over the AUTHORED mirror (model-free, §9).

        The rows come from a `MirrorView` (Invariant 6, structural): its only constructor is
        the MIRROR_READABLE projection and it cannot hold a non-authored row, so observed
        exhaust reaching this clustering is unrepresentable — not merely filtered out."""
        rows = MirrorView.project(self.store).rows()
        self._snippets = note_snippets(rows, limit=_SNIPPET_CHARS)   # grounding text per note
        notes = note_centroids(rows)
        return self.clusterer(notes, threshold=self.threshold,
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
            leaf_digests = [m.digest for m in cluster.members]
            # Emit the attestation BEFORE writing the record so the record can link to it. The
            # attestor auto-chains to the ingest attestations that produced these authored
            # digests (verifiable lineage to authored content, attestation-layer.md §3).
            attestation_id = None
            if self.attestor is not None:
                att = self.attestor.emit(
                    agent_role="dreamer", action="dream_pass",
                    input_hashes=leaf_digests,
                    output_hashes=[artifact_id(DREAM, None, cluster.titles)],
                )
                attestation_id = att.id
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
                derived_from=leaf_digests,
                attestation_id=attestation_id,
            )
            themes.append(Theme(titles=cluster.titles, summary=output,
                                check=check, artifact=artifact))
        return themes

    # ------------------------------------------------------------------ loop v2 (BUILD §3.1)
    def dream_v2(self, *, config: Config | None = None) -> list[Theme]:
        """The strong-Dreamer pass — deterministic structure first, the earned model call last:

            1. BUILD 𝔎|_MR (firewall structural: the complex is built from a MirrorView)
          2–5. LOCATE / THEME / TENSION / GAPS — the interpreter panel over the complex
            6. SUPPORT — noisy-OR multi-path grounding on the derivation DAG (§6.1)
            7. ADJUDICATE — c = min{1, γ^d·g·(1+λ(|Agr|−1))}, confidence-ordered
            8. SYNTHESIZE — the ONLY model call(s): narrate each selected candidate,
               grounded in its authored evidence, mirror-not-oracle
            9. STORE — interpreted-only, derives→authored leaves, acyclic, attested
           10. MEASURE — append the structural snapshot (§5.4; feeds the A2 drift axes)

        Gated by the dream-R&D hard boundary (`[dream_rnd] enabled`, OFF by default): the live
        `dream()` above is UNCHANGED and remains the cron path until a deliberate flip. Every
        structural judgment here is deterministic and model-free; `self.synthesize` is the only
        model seam, invoked once per stored dream and nowhere else. Trough-only when wired
        (a `dream` job routes to the synthesis tier, which the foreground gate blocks)."""
        rnd = require_rnd_enabled(config)
        view = MirrorView.project(self.store)
        rows = view.rows()
        self._snippets = note_snippets(rows, limit=_SNIPPET_CHARS)
        titles: dict[str, str] = {}
        for r in rows:
            titles.setdefault(r["digest"], r.get("title", ""))
        authored = set(titles)

        # 1–5: one shared complex (persisted edges overlaid ⇒ the tension lens can fire),
        # both lens registries + tension over it.
        graph = MirrorGraph.build(view, sigma=rnd.sigma)
        ctx = build_structural_context(view, rnd, edges=self.edge_store)
        claims = collect_claims(graph, ctx, rnd)

        # 6–7: multi-path support feeds g; the clamp law ranks.
        from core.dreaming.adjudicator import adjudicate  # local: v1 constructions never pay it
        refs_of = {a.id: a.derived_from for a in self.derived.all()}
        entries = adjudicate(
            claims, authored_digests=authored, agreement_jaccard=rnd.agreement_jaccard,
            support_of=lambda ev: grounding_with_support(ev, refs_of, authored),
        )

        # 8–9: the earned narration, top candidates only; grounded or not kept quiet.
        themes: list[Theme] = []
        for entry in entries[: self.max_clusters]:
            if not entry.evidence or entry.confidence <= 0.0:
                continue                       # an ungrounded candidate has not earned the model
            messages = frame_context(
                DREAMER_ROLE, _DREAM_TASK,
                context_blocks=[self._format_evidence(entry.statement, entry.evidence, titles)],
            )
            output = self.synthesize(messages)
            sources = [Source(title=titles.get(d, d), digest=d) for d in entry.evidence]
            check = self_evaluate(output, sources=sources, judge=self.judge)
            subjects = tuple(titles.get(d, d) for d in entry.evidence)
            attestation_id = None
            if self.attestor is not None:
                att = self.attestor.emit(
                    agent_role="dreamer", action="dream_pass_v2",
                    input_hashes=list(entry.evidence),
                    output_hashes=[artifact_id(DREAM, None, subjects)],
                )
                attestation_id = att.id
            artifact = self.derived.add(
                kind=DREAM,
                summary=output,
                subjects=subjects,
                data={"grounded": check.passed, "check": list(check.notes),
                      "confidence": entry.confidence, "methods": list(entry.methods),
                      "statement": entry.statement, "loop": "v2"},
                derived_from=entry.evidence,   # authored leaves — acyclic, depth 1 (G2)
                attestation_id=attestation_id,
            )
            themes.append(Theme(titles=subjects, summary=output, check=check,
                                artifact=artifact))

        # 10: the system watches its own structure evolve (§5.4 → the A2 drift axes).
        if self.snapshots is not None:
            self.snapshots.write(compute_snapshot(
                ctx.complex, distances=ctx.distances,
                sbm_k_max=rnd.sbm_k_max, hole_min_persistence=rnd.hole_min_persistence,
            ))
        return themes

    def _format_evidence(self, statement: str, evidence: tuple[str, ...],
                         titles: dict[str, str]) -> str:
        """The synthesis context for one adjudicated candidate: the structural observation the
        instruments made, plus the authored notes (the ONLY citable evidence) with snippets."""
        blocks = [
            f"[[{titles.get(d, d)}]]\n{self._snippets.get(d, '')[:_SNIPPET_CHARS]}"
            for d in evidence
        ]
        return (
            f"A structural pattern found across the notes: {statement}\n\n"
            "Notes involved (the ONLY evidence you may cite):\n\n"
            + "\n\n---\n\n".join(blocks)
        )


def build_dreamer(config: Config | None = None, *, tier: str = "synthesis") -> Dreamer:
    """Wire a Dreamer against the real configured stores + synthesis model. Pulling the
    synthesis-tier model is required only to actually run it (the unit path injects a fake)."""
    from config.loader import get_config
    from core.attestation import build_attestor
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
        attestor=build_attestor(cfg),
    )
