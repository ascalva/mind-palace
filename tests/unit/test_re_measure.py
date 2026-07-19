"""bp-073 Item 1 — the Δ composed-graph assembly over the dialogue-artifact corpus.

`assemble_composed_graph` builds a `ComposedGraph` (fixtured: injected embeddings + injected C-edge
rows) whose E_sim is doc cosine ≥ the loosest grid σ and whose E_proven is witnessed shared-witness
co-production. These tests pin the acceptance and the three falsifiers (bp-073 §7 Item 1):
- a proven edge minted WITHOUT a witness → `WitnesslessProvenEdge` (fail loud);
- a node-pair only ever appears from a genuine two-doc co-production, never from an endpoint-less
  or single-doc session;
- E_sim and E_proven are NOT silently merged — `classes_of` keeps the attribution;
and the headline: a proven bridge joins two σ-components a fixture keeps sim-disconnected,
feeding the REAL `core.graph.sigma_star` unchanged (the whole point — no new instrument).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import cast

import pytest

from core.dreaming.graph import MirrorGraph
from core.graph.composed import E_PROVEN, E_SIM, ComposedGraph
from core.graph.sigma_star import build_max_spanning_tree, sigma_star
from eval.harness.re_measure import (
    WitnesslessProvenEdge,
    assemble_composed_graph,
    doc_node_ids,
    load_causal_edges,
    open_causal_edges_ro,
    proven_pairs_from_causal,
    re_measure_oq0031,
    resolve_doc_path,
    sim_edges_from_embeddings,
)

_GRID = (0.5, 0.7, 0.9)
_FLOOR = _GRID[0]


def _as_mirror(g: ComposedGraph) -> MirrorGraph:
    return cast(MirrorGraph, g)


def _edge(session: str, order: int, dst: str, *, dst_type: str = "doc",
          digest: str | None = None, turn: int = 0) -> dict[str, object]:
    """One causal_edges row (the `all_edges()` dict shape). `digest=None` → a per-session token;
    `digest=""` passes an explicitly EMPTY witness (the fail-loud fixture)."""
    return {
        "session_id": session, "event_order": order, "kind": "C",
        "dst_type": dst_type, "dst": dst,
        "witness_digest": f"digest-{session}" if digest is None else digest, "witness_turn": turn,
        "pair_cut_sha": "",
    }


# Two orthogonal E_sim components: {da—db} and {dc—dd}. 4-dim one-hot-ish centroids so the cross
# cosines are 0 (< floor) and the intra ones are 1.0 — the fixture keeps {da,db} and {dc,dd} apart.
_NODES = ("da", "db", "dc", "dd")
_EMB = {
    "da": (1.0, 0.02, 0.0, 0.0),
    "db": (1.0, 0.00, 0.0, 0.0),
    "dc": (0.0, 0.0, 1.0, 0.02),
    "dd": (0.0, 0.0, 1.0, 0.00),
}


def test_sim_edges_threshold_at_floor_reproduce_two_components():
    """E_sim keeps only cosine ≥ floor: da—db and dc—dd (≈1.0), NOT the orthogonal cross pairs."""
    edges = sim_edges_from_embeddings(_EMB, node_ids=_NODES, sigma_floor=_FLOOR)
    connected = {(a, b) for a, b, _ in edges}
    assert connected == {("da", "db"), ("dc", "dd")}


def test_proven_bridge_joins_two_sim_components():
    """The headline acceptance: one session co-produces db and dc (a proven bridge across the E_sim
    gap), so da—dd — unconnected under E_sim alone — becomes connected, and the REAL σ* reads it."""
    # A single session writes db then dc → a witnessed co-production bridge db—dc.
    causal = [_edge("s1", 3, "db", turn=1), _edge("s1", 5, "dc", turn=2)]

    g_no = assemble_composed_graph(node_ids=_NODES, embeddings=_EMB, causal_edges=[],
                                   sigma_floor=_FLOOR)
    g_br = assemble_composed_graph(node_ids=_NODES, embeddings=_EMB, causal_edges=causal,
                                   sigma_floor=_FLOOR)

    f_no = build_max_spanning_tree(_as_mirror(g_no))
    f_br = build_max_spanning_tree(_as_mirror(g_br))
    assert sigma_star(f_no, "da", "dd", grid=_GRID).sigma_star is None          # split before
    reading = sigma_star(f_br, "da", "dd", grid=_GRID)
    assert reading.sigma_star is not None                                       # bridged after
    assert reading.chain == ("da", "db", "dc", "dd")                  # via the proven edge
    assert g_br.classes_of("db", "dc") == frozenset({E_PROVEN})       # attributed to proven


def test_attribution_survives_when_a_pair_is_both_sim_and_proven():
    """A pair carried by BOTH classes keeps both tags — E_sim and E_proven not silently merged."""
    causal = [_edge("s1", 1, "da", turn=1), _edge("s1", 2, "db", turn=2)]   # da,db also a sim pair
    g = assemble_composed_graph(node_ids=_NODES, embeddings=_EMB, causal_edges=causal,
                                sigma_floor=_FLOOR)
    assert g.classes_of("da", "db") == frozenset({E_SIM, E_PROVEN})


def test_single_doc_session_mints_no_pair_and_non_doc_endpoints_ignored():
    """A session with one doc endpoint (plus commit/file endpoints) yields no co-production pair —
    no node-pair from an endpoint-less / single-doc session (the falsifier)."""
    causal = [
        _edge("s1", 1, "da", turn=1),                                   # lone doc
        _edge("s1", 2, "abc1234", dst_type="commit", turn=1),           # non-doc — ignored
        _edge("s1", 3, "/repo/x.py", dst_type="file", turn=2),         # non-doc — ignored
    ]
    assert proven_pairs_from_causal(causal, node_ids=_NODES) == []


def test_doc_endpoint_outside_node_set_is_not_paired():
    """A doc endpoint not in the node set is dropped, so it cannot pair with an in-set doc."""
    causal = [_edge("s1", 1, "da", turn=1), _edge("s1", 2, "d-not-a-node", turn=2)]
    assert proven_pairs_from_causal(causal, node_ids=_NODES) == []


def test_witness_is_required_fail_loud():
    """A doc endpoint with an empty witness_digest raises — no unwitnessed proven edge (Item 1
    falsifier: 'a proven edge minted without a witness')."""
    causal = [_edge("s1", 1, "da", digest="", turn=1), _edge("s1", 2, "db", turn=2)]
    with pytest.raises(WitnesslessProvenEdge):
        proven_pairs_from_causal(causal, node_ids=_NODES)


def test_proven_pair_carries_both_endpoints_witness():
    """The witnessed pair carries the session id and both writes' (order, turn, digest) — the
    concatenated witness tuple (the §2.5 witness law)."""
    causal = [_edge("s2", 7, "db", digest="dig2", turn=4),
              _edge("s2", 9, "dc", digest="dig2", turn=6)]
    (pair,) = proven_pairs_from_causal(causal, node_ids=_NODES)
    assert (pair.a, pair.b) == ("db", "dc") and pair.session_id == "s2"
    assert {ep.event_order for ep in pair.endpoints} == {7, 9}
    assert pair.witness_digests == ("dig2", "dig2")


def test_same_pair_across_two_sessions_dedups_to_one_edge_two_witnesses():
    """A doc-pair co-produced in two sessions yields two witnessed ProvenPairs but ONE graph edge
    (compose flattens by max weight) — the witnesses are retained, the edge not double-counted."""
    causal = [
        _edge("s1", 1, "db", turn=1), _edge("s1", 2, "dc", turn=2),
        _edge("s2", 1, "db", turn=1), _edge("s2", 2, "dc", turn=2),
    ]
    pairs = proven_pairs_from_causal(causal, node_ids=_NODES)
    assert len(pairs) == 2                                              # two witnesses
    assert {p.session_id for p in pairs} == {"s1", "s2"}
    g = assemble_composed_graph(node_ids=_NODES, embeddings=_EMB, causal_edges=causal,
                                sigma_floor=_FLOOR)
    ia, ib = g.nodes.index("db"), g.nodes.index("dc")
    assert g.sim[ia, ib] == 1.0                                        # one edge, weight 1.0
    assert g.classes_of("db", "dc") == frozenset({E_PROVEN})


# ── Item 2: the re-measure + the oq-0031 verdict ──────────────────────────────────────────────
def test_re_measure_discriminates_when_a_proven_bridge_exists():
    """A proven co-production bridge (db—dc) makes da—dd connected: the report attributes it as a
    proven bridge (bottleneck via E_proven) and `discriminates` is True — the oq-0031 falsifier."""
    causal = [_edge("s1", 1, "db", turn=1), _edge("s1", 2, "dc", turn=2)]
    report = re_measure_oq0031(node_ids=_NODES, embeddings=_EMB, causal_edges=causal, grid=_GRID)
    assert report.discriminates is True
    assert report.n_proven_edges == 1
    bridged = {(b.a, b.b) for b in report.proven_bridges}
    assert ("da", "dd") in bridged
    for b in report.proven_bridges:
        assert b.chain_uses_proven is True             # the connecting path crosses the proven edge
    assert report.n_sigma_uplifted >= 1               # σ*-uplift subsumes the None→reading bridge


def test_re_measure_does_not_discriminate_without_proven_edges():
    """With no C-edges, E_proven is empty → no bridge → `discriminates` False, and the saturation
    gauge is identical under E_sim-only and full (E_proven added nothing) — the honest null."""
    report = re_measure_oq0031(node_ids=_NODES, embeddings=_EMB, causal_edges=[], grid=_GRID)
    assert report.discriminates is False
    assert report.proven_bridges == ()
    assert report.n_proven_edges == 0
    assert report.n_sigma_uplifted == 0                # nothing raised σ* without proven edges
    for sim_only, full in report.frac_connected_by_sigma.values():
        assert sim_only == full                        # E_proven changed nothing


def test_re_measure_saturation_gauge_shifts_with_proven_edges():
    """The frac_connected gauge rises under E_sim∪E_proven where a bridge lands — discrimination
    E_sim alone did not show (the finding-0096 analog: the curve is no longer identical)."""
    causal = [_edge("s1", 1, "db", turn=1), _edge("s1", 2, "dc", turn=2)]
    report = re_measure_oq0031(node_ids=_NODES, embeddings=_EMB, causal_edges=causal, grid=_GRID)
    # at the loosest σ, the proven bridge connects the two components → full > sim-only.
    sim_only, full = report.frac_connected_by_sigma[_FLOOR]
    assert full > sim_only


def test_re_measure_notes_golden_recall_non_transfer():
    """The report states golden_recall does not transfer — honesty, not forced green (Item 0 Q4)."""
    report = re_measure_oq0031(node_ids=_NODES, embeddings=_EMB, causal_edges=[], grid=_GRID)
    assert any("golden_recall" in n for n in report.notes)


# ── Item 2b: read-only by construction ────────────────────────────────────────────────────────
def _tiny_causal_db(path: Path) -> None:
    """A minimal causal_edges store to open read-only."""
    conn = sqlite3.connect(str(path))
    conn.executescript(
        "CREATE TABLE causal_edges (edge_id TEXT PRIMARY KEY, session_id TEXT, event_order INTEGER,"
        " kind TEXT, dst_type TEXT, dst TEXT, witness_digest TEXT, witness_turn INTEGER,"
        " pair_cut_sha TEXT);"
    )
    conn.execute(
        "INSERT INTO causal_edges VALUES ('e1','s1',1,'C','doc','bp-001','dig-s1',2,'')")
    conn.commit()
    conn.close()


def test_open_causal_edges_ro_refuses_writes(tmp_path: Path):
    """The measurement's C-edge handle is opened `mode=ro`: a write through it raises
    OperationalError — the daemon-owned store cannot be mutated or corrupted by Δ (Item 2b)."""
    db = tmp_path / "causal_edges.sqlite"
    _tiny_causal_db(db)
    conn = open_causal_edges_ro(db)
    rows = load_causal_edges(conn)
    assert doc_node_ids(rows) == ["bp-001"]                     # reads work
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("INSERT INTO causal_edges VALUES ('e2','s2',1,'C','doc','x','d',0,'')")
    conn.close()


def test_resolve_doc_path_maps_ids_to_real_docs():
    """The artifact-id → file resolver finds this build plan and a finding on disk (read-only)."""
    root = Path(__file__).resolve().parents[2]
    assert resolve_doc_path("bp-073", repo_root=root) == root / "docs/build-plans/bp-073/plan.md"
    finding = resolve_doc_path("finding-0112", repo_root=root)
    assert finding == root / "docs/findings/finding-0112.md"
    assert resolve_doc_path("does-not-exist-xyz", repo_root=root) is None
