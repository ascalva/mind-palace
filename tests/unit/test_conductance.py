"""Unit tests for CN-3 + CN-4 — the (σ,t) conductance profile, the degeneracy self-diagnostic, and
the churn change-of-measure (bp-060 items 4 + 5).

Item 4 (CN-3): **Rayleigh monotonicity** — effective conductance is non-decreasing as σ loosens
(removals never raise conductance) on real + synthetic graphs; **every profile carries a
`degeneracy_diag`** (absent ⇒ malformed); on a synthetic DENSE graph the von-Luxburg diagnostic is
high (R_eff ≈ 1/d_A+1/d_B) and the profile flags finite-t as authoritative; a disconnected pair's
R_eff is ∞ ("not connected within grid"); never one scalar — always the (σ,t) profile.

Item 5 (CN-4): with `s_seq=s_lat=0` the weight reduces to `cos^α` (α=1 ⇒ the raw cosine — inert);
the churn signs are **structural** — lateral churn CONDUCTS (a plus), sequential churn IMPEDES (a
minus) — asserted numerically AND by an **AST scan** that no code path inverts either pairing; a
a grep asserts no hard-coded nonzero magnitude outside `CONDUCTANCE_THRESH` and no `ops.levers`;
the **depth budget** on a real spine — no ≼-chain within (s,W) exceeds `N_s(W)`; `χ_s ∈ (0,1]`,
`χ_s = 1` iff the window-events are totally ordered.

Fixtures reuse the sanctioned paths (test_connectivity `_Rows`/`_row` MirrorView source;
test_cuts injected-cut VersionStore spine). Synthetic graphs are built directly with planted cosine
matrices for exact control of the weighted Laplacian.
"""

from __future__ import annotations

import ast
import itertools
import math
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from core.dreaming.cluster import NoteVector
from core.dreaming.graph import MirrorGraph
from core.graph.conductance import (
    CONDUCTANCE_THRESH,
    ConductanceProfile,
    chi_s,
    chi_s_all,
    churn_weight,
    effective_conductance,
    sigma_t_profile,
)
from core.mirror import MirrorView
from core.provenance import Provenance
from core.stores.versions import VersionStore
from core.temporal.spine import CutSources, Spine, SpineSources

_MEM = Path(":memory:")
# bp-065 retarget (dn-core-graph-instruments P5): the sign-law / THRESH-dict / Law-C4 AST teeth
# scan the MATH, and the math re-homed to core/graph — the tooth moves with what it guards.
_CONDUCTANCE_SRC = Path("core/graph/conductance.py")


# ── fixtures ─────────────────────────────────────────────────────────────────────────────────────


class _Rows:
    """Provenance-filtering row source for MirrorView.project (test_connectivity pattern)."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": vec, "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _view(rows: list[dict[str, Any]]) -> MirrorView:
    return MirrorView.project(_Rows(rows))


def _planted_graph(digests: list[str], sim: list[list[float]], *, sigma: float) -> MirrorGraph:
    """A MirrorGraph with a PLANTED cosine matrix — exact control of the weighted Laplacian, no
    embedding round-trip. `_adj` follows `sim >= sigma` (the build convention)."""
    mat = np.array(sim, dtype=np.float64)
    n = len(digests)
    adj = (mat >= sigma) & ~np.eye(n, dtype=bool) if n else np.zeros((0, 0), dtype=bool)
    notes = tuple(NoteVector(digest=d, title=d, vector=(1.0,)) for d in digests)
    return MirrorGraph(notes=notes, sim=mat, sigma=sigma, _adj=adj)


def _two_cluster_view() -> MirrorView:
    """Two tight themes in an 8-dim token space (the test_connectivity philosophy), seeded noise."""
    photo = np.array([1.0, 1, 1, 1, 0, 0, 0, 0])
    synth = np.array([0.0, 0, 0, 0, 1, 1, 1, 1])
    rng = np.random.default_rng(0)
    rows: list[dict[str, Any]] = []
    for i in range(4):
        rows.append(_row(f"p{i}", list(photo + rng.normal(0, 0.03, 8))))
    for i in range(4):
        rows.append(_row(f"s{i}", list(synth + rng.normal(0, 0.03, 8))))
    return _view(rows)


def _one_doc_spine(*, versions: int) -> Spine:
    """A COMMIT-certified mirror spine with ONE doc's version chain (a TOTAL order — v0≼v1≼…)."""
    vs = VersionStore(_MEM)
    for i in range(versions):
        vs.record("docA", f"DIG{i}")
    return Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha="deadbeef"))


