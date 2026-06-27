"""Adversarial: PII in research criteria is refused at the airlock, not silently passed.

holistic-testing.md §1c (test_pii_scrubber_raises_on_doubt). The de-identifier is the privacy
boundary (§16, Invariant 11): a topic carrying an email/phone/URL raises rather than letting
doubt cross, and a hand-built dirty criteria can't bypass it — assert_clean re-checks at emit.
"""

from __future__ import annotations

import pytest

from core.research.criteria import DeidentificationError, ResearchCriteria, deidentify


@pytest.mark.parametrize("dirty_topic", [
    "contact alberto@example.com about migraines",
    "my number is +1 415 555 0199",
    "see https://intranet.local/patient/4815162342",
])
def test_pii_in_topic_is_refused(dirty_topic):
    # The topic itself crosses the airlock, so doubt there must raise, not drop-and-continue.
    with pytest.raises(DeidentificationError):
        deidentify(dirty_topic, ["migraine prophylaxis"])


def test_hand_built_dirty_criteria_cannot_bypass_emit():
    # Skipping deidentify() doesn't help: assert_clean re-validates at the boundary.
    dirty = ResearchCriteria(topic="ok", terms=("email me at a@b.com",))
    with pytest.raises(DeidentificationError):
        dirty.assert_clean()
