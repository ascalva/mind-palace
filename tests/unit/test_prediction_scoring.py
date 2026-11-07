"""The prediction scorer (`eval/predictions/scoring.py`, dn-prediction-ledger G5): proper scores,
comparisons resampled by cluster, the three controls, late predictions excluded, and a pilot that
never shows which arm is ahead."""

from __future__ import annotations

import json
import math
import random
import sys
import tempfile
from collections.abc import Callable
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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
    factor,
    growth,
    growth_path,
    growth_report,
    holm,
    known_edge,
    log_factor,
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
PROTOCOL = Protocol(name="test", primary=Comparison("main", "a", "b"),
                    secondary=(Comparison("main", "ref", "a"),),
                    arms=("ref", "null", "a", "b"), reference="ref", null="null",
                    bootstrap=2000)

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
                batch.append(Prediction(qid, arm, "r1", predict(m, o, rng)))
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
    plain = Protocol(name="plain", primary=Comparison("main", "a", "b"), arms=("a", "b"))
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
    led.add_prediction(Prediction("q", "a", "r1", 0.9))
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
                Prediction("a", "a", "r1", 0.5), Prediction("b", "a", "r1", 0.5)])
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


# -- the growth readout (GRW-1) -----------------------------------------------------------------

def ledger_from(path: Path, rows: list[tuple[float, float, bool]], *,
                protocol: Protocol = PROTOCOL) -> Ledger:
    """A ledger of one round in which `ref` says `r`, `a` says `p` and the outcome is `o`, per
    row, each question its own cluster; `b` and `null` copy the reference."""
    clock = Clock(T0)
    led = Ledger(path, clock=clock)
    led.register(protocol)
    batch: list[Record] = []
    for i, (r, p, _) in enumerate(rows):
        qid = f"q{i}"
        batch.append(Question(qid, "main", "test", qid, "test", CLOSE, f"c{i}"))
        batch.extend(Prediction(qid, arm, "r1", r) for arm in ("ref", "null", "b"))
        batch.append(Prediction(qid, "a", "r1", p))
    clock.at = T0 + timedelta(hours=1)
    led.extend(batch)
    clock.at = CLOSE + timedelta(hours=1)
    led.extend([Resolution(f"q{i}", int(o), CLOSE + timedelta(minutes=i), "test:settled")
                for i, (_, _, o) in enumerate(rows)])
    return led


probabilities = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(st.lists(st.tuples(probabilities, probabilities, st.booleans()), min_size=1, max_size=25))
@settings(max_examples=40, deadline=None)
def test_the_growth_is_the_exponential_of_the_cumulative_log_score_advantage(
        rows: list[tuple[float, float, bool]]) -> None:
    """GRW-1 on random ledgers: at the full stake the readout's log growth is the cumulative
    log-score advantage itself, read from the ledger's clipped log scores, and the product of the
    factors is its exponential; each factor is exp of its pair's advantage."""
    with tempfile.TemporaryDirectory() as tmp:
        t = table(ledger_from(Path(tmp) / "l.jsonl", rows).entries())
    clip = t.protocol.log_clip
    for r, p, o in rows:
        advantage = log_loss(r, int(o), clip) - log_loss(p, int(o), clip)
        assert factor(p, r, int(o), clip) == pytest.approx(math.exp(advantage), rel=1e-9)
    g = growth(t, "main", "a")
    assert g is not None and g.n == len(rows) and g.stake == 1.0
    assert g.log_advantage == pytest.approx(
        sum(log_loss(r, int(o), clip) - log_loss(p, int(o), clip) for r, p, o in rows))
    assert g.log_growth == g.log_advantage and not g.growth_is_log
    assert math.prod(factor(p, r, int(o), clip) for r, p, o in rows) == \
        pytest.approx(g.growth, rel=1e-9)
    assert g.growth == pytest.approx(math.exp(g.log_advantage), rel=1e-9)
    assert g.growth > 0 and g.worst_factor > 0                       # GRW-5: no ruin
    assert 0.0 <= g.drawdown <= 1.0


