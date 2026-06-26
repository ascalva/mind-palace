"""The curator (BUILD-SPEC §9) — deterministic detection, model seam for contradictions.

Proves: near-duplicate authored notes are flagged (candidates, never merged); derived rows
orphaned from the raw store are flagged for pruning; contradiction detection is DEFERRED until
a detector is injected (never faked); findings persist as INTERPRETED, and curation reads the
authored corpus but writes only to the derived store (the §8 firewall).
"""

from core.curator import CONTRADICTION, NEAR_DUPLICATE, PRUNE_CANDIDATE, Curator
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.derived import FINDING, DerivedStore

ROWS = [
    {"digest": "d1", "title": "orig", "text": "a", "provenance": "authored",
     "vector": [1.0, 0.0, 0.0]},
    {"digest": "d2", "title": "dup", "text": "a", "provenance": "authored",
     "vector": [0.999, 0.001, 0.0]},     # near-identical to orig
    {"digest": "d3", "title": "orphan", "text": "b", "provenance": "authored",
     "vector": [0.0, 1.0, 0.0]},         # digest absent from the raw store -> prune candidate
]


class FakeStore:
    def __init__(self, rows):
        self.rows = rows

    def all_rows(self, *, provenances=None):
        if provenances is None:
            return list(self.rows)
        allowed = {str(p) for p in provenances}
        return [r for r in self.rows if r["provenance"] in allowed]


class FakeRaw:
    def __init__(self, digests):
        self.digests = set(digests)

    def exists(self, digest):
        return digest in self.digests


def _curator(tmp_path, *, raw=None, detector=None):
    return Curator(
        store=FakeStore(list(ROWS)),
        derived=DerivedStore(tmp_path / "derived.sqlite"),
        raw=raw,
        near_dup_threshold=0.99,
        cluster_threshold=0.6,
        min_cluster_size=2,
        contradiction_detector=detector,
    )


def test_near_duplicates_are_flagged_as_candidates(tmp_path):
    c = _curator(tmp_path)
    finds = c.near_duplicates()
    assert len(finds) == 1
    assert set(finds[0].subjects) == {"orig", "dup"}
    assert finds[0].subkind == NEAR_DUPLICATE
    assert finds[0].data["similarity"] >= 0.99


def test_orphaned_derived_rows_are_flagged_for_pruning(tmp_path):
    c = _curator(tmp_path, raw=FakeRaw({"d1", "d2"}))   # d3 is orphaned
    finds = c.prune_candidates()
    assert [f.subjects for f in finds] == [("orphan",)]
    assert finds[0].subkind == PRUNE_CANDIDATE


def test_prune_is_skipped_without_a_raw_store(tmp_path):
    assert _curator(tmp_path, raw=None).prune_candidates() == []


def test_contradiction_detection_is_deferred_without_a_detector(tmp_path):
    c = _curator(tmp_path)
    report = c.curate()
    assert report.contradiction_detection_deferred is True
    assert report.of(CONTRADICTION) == ()               # never faked


def test_injected_detector_produces_contradiction_findings(tmp_path):
    seen = []

    def detector(cluster, block):
        seen.append(cluster.titles)
        return ["orig and dup disagree about X"]

    c = _curator(tmp_path, detector=detector)
    finds = c.contradictions()
    assert seen == [("orig", "dup")]                    # ran over the theme cluster
    assert len(finds) == 1 and finds[0].subkind == CONTRADICTION
    assert finds[0].detail == "orig and dup disagree about X"


def test_curate_persists_findings_as_interpreted(tmp_path):
    c = _curator(tmp_path, raw=FakeRaw({"d1", "d2"}))
    report = c.curate()
    assert len(report.findings) >= 2                    # near-dup + prune
    stored = c.derived.all(kind=FINDING)
    assert len(stored) == len(report.findings)
    assert all(a.provenance is Provenance.INTERPRETED for a in stored)


def test_near_duplicates_read_the_mirror_only(tmp_path):
    # The near-dup scan must use the AUTHORED mirror, not all provenances.
    seen = {}

    class Recorder(FakeStore):
        def all_rows(self, *, provenances=None):
            seen["prov"] = provenances
            return super().all_rows(provenances=provenances)

    c = Curator(store=Recorder(list(ROWS)), derived=DerivedStore(tmp_path / "d.sqlite"),
                near_dup_threshold=0.99)
    c.near_duplicates()
    assert seen["prov"] == MIRROR_READABLE
