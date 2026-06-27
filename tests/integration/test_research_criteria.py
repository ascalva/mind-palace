"""De-identification is the airlock's privacy boundary (§16, Invariant 11).

Only de-identified topical criteria may leave the sealed core; the corpus never does. These
tests pin both layers of defense: the conservative term scrubber, and the structural fact
that the type which crosses cannot carry note content.
"""

from __future__ import annotations

import pytest

from core.research.criteria import (
    DeidentificationError,
    ResearchCriteria,
    deidentify,
)


def test_clean_terms_pass_through():
    c = deidentify("migraine and stress", ["migraine prophylaxis", "chronic stress"])
    assert c.topic == "migraine and stress"
    assert c.terms == ("migraine prophylaxis", "chronic stress")


@pytest.mark.parametrize("bad", [
    "email me at alberto@example.com",       # email
    "see https://example.com/x",             # url
    "call +1 415 555 0199",                  # phone
    "@alberto on twitter",                   # handle
    "patient id 1234567",                    # long digit run
    "on 03/14/2026 i felt",                  # explicit date
    "a very long narrative sentence that is clearly not a topical search term at all here",
])
def test_unsafe_terms_are_dropped(bad):
    # A clean term survives; the unsafe one is dropped (conservative), not passed through.
    c = deidentify("headache", ["migraine", bad])
    assert "migraine" in c.terms
    assert all(bad != t for t in c.terms)


def test_all_unsafe_terms_raises():
    with pytest.raises(DeidentificationError):
        deidentify("x", ["a@b.com", "http://y", "+1 415 555 0100"])


def test_pii_topic_raises():
    # The topic itself crosses the airlock, so it must be clean too.
    with pytest.raises(DeidentificationError):
        deidentify("contact alberto@example.com", ["migraine"])


def test_to_request_carries_only_criteria_fields():
    # Structural firewall: the outbound payload has no field that could hold corpus content.
    c = deidentify("sleep", ["insomnia", "cbt"], from_year=2018,
                   publication_types=["meta-analysis", "garbage-type"], max_results=999)
    req = c.to_request()
    assert set(req) == {"id", "topic", "terms", "filters"}
    assert set(req["filters"]) == {"from_year", "publication_types", "max_results"}
    # publication types filtered to the allowlist; max_results capped at 100.
    assert req["filters"]["publication_types"] == ["meta-analysis"]
    assert req["filters"]["max_results"] == 100


def test_assert_clean_catches_hand_built_dirty_criteria():
    # Bypassing deidentify() doesn't help: assert_clean re-validates at the emit boundary.
    dirty = ResearchCriteria(topic="ok", terms=("contact me at a@b.com",))
    with pytest.raises(DeidentificationError):
        dirty.assert_clean()


def test_dedup_preserves_order():
    c = deidentify("t", ["migraine", "migraine", "stress"])
    assert c.terms == ("migraine", "stress")