def test_a_mutated_factor_breaks_the_identity(tmp_path: Path) -> None:
    """The control: the half stake's growth, and a growth read without the reference, are not
    the exponential of the cumulative advantage."""
    rows = [(0.5, 0.8, True), (0.3, 0.2, False), (0.6, 0.9, False), (0.4, 0.7, True)]
    t = table(ledger_from(tmp_path / "l.jsonl", rows).entries())
    full = growth(t, "main", "a")
    half = growth(t, "main", "a", stake=0.5)
    assert full is not None and half is not None
    assert half.growth != pytest.approx(math.exp(half.log_advantage), rel=1e-6)
    clip = t.protocol.log_clip
    reference_free = math.prod(p if o else 1 - p for _, p, o in rows)
    assert reference_free != pytest.approx(math.exp(full.log_advantage), rel=1e-6)
    assert math.prod(factor(p, r, int(o), clip) for r, p, o in rows) == \
        pytest.approx(full.growth, rel=1e-12)


@pytest.mark.parametrize("rows", [
    pytest.param([(0.001, 0.999, True)] * 103, id="103-factors-of-999"),
    pytest.param([(0.999, 0.001, True)] * 108, id="108-factors-of-1-over-999"),
])
def test_a_run_whose_product_leaves_the_float_range_is_read_in_log_space(
        tmp_path: Path, rows: list[tuple[float, float, bool]],
        capsys: pytest.CaptureFixture[str]) -> None:
    """103 factors of 999 overflow a running product to inf, and 108 of 1/999 underflow it to 0,
    whose log raises. In log space the log growth is finite and is the exact sum of the clipped
    log-score differences; the growth, outside the float range, is reported as that log, flagged,
    and the command line prints it as e^x. The fractional stakes stay finite."""
    led = ledger_from(tmp_path / "l.jsonl", rows)
    t = table(led.entries())
    clip = t.protocol.log_clip
    exact = math.fsum(log_loss(r, int(o), clip) - log_loss(p, int(o), clip) for r, p, o in rows)
    assert abs(exact) > math.log(sys.float_info.max)           # its exponential is out of range
    g = growth(t, "main", "a")
    assert g is not None and math.isfinite(g.growth)
    assert g.growth_is_log and g.growth == g.log_growth == g.log_advantage
    assert g.log_growth == pytest.approx(exact, rel=1e-12)
    assert g.worst_factor > 0 and 0.0 <= g.drawdown <= 1.0
    r, p, o = rows[0]
    for stake in (0.5, 0.25):
        h = growth(t, "main", "a", stake=stake)
        assert h is not None and math.isfinite(h.growth) and not h.growth_is_log
        assert h.log_growth == pytest.approx(
            len(rows) * math.log1p(stake * (factor(p, r, int(o), clip) - 1.0)), rel=1e-12)
    assert main(["growth", "--ledger", str(led.path), "--unblind"]) == 0
    assert f"e^{exact:.2f}" in capsys.readouterr().out
    assert main(["growth", "--ledger", str(led.path), "--unblind", "--json"]) == 0
    full = [x for x in json.loads(capsys.readouterr().out)["readouts"]
            if x["arm"] == "a" and x["stake"] == 1.0]
    assert len(full) == 1 and full[0]["growth_is_log"] and full[0]["growth"] == g.log_growth


def test_the_growth_path_on_a_hand_sequence() -> None:
    """Factors 2, 1/2, 2: growth 2, per pair the cube root of 2, worst 1/2, the drawdown the fall
    from 2 to 1, and seven more such pairs to 10x at the realized mean; the half stake turns the
    factors 2 and 1/2 into 3/2 and 3/4, and a stake above 1 is refused."""
    two, half = math.log(2.0), math.log(0.5)
    path = growth_path([two, half, two], target=10.0)
    assert path.growth == pytest.approx(2.0) and not path.growth_is_log
    assert path.log_growth == pytest.approx(two)
    assert path.geometric_mean == pytest.approx(2 ** (1 / 3))
    assert path.worst_factor == pytest.approx(0.5) and path.drawdown == pytest.approx(0.5)
    assert path.to_target == math.ceil((math.log(10) - math.log(2)) / (math.log(2) / 3)) == 7
    assert growth_path([two, half, two], target=2.0).to_target == 0
    assert growth_path([half, half], target=10.0).to_target is None
    assert log_factor(0.8, 0.4, 1, 0.001, stake=0.5) == pytest.approx(math.log(1.5))
    assert log_factor(0.2, 0.4, 1, 0.001, stake=0.5) == pytest.approx(math.log(0.75))
    assert log_factor(0.8, 0.4, 1, 0.001) == log_loss(0.4, 1, 0.001) - log_loss(0.8, 1, 0.001)
    with pytest.raises(ValueError, match="GRW-5"):
        log_factor(0.8, 0.4, 1, 0.001, stake=2.0)
    with pytest.raises(ValueError, match="no factors"):
        growth_path([], target=10.0)