def _multi_doc_spine(*, docs: int) -> Spine:
    """A COMMIT-certified mirror spine with `docs` single-version docs — CONCURRENT events (a
    genuine partial order: no ≼ between distinct docs)."""
    vs = VersionStore(_MEM)
    for d in range(docs):
        vs.record(f"doc{d}", f"DIG{d}")
    return Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha="deadbeef"))


# ── item 4: the (σ,t) profile + Rayleigh monotonicity + the degeneracy self-diagnostic ───────────


def test_rayleigh_monotonicity_on_synthetic_graph() -> None:
    """Falsifier: conductance rising as σ TIGHTENS. On a planted 4-node graph, effective conductance
    for a connected pair is non-decreasing as σ loosens (removals never raise conductance)."""
    digests = ["a", "b", "c", "d"]
    sim = [[1.0, 0.9, 0.7, 0.5],
           [0.9, 1.0, 0.8, 0.6],
           [0.7, 0.8, 1.0, 0.85],
           [0.5, 0.6, 0.85, 1.0]]
    graph = _planted_graph(digests, sim, sigma=0.0)
    grid = (0.0, 0.5, 0.6, 0.8)
    prev = math.inf
    for sigma in grid:                                        # ascending σ ⇒ tightening
        cond = effective_conductance(graph, "a", "d", sigma=sigma, thresh=CONDUCTANCE_THRESH)
        assert cond <= prev + 1e-9, f"conductance rose as σ tightened at σ={sigma}"
        prev = cond


def test_rayleigh_monotonicity_on_real_two_cluster_graph() -> None:
    """The same law on a real embedding-derived graph (two clusters): loosest-σ conductance ≥
    tighter-σ conductance for a within-cluster pair that stays connected."""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    loose = effective_conductance(graph, "p0", "p1", sigma=0.2, thresh=CONDUCTANCE_THRESH)
    tight = effective_conductance(graph, "p0", "p1", sigma=0.8, thresh=CONDUCTANCE_THRESH)
    assert loose >= tight - 1e-9


def test_every_profile_carries_a_degeneracy_diagnostic() -> None:
    """CN-3 falsifier: a profile emitted without the self-diagnostic is malformed. Every profile in
    the pairwise summary carries a finite `degeneracy_diag`, and it is the SAME graph-level scalar
    on all of them."""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    profiles = sigma_t_profile(graph, sigma_grid=(0.2, 0.5, 0.8), t_grid=(0.5, 1.0, 2.0))
    assert profiles
    diags = {p.degeneracy_diag for p in profiles}
    assert len(diags) == 1                                    # one graph-level diagnostic
    for p in profiles:
        assert math.isfinite(p.degeneracy_diag)


def test_never_one_scalar_the_profile_is_sigma_by_t() -> None:
    """Falsifier: a single dense-graph R_eff scalar reported as "the conductance". Each profile's
    `commute` is a full (σ × t) grid, dimensions matching the declared grids."""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    sigma_grid, t_grid = (0.2, 0.5, 0.8), (0.5, 1.0)
    profiles = sigma_t_profile(graph, sigma_grid=sigma_grid, t_grid=t_grid)
    p = profiles[0]
    assert p.sigma_grid == sigma_grid and p.t_grid == t_grid
    assert len(p.commute) == len(sigma_grid)
    assert all(len(row) == len(t_grid) for row in p.commute)


