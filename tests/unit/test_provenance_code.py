"""core/kernel/provenance.py — the CODE class (bp-092 Item 2, dn-code-ingest-pipeline §2.3).

CODE is the seventh provenance class: builder-produced reality read from the repo instrument,
mirror-EXCLUDED by construction so the self-model and the §15 baselines never see code.
"""

from __future__ import annotations

from core.kernel.provenance import MIRROR_READABLE, Provenance


def test_code_is_a_provenance_class_with_the_expected_value():
    assert Provenance.CODE.value == "code"
    assert Provenance("code") is Provenance.CODE


def test_code_is_excluded_from_the_mirror():
    # the firewall: CODE ∉ MIRROR_READABLE = {authored-solo, authored-dialogue}
    assert Provenance.CODE not in MIRROR_READABLE
    assert MIRROR_READABLE == frozenset(
        {Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE})


def test_code_is_distinct_from_observed_and_the_authored_classes():
    assert Provenance.CODE not in {
        Provenance.OBSERVED, Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE,
        Provenance.CURATED, Provenance.INTERPRETED, Provenance.DERIVED_STRATUM,
    }
