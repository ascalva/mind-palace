"""The prediction ledger (`eval/predictions/ledger.py`, dn-prediction-ledger G4): the protocol is
the genesis, the chain catches any edit, the ledger's own clock decides what was predicted before
a question closed or resolved, and once predictions exist the bar cannot move."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from eval.predictions.ledger import (
    GENESIS_PREV,
    Comparison,
    Ledger,
    LedgerCorrupt,
    LedgerError,
    Prediction,
    Protocol,
    Question,
    Resolution,
    Void,
    line_hash,
)

T0 = datetime(2026, 11, 6, 21, 0, tzinfo=UTC)
PROTOCOL = Protocol(name="test", primary=Comparison("main", "a", "b"),
                    arms=("ref", "null", "a", "b"), reference="ref", null="null")


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def question(qid: str = "q1", *, closes: datetime = T0 + timedelta(days=10),
             cluster: str = "c1", family: str = "main") -> Question:
    return Question(qid=qid, family=family, source="test", text=f"will {qid} happen",
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
    ledger.add_prediction(Prediction("q1", "a", "r1", 0.40))
    ledger.add_prediction(Prediction("q1", "b", "r1", 0.45))
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


def test_the_ledger_stamps_the_time_and_a_prediction_carries_none(ledger: Ledger,
                                                                  clock: Clock) -> None:
    clock.at = T0 + timedelta(hours=1)
    entry = ledger.add_prediction(Prediction("q1", "a", "r1", 0.4))
    assert entry.recorded_at == clock.at
    assert not {"recorded_at", "at", "time", "emitted_at"} & set(entry.body)


@pytest.mark.parametrize("bad", [
    Prediction("nope", "a", "r1", 0.5),             # unknown question
    Prediction("q1", "c", "r1", 0.5),               # an arm the protocol does not register
    Prediction("q1", "a", "r1", 1.5),
    Prediction("q1", "a", "r1", -0.1),
    Prediction("q1", "a", "r1", math.nan),
    Prediction("q1", "a", "", 0.5),                 # no round
])
def test_a_malformed_prediction_is_refused_and_writes_nothing(ledger: Ledger,
                                                              bad: Prediction) -> None:
    before = lines(ledger)
    with pytest.raises(LedgerError):
        ledger.add_prediction(bad)
    assert lines(ledger) == before


def test_a_boolean_is_not_a_probability(ledger: Ledger) -> None:
    with pytest.raises(LedgerError, match="probability"):
        ledger.add_prediction(Prediction("q1", "a", "r1", True))


def test_one_prediction_per_arm_question_and_round(ledger: Ledger) -> None:
    ledger.add_prediction(Prediction("q1", "a", "r1", 0.4))
    with pytest.raises(LedgerError, match="already predicted"):
        ledger.add_prediction(Prediction("q1", "a", "r1", 0.6))
    ledger.add_prediction(Prediction("q1", "a", "r2", 0.6))


def test_no_prediction_after_the_question_closes(ledger: Ledger, clock: Clock) -> None:
    clock.at = T0 + timedelta(days=10)              # exactly the close
    with pytest.raises(LedgerError, match="closed"):
        ledger.add_prediction(Prediction("q1", "a", "r9", 0.5))


def test_no_prediction_after_a_resolution_or_a_void(ledger: Ledger) -> None:
    ledger.add_question(question("q2", cluster="c2"))
    ledger.resolve(Resolution("q1", 1, T0 + timedelta(hours=2), "test:settled"))
    ledger.void(Void("q2", "the source withdrew the question"))
    with pytest.raises(LedgerError, match="resolved"):
        ledger.add_prediction(Prediction("q1", "a", "r1", 0.5))
    with pytest.raises(LedgerError, match="voided"):
        ledger.add_prediction(Prediction("q2", "a", "r1", 0.5))


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


def test_a_question_belongs_to_a_declared_family(ledger: Ledger) -> None:
    with pytest.raises(LedgerError, match="family"):
        ledger.add_question(question("q4", family="undeclared"))


def test_extend_is_all_or_nothing(ledger: Ledger) -> None:
    before = lines(ledger)
    with pytest.raises(LedgerError, match="unknown question"):
        ledger.extend([Prediction("q1", "a", "r1", 0.4), Prediction("missing", "b", "r1", 0.5)])
    assert lines(ledger) == before
    written = ledger.extend([question("q2", cluster="c2"), Prediction("q2", "a", "r1", 0.3)])
    assert [e.kind for e in written] == ["question", "prediction"]
    assert ledger.verify().seq == written[-1].seq


def test_once_predictions_exist_the_bar_does_not_move(ledger: Ledger) -> None:
    ledger.amend(replace(PROTOCOL, delta=0.05))      # before any prediction: allowed
    ledger.add_prediction(Prediction("q1", "a", "r1", 0.4))
    current = replace(PROTOCOL, delta=0.05)
    for moved in (replace(current, delta=0.02), replace(current, alpha=0.10),
                  replace(current, primary=Comparison("main", "ref", "b")),
                  replace(current, reference="a", null=None)):
        with pytest.raises(LedgerError, match="may not move"):
            ledger.amend(moved)
    widened = replace(current, arms=("ref", "null", "a", "b", "c"), families=("main", "other"))
    ledger.amend(widened)
    with pytest.raises(LedgerError, match="never drop"):
        ledger.amend(replace(widened, families=("main",)))
    with pytest.raises(LedgerError, match="never drop"):
        ledger.amend(replace(widened, arms=("ref", "null", "a", "b")))
    ledger.amend(replace(widened, n_clusters=126))
    with pytest.raises(LedgerError, match="already fixed"):
        ledger.amend(replace(widened, n_clusters=60))


def test_the_protocol_checks_its_own_names() -> None:
    with pytest.raises(LedgerError, match="arms must be names"):
        Protocol(name="x", primary=Comparison("main", "a", "b"), arms=("a", "b", "has space"))
    with pytest.raises(LedgerError, match="does not register"):
        Protocol(name="x", primary=Comparison("main", "a", "c"), arms=("a", "b"))
    with pytest.raises(LedgerError, match="does not declare"):
        Protocol(name="x", primary=Comparison("other", "a", "b"), arms=("a", "b"))
    with pytest.raises(LedgerError, match="reference arm"):
        Protocol(name="x", primary=Comparison("main", "a", "b"), arms=("a", "b"),
                 reference="ref")
    with pytest.raises(LedgerError, match="copies a reference"):
        Protocol(name="x", primary=Comparison("main", "a", "b"), arms=("a", "b"), null="a")


def test_the_head_names_the_last_line(ledger: Ledger) -> None:
    ledger.add_prediction(Prediction("q1", "a", "r1", 0.4))
    head = ledger.verify()
    last = json.loads(lines(ledger)[-1])
    assert (head.seq, head.hash) == (last["seq"], last["hash"])
    assert head.counts["prediction"] == 1 and head.counts["protocol"] == 1


def test_an_arm_may_name_a_model_variant(tmp_path: Path, clock: Clock) -> None:
    arms = ("a", "b", "dreamer:model-x", "dreamer:model-y")
    led = Ledger(tmp_path / "v.jsonl", clock=clock)
    led.register(Protocol(name="v", primary=Comparison("main", "a", "b"), arms=arms))
    led.add_question(question())
    led.add_prediction(Prediction("q1", "dreamer:model-x", "r1", 0.4, model="model-x"))
    led.add_prediction(Prediction("q1", "dreamer:model-y", "r1", 0.5, model="model-y"))
    with pytest.raises(LedgerError, match="not registered"):
        led.add_prediction(Prediction("q1", "dreamer:other", "r1", 0.5))


@pytest.mark.parametrize("arm", ["dreamer:", ":model", "dreamer:two words", "a:b:c", ""])
def test_a_malformed_variant_is_not_an_arm(arm: str) -> None:
    with pytest.raises(LedgerError, match="arms must be names"):
        Protocol(name="x", primary=Comparison("main", "a", "b"), arms=("a", "b", arm))


def test_a_pinned_arm_refuses_a_changed_config(tmp_path: Path, clock: Clock) -> None:
    """A long run gets tweaked; a tweak to a pinned arm is a new variant, never a silent change
    to an arm the primary comparison names."""
    pinned = replace(PROTOCOL, pinned={"b": "sha256:aaa"})
    led = Ledger(tmp_path / "p.jsonl", clock=clock)
    led.register(pinned)
    led.add_question(question())
    with pytest.raises(LedgerError, match="pinned"):
        led.add_prediction(Prediction("q1", "b", "r1", 0.4, config="sha256:bbb"))
    led.add_prediction(Prediction("q1", "b", "r1", 0.4, config="sha256:aaa"))
    with pytest.raises(LedgerError, match="keep their"):
        led.amend(replace(pinned, pinned={"b": "sha256:bbb"}))
    led.amend(replace(pinned, arms=(*PROTOCOL.arms, "b:v2"),
                      pinned={"b": "sha256:aaa", "b:v2": "sha256:bbb"}))
    led.add_prediction(Prediction("q1", "b:v2", "r1", 0.45, config="sha256:bbb"))


def test_a_pin_names_a_registered_arm() -> None:
    with pytest.raises(LedgerError, match="pinned arms"):
        replace(PROTOCOL, pinned={"c": "sha256:aaa"})