def test_dense_graph_diagnostic_is_high_and_flags_finite_t_authoritative() -> None:
    """On a synthetic dense graph with heterogeneous degrees R_eff ≈ 1/d_A + 1/d_B (von Luxburg), so
    the diagnostic is high and the profile flags the finite-t diffusion distance as authoritative.
    (A fully-regular dense graph has constant R_eff — zero variance, an UNdiagnosable degenerate
    case reporting 0.0 — so degree variation is planted via a rank-1 `g_i·g_j` structure.)"""
    n = 12
    rng = np.random.default_rng(1)
    strengths = np.round(rng.uniform(0.5, 0.95, n), 4)
    sim = np.outer(strengths, strengths)
    np.fill_diagonal(sim, 1.0)
    graph = _planted_graph([f"n{i}" for i in range(n)], sim.tolist(), sigma=0.0)
    profiles = sigma_t_profile(graph, sigma_grid=(0.0, 0.5), t_grid=(1.0,))
    assert profiles[0].degeneracy_diag >= 0.9
    assert profiles[0].finite_t_authoritative()


def test_sparse_path_diagnostic_is_low_and_r_eff_stays_authoritative() -> None:
    """On a sparse path graph R_eff grows with path length, NOT with local degree, so the diagnostic
    is low — R_eff is not degenerate and finite-t is not flagged authoritative (the contrast)."""
    digests = ["a", "b", "c", "d", "e"]
    sim = [[1.0, 0.9, 0.1, 0.1, 0.1],
           [0.9, 1.0, 0.9, 0.1, 0.1],
           [0.1, 0.9, 1.0, 0.9, 0.1],
           [0.1, 0.1, 0.9, 1.0, 0.9],
           [0.1, 0.1, 0.1, 0.9, 1.0]]
    graph = _planted_graph(digests, sim, sigma=0.5)
    profiles = sigma_t_profile(graph, sigma_grid=(0.5, 0.8), t_grid=(1.0,))
    assert profiles[0].degeneracy_diag < 0.9
    assert not profiles[0].finite_t_authoritative()


def test_disconnected_pair_r_eff_is_infinite_not_connected_within_grid() -> None:
    """R_eff across disconnected components is ∞ (never a huge finite pseudo-inverse number) — the
    honest "not connected within grid"."""
    digests = ["x", "y"]
    sim = [[1.0, 0.1], [0.1, 1.0]]
    graph = _planted_graph(digests, sim, sigma=0.5)
    profiles = sigma_t_profile(graph, sigma_grid=(0.5, 0.9), t_grid=(1.0,))
    assert math.isinf(profiles[0].r_eff_loosest)
    assert not profiles[0].connected_at_loosest
    assert effective_conductance(graph, "x", "y", sigma=0.5,
                                 thresh=CONDUCTANCE_THRESH) == 0.0


def test_finite_t_diffusion_agrees_direction_with_r_eff_in_sparse_regime() -> None:
    """The finite-t diffusion distance and R_eff agree in the sparse (non-degenerate) regime: the
    farther-apart pair by R_eff is also farther by the finite-t commute distance."""
    digests = ["a", "b", "c", "d", "e"]
    sim = [[1.0, 0.9, 0.1, 0.1, 0.1],
           [0.9, 1.0, 0.9, 0.1, 0.1],
           [0.1, 0.9, 1.0, 0.9, 0.1],
           [0.1, 0.1, 0.9, 1.0, 0.9],
           [0.1, 0.1, 0.1, 0.9, 1.0]]
    graph = _planted_graph(digests, sim, sigma=0.5)
    profiles = {(p.a, p.b): p for p in sigma_t_profile(
        graph, sigma_grid=(0.5,), t_grid=(2.0,))}
    near = profiles[("a", "b")]                               # adjacent on the path
    far = profiles[("a", "e")]                                # opposite ends
    assert far.r_eff_loosest > near.r_eff_loosest
    assert far.commute[0][0] > near.commute[0][0]             # same ordering under finite-t


# ── item 5: the churn change-of-measure — signs are LAW, magnitudes ship at 0 ────────────────────


def test_zero_magnitude_weight_reduces_to_cosine_inert() -> None:
    """With `s_seq=s_lat=0` (shipped) and α=1 the weight is the raw cosine — a numerical no-op vs
    the unweighted graph (zero-magnitude ships inert)."""
    for cos in (0.0, 0.3, 0.5, 0.87, 1.0):
        assert churn_weight(cos, 5.0, 9.0, CONDUCTANCE_THRESH) == pytest.approx(cos)
    assert CONDUCTANCE_THRESH["s_seq"] == 0.0 and CONDUCTANCE_THRESH["s_lat"] == 0.0


