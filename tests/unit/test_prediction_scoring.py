"""The prediction scorer (`eval/predictions/scoring.py`, dn-prediction-ledger G5): proper scores,
comparisons resampled by cluster, the three controls, late predictions excluded, and a pilot that
never shows which arm is ahead."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from eval.predictions.__main__ import main
from eval.predictions.ledger import (
    Comparison,
    Ledger,
    Prediction,
    Protocol,
    Question,
    Record,
    Resolution,
    Void,
)
from eval.predictions.scoring import (
    Blinded,
    Pair,
    Pilot,
    brier,
    cluster_bootstrap,
    first_n,
    holm,
    known_edge,
    log_loss,
    murphy,
    null_check,
    oracle_pairs,
    pairs,
    pilot,
    report,
    required_clusters,
    table,
)

T0 = datetime(2026, 11, 6, 21, 0, tzinfo=UTC)
CLOSE = T0 + timedelta(days=10)
PINS = {"a": "sha256:" + "a" * 64, "b": "sha256:" + "b" * 64}
PROTOCOL = Protocol(name="test", primary=Comparison("main", "a", "b"),
                    secondary=(Comparison("main", "ref", "a"),),
                    arms=("ref", "null", "a", "b"), reference="ref", null="null",
                    bootstrap=2000, pinned=PINS)

Arm = Callable[[float, int, random.Random], float]


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def build(path: Path, *, clusters: int, per_cluster: int = 1, arms: dict[str, Arm],
          seed: int = 7, protocol: Protocol = PROTOCOL) -> Ledger:
    """A calibrated reference: each question's probability m is drawn, its outcome is
    Bernoulli(m), and each arm predicts from (m, outcome). Arms that read the outcome are only
    for controls."""
    rng = random.Random(seed)
    clock = Clock(T0)
    led = Ledger(path, clock=clock)
    led.register(protocol)
    batch: list[Record] = []
    truth: list[tuple[str, int]] = []
    for c in range(clusters):
        for j in range(per_cluster):
            qid = f"q{c}-{j}"
            m = rng.uniform(0.05, 0.95)
            o = 1 if rng.random() < m else 0
            batch.append(Question(qid, "main", "test", qid, "test", CLOSE, f"c{c}"))
            for arm, predict in arms.items():
                batch.append(Prediction(qid, arm, "r1", predict(m, o, rng),
                                        config=protocol.pinned.get(arm, "")))
            truth.append((qid, o))
    clock.at = T0 + timedelta(hours=1)
    led.extend(batch)
    clock.at = CLOSE + timedelta(hours=1)
    led.extend([Resolution(qid, o, CLOSE, "test:settled") for qid, o in truth])
    return led


def reference(m: float, o: int, rng: random.Random) -> float:
    return m


def noisy(m: float, o: int, rng: random.Random) -> float:
    return min(1.0, max(0.0, m + rng.gauss(0, 0.1)))


FOUR: dict[str, Arm] = {"ref": reference, "null": reference, "a": noisy, "b": noisy}


def test_brier_and_log_values() -> None:
    assert brier(0.7, 1) == pytest.approx(0.09)
    assert brier(0.7, 0) == pytest.approx(0.49)
    assert log_loss(0.0, 1, 0.001) == pytest.approx(-math.log(0.001))
    assert log_loss(1.0, 1, 0.001) == pytest.approx(-math.log(0.999))


@pytest.mark.parametrize("q", [0.1, 0.25, 0.5, 0.73, 0.9])
def test_both_scores_are_strictly_proper(q: float) -> None:
    grid = [i / 100 for i in range(1, 100)]

    def expected(score: Callable[[float, int], float]) -> list[float]:
        return [q * score(p, 1) + (1 - q) * score(p, 0) for p in grid]

    for score in (brier, lambda p, o: log_loss(p, o, 0.001)):
        values = expected(score)
        assert grid[values.index(min(values))] == pytest.approx(q, abs=0.005)


def test_the_null_copy_of_the_reference_scores_exactly_zero(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=40, arms=FOUR)
    t = table(led.entries())
    assert null_check(t) is True
    assert all(p.d == 0.0 for p in pairs(t, Comparison("main", "ref", "null")))


def test_a_wrong_copy_fails_the_null_check(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=10, arms={
        "ref": reference, "null": lambda m, o, r: min(1.0, m + 0.01), "a": noisy, "b": noisy})
    assert null_check(table(led.entries())) is False


def test_no_null_arm_means_no_null_check(tmp_path: Path) -> None:
    plain = Protocol(name="plain", primary=Comparison("main", "a", "b"), arms=("a", "b"),
                     pinned=PINS)
    led = build(tmp_path / "l.jsonl", clusters=5, arms={"a": noisy, "b": noisy},
                protocol=plain)
    assert null_check(table(led.entries())) is None


def test_the_oracle_has_maximal_skill(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    oracle = oracle_pairs(table(led.entries()), "main", "ref")
    assert all(p.d >= 0 for p in oracle) and sum(p.d for p in oracle) > 0


def test_the_known_edge_is_seen_with_enough_clusters_and_not_with_few(tmp_path: Path) -> None:
    """a and b are equally noisy here: the real mean is about 0. The control moves it to δ
    exactly and asks whether the spread the run actually has would let δ show (F-3)."""
    def powered(clusters: int) -> bool:
        led = build(tmp_path / f"l{clusters}.jsonl", clusters=clusters,
                    arms={"ref": reference, "a": noisy, "b": noisy}, seed=clusters)
        ps = known_edge(pairs(table(led.entries()), PROTOCOL.primary), 0.02)
        assert sum(p.d for p in ps) / len(ps) == pytest.approx(0.02)
        return cluster_bootstrap(ps, resamples=2000, seed=1, alpha=0.05).lo > 0

    assert powered(600)
    assert not powered(8)


def test_clusters_resample_as_units() -> None:
    values = [0.1, -0.05, 0.08, -0.02]
    grouped = [Pair(f"q{c}-{j}", "r", f"c{c}", v) for c, v in enumerate(values) for j in range(25)]
    spread = [Pair(f"q{i}", "r", f"s{i}", values[i % 4]) for i in range(100)]
    a = cluster_bootstrap(grouped, resamples=4000, seed=3, alpha=0.05)
    b = cluster_bootstrap(spread, resamples=4000, seed=3, alpha=0.05)
    assert a.mean == pytest.approx(b.mean)
    assert (a.hi - a.lo) > 2 * (b.hi - b.lo)


def test_the_bootstrap_is_reproducible_from_its_seed() -> None:
    ps = [Pair(f"q{i}", "r", f"c{i % 7}", (i % 5 - 2) / 10) for i in range(70)]
    assert cluster_bootstrap(ps, resamples=2000, seed=9, alpha=0.05) == \
        cluster_bootstrap(ps, resamples=2000, seed=9, alpha=0.05)


def test_one_cluster_has_no_interval() -> None:
    ps = [Pair(f"q{i}", "r", "c", 0.01) for i in range(10)]
    i = cluster_bootstrap(ps, resamples=2000, seed=1, alpha=0.05)
    assert i.mean == pytest.approx(0.01) and math.isnan(i.lo) and math.isnan(i.hi)


def test_required_clusters_matches_the_note() -> None:
    assert required_clusters(0.08, 0.02, 0.05, 0.80) == 126
    assert required_clusters(0.08, 0.01, 0.05, 0.80) == 503


def test_the_murphy_decomposition_is_exact() -> None:
    rng = random.Random(5)
    ps = [rng.random() for _ in range(500)]
    os_ = [1 if rng.random() < p else 0 for p in ps]
    d = murphy(ps, os_)
    total = sum(brier(p, o) for p, o in zip(ps, os_, strict=True)) / len(ps)
    assert d.reliability - d.resolution + d.uncertainty + d.residual == pytest.approx(total)

    binned = [round(int(p * 10) / 10 + 0.05, 2) for p in ps]   # constant within each bin
    e = murphy(binned, os_)
    assert e.residual == pytest.approx(0.0, abs=1e-12)


def test_a_prediction_recorded_after_the_world_resolved_is_late(tmp_path: Path) -> None:
    clock = Clock(T0)
    led = Ledger(tmp_path / "l.jsonl", clock=clock)
    led.register(PROTOCOL)
    led.add_question(Question("q", "main", "test", "q", "test", CLOSE, "c"))
    clock.at = T0 + timedelta(hours=3)              # the source settled at T0 + 2h, unseen
    led.add_prediction(Prediction("q", "a", "r1", 0.9, config=PINS["a"]))
    clock.at = T0 + timedelta(hours=4)
    led.resolve(Resolution("q", 1, T0 + timedelta(hours=2), "test:early"))
    t = table(led.entries())
    assert (t.late, len(t.scored)) == (1, 0)


def test_open_and_voided_predictions_are_counted_not_scored(tmp_path: Path) -> None:
    clock = Clock(T0)
    led = Ledger(tmp_path / "l.jsonl", clock=clock)
    led.register(PROTOCOL)
    led.extend([Question("a", "main", "t", "a", "t", CLOSE, "c1"),
                Question("b", "main", "t", "b", "t", CLOSE, "c2"),
                Prediction("a", "a", "r1", 0.5, config=PINS["a"]),
                Prediction("b", "a", "r1", 0.5, config=PINS["a"])])
    led.void(Void("b", "withdrawn"))
    t = table(led.entries())
    assert (t.open, t.voided, len(t.scored)) == (1, 1, 0)


def test_the_report_is_blinded_until_n(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    with pytest.raises(Blinded, match="not fixed"):
        report(table(led.entries()))
    led.amend(replace(PROTOCOL, n_clusters=1000))
    with pytest.raises(Blinded, match="1000"):
        report(table(led.entries()))
    out = report(table(led.entries()), unblind=True)
    assert set(out) >= {"primary", "secondary", "controls", "arms", "counts"}


def test_the_report_reads_once_n_is_reached(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    led.amend(replace(PROTOCOL, n_clusters=30))
    out = report(table(led.entries()))
    controls = out["controls"]
    assert isinstance(controls, dict) and controls["null_exact"] is True
    assert controls["oracle"] is not None


def test_waiting_past_n_reads_the_same_clusters_as_stopping_at_n(tmp_path: Path) -> None:
    """Control: the old report read all 50 clusters, so its primary differed from the 30-cluster
    ledger's, and a reader could stop whenever the interval looked good."""
    at_n = build(tmp_path / "n.jsonl", clusters=30, arms=FOUR)
    at_n.amend(replace(PROTOCOL, n_clusters=30))
    past = build(tmp_path / "p.jsonl", clusters=50, arms=FOUR)
    past.amend(replace(PROTOCOL, n_clusters=30))
    a, b = report(table(at_n.entries())), report(table(past.entries()))
    assert a["beyond_n"] == {"clusters": 0, "pairs": 0}
    assert b["beyond_n"] == {"clusters": 20, "pairs": 20}
    assert b["primary"] == a["primary"] and b["secondary"] == a["secondary"]
    assert b["arms"] == a["arms"] and b["controls"] == a["controls"]
    counts = b["counts"]
    assert isinstance(counts, dict) and counts["scored"] == 30 * 4


