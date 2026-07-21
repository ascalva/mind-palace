# ── Family 1 boundary (capability algebra · the agent layer) · docs/NOTATION.md ──
# OBJECT:    the first full INTEGRATOR (dn-agent-taxonomy §2.1/§2.5) — deterministic,
#            model-free, multi-strata read, edges-only write. It resolves the references the
#            dialogue sensor's L1 action log names (commit shas, file paths, artifact ids)
#            against the commit ledger, minting C-fiber PROVEN edges (a DIALOGUE action → the
#            endpoint it produced), each carrying its witness and pair-cut.
# INVARIANT: every edge is the image of ONE L1 tool record under a deterministic map (the
#            witness law — E_proven, re-derivable). NO model, NO time-join, NO inference, NO
#            fan-out to a commit's tree (the ledger holds the tree, not the diff — fanning
#            would be an inferred edge; finding-0111). Born inside `INTEGRATOR_SCOPE`; the
#            wiring asserts conformance (actual handles ⊑ declared scope).
# ENFORCED:  static (pure-core typing; mypy) + guard (tests/unit/test_integrator.py proves the
#            resolver, the named-not-dropped accounting, witness-keyed idempotency, and that
#            the handle inventory conforms while a smuggled handle is rejected).
"""The chat↔code↔doc integrator — the role's first full instance (bp-071, dn-agent-taxonomy §2.5).

`integrate` walks the L1 action log (bp-069's `ChatEventStore`, read) and, per session, mints the
proven C-fiber edges its events directly witness (finding-0111): a `commit` event resolves against
the commit ledger by abbreviated-sha prefix match (→ a `commit` edge carrying the (digest, full-sha)
pair-cut); a `file_edit`/`build_plan`/`finding`/`design_note` event mints its endpoint directly (the
Write tool record is the proof → a `file`/`doc` edge, no commit anchor). Endpoints are never fanned
out from a commit's file set — the ledger stores the full tree, not the diff. Composing
action→commit with commit→file is Δ's `ComposedGraph` job (C≠D composition), not this agent's.

Model-free and edge-only: it holds three handles (L1 read, ledger read, edge write) and nothing
else — no model, no embedder, no network, no vault. Born scoped (`INTEGRATOR_SCOPE`);
`build_integrator` asserts the handle inventory conforms. Incremental like L1: replace-per-digest.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from core.agent_scope import Handle, HandleInventory, assert_conforms, integrator_scope
from core.config import Config
from core.integrator_math import CoverageGauge, IntegrationReport
from core.scope import Stratum
from core.stores.causal_edges import CausalEdge, CausalEdgeStore
from core.stores.chat_events import ChatEventStore

# The role's born scope (dn-agent-taxonomy §2.1/§2.5; plan §6): reads L1 (DIALOGUE), the commit
# ledger (OBSERVED), and the corpus artifacts (DIALOGUE_ARTIFACT); writes fibers {C, F}. F is
# declared-but-unfed in v1 — no read/cite endpoint survives the landed L1 (finding-0111).
INTEGRATOR_SCOPE = integrator_scope(
    read=[(Stratum.DIALOGUE, "L1"), (Stratum.OBSERVED, "commit-ledger"),
          (Stratum.DIALOGUE_ARTIFACT, "*")],
    write_fibers=["C", "F"],
)

# L1 event kinds that name an endpoint a proven edge can point at. A `commit` resolves against the
# ledger; the write kinds mint their endpoint directly (dst_type below). Every OTHER kind
# (prompt/response/tool_use/ratify) names no external endpoint — non-integrable, not a drop.
_WRITE_KIND_TO_DST: dict[str, str] = {
    "file_edit": "file", "build_plan": "doc", "finding": "doc", "design_note": "doc",
}


# `IntegrationReport` + `CoverageGauge` — the pure gauge instruments — relocated to the inner
# `core/integrator_math.py` (bp-089, S1′); imported above for use here. This module keeps the
# `ledger`/acquisition machinery (sqlite) and therefore stays OUTER.

_INTEGRABLE_KINDS = frozenset({"commit", *_WRITE_KIND_TO_DST})


def coverage_gauge(events: ChatEventStore, edges: CausalEdgeStore) -> CoverageGauge:
    """Compute the standing C-coverage over the L1 action log and the minted edges (bp-071 §1):
    the fraction of endpoint-naming D-events that carry a proven C-edge. Deterministic, model-free —
    a pure read over the two stores. An event is witnessed iff a causal edge shares its
    (session_id, event_order); an unresolved commit names an endpoint but mints no edge (the honest
    partial-coverage gap the parity gauge — `IntegrationReport.is_fully_accounted` — accounts by
    reason at pass time)."""
    integrable = sum(1 for sid in events.sessions()
                     for ev in events.events_for(sid) if str(ev["kind"]) in _INTEGRABLE_KINDS)
    witnessed = len({(e["session_id"], e["event_order"]) for e in edges.all_edges()})
    return CoverageGauge(integrable=integrable, witnessed=witnessed)


@dataclass
class Integrator:
    """The integrator agent — tools are the wiring, the discipline is over them. Three handles:
    the L1 store (read), the commit ledger (read), the C-fiber edge store (write). No model."""

    events: ChatEventStore
    ledger: sqlite3.Connection
    edges: CausalEdgeStore

    def handle_inventory(self) -> HandleInventory:
        """The actual store handles this agent holds, as scope coordinates — checked against
        `INTEGRATOR_SCOPE` by `assert_conforms` (guard tier; dn-agent-taxonomy §2.1)."""
        return (
            Handle("chat_events", Stratum.DIALOGUE),                     # L1 read
            Handle("commit_ledger", Stratum.OBSERVED),                   # ledger read
            Handle("causal_edges", Stratum.DIALOGUE, writes_fiber="C"),  # C-fiber write
        )

    def integrate(self, *, max_sessions: int) -> IntegrationReport:
        """Re-integrate up to `max_sessions` sessions whose L1 changed since the last pass.
        A session is skipped when its stored edge-digest equals the L1 digest (no churn);
        otherwise its edges are re-minted wholesale (replace-per-session — a grown session
        stays consistent). Accounts every event; never drops a ref silently."""
        report = IntegrationReport()
        for session_id in self.events.sessions():
            if report.sessions_processed >= max_sessions:
                break
            digest = self.events.digest_for(session_id)
            if digest is None:
                continue                                    # never projected — nothing to read
            if self.edges.digest_for(session_id) == digest:
                report.sessions_skipped += 1
                continue                                    # unchanged — no re-integration
            edges = self._resolve_session(session_id, digest, report)
            self.edges.replace_session(session_id, edges, digest)
            report.edges_minted += len(edges)
            report.sessions_processed += 1
        return report

    def _resolve_session(self, session_id: str, digest: str,
                         report: IntegrationReport) -> list[CausalEdge]:
        """Resolve one session's L1 events into proven edges, updating `report`'s accounting."""
        out: list[CausalEdge] = []
        for ev in self.events.events_for(session_id):
            kind = str(ev["kind"])
            ref = str(ev["ref"])
            order = int(ev["ord"])
            turn = int(ev["turn_index"])
            if kind == "commit":
                report.commit_events += 1
                status, full_sha = self._resolve_commit(ref)
                if status != "resolved":
                    report.name_unresolved(status)          # NAMED, not dropped
                    continue
                report.commit_resolved += 1
                out.append(CausalEdge.mint(
                    session_id=session_id, event_order=order, kind="C",
                    dst_type="commit", dst=full_sha,
                    witness_digest=digest, witness_turn=turn, pair_cut_sha=full_sha))
            elif kind in _WRITE_KIND_TO_DST:
                report.write_events += 1
                out.append(CausalEdge.mint(
                    session_id=session_id, event_order=order, kind="C",
                    dst_type=_WRITE_KIND_TO_DST[kind], dst=ref,
                    witness_digest=digest, witness_turn=turn, pair_cut_sha=""))
            else:
                report.non_integrable += 1                  # prompt/response/tool_use/ratify
        return out

    def _resolve_commit(self, ref: str) -> tuple[str, str]:
        """Resolve an abbreviated commit sha against the ledger by prefix (finding-0111): the L1
        ref is git's abbreviation, the ledger key is the full 40-char sha. Returns
        `("resolved", full_sha)` or a NAMED reason (`unparsed-sha` | `unknown-sha` |
        `ambiguous-sha`) — never a silent drop."""
        if not ref:
            return "unparsed-sha", ""                       # the commit result carried no sha
        try:
            rows = self.ledger.execute(
                "SELECT commit_sha FROM snapshots WHERE commit_sha LIKE ?", [ref + "%"]).fetchall()
        except sqlite3.OperationalError:
            return "unknown-sha", ""                         # no ledger yet (code sensor unrun)
        if not rows:
            return "unknown-sha", ""                        # not on main / pruned / rewritten
        if len(rows) > 1:
            return "ambiguous-sha", ""                      # prefix collision (defensive)
        return "resolved", str(rows[0][0])


def build_integrator(config: Config | None = None) -> Integrator:
    """Wire the integrator's handles against the real L1 store and commit ledger, and ASSERT the
    inventory conforms to `INTEGRATOR_SCOPE` (born scoped; fail-fast at wiring — dn-agent-taxonomy
    §2.1 / bp-070 D2). Same-species as `build_chat_event_projector` / `build_code_sensor`."""
    from core.config import get_config
    from core.stores.causal_edges import open_causal_edge_store
    from core.stores.chat_events import open_chat_event_store

    cfg = config or get_config()
    # The commit ledger (`code_snapshots.sqlite`) is the OBSERVED-stratum record, WRITTEN by the
    # code sensor (`ops.code_snapshot`); the integrator only READS `snapshots.commit_sha`. Core
    # stays self-contained (finding-0103): a direct sqlite connection to the file — never an `ops`
    # import — and `_resolve_commit` tolerates a not-yet-created ledger (names every sha unknown).
    ledger = sqlite3.connect(str(cfg.paths.data_dir / "code_snapshots.sqlite"))
    integrator = Integrator(
        events=open_chat_event_store(cfg),
        ledger=ledger,
        edges=open_causal_edge_store(cfg),
    )
    assert_conforms(INTEGRATOR_SCOPE, integrator.handle_inventory())
    return integrator
