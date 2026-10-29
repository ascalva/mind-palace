"""Property-based tests for the heartbeat (ops/heartbeat.py) and the ledger's time parser.

Generated inputs, not chosen ones: whatever `pmset` prints, whatever sits in the pause file and
whatever time a model writes, the heartbeat neither crashes nor overreaches. The decision table's
safety invariant: a blocker can only take permission away, never grant it (monotonicity).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from core.stores.tasks import parse_when
from ops import heartbeat as hb

NOW = datetime(2026, 10, 29, 12, 0)

_power = st.builds(hb.Power, st.sampled_from(["ac", "battery", "unknown"]),
                   st.one_of(st.none(), st.integers(0, 100)), st.booleans())
_sensed = st.builds(
    hb.Sensed, at=st.just("2026-10-29T12:00:00"), power=_power,
    thermal_warning=st.one_of(st.none(), st.booleans()),
    chat_model=st.sampled_from(["busy", "loaded", "asleep", "down", "unknown"]),
    embedder=st.sampled_from(["busy", "loaded", "asleep", "down", "unknown"]),
    jobs=st.lists(st.text(max_size=8), max_size=3), to_notify=st.just([]),
    pending=st.dictionaries(st.sampled_from(["openwebui", "opencode"]),
                            st.one_of(st.none(), st.booleans())),
    breaker=st.sampled_from(["", "open after 3 failed syncs in a row; next try 13:00"]),
    free_gb=st.floats(0, 1000, allow_nan=False))
_policy = st.builds(hb.Policy, min_battery_pct=st.integers(0, 100),
                    min_free_gb=st.floats(0, 100, allow_nan=False),
                    actions=st.sampled_from([hb.ACTIONS, ("notify",), ("sync-dialogue",), ()]))


@given(_sensed, _policy)
@settings(max_examples=500)
def test_decide_is_total_and_never_wakes_the_agent(s, p):
    out = hb.decide(s, p)
    assert [d.action for d in out] == ["notify", "sync-dialogue", "wake-agent"]
    assert all(d.reason for d in out) and out[2].go is False


_ADD_BLOCKER = {   # each adds one blocker and changes nothing else
    "low power": lambda s: replace(s, power=replace(s.power, low_power=True)),
    "power unreadable": lambda s: replace(s, power=hb.Power("unknown", None, s.power.low_power)),
    "thermal warning": lambda s: replace(s, thermal_warning=True),
    "thermal unreadable": lambda s: replace(s, thermal_warning=None),
    "embedder down": lambda s: replace(s, embedder="down"),
    "chat busy": lambda s: replace(s, chat_model="busy"),
    "a job": lambda s: replace(s, jobs=[*s.jobs, "#9 re-embed"]),
    "breaker open": lambda s: replace(s, breaker="open after 9 failed syncs; next try 20:00"),
}


@given(_sensed, _policy, st.sampled_from(sorted(_ADD_BLOCKER)))
@settings(max_examples=1000)
def test_a_blocker_only_takes_permission_away(s, p, blocker):
    """Monotonicity, the table's safety invariant: adding a blocker never grants a sync, and
    every one of these blocks outright."""
    before = hb.decide(s, p)[1].go
    after = hb.decide(_ADD_BLOCKER[blocker](s), p)[1].go
    assert not (after and not before)
    assert after is False


@given(st.text(max_size=400), st.text(max_size=200), st.text(max_size=400))
@settings(max_examples=300)
def test_readings_never_crash_on_whatever_pmset_prints(batt, settings_out, therm):
    def run(argv):
        return {"batt": batt, "therm": therm}.get(list(argv)[-1], settings_out)

    power = hb.read_power(run)
    assert power.source in ("ac", "battery", "unknown")
    assert power.percent is None or power.percent >= 0
    assert hb.read_thermal(run) in (True, False, None)


@given(st.binary(max_size=300))
@settings(max_examples=300)
def test_no_pause_file_can_pause_past_the_cap(tmp_path_factory, raw):
    d = tmp_path_factory.mktemp("pause")
    (d / hb.PAUSE_FILE).write_bytes(raw)
    until = hb.paused_until(d, now=NOW)
    assert until is None or NOW < datetime.fromisoformat(until) <= NOW + hb.MAX_PAUSE


@given(st.text(max_size=40))
@settings(max_examples=500)
def test_parse_when_answers_or_refuses_nothing_else(text):
    try:
        out = parse_when(text, now=NOW)
    except ValueError:
        return
    assert datetime.fromisoformat(out).second == 0 and len(out) == 16


@given(st.integers(0, 60 * 24 * 7), st.sampled_from(["m", "h", "d"]))
@settings(max_examples=300)
def test_a_pause_ends_in_the_future_within_seven_days_or_is_refused(tmp_path_factory, n, unit):
    d = tmp_path_factory.mktemp("pause")
    try:
        until = datetime.fromisoformat(hb.pause(d, f"{n}{unit}", now=NOW))
    except ValueError:
        return
    assert NOW < until <= NOW + timedelta(days=7)
    assert hb.paused_until(d, now=NOW) == until.isoformat(timespec="minutes")
