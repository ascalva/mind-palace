"""The forecast ledger (`eval/forecast/ledger.py`, dn-market-forecast-experiment D5): the protocol
is the genesis, the chain catches any edit, the ledger's own clock decides what was forecast
before a question closed or resolved, and once forecasts exist the bar cannot move."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from eval.forecast.ledger import (
    GENESIS_PREV,
    Comparison,
    Family,
    Forecast,
    Ledger,
    LedgerCorrupt,
    LedgerError,
    Protocol,
    Question,
    Resolution,
    Void,
    line_hash,
)

T0 = datetime(2026, 11, 6, 21, 0, tzinfo=UTC)
PROTOCOL = Protocol(name="test", primary=Comparison(Family.EVENT, "W", "P"),
                    arms=("M", "NULL", "W", "P"))


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def question(qid: str = "q1", *, closes: datetime = T0 + timedelta(days=10),
             cluster: str = "c1") -> Question:
    return Question(qid=qid, family=Family.EVENT, source="test", text=f"will {qid} happen",
                    resolution_text="the source's own words", closes_at=closes, cluster=cluster)


@pytest.fixture
def clock() -> Clock:
    return Clock(T0)


@pytest.fixture
def ledger(tmp_path: Path, clock: Clock) -> Ledger:
    led = Ledger(tmp_path / "ledger.jsonl", clock=clock)
    led.register(PROTOCOL)
    led.add_question(question())
    return led


def lines(led: Ledger) -> list[str]:
    return led.path.read_text(encoding="utf-8").splitlines()


def test_the_protocol_is_the_genesis_and_is_registered_once(tmp_path: Path, clock: Clock) -> None:
    led = Ledger(tmp_path / "ledger.jsonl", clock=clock)
    with pytest.raises(LedgerError, match="protocol"):
        led.add_question(question())
    with pytest.raises(LedgerError, match="nothing to amend"):
        led.amend(PROTOCOL)
    genesis = led.register(PROTOCOL)
    assert (genesis.seq, genesis.kind, genesis.prev) == (0, "protocol", GENESIS_PREV)
    with pytest.raises(LedgerError, match="amend"):
        led.register(PROTOCOL)
    assert led.amend(replace(PROTOCOL, notes="a visible amendment")).seq == 1


def test_a_file_whose_first_record_is_not_the_protocol_does_not_verify(tmp_path: Path) -> None:
    body: dict[str, object] = dict(question().body())
    recorded = T0.isoformat()
    digest = line_hash(0, "question", body, recorded, GENESIS_PREV)
    path = tmp_path / "ledger.jsonl"
    path.write_text(json.dumps({"seq": 0, "kind": "question", "body": body,
                                "recorded_at": recorded, "prev": GENESIS_PREV,
                                "hash": digest}) + "\n", encoding="utf-8")
    with pytest.raises(LedgerCorrupt, match="genesis"):
        Ledger(path).verify()


def test_the_chain_catches_an_edited_a_dropped_and_a_swapped_line(ledger: Ledger) -> None:
    ledger.add_forecast(Forecast("q1", "W", "r1", 0.40))
    ledger.add_forecast(Forecast("q1", "P", "r1", 0.45))
    good = lines(ledger)
    assert ledger.verify().seq == 3

    edited = json.loads(good[2])
    edited["body"]["p"] = 0.99                      # the hash is left as it was
    ledger.path.write_text("\n".join([*good[:2], json.dumps(edited), *good[3:]]) + "\n")
    with pytest.raises(LedgerCorrupt, match="hash mismatch"):
        ledger.verify()

    ledger.path.write_text("\n".join([*good[:2], *good[3:]]) + "\n")
    with pytest.raises(LedgerCorrupt, match="seq"):
        ledger.verify()

    ledger.path.write_text("\n".join([good[0], good[1], good[3], good[2]]) + "\n")
    with pytest.raises(LedgerCorrupt):
        ledger.verify()


def test_the_ledger_stamps_the_time_and_a_forecast_carries_none(ledger: Ledger,
                                                                clock: Clock) -> None:
    clock.at = T0 + timedelta(hours=1)
    entry = ledger.add_forecast(Forecast("q1", "W", "r1", 0.4))
    assert entry.recorded_at == clock.at
    assert not {"recorded_at", "at", "time", "emitted_at"} & set(entry.body)


@pytest.mark.parametrize("bad", [
    Forecast("nope", "W", "r1", 0.5),               # unknown question
    Forecast("q1", "I", "r1", 0.5),                 # an arm the protocol does not register
    Forecast("q1", "W", "r1", 1.5),
    Forecast("q1", "W", "r1", -0.1),
    Forecast("q1", "W", "r1", math.nan),
    Forecast("q1", "W", "", 0.5),                   # no round
])
def test_a_malformed_forecast_is_refused_and_writes_nothing(ledger: Ledger, bad: Forecast) -> None:
    before = lines(ledger)
    with pytest.raises(LedgerError):
        ledger.add_forecast(bad)
    assert lines(ledger) == before


def test_a_boolean_is_not_a_probability(ledger: Ledger) -> None:
    with pytest.raises(LedgerError, match="probability"):
        ledger.add_forecast(Forecast("q1", "W", "r1", True))


def test_one_forecast_per_arm_question_and_round(ledger: Ledger) -> None:
    ledger.add_forecast(Forecast("q1", "W", "r1", 0.4))
    with pytest.raises(LedgerError, match="already forecast"):
        ledger.add_forecast(Forecast("q1", "W", "r1", 0.6))
    ledger.add_forecast(Forecast("q1", "W", "r2", 0.6))


def test_no_forecast_after_the_question_closes(ledger: Ledger, clock: Clock) -> None:
    clock.at = T0 + timedelta(days=10)              # exactly the close
    with pytest.raises(LedgerError, match="closed"):
        ledger.add_forecast(Forecast("q1", "W", "r9", 0.5))


def test_no_forecast_after_a_resolution_or_a_void(ledger: Ledger) -> None:
    ledger.add_question(question("q2", cluster="c2"))
    ledger.resolve(Resolution("q1", 1, T0 + timedelta(hours=2), "test:settled"))
    ledger.void(Void("q2", "the market was cancelled"))
    with pytest.raises(LedgerError, match="resolved"):
        ledger.add_forecast(Forecast("q1", "W", "r1", 0.5))
    with pytest.raises(LedgerError, match="voided"):
        ledger.add_forecast(Forecast("q2", "W", "r1", 0.5))


def test_a_resolution_is_binary_and_happens_once(ledger: Ledger) -> None:
    with pytest.raises(LedgerError, match="0 or 1"):
        ledger.resolve(Resolution("q1", 2, T0, "test"))
    ledger.resolve(Resolution("q1", 0, T0, "test"))
    with pytest.raises(LedgerError, match="already resolved"):
        ledger.resolve(Resolution("q1", 1, T0, "test"))


def test_naive_datetimes_are_refused(ledger: Ledger) -> None:
    before = lines(ledger)
    with pytest.raises(LedgerError, match="timezone"):
        ledger.add_question(question("q3", closes=datetime(2026, 12, 1)))
    with pytest.raises(LedgerError, match="timezone"):
        ledger.resolve(Resolution("q1", 1, datetime(2026, 11, 7), "test"))
    assert lines(ledger) == before


def test_a_question_that_already_closed_is_refused(ledger: Ledger) -> None:
    with pytest.raises(LedgerError, match="closed before"):
        ledger.add_question(question("old", closes=T0 - timedelta(days=1)))


def test_extend_is_all_or_nothing(ledger: Ledger) -> None:
    before = lines(ledger)
    with pytest.raises(LedgerError, match="unknown question"):
        ledger.extend([Forecast("q1", "W", "r1", 0.4), Forecast("missing", "P", "r1", 0.5)])
    assert lines(ledger) == before
    written = ledger.extend([question("q2", cluster="c2"), Forecast("q2", "W", "r1", 0.3)])
    assert [e.kind for e in written] == ["question", "forecast"]
    assert ledger.verify().seq == written[-1].seq


def test_once_forecasts_exist_the_bar_does_not_move(ledger: Ledger) -> None:
    ledger.amend(replace(PROTOCOL, delta=0.05))      # before any forecast: allowed
    ledger.add_forecast(Forecast("q1", "W", "r1", 0.4))
    current = replace(PROTOCOL, delta=0.05)
    for moved in (replace(current, delta=0.02), replace(current, alpha=0.10),
                  replace(current, primary=Comparison(Family.EVENT, "M", "P"))):
        with pytest.raises(LedgerError, match="may not move"):
            ledger.amend(moved)
    with pytest.raises(LedgerError, match="never remove"):
        ledger.amend(replace(current, arms=("M", "W", "P")))
    ledger.amend(replace(current, arms=("M", "NULL", "W", "P", "L"), n_clusters=126))
    with pytest.raises(LedgerError, match="already fixed"):
        ledger.amend(replace(current, arms=("M", "NULL", "W", "P", "L"), n_clusters=60))


def test_the_protocol_refuses_arms_outside_d4() -> None:
    with pytest.raises(LedgerError, match="D4"):
        Protocol(name="x", primary=Comparison(Family.EVENT, "W", "P"), arms=("W", "P", "Z"))
    with pytest.raises(LedgerError, match="does not register"):
        Protocol(name="x", primary=Comparison(Family.EVENT, "W", "L"), arms=("W", "P"))


def test_the_head_names_the_last_line(ledger: Ledger) -> None:
    ledger.add_forecast(Forecast("q1", "W", "r1", 0.4))
    head = ledger.verify()
    last = json.loads(lines(ledger)[-1])
    assert (head.seq, head.hash) == (last["seq"], last["hash"])
    assert head.counts["forecast"] == 1 and head.counts["protocol"] == 1
