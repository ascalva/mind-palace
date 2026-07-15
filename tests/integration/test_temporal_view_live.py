"""`TemporalView` β₁ on the LIVE citation graph, cross-checked vs an independent ripser oracle
(bp-037 / CQ-wire, Item 3).

The Item-7 falsifier lifted from fixtures onto the live store: β₁ of `X_cite` at HEAD must agree
when computed two INDEPENDENT ways — the Hodge null space (`dim ker L₁`, via `TemporalView`) and
ripser H₁ at scale `t=0` (`citation_distance_matrix`). A disagreement is a real assembly bug the
unit fixtures missed (plan §10 stop-and-raise → a codebase finding, NOT a relaxed assertion). The
test PRINTS the live β₁ + corpus size (the monitored corpus-topology datum).

**Skip, not fail, when the anchor carries no citation structure.** The projected reference store
lives in the running system's data dir; a fresh git worktree / a code-only commit has no
`corpus_to_corpus` edges at HEAD → environmental skip, exactly as bp-035's oracle skips at an
un-projected HEAD. It does NOT assert a fixed β₁ VALUE (the corpus grows) — only that the two agree.
"""

from __future__ import annotations

import subprocess

import pytest

from config.loader import REPO_ROOT, get_config
from core.complex.topology import persistence
from core.stores.reference_edges import open_reference_edge_store
from core.temporal.complex import build_citation_complex, citation_distance_matrix
from core.temporal_view import open_temporal_view


def _head_sha() -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],  # noqa: S607
                          capture_output=True, text=True, check=True).stdout.strip()


def _ripser_b1(cx) -> int:
    """Independent β₁: ripser H₁ alive at `t=0` on `citation_distance_matrix` (0 on an edge, 1
    off) — the SAME oracle the unit test uses, reimplemented here (a different computation than the
    Hodge null space `dim_ker_L1` the view reports)."""
    D = citation_distance_matrix(cx)
    if D.shape[0] < 1:
        return 0
    dgm1 = persistence(D, maxdim=1)["dgms"][1]
    return sum(1 for b, d in dgm1 if b <= 1e-9 < d)


def test_live_beta1_agrees_with_independent_ripser_oracle() -> None:
    head = _head_sha()

    # The view IS the probe: it assembles X_cite at HEAD. No corpus→corpus edges at the anchor (a
    # fresh worktree, a code-only commit, deploy-lag) → environmental skip, not a failure.
    view = open_temporal_view(commit=head)
    if view.n_edges == 0:
        pytest.skip(f"no corpus→corpus citation edges at HEAD {head[:12]} in this checkout "
                    "(environmental — the projected store lives in the running system's data dir)")

    # The INDEPENDENT oracle: rebuild the same anchored complex and count β₁ a DIFFERENT way (ripser
    # H₁), never the Hodge null space the view uses.
    store = open_reference_edge_store(get_config())
    try:
        cx = build_citation_complex(store, commit=head)
    finally:
        store.close()

    b1_hodge = view.citation_threads()
    b1_ripser = _ripser_b1(cx)

    # PRINT the corpus-topology datum (visible with `pytest -s`/`-rP`).
    print("\n=== X_cite β₁ — Hodge null-space vs ripser, live store @ HEAD ===")
    print(f"anchor commit: {head[:12]}   corpus at anchor: n_nodes={view.n_nodes}  "
          f"n_edges={view.n_edges}")
    print(f"β₁ (dim ker L₁, via TemporalView): {b1_hodge}")
    print(f"β₁ (ripser H₁ @ t=0, independent): {b1_ripser}")
    print(f"∂₁∂₂ = 0 self-check: {view.boundary_composition_is_zero()}")

    assert b1_hodge == b1_ripser, (
        f"live β₁ disagreement: TemporalView/dim_ker_L1={b1_hodge} vs ripser={b1_ripser} — an "
        "assembly bug the fixtures missed (plan §10 stop-and-raise → a codebase finding, NOT a "
        "relaxed assertion)")
    assert view.boundary_composition_is_zero() is True   # ∂₁∂₂=0 on the live citation backbone
    assert view.n_nodes >= 1                              # the anchor carried citation structure


