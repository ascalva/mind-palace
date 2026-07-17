"""Quality battery for CN-3 reconnection + the conductance entry point (bp-060 item 6).

Same statistical philosophy as the σ* battery (bp-059): planted structure with KNOWN cosines,
asserting BOUNDS and RELATIONSHIPS, never exact floats. Model-free and deterministic.

The reconnection rider is verified on SYNTHETIC cut-pairs (v1 has no historical graph — plan §11):

* **new-edge** `G2 = G1 + {e}` — a Δ-conductance spike; leave-one-out names `e` and reverting it
  erases the rise.
* **edit-rise** `G2 = G1` with one EXISTING edge's weight RAISED (no new edge) — the rise is still
  attributed to the weight-increased edge (finding-0099). The test asserts the new-edge set is empty
  so a new-edges-only enumeration would report "no attribution" — the exact failure mode 0099 names.
* **decay-only** `G2 = G1 − edges` / weights lowered — NO conductance rise (the null).

The entry point `run_conductance` is driven over a `MirrorView` + a certified mirror spine, writing
to an in-memory `EvalResultsStore` (the dry-run path — it never writes to a core store): every
reading's evidence decodes to both grids + the cut fingerprint; `put()` is idempotent; the
real-corpus forward scan reports the sanctioned "no cut pair yet" partial.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from core.dreaming.cluster import NoteVector
from core.dreaming.graph import MirrorGraph
from core.mirror import MirrorView
from core.provenance import Provenance
from core.stores.versions import VersionStore
from core.temporal.spine import CutSources, Spine, SpineSources
from eval.harness.conductance import (
    METRIC_DEGENERACY,
    METRIC_FRAC_CONNECTED,
    METRIC_N_PAIRS,
    ConductanceEvidence,
    reconnection_scan,
    run_conductance,
)
from eval.harness.connectivity import ConnEvidence, cut_fingerprint
from eval.harness.store import EvalResultsStore

_MEM = Path(":memory:")


# ── fixtures ─────────────────────────────────────────────────────────────────────────────────────


class _Rows:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _row(digest: str, vec: np.ndarray) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": list(vec), "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _planted_graph(digests: list[str], sim: list[list[float]], *, sigma: float) -> MirrorGraph:
    """A MirrorGraph with a PLANTED cosine matrix — exact control of the before/after weights."""
    mat = np.array(sim, dtype=np.float64)
    n = len(digests)
    adj = (mat >= sigma) & ~np.eye(n, dtype=bool) if n else np.zeros((0, 0), dtype=bool)
    notes = tuple(NoteVector(digest=d, title=d, vector=(1.0,)) for d in digests)
    return MirrorGraph(notes=notes, sim=mat, sigma=sigma, _adj=adj)


def _bridged_two_cluster_view() -> MirrorView:
    """Two tight clusters joined by one weak bridge (the bp-059 fixture, exact cosines)."""
    e = np.eye(6)
    tail = float(np.sqrt(1 - 0.95**2))
    a0 = e[0]
    a1 = 0.95 * e[0] + tail * e[1]
    b0 = 0.5 * e[0] + float(np.sqrt(1 - 0.25)) * e[2]
    b1 = 0.95 * b0 + tail * e[3]
    rows = [_row("a0", a0), _row("a1", a1), _row("b0", b0), _row("b1", b1)]
    return MirrorView.project(_Rows(rows))


def _mirror_spine(*, docs: tuple[str, ...] = ("docA", "docB")) -> Spine:
    """A COMMIT-certified mirror spine (test_cuts pattern) — a real mirror frontier for the cut."""
    vs = VersionStore(_MEM)
    for i, d in enumerate(docs):
        vs.record(d, f"DIG{i}")
    return Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha="deadbeef"))


# a 4-node base: two strong pairs {a,b} and {c,d}, DISCONNECTED across the divide (cross cos 0.2)
_BASE = [[1.0, 0.9, 0.2, 0.2],
         [0.9, 1.0, 0.2, 0.2],
         [0.2, 0.2, 1.0, 0.9],
         [0.2, 0.2, 0.9, 1.0]]
_DIGESTS = ["a", "b", "c", "d"]
_SIGMA = 0.3                                            # cross cos 0.2 < σ ⇒ no cross edge in _BASE


def _with_edge(sim: list[list[float]], i: int, j: int, value: float) -> list[list[float]]:
    out = [row[:] for row in sim]
    out[i][j] = out[j][i] = value
    return out


def _new_edges(before: MirrorGraph, after: MirrorGraph) -> set[frozenset[str]]:
    """The edges present in `after` but ABSENT in `before` (the new-edges-only enumeration set)."""
    def edges(g: MirrorGraph) -> set[frozenset[str]]:
        return {frozenset((g.digest(i), g.digest(j)))
                for i in range(g.n) for j in g.neighbors(i) if j > i}
    return edges(after) - edges(before)


# ── item 6: the reconnection rider (synthetic-verified over the weight-increased set) ─────────────


def test_new_edge_cut_pair_reports_rise_and_names_the_bridge() -> None:
    """`G2 = G1 + {a–c}` bridges the two clusters: a positive Δ-conductance across the (a,c) divide,
    and leave-one-out names `a–c` as the bridging edge (reverting it erases the rise)."""
    before = _planted_graph(_DIGESTS, _BASE, sigma=_SIGMA)
    after = _planted_graph(_DIGESTS, _with_edge(_BASE, 0, 2, 0.8), sigma=_SIGMA)
    events = reconnection_scan(before, after, proper_time_gap=7)
    ac = next(e for e in events if {e.a, e.b} == {"a", "c"})
    assert ac.delta_conductance > 0
    assert ac.proper_time_gap == 7
    assert ("a", "c") in ac.bridging_edges                # leave-one-out CONFIRMED, not guessed


def test_edit_rise_is_attributed_and_new_edges_only_would_fail() -> None:
    """finding-0099: `G2 = G1` with the EXISTING `a–c` edge's weight RAISED (no new edge). The scan
    reports the rise and names the weight-increased edge. The new-edge set is EMPTY — a
    new-edges-only enumeration finds nothing to attribute (the exact failure mode 0099 names) — yet
    the weighted scan attributes it correctly."""
    base_edited = _with_edge(_BASE, 0, 2, 0.5)            # a–c already an edge at 0.5
    before = _planted_graph(_DIGESTS, base_edited, sigma=_SIGMA)
    after = _planted_graph(_DIGESTS, _with_edge(base_edited, 0, 2, 0.85), sigma=_SIGMA)  # raise it
    assert _new_edges(before, after) == set()             # NO new edge — new-edges-only would fail
    events = reconnection_scan(before, after, proper_time_gap=4)
    ac = next(e for e in events if {e.a, e.b} == {"a", "c"})
    assert ac.delta_conductance > 0
    assert ("a", "c") in ac.bridging_edges                # the weight-increased edge, LOO-confirmed


def test_decay_only_interval_shows_no_conductance_rise_the_null() -> None:
    """`G2 = G1` with an edge weight LOWERED (edit-apart) and no weight increased anywhere — no
    conductance rise on any pair (the null). A rise here would break monotonicity/attribution."""
    before = _planted_graph(_DIGESTS, _with_edge(_BASE, 0, 2, 0.8), sigma=_SIGMA)   # a–c present
    after = _planted_graph(_DIGESTS, _with_edge(_BASE, 0, 2, 0.4), sigma=_SIGMA)    # a–c weakened
    events = reconnection_scan(before, after, proper_time_gap=2)
    assert all(e.delta_conductance <= 1e-9 for e in events)   # no rise → no reconnection event
    assert events == []                                       # scan reports nothing on the null


def test_reported_bridges_are_only_leave_one_out_confirmed_never_guessed() -> None:
    """CN-3 falsifier: a named bridge that leave-one-out does NOT confirm. Reverting every reported
    bridging edge in isolation must actually erase the rise for that pair — verified independently
    here (the guessed-reconnection guard)."""
    before = _planted_graph(_DIGESTS, _BASE, sigma=_SIGMA)
    after = _planted_graph(_DIGESTS, _with_edge(_BASE, 0, 2, 0.8), sigma=_SIGMA)
    for event in reconnection_scan(before, after, proper_time_gap=1):
        for edge in event.bridging_edges:                 # each reported edge is truly load-bearing
            reverted = _planted_graph(_DIGESTS, _BASE, sigma=_SIGMA)   # _BASE lacks a–c: reverted
            assert {edge[0], edge[1]} == {"a", "c"}
            # reconnection over the reverted-to-before pair yields no rise for this event's pair
            back = reconnection_scan(before, reverted, proper_time_gap=1)
            assert all(e.delta_conductance <= 1e-9 for e in back)


# ── item 6: the entry point + keyed readings + the sanctioned partial ────────────────────────────


def test_run_conductance_writes_readings_with_degeneracy_and_aggregates() -> None:
    grid, t_grid = (0.4, 0.6, 0.8), (0.5, 1.0)
    store = EvalResultsStore(_MEM)
    result = run_conductance(view=_bridged_two_cluster_view(), spine=_mirror_spine(),
                             sigma_grid=grid, t_grid=t_grid, eval_store=store,
                             base_fingerprint="cfg-fp")
    assert result.readings_written > 0
    assert result.aggregates[METRIC_N_PAIRS] == 6.0       # C(4,2)
    assert METRIC_DEGENERACY in result.aggregates         # the self-diagnostic is always written
    assert 0.0 <= result.aggregates[METRIC_FRAC_CONNECTED] <= 1.0
    # every emitted profile carries the (σ,t) grids, the diagnostic, and the attached χ_s
    for p in result.profiles:
        assert p.sigma_grid == grid and p.t_grid == t_grid
        assert "mirror" in p.chi_s                         # per-stratum χ_s attached from the spine
        assert 0.0 < p.chi_s["mirror"] <= 1.0


def test_every_reading_evidence_decodes_to_both_grids_and_the_cut() -> None:
    """Each reading's evidence pins the σ-grid, the t-grid, AND the certified cut fingerprint (the
    (σ,t) index discipline — plan §3 risk-b) and round-trips through `ConductanceEvidence`."""
    grid, t_grid = (0.4, 0.6, 0.8), (0.5, 1.0, 2.0)
    spine = _mirror_spine()
    store = EvalResultsStore(_MEM)
    run_conductance(view=_bridged_two_cluster_view(), spine=spine, sigma_grid=grid, t_grid=t_grid,
                    eval_store=store, base_fingerprint="cfg-fp")
    expected_cut_fp = cut_fingerprint(spine.cut_at(strata=frozenset({"mirror"})))
    rows = store.query()
    assert rows
    for reading in rows:
        decoded = json.loads(reading.evidence_ref or "")
        assert decoded["instrument"] == "conductance/v1"
        assert decoded["sigma_grid"] == list(grid)
        assert decoded["t_grid"] == list(t_grid)          # the SECOND index is pinned
        assert decoded["cut_fingerprint"] == expected_cut_fp
        # round-trips through the dataclass
        ev = ConductanceEvidence(
            conn=ConnEvidence(grid=tuple(decoded["sigma_grid"]),
                              base_fingerprint=decoded["base_fingerprint"],
                              cut_fingerprint=decoded["cut_fingerprint"]),
            t_grid=tuple(decoded["t_grid"]),
        )
        assert json.loads(ev.as_ref()) == decoded


def test_put_is_idempotent_a_second_run_writes_zero() -> None:
    grid, t_grid = (0.4, 0.6, 0.8), (0.5, 1.0)
    view = _bridged_two_cluster_view()
    store = EvalResultsStore(_MEM)
    first = run_conductance(view=view, spine=_mirror_spine(), sigma_grid=grid, t_grid=t_grid,
                            eval_store=store, base_fingerprint="cfg-fp")
    second = run_conductance(view=view, spine=_mirror_spine(), sigma_grid=grid, t_grid=t_grid,
                             eval_store=store, base_fingerprint="cfg-fp")
    assert first.readings_written > 0
    assert second.readings_written == 0                   # every key already present (append-only)


def test_real_corpus_forward_scan_reports_the_sanctioned_no_cut_pair_partial() -> None:
    """v1 holds only the latest certified cut (no historical graph — bp-059's parked prerequisite),
    so `run_conductance` emits NO reconnection events and NOTES the partial (never reconstructs a
    past graph)."""
    result = run_conductance(view=_bridged_two_cluster_view(), spine=_mirror_spine(),
                             sigma_grid=(0.4, 0.6), t_grid=(1.0,),
                             eval_store=EvalResultsStore(_MEM), base_fingerprint="fp")
    assert result.reconnections == ()
    assert any("no cut pair yet" in n for n in result.notes)


def test_uncertified_spine_emits_nothing() -> None:
    """The fail-closed cut discipline (inherited from `acquire_mirror_cut`): an uncertified spine
    (no commit SHA) raises before any reading is written."""
    import pytest

    from core.temporal.spine import CutCertificateError

    bad = Spine.derive(SpineSources(versions=VersionStore(_MEM)),
                       cut_sources=CutSources(commit_sha=None))
    with pytest.raises(CutCertificateError):
        run_conductance(view=_bridged_two_cluster_view(), spine=bad, sigma_grid=(0.4,),
                        t_grid=(1.0,), eval_store=EvalResultsStore(_MEM), base_fingerprint="fp")


def test_singleton_corpus_emits_no_readings_and_notes_it() -> None:
    view = MirrorView.project(_Rows([_row("only", np.array([1.0, 0, 0, 0, 0, 0]))]))
    store = EvalResultsStore(_MEM)
    result = run_conductance(view=view, spine=_mirror_spine(), sigma_grid=(0.4, 0.8),
                             t_grid=(1.0,), eval_store=store, base_fingerprint="fp")
    assert result.readings_written == 0
    assert result.profiles == ()
    assert result.notes and store.query() == []
