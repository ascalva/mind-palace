"""The dreaming agent (BUILD-SPEC §9) — deterministic, with fakes for the store + model.

Proves: dreaming reads the AUTHORED mirror only (the firewall); clusters become themes; the
synthesis context is Constitution-first and grounded in the cluster's notes; output is stored
as INTERPRETED dreams; the pre-return grounding check runs (passes a grounded reflection,
flags a fabricated citation). The live synthesis run is test_dreaming_live.py.
"""

from core.constitution import load_constitution
from core.dreaming import Dreamer
from core.provenance import MIRROR_READABLE
from core.selfcheck import FAIL
from core.stores.derived import DREAM, DerivedStore

ROWS = [
    {"digest": "d1", "title": "sleep-1", "text": "racing thoughts at night",
     "provenance": "authored", "vector": [1.0, 0.0, 0.0]},
    {"digest": "d2", "title": "sleep-2", "text": "slow breathing before bed",
     "provenance": "authored", "vector": [0.96, 0.04, 0.0]},   # clusters with sleep-1
    {"digest": "d3", "title": "cooking", "text": "slow-cooked ragu",
     "provenance": "authored", "vector": [0.0, 0.0, 1.0]},     # isolated -> dropped (<min_size)
]


class FakeStore:
    def __init__(self, rows):
        self.rows = rows
        self.last_provenances = "unset"

    def all_rows(self, *, provenances=None):
        self.last_provenances = provenances
        if provenances is None:
            return list(self.rows)
        allowed = {str(p) for p in provenances}
        return [r for r in self.rows if r["provenance"] in allowed]


class CapturingSynth:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def __call__(self, messages):
        self.calls.append(messages)
        return self.reply


def _dreamer(tmp_path, reply, rows=ROWS):
    return Dreamer(
        store=FakeStore(list(rows)),
        synthesize=CapturingSynth(reply),
        derived=DerivedStore(tmp_path / "derived.sqlite"),
        threshold=0.6, min_cluster_size=2,
    )


def test_dreaming_reads_the_authored_mirror_only(tmp_path):
    d = _dreamer(tmp_path, "Per [[sleep-1]] and [[sleep-2]], a theme of rest.")
    d.dream()
    assert d.store.last_provenances == MIRROR_READABLE   # firewall: observed can't seed a dream


def test_cluster_becomes_a_grounded_theme_and_is_stored(tmp_path):
    d = _dreamer(tmp_path, "Per [[sleep-1]] and [[sleep-2]], rest recurs as a theme.")
    themes = d.dream()
    assert len(themes) == 1
    assert set(themes[0].titles) == {"sleep-1", "sleep-2"}
    assert themes[0].check.passed                         # citations resolve to the cluster
    stored = d.derived.all(kind=DREAM)
    assert len(stored) == 1 and stored[0].subjects == themes[0].artifact.subjects


def test_synthesis_context_is_constitution_first_and_grounded(tmp_path):
    d = _dreamer(tmp_path, "[[sleep-1]] theme")
    d.dream()
    messages = d.synthesize.calls[0]
    assert messages[0]["content"] == load_constitution()              # Constitution outermost
    assert any("dreaming agent" in m["content"] for m in messages)    # role present
    assert any("[[sleep-1]]" in m["content"] for m in messages)       # grounded in the notes


def test_fabricated_citation_in_a_dream_is_flagged(tmp_path):
    d = _dreamer(tmp_path, "According to [[Not A Real Note]], do X.")
    themes = d.dream()
    assert not themes[0].check.passed
    assert any(f.status == FAIL for f in themes[0].check.findings)
    assert themes[0].artifact.data["grounded"] is False


def test_no_clusters_yields_no_dreams(tmp_path):
    # Single note per theme -> nothing meets min_cluster_size.
    rows = [ROWS[0], ROWS[2]]
    d = _dreamer(tmp_path, "unused", rows=rows)
    assert d.dream() == []
    assert d.derived.count() == 0