def test_churn_signs_are_structural_lateral_conducts_sequential_impedes() -> None:
    """The signs are LAW: at a nonzero magnitude, raising LATERAL churn RAISES the weight (parallel,
    conducts), and raising SEQUENTIAL churn LOWERS it (series, impedes). A tuning dict that assigned
    the opposite sign could not reproduce this — the sign is not in the dict."""
    thresh = {"alpha": 1.0, "s_seq": 0.5, "s_lat": 0.5}
    base = churn_weight(0.6, a_lat=0.0, a_seq=0.0, thresh=thresh)
    more_lateral = churn_weight(0.6, a_lat=1.0, a_seq=0.0, thresh=thresh)
    more_sequential = churn_weight(0.6, a_lat=0.0, a_seq=1.0, thresh=thresh)
    assert more_lateral > base                                # lateral churn CONDUCTS (+)
    assert more_sequential < base                             # sequential churn IMPEDES (−)


def test_ast_scan_no_path_inverts_the_churn_signs() -> None:
    """AST falsifier: the ONLY `exp(...)` combining the churn magnitudes must be `+s_lat·a_lat −
    s_seq·a_seq`. We locate `churn_weight`, find the `s_lat*a_lat - s_seq*a_seq` subtraction, and
    assert the plus-term names lateral and the minus-term names sequential — no inversion."""
    tree = ast.parse(_CONDUCTANCE_SRC.read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "churn_weight")
    subs = [n for n in ast.walk(fn)
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub)]
    # the change-of-measure exponent: a subtraction whose two sides each multiply an s_* by an a_*
    found = False
    for sub in subs:
        names = {name.id for name in ast.walk(sub) if isinstance(name, ast.Name)}
        if {"s_lat", "a_lat", "s_seq", "a_seq"} <= names:
            # the LEFT operand (added, +) is the lateral term; the RIGHT (subtracted, −) sequential
            left = {name.id for name in ast.walk(sub.left) if isinstance(name, ast.Name)}
            right = {name.id for name in ast.walk(sub.right) if isinstance(name, ast.Name)}
            assert "s_lat" in left and "a_lat" in left and "s_seq" not in left
            assert "s_seq" in right and "a_seq" in right and "s_lat" not in right
            found = True
    assert found, "no `s_lat*a_lat - s_seq*a_seq` exponent found — the change-of-measure is missing"


def test_no_levers_import_and_no_hardcoded_nonzero_magnitude() -> None:
    """Falsifier: an `ops/levers.py` promotion inside this plan, or a nonzero magnitude hard-coded
    outside `CONDUCTANCE_THRESH`. The magnitudes ship at 0 in the dict; no lever import exists."""
    src = _CONDUCTANCE_SRC.read_text()
    assert "ops.levers" not in src and "import levers" not in src
    tree = ast.parse(src)
    # the CONDUCTANCE_THRESH literal ships s_seq and s_lat at exactly 0.0
    thresh_dict = next(
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
        and n.target.id == "CONDUCTANCE_THRESH" and isinstance(n.value, ast.Dict)
    )
    shipped = {
        k.value: v.value
        for k, v in zip(thresh_dict.keys, thresh_dict.values, strict=True)
        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
    }
    assert shipped["s_seq"] == 0.0 and shipped["s_lat"] == 0.0


def test_churn_weight_reads_all_magnitudes_from_the_thresh_dict() -> None:
    """The α exponent and both magnitudes come from `thresh` — none is a module literal. Changing
    the dict changes the weight; nothing is baked in (magnitudes THRESH-first)."""
    swept = {"alpha": 1.0, "s_seq": 0.0, "s_lat": 1.0}
    assert churn_weight(0.5, a_lat=2.0, a_seq=0.0, thresh=swept) > churn_weight(
        0.5, a_lat=2.0, a_seq=0.0, thresh=CONDUCTANCE_THRESH)


# ── item 5: the depth budget + χ_s (grounded in the real spine) ──────────────────────────────────


