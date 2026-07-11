"""The Dreamer loop v2 end to end (H8/H9; BUILD §3.1) — flag-gated, deterministic, one model seam.

build → locate/theme/tension/gaps (the panel over one complex) → noisy-OR support → adjudicate →
the earned synthesis per selected candidate → interpreted store → structural snapshot. The live
`dream()` (v1) is untouched — `dream_v2` refuses without the dream-R&D flag, exactly like the
panel it consumes.
"""

from __future__ import annotations

import dataclasses
from typing import Any, cast

import pytest

from config.loader import load_config
from core.complex.temporal import SnapshotStore
from core.complex_types import EdgeSign
from core.dreaming.dreamer import Dreamer
from core.dreaming.rnd import DreamRnDDisabledError
from core.provenance import Provenance
from core.stores.derived import DerivedStore
from core.stores.edges import CONTRADICTS, EdgeStore

# Two clusters (A, B) held together by a bridge note (g1), plus an isolated outlier (z1) —
# the same planted shape the R0/R1 tests use, so every lens fires deterministically.
ROWS = [
    {"digest": "dA1", "title": "A1", "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0],
     "text": "alpha one"},
    {"digest": "dA2", "title": "A2", "provenance": "authored-solo", "vector": [0.97, 0.03, 0.0],
     "text": "alpha two"},
    {"digest": "dB1", "title": "B1", "provenance": "authored-solo", "vector": [0.0, 1.0, 0.0],
     "text": "beta one"},
    {"digest": "dB2", "title": "B2", "provenance": "authored-solo", "vector": [0.0, 0.97, 0.03],
     "text": "beta two"},
    {"digest": "dG1", "title": "G1", "provenance": "authored-solo", "vector": [0.7, 0.7, 0.0],
     "text": "the bridge"},
    {"digest": "dZ1", "title": "Z1", "provenance": "authored-solo", "vector": [0.0, 0.0, 1.0],
     "text": "outlier"},
]
AUTHORED = {r["digest"] for r in ROWS}


class _RowSource:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances=None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


class _CountingSynth:
    """Echoes the [[titles]] in the evidence block (grounded ⇒ self-check passes) and counts
    invocations — the proof that synthesis is the ONLY model seam the pass exercises."""

    def __init__(self):
        self.calls = 0

    def __call__(self, messages) -> str:
        self.calls += 1
        import re
        content = messages[-1]["content"] if messages else ""
        titles = re.findall(r"\[\[([^\]]+)\]\]", content)
        cites = " ".join(f"[[{t}]]" for t in dict.fromkeys(titles))
        return f"A structural pattern connects {cites}."


def _on_config():
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True))


def _dreamer(tmp_path, *, edge_store=None, snapshots=None, derived=None) -> Dreamer:
    return Dreamer(
        store=_RowSource(ROWS),
        synthesize=_CountingSynth(),
        derived=derived if derived is not None else DerivedStore(tmp_path / "derived.sqlite"),
        edge_store=edge_store,
        snapshots=snapshots,
    )


def test_dream_v2_refuses_when_flag_off(tmp_path):
    with pytest.raises(DreamRnDDisabledError):
        _dreamer(tmp_path).dream_v2(config=load_config())


def test_dream_v2_end_to_end(tmp_path):
    snapshots = SnapshotStore(tmp_path / "structural.duckdb")
    dreamer = _dreamer(tmp_path, snapshots=snapshots)
    themes = dreamer.dream_v2(config=_on_config())

    # Dreams were produced from adjudicated candidates, all grounded and self-check-passing.
    assert themes
    assert all(t.check.passed for t in themes), [t.check.notes for t in themes]
    stored = dreamer.derived.all(kind="dream")
    assert len(stored) == len(themes)
    for art in stored:
        assert art.provenance is Provenance.INTERPRETED       # §8 firewall, structural
        assert art.derived_from and set(art.derived_from) <= AUTHORED   # leaves are authored
        assert art.data["loop"] == "v2"
        assert 0.0 < art.data["confidence"] <= 1.0
        assert art.data["methods"]                            # which lenses corroborated

    # The ONLY model seam: synthesis, once per stored dream, nothing else.
    # dreamer.synthesize is statically Synthesizer (Callable[[list[Message]], str]) -- _dreamer()
    # always injects a _CountingSynth (this file), which additionally counts invocations.
    synth = cast(_CountingSynth, dreamer.synthesize)
    assert synth.calls == len(themes)

    # 10. MEASURE — the snapshot persisted with the planted structure's invariants.
    assert snapshots.count() == 1
    latest = snapshots.latest_structural()
    assert latest is not None
    assert latest["frustration"] == pytest.approx(0.0, abs=1e-6)   # no contradiction asserted
    snapshots.close()


def test_dream_v2_orders_by_confidence_and_earns_the_model(tmp_path):
    dreamer = _dreamer(tmp_path)
    themes = dreamer.dream_v2(config=_on_config())
    confs = [t.artifact.data["confidence"] for t in themes]
    assert confs == sorted(confs, reverse=True)               # top candidates first
    # every synthesis was earned by a grounded candidate (no c=0 junk narrated)
    assert all(c > 0.0 for c in confs)


def test_dream_v2_tension_lens_fires_on_an_asserted_contradiction(tmp_path):
    edges = EdgeStore(tmp_path / "edges.sqlite")
    # a contradiction INSIDE cluster A closes a frustrated triangle with the bridge note
    edges.add("dA1", "dA2", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS)
    snapshots = SnapshotStore(tmp_path / "structural.duckdb")
    dreamer = _dreamer(tmp_path, edge_store=edges, snapshots=snapshots)
    themes = dreamer.dream_v2(config=_on_config())

    tension = [t for t in themes if "tension" in t.artifact.data["methods"]]
    assert tension, "the asserted contradiction did not surface as a tension theme"
    assert {"dA1", "dA2"} <= set(tension[0].artifact.derived_from)
    latest = snapshots.latest_structural()
    assert latest is not None   # dream_v2 just took a structural snapshot this pass
    assert latest["frustration"] > 0.0     # and the gauge saw it
    snapshots.close()


def test_dream_v2_two_passes_build_a_drift_trajectory(tmp_path):
    snapshots = SnapshotStore(tmp_path / "structural.duckdb")
    derived = DerivedStore(tmp_path / "derived.sqlite")
    _dreamer(tmp_path, snapshots=snapshots, derived=derived).dream_v2(config=_on_config())
    _dreamer(tmp_path, snapshots=snapshots, derived=derived).dream_v2(config=_on_config())
    traj = snapshots.trajectory("frustration")
    assert len(traj) == 2                                     # the F4 trajectory computes
    assert [v for _, v in traj] == pytest.approx([0.0, 0.0])
    snapshots.close()


def test_dream_v2_is_deterministic(tmp_path):
    a = _dreamer(tmp_path / "a").dream_v2(config=_on_config())
    b = _dreamer(tmp_path / "b").dream_v2(config=_on_config())
    assert [(t.titles, t.summary) for t in a] == [(t.titles, t.summary) for t in b]


def test_v1_dream_is_untouched(tmp_path):
    # The live path: same store, plain dream() — still the Phase-7 cluster→synthesize loop,
    # no flag needed, no snapshot, no panel. (F9 and the cron path rest on this.)
    dreamer = _dreamer(tmp_path)
    themes = dreamer.dream()
    assert themes and all(t.check.passed for t in themes)
    assert all("loop" not in t.artifact.data for t in themes)