def test_the_path_in_log_space_holds_runs_beyond_the_float_range() -> None:
    """The two runs whose product leaves the float range, as log factors: the log growth is the
    exact sum, the growth is reported as that log, and nothing raises."""
    for value, n in ((999.0, 103), (1 / 999, 108)):
        logs = [math.log(value)] * n
        path = growth_path(logs, target=10.0)
        assert math.isfinite(path.log_growth) and path.growth_is_log
        assert path.log_growth == math.fsum(logs)                     # the exact sum, rounded
        assert path.growth == path.log_growth
        assert path.geometric_mean == pytest.approx(value)
        assert path.worst_factor == pytest.approx(value)
    assert growth_path([math.log(999.0)] * 103, target=10.0).to_target == 0
    down = growth_path([math.log(1 / 999)] * 108, target=10.0)
    assert down.to_target is None and down.drawdown == 1.0       # 1 - e^-746 rounds to 1


def test_the_null_arm_grows_by_exactly_one(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    t = table(led.entries())
    for stake in (1.0, 0.5, 0.25):
        g = growth(t, "main", "null", stake=stake)
        assert g is not None and g.growth == 1.0 and g.drawdown == 0.0 and g.worst_factor == 1.0
        assert g.log_growth == 0.0 and not g.growth_is_log
        assert g.log_advantage == 0.0 and g.to_target is None


def _shown(out: dict[str, object]) -> set[tuple[str, str]]:
    readouts = out["readouts"]
    assert isinstance(readouts, list)
    return {(g["arm"], g["family"]) for g in readouts}


def test_the_growth_readout_withholds_the_primary_comparison_before_n(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=30, arms=FOUR)
    out = growth_report(table(led.entries()))
    assert _shown(out) == {("null", "main")}
    assert out["withheld"] == [{"arm": "a", "family": "main"}, {"arm": "b", "family": "main"}]
    assert isinstance(out["blinded"], str) and "not fixed" in out["blinded"]
    led.amend(replace(PROTOCOL, n_clusters=30))
    out = growth_report(table(led.entries()))
    assert _shown(out) == {("null", "main"), ("a", "main"), ("b", "main")}
    assert out["withheld"] == [] and out["blinded"] is None
    assert out["target"] == 10.0 and out["stakes"] == [1.0, 0.5, 0.25]
    assert "growth" in report(table(led.entries()))


def test_the_growth_cli_reads_the_null_arm_and_withholds_the_rest(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    led = build(tmp_path / "l.jsonl", clusters=10, arms=FOUR)
    path = str(led.path)
    assert main(["growth", "--ledger", path]) == 0
    text = capsys.readouterr().out
    assert "withheld before N: a on main, b on main" in text
    assert text.count("\nnull ") == 3 and "\na " not in text
    assert main(["growth", "--ledger", path, "--unblind", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert {g["arm"] for g in out["readouts"]} == {"null", "a", "b"} and out["withheld"] == []


def test_a_protocol_without_a_growth_target_reads_the_default(tmp_path: Path) -> None:
    led = build(tmp_path / "l.jsonl", clusters=5, arms=FOUR)
    assert table(led.entries()).protocol.growth_target == 10.0
    body = dict(PROTOCOL.body())
    del body["growth_target"]
    assert Protocol.parse(body).growth_target == 10.0
    led.amend(replace(PROTOCOL, growth_target=4.0))      # a reading an amendment may change
    assert table(led.entries()).protocol.growth_target == 4.0
    with pytest.raises(ValueError, match="growth_target"):
        replace(PROTOCOL, growth_target=1.0)