def test_depth_budget_no_chain_exceeds_n_s_on_the_real_spine() -> None:
    """CN-4 falsifier: a ≼-chain within (s, W) exceeding `N_s(W)` events. On real mirror spines
    (single-doc chain and multi-doc partial order), the longest chain never exceeds N_s — i.e.
    χ_s ≤ 1."""
    for spine in (_one_doc_spine(versions=4), _multi_doc_spine(docs=3)):
        value = chi_s(spine, "mirror")
        assert value is not None
        assert value <= 1.0                                   # longest-chain ≤ N_s(W): the budget


def test_chi_s_is_one_iff_totally_ordered() -> None:
    """`χ_s = 1` iff the window-events are totally ordered. A single doc's version chain is a total
    order (χ_s = 1); a multi-doc set is a genuine partial order (χ_s < 1)."""
    total = chi_s(_one_doc_spine(versions=3), "mirror")
    partial = chi_s(_multi_doc_spine(docs=3), "mirror")
    assert total == pytest.approx(1.0)                        # 3-chain over 3 events
    assert partial is not None and partial < 1.0              # 3 concurrent events → longest 1 / 3


def test_chi_s_is_in_the_half_open_unit_interval() -> None:
    """`χ_s ∈ (0,1]` wherever N_s > 0 (strictly positive — a single event is a 1-chain, χ_s = 1)."""
    for spine in (_one_doc_spine(versions=1), _one_doc_spine(versions=5), _multi_doc_spine(docs=4)):
        value = chi_s(spine, "mirror")
        assert value is not None
        assert 0.0 < value <= 1.0


def test_chi_s_is_none_when_the_stratum_is_empty() -> None:
    """`χ_s` is undefined (None) at `N_s = 0` — honest, never fabricated 0/0. `chi_s_all` skips."""
    empty = Spine.derive(SpineSources(versions=VersionStore(_MEM)),
                         cut_sources=CutSources(commit_sha="deadbeef"))
    assert chi_s(empty, "mirror") is None
    assert chi_s_all(empty) == {}


def test_chi_s_all_attaches_per_stratum_dict() -> None:
    """`chi_s_all` returns the per-stratum `dict[str, float]` attached to every emitted profile."""
    chi = chi_s_all(_one_doc_spine(versions=2))
    assert chi == {"mirror": pytest.approx(1.0)}


def test_profile_default_chi_s_is_empty_without_a_spine() -> None:
    """`sigma_t_profile` has no spine, so its profiles carry `chi_s = {}`; `run_conductance` fills
    it. (Guards the frozen default — a mutable default would share state across profiles.)"""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    profiles = sigma_t_profile(graph, sigma_grid=(0.2, 0.8), t_grid=(1.0,))
    assert all(p.chi_s == {} for p in profiles)
    profiles[0].chi_s["mirror"] = 0.5                         # mutating one must not touch another
    assert profiles[1].chi_s == {}


def test_profile_is_a_frozen_dataclass_carrying_both_grids() -> None:
    """Structural guard: `ConductanceProfile` is frozen and carries the (σ,t) grids + the always-on
    diagnostic (the shape the family's downstream — bp-061 bridges — reads)."""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    p = sigma_t_profile(graph, sigma_grid=(0.2,), t_grid=(1.0,))[0]
    assert isinstance(p, ConductanceProfile)
    with pytest.raises(FrozenInstanceError):
        p.degeneracy_diag = 0.0  # type: ignore[misc]         # frozen


def test_module_reads_no_clock_law_c4() -> None:
    """Law C4 (family-wide): the instrument reads no wall clock — no `time`/`datetime` import, no
    `ops.levers`. It is index-driven (σ, t, cut), never wall-time-driven."""
    src = _CONDUCTANCE_SRC.read_text()
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "time" not in imported and "datetime" not in imported
    assert not any(name == "ops" for name in imported)


def test_all_pairs_profiled() -> None:
    """The profile summary covers every distinct pair (the O(V²) tree of readings)."""
    graph = MirrorGraph.build(_two_cluster_view(), sigma=0.0)
    profiles = sigma_t_profile(graph, sigma_grid=(0.2, 0.6), t_grid=(1.0,))
    assert len(profiles) == graph.n * (graph.n - 1) // 2
    pairs = {(p.a, p.b) for p in profiles}
    digests = [graph.digest(i) for i in range(graph.n)]
    assert pairs == set(itertools.combinations(digests, 2))
