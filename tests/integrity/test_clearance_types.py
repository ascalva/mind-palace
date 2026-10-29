"""The clearance lattice in the TYPE SYSTEM (dn-vector-membership-store A3.4) — integrity tier.

Owner ruling 2026-10-29: "accessible records without the correct permission should be
unrepresentable, and also enforced by the type system". This runs mypy in-process, under the
repo's own configuration, over a fixture of flows into mirror-only consumers, and asserts that
EXACTLY the mis-flows are errors: observed records, the top label, an unminted constructor call.

The negative control erases the label (the same sinks typed `Row[Any]` …) and asserts mypy then
accepts every flow — so green means the label does the work, not that mypy looked at nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from mypy import api

REPO_ROOT = Path(__file__).resolve().parents[2]

FLOWS = '''\
from typing import Any, Literal

from core.kernel.clearance import MIRROR_READ, Clearance, MirrorClass, Occupancy, PlaneHit, Row
from core.kernel.provenance import Provenance

SOLO = Literal[Provenance.AUTHORED_SOLO]
OBS = Literal[Provenance.OBSERVED]


def mirror_rows(rows: tuple[Row[MirrorClass], ...]) -> None: ...
def mirror_occ(xs: tuple[Occupancy[MirrorClass], ...]) -> None: ...
def mirror_hits(xs: tuple[PlaneHit[MirrorClass], ...]) -> None: ...
def mirror_clearance(c: Clearance[MirrorClass]) -> None: ...


def flows(solo_r: tuple[Row[SOLO], ...], obs_r: tuple[Row[OBS], ...],
          top_r: tuple[Row[Provenance], ...], solo_o: tuple[Occupancy[SOLO], ...],
          obs_o: tuple[Occupancy[OBS], ...], solo_h: tuple[PlaneHit[SOLO], ...],
          obs_h: tuple[PlaneHit[OBS], ...], solo_c: Clearance[SOLO],
          top_c: Clearance[Provenance]) -> None:
    mirror_rows(solo_r)
    mirror_occ(solo_o)
    mirror_hits(solo_h)
    mirror_clearance(solo_c)
    mirror_clearance(MIRROR_READ)
    mirror_rows(obs_r)  # E
    mirror_rows(top_r)  # E
    mirror_occ(obs_o)  # E
    mirror_hits(obs_h)  # E
    mirror_clearance(top_c)  # E
    Clearance({Provenance.OBSERVED}, "forged", mint=object())  # E
    Row(MIRROR_READ, {"provenance": "authored-solo"})  # E
'''


def _mypy_errors(tmp_path: Path, source: str) -> set[int]:
    f = tmp_path / "flows.py"
    f.write_text(source)
    out, err, _ = api.run(["--config-file", str(REPO_ROOT / "pyproject.toml"),
                           "--cache-dir", str(tmp_path / ".mypy_cache"), str(f)])
    assert "Cannot find implementation" not in out, out
    return {int(m.group(1)) for m in re.finditer(r"flows\.py:(\d+): error", out)}


def _marked(source: str) -> set[int]:
    return {i for i, line in enumerate(source.splitlines(), 1) if line.endswith("# E")}


@pytest.fixture(autouse=True)
def _repo_on_mypy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYPYPATH", str(REPO_ROOT))


def test_exactly_the_mis_flows_fail_type_checking(tmp_path: Path) -> None:
    assert _mypy_errors(tmp_path, FLOWS) == _marked(FLOWS)


def test_negative_control_an_erased_label_accepts_every_flow(tmp_path: Path) -> None:
    """With the sinks' label erased to `Any`, the same mis-flows type-check — proving the errors
    above come from the label, not from some unrelated mistake in the fixture."""
    erased = (FLOWS.replace("Row[MirrorClass]", "Row[Any]")
              .replace("Occupancy[MirrorClass]", "Occupancy[Any]")
              .replace("PlaneHit[MirrorClass]", "PlaneHit[Any]")
              .replace("Clearance[MirrorClass]", "Clearance[Any]"))
    unminted = ("mint=object()", "Row(MIRROR_READ")       # still wrong without any label
    still_wrong = {i for i, line in enumerate(erased.splitlines(), 1)
                   if line.endswith("# E") and any(u in line for u in unminted)}
    assert _mypy_errors(tmp_path, erased) == still_wrong
