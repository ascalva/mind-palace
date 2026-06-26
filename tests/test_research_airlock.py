"""Core side of the airlock handoff (§16, Invariant 2 & 11).

The sealed core writes de-identified criteria and reads public literature on disk only — no
S3, no network, no import of the bridge. These tests pin the round-trip and the outbound
firewall (emit re-asserts cleanliness; only criteria fields are serialized).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.research.airlock import ResearchAirlock
from core.research.criteria import DeidentificationError, ResearchCriteria, deidentify


def test_emit_writes_only_de_identified_criteria(tmp_path: Path):
    airlock = ResearchAirlock(handoff=tmp_path)
    c = deidentify("migraine", ["migraine prophylaxis"], from_year=2015)
    rid = airlock.emit(c)

    written = json.loads((tmp_path / "requests" / f"{rid}.json").read_text())
    # Exactly the de-identified criteria (+ a timestamp). No corpus content can appear.
    assert set(written) == {"id", "topic", "terms", "filters", "ts"}
    assert written["terms"] == ["migraine prophylaxis"]


def test_emit_refuses_dirty_criteria_at_the_boundary(tmp_path: Path):
    airlock = ResearchAirlock(handoff=tmp_path)
    dirty = ResearchCriteria(topic="ok", terms=("reach me at a@b.com",))
    with pytest.raises(DeidentificationError):
        airlock.emit(dirty)
    # Nothing leaked to the requests dir.
    assert not list((tmp_path / "requests").glob("*.json"))


def test_collect_round_trips_a_results_file(tmp_path: Path):
    airlock = ResearchAirlock(handoff=tmp_path)
    result = {
        "criteria_id": "abc",
        "papers": [{
            "source": "openalex", "id": "W1", "title": "A review of migraine prophylaxis",
            "abstract": "...", "year": 2020, "venue": "Headache", "type": "review",
            "doi": "10.1/x", "url": "https://doi.org/10.1/x", "is_preprint": False,
        }],
        "sources_queried": ["openalex"],
        "ts": "2026-06-26T00:00:00",
    }
    (tmp_path / "results" / "abc.json").write_text(json.dumps(result))

    got = airlock.collect_one("abc")
    assert got is not None
    assert got.criteria_id == "abc"
    assert got.papers[0].title.startswith("A review")
    assert got.papers[0].is_preprint is False
    # Consumed by default.
    assert airlock.collect_one("abc") is None


def test_airlock_module_touches_no_network_or_zones():
    # Structural: the core-side airlock never reaches S3/network/edge/cloud.
    import core.research.airlock as mod
    import core.research.criteria as crit
    import core.research.rank as rank

    for m in (mod, crit, rank):
        src = Path(m.__file__).read_text()
        assert "boto3" not in src
        assert "import edge" not in src
        assert "import cloud" not in src