# ── bp-038 Item 3: live two-snapshot coherence ‖[d,τ]‖ + supersession health ──────────────────

def _snapshot_by_commit() -> tuple[dict[str, set[tuple[str, str]]], dict[str, set[str]]]:
    """Per-commit (undirected non-self citation pairs, all-endpoint node set) from the live store —
    matching build_citation_complex's edge/node rules (self-citations are nodes but not 1-cells)."""
    from config.loader import get_config
    from core.stores.reference_edges import open_reference_edge_store

    store = open_reference_edge_store(get_config())
    try:
        pairs: dict[str, set[tuple[str, str]]] = {}
        nodes: dict[str, set[str]] = {}
        for e in store.all(direction="corpus_to_corpus"):
            nodes.setdefault(e.commit_sha, set()).update((e.source_ref, e.target_ref))
            if e.source_ref != e.target_ref:
                lo, hi = sorted((e.source_ref, e.target_ref))
                pairs.setdefault(e.commit_sha, set()).add((lo, hi))
    finally:
        store.close()
    return pairs, nodes


def _two_most_recent_distinct_snapshots():
    """(older, newer, pairs_old, nodes_old, pairs_new, nodes_new) for the two most-recent commits
    (git order) whose citation EDGE sets differ — or None if <2 distinct snapshots exist."""
    log = subprocess.run(["git", "-C", str(REPO_ROOT), "log", "--format=%H", "-80"],  # noqa: S607
                         capture_output=True, text=True, check=True).stdout.split()
    pairs, nodes = _snapshot_by_commit()
    newer = next((s for s in log if s in pairs or s in nodes), None)
    if newer is None:
        return None
    snap_new = pairs.get(newer, set())
    passed_newer = False
    for sha in log:
        if sha == newer:
            passed_newer = True
            continue
        if passed_newer and (sha in pairs or sha in nodes) and pairs.get(sha, set()) != snap_new:
            return (sha, newer, pairs.get(sha, set()), nodes.get(sha, set()),
                    snap_new, nodes.get(newer, set()))
    return None


def test_live_two_snapshot_coherence_and_supersession_health() -> None:
    from core.temporal_view import open_coherence, open_supersession_wellfounded

    found = _two_most_recent_distinct_snapshots()
    if found is None:
        pytest.skip("fewer than two DISTINCT corpus→corpus snapshots here (environmental)")
    older, newer, pairs_old, nodes_old, pairs_new, nodes_new = found

    report = open_coherence(commit_from=older, commit_to=newer)

    # INDEPENDENT oracle: restrict-to-common via pure set arithmetic (no operator machinery).
    common = nodes_old & nodes_new
    restricted_old = {p for p in pairs_old if p[0] in common and p[1] in common}
    severed_indep = restricted_old - pairs_new

    print("\n=== two-snapshot citation coherence ‖[d,τ]‖ — live store ===")
    print(f"from {older[:12]} → to {newer[:12]}")
    print(f"common nodes: {report.common_nodes}  ‖[d,τ]‖: {report.coherence_norm}  "
          f"flat: {report.is_flat}  +nodes {report.nodes_added} / -nodes {report.nodes_dropped}")
    print(f"severed (set-diff): {len(severed_indep)}  pairs: {sorted(report.severed)}")

    assert set(report.severed) == severed_indep      # the wiring produces the right severed set
    assert report.coherence_norm == len(report.severed)     # ‖[d,τ]‖ == count (Result 2, live)
    assert report.is_flat == (report.coherence_norm == 0)   # flatness ⟺ no severing
    assert report.common_nodes == len(common)
    assert report.nodes_dropped == len(nodes_old - nodes_new)

    # supersession well-foundedness over the newer anchor's corpus nodes (a cycle would RAISE, §10).
    assert open_supersession_wellfounded(commit=newer) is True
