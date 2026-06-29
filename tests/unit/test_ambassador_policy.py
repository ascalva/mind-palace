"""The two cross-cutting deltas (Track B / authoritative note §5): effort narration register +
the earned-interruption policy.
"""

from agents.ambassador.policy import (
    LEAKY_NOUNS,
    InterruptionPolicy,
    Sensitivity,
    narrate_effort,
    parse_sensitivity,
)


def test_effort_narration_is_plain_and_leaks_no_internals():
    for text in (narrate_effort("my sleep patterns"), narrate_effort()):
        low = text.lower()
        for noun in LEAKY_NOUNS:
            assert noun not in low, f"effort narration leaked internal noun {noun!r}: {text!r}"
        assert "dig" in low                      # the RIGHT register: honest about the work + wait
    assert "sleep patterns" in narrate_effort("my sleep patterns")


def test_interruption_policy_matrix():
    off = InterruptionPolicy(Sensitivity.OFF)
    earned = InterruptionPolicy(Sensitivity.EARNED_ONLY)
    verbose = InterruptionPolicy(Sensitivity.VERBOSE)

    assert off.admits(True) is False and off.admits(False) is False        # never
    assert earned.admits(True) is True and earned.admits(False) is False   # only the earned
    assert verbose.admits(True) is True and verbose.admits(False) is True   # freely


def test_default_policy_is_earned_only():
    assert InterruptionPolicy().sensitivity is Sensitivity.EARNED_ONLY


def test_parse_sensitivity_is_tolerant():
    assert parse_sensitivity("off") is Sensitivity.OFF
    assert parse_sensitivity("VERBOSE") is Sensitivity.VERBOSE
    assert parse_sensitivity("nonsense") is Sensitivity.EARNED_ONLY    # safe default
