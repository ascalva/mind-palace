"""The sensing firewall — observed exhaust provably cannot reach the authored mirror (Track G
item G3; Invariant 6, both directions).

The Track-G constraint: a sensing hand's observations are `observed`-tier and never touch the
authored mirror. This is not a call-site convention — it is the SAME structural partition that
guards the introspective read path, applied to the new inbound flow:

  * a `SensedObservation.to_row()` is stamped `observed` with no parameter (unforgeable), and
  * `MirrorView` refuses an `observed` row (`NonMirrorRowError`), while `ObservedView` refuses
    anything that is NOT `observed`,

so the two views partition the provenance tiers with no representable overlap: sensed data can
enter the assistant-tier `ObservedView` and CANNOT enter the mirror the dreamer clusters over.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.sensing import NonObservedRowError, ObservedView, SensedObservation

_REPO_ROOT = Path(__file__).resolve().parents[2]
# The private / orchestration zones an edge effector must never reach back into: `core` holds
# the vault-adjacent stores, `ops` the gate/ledger, `scheduler` the supervisor. An effector
# importing any of them would collapse "network and private data never share a component"
# (Invariant 2) — it is a Zone-B dumb pipe, coupled to the core only through the filesystem
# handoff, exactly like the bridge and the monitor.
_FORBIDDEN_EDGE_IMPORTS = frozenset({"core", "ops", "scheduler"})


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".", 1)[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _observation(body: str = "third-party exhaust") -> SensedObservation:
    return SensedObservation(request_id="r1", upstream="open-meteo", ts="t", body=body)


def test_sensed_rows_are_observed_tier():
    row = _observation().to_row()
    assert row["provenance"] == Provenance.OBSERVED.value
    assert Provenance.OBSERVED not in MIRROR_READABLE  # observed is outside the firewall


def test_sensed_observation_cannot_be_projected_into_a_mirror_view():
    # The load-bearing firewall claim: a sensed row handed to the mirror is UNREPRESENTABLE —
    # a type error at construction, not a check that could be forgotten.
    row = _observation().to_row()
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=(row,))


def test_a_store_of_sensed_rows_projects_to_an_empty_mirror():
    # Even routed through the sanctioned projection, observed rows never survive π_MR.
    class FakeStore:
        def __init__(self, rows):
            self._rows = rows

        def all_rows(self, *, provenances=None):
            if provenances is None:
                return list(self._rows)
            allowed = {str(p) for p in provenances}
            return [r for r in self._rows if r["provenance"] in allowed]

    store = FakeStore([_observation().to_row(), _observation("more exhaust").to_row()])
    view = MirrorView.project(store)
    assert len(view) == 0  # nothing observed reaches the mirror


def test_observed_view_refuses_authored_rows():
    # The partition's other half: the assistant-tier view refuses ground truth, so the two
    # tiers cannot be conflated in either direction.
    authored = {"provenance": Provenance.AUTHORED_SOLO.value, "text": "the owner wrote this"}
    with pytest.raises(NonObservedRowError):
        ObservedView(_rows=(authored,))


def test_observed_view_refuses_interpreted_and_curated_rows():
    for prov in (Provenance.INTERPRETED, Provenance.CURATED):
        with pytest.raises(NonObservedRowError):
            ObservedView(_rows=({"provenance": prov.value},))


def test_views_partition_the_tiers_with_no_overlap():
    # No single row is admissible to BOTH views — the tiers are disjoint by type.
    observed_row = _observation().to_row()
    authored_row = {"provenance": Provenance.AUTHORED_SOLO.value}

    ObservedView(_rows=(observed_row,))                       # observed → ObservedView ok
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=(observed_row,))                     # observed → MirrorView refused

    MirrorView(_rows=(authored_row,))                        # authored → MirrorView ok
    with pytest.raises(NonObservedRowError):
        ObservedView(_rows=(authored_row,))                  # authored → ObservedView refused


# --- the effector is a Zone-B dumb pipe: it never imports the private zones ------------------
def test_effectors_never_import_core_ops_or_scheduler():
    # Invariant 2, the edge→core direction: the sensing effector couples to the sealed core
    # ONLY through the filesystem handoff (mirrored wire shapes), never a Python import — so a
    # networked process can hold no handle to the vault-adjacent stores. The static core→edge
    # firewall (test_import_firewall.py) proves the other direction; this proves this one.
    offenders: dict[str, set[str]] = {}
    for path in (_REPO_ROOT / "edge" / "effectors").rglob("*.py"):
        bad = _import_roots(path) & _FORBIDDEN_EDGE_IMPORTS
        if bad:
            offenders[path.relative_to(_REPO_ROOT).as_posix()] = bad
    assert not offenders, f"edge/effectors reaches into private zones: {offenders}"