def test_the_first_n_clusters_are_the_first_to_enter_the_ledger(tmp_path: Path) -> None:
    """The order is the ledger's own lines, not the cluster names or the question ids."""
    clock = Clock(T0)
    led = Ledger(tmp_path / "o.jsonl", clock=clock)
    led.register(replace(PROTOCOL, n_clusters=2))
    for cluster in ("z", "m", "a"):                 # entered in this order, sorted the other way
        qid = f"q-{cluster}"
        clock.at += timedelta(minutes=1)
        led.extend([Question(qid, "main", "t", qid, "t", CLOSE, cluster),
                    Prediction(qid, "a", "r1", 0.5, config=PINS["a"]),
                    Prediction(qid, "b", "r1", 0.9, config=PINS["b"])])
    clock.at = CLOSE + timedelta(hours=1)
    led.extend([Resolution(f"q-{c}", 1, CLOSE, "t:s") for c in ("z", "m", "a")])
    t = table(led.entries())
    kept, beyond = first_n(t, 2)
    assert {s.cluster for s in kept.scored} == {"z", "m"}
    assert beyond == {"clusters": 1, "pairs": 1}
    out = report(t)
    assert out["beyond_n"] == beyond
    primary = out["primary"]
    assert isinstance(primary, dict) and primary["clusters"] == 2


def test_the_pilot_carries_no_mean(tmp_path: Path) -> None:
    assert not {f.name for f in fields(Pilot)} & {"mean", "lo", "hi", "p_value", "d"}
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    reading = pilot(table(led.entries()))
    assert reading.n_clusters == 30 and reading.sd > 0 and reading.required is not None
    assert reading.null_exact is True


def test_holm_adjusts_step_down() -> None:
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([]) == []


def test_the_cli_verifies_and_refuses_to_score_before_n(tmp_path: Path,
                                                        capsys: pytest.CaptureFixture[str]) -> None:
    led = build(tmp_path / "l.jsonl", clusters=10, arms=FOUR)
    path = str(led.path)
    assert main(["verify", "--ledger", path]) == 0
    assert "ok:" in capsys.readouterr().out
    assert main(["power", "--ledger", path, "--json"]) == 0
    assert '"mean"' not in capsys.readouterr().out
    assert main(["score", "--ledger", path]) == 2
    led.path.write_text(led.path.read_text().replace('"p":0.', '"p":0.0', 1))
    assert main(["verify", "--ledger", path]) == 1
