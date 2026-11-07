"""Scoring a prediction ledger: `docs/design-notes/dn-prediction-ledger.md` G5.

Every number the scorer uses comes from the ledger's protocol record, never from a default here.

- **Scores.** Brier (primary) and the log score with `p` clipped to the protocol's bound. Both
  are strictly proper: the expected score is best only at the true probability.
- **The unit** is a (question, round) pair. Two arms are compared on the pairs both predicted;
  the statistic is `d = Brier(baseline) - Brier(arm)`, positive when the arm is better.
- **Clusters.** Pairs are resampled by their question's cluster, never one by one: questions
  that turn on the same underlying event are one observation, not several.
- **Late predictions** (recorded at or after the time the source says the question resolved)
  are excluded and counted (F-2).
- **The controls.** NULL is a recorded copy of the protocol's reference arm whose skill must be
  exactly 0 (F-1). KNOWN-EDGE and ORACLE are derived, never recorded. KNOWN-EDGE is the primary
  comparison's own pair differences, centered and moved to a true mean of δ: the same clusters
  and the same spread, so whether its interval excludes 0 is the power the run has at its
  realized N (F-3), and it says nothing of the real mean. An arm that merely leaned toward the
  outcome would improve on every question and be "detected" at any N, which is why the control
  borrows the real noise instead. ORACLE is `p = o` against the reference arm: the scorer can see
  an edge at all.
- **Blinding.** `pilot` reports the spread of the primary comparison's cluster means and the
  number of clusters it implies, never a mean. `report` refuses the comparisons until the
  protocol's `n_clusters` is fixed and reached, unless the caller unblinds on purpose.
- **The growth readout** (`growth`, dn-prediction-ledger G8): per arm against the reference arm,
  the growth of a proportional stake over the scored pairs, a thought experiment the scorer
  computes and nothing that stakes anything. By GRW-1 (`formal/Palace/Growth.lean`) it is the
  exponential of the cumulative log-score advantage of the arm over the reference, so it reads
  the ledger's own log scores as a holding. Before N the primary comparison's arms are withheld,
  as `report` withholds the mean.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from statistics import NormalDist

import numpy as np
import numpy.typing as npt

from eval.predictions.ledger import Comparison, Entry, LedgerError, Prediction, Protocol, replay

BINS = 10
_CHUNK = 1000


class Blinded(RuntimeError):
    """The comparisons are not readable yet: N is not fixed, or not reached."""


def brier(p: float, outcome: int) -> float:
    return (p - outcome) ** 2


def log_loss(p: float, outcome: int, clip: float) -> float:
    q = min(max(p, clip), 1.0 - clip)
    return -math.log(q if outcome == 1 else 1.0 - q)


@dataclass(frozen=True)
class Scored:
    """One arm's prediction on one (question, round), with the outcome."""

    qid: str
    round: str
    cluster: str
    family: str
    arm: str
    p: float
    outcome: int
    resolved_at: datetime


@dataclass(frozen=True)
class Table:
    protocol: Protocol
    scored: tuple[Scored, ...]
    late: int
    open: int
    voided: int


def table(entries: Sequence[Entry]) -> Table:
    """The scoreable predictions of a verified chain. The protocol in force is the last one."""
    state = replay(list(entries))
    if state.protocol is None:
        raise LedgerError("the ledger has no protocol")
    scored: list[Scored] = []
    late = open_ = voided = 0
    for entry in entries:
        if entry.kind != "prediction":
            continue
        p = Prediction.parse(entry.body)
        if p.qid in state.voids:
            voided += 1
            continue
        resolution = state.resolutions.get(p.qid)
        if resolution is None:
            open_ += 1
            continue
        if entry.recorded_at >= resolution.resolved_at:
            late += 1
            continue
        q = state.questions[p.qid]
        scored.append(Scored(p.qid, p.round, q.cluster, q.family, p.arm, p.p, resolution.outcome,
                             resolution.resolved_at))
    return Table(state.protocol, tuple(scored), late, open_, voided)


# -- one arm ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Bin:
    lo: float
    hi: float
    n: int
    mean_p: float
    frequency: float


@dataclass(frozen=True)
class Murphy:
    """Brier = reliability - resolution + uncertainty + residual. The residual is the within-bin
    part, exactly 0 when predictions are constant within each bin."""

    reliability: float
    resolution: float
    uncertainty: float
    residual: float
    bins: tuple[Bin, ...]


def murphy(ps: Sequence[float], outcomes: Sequence[int], bins: int = BINS) -> Murphy:
    if not ps or len(ps) != len(outcomes):
        raise ValueError("murphy needs equal, non-empty sequences")
    n = len(ps)
    base = sum(outcomes) / n
    groups: dict[int, list[int]] = defaultdict(list)
    for i, p in enumerate(ps):
        groups[min(int(p * bins), bins - 1)].append(i)
    rel = res = 0.0
    table_: list[Bin] = []
    for b in sorted(groups):
        members = groups[b]
        k = len(members)
        mean_p = sum(ps[i] for i in members) / k
        freq = sum(outcomes[i] for i in members) / k
        rel += k * (mean_p - freq) ** 2
        res += k * (freq - base) ** 2
        table_.append(Bin(b / bins, (b + 1) / bins, k, mean_p, freq))
    rel, res = rel / n, res / n
    unc = base * (1.0 - base)
    total = sum(brier(p, o) for p, o in zip(ps, outcomes, strict=True)) / n
    return Murphy(rel, res, unc, total - (rel - res + unc), tuple(table_))


@dataclass(frozen=True)
class ArmSummary:
    arm: str
    family: str
    n: int
    clusters: int
    brier: float
    log: float
    murphy: Murphy


def summarize(t: Table, arm: str, family: str) -> ArmSummary | None:
    rows = [s for s in t.scored if s.arm == arm and s.family == family]
    if not rows:
        return None
    return ArmSummary(
        arm=arm,
        family=family,
        n=len(rows),
        clusters=len({s.cluster for s in rows}),
        brier=sum(brier(s.p, s.outcome) for s in rows) / len(rows),
        log=sum(log_loss(s.p, s.outcome, t.protocol.log_clip) for s in rows) / len(rows),
        murphy=murphy([s.p for s in rows], [s.outcome for s in rows]),
    )


# -- two arms -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Pair:
    qid: str
    round: str
    cluster: str
    d: float


def pairs(t: Table, c: Comparison) -> list[Pair]:
    """The (question, round) pairs both arms predicted, `d = Brier(baseline) - Brier(arm)`."""
    base = {(s.qid, s.round): s for s in t.scored if s.arm == c.baseline and s.family == c.family}
    arm = {(s.qid, s.round): s for s in t.scored if s.arm == c.arm and s.family == c.family}
    out: list[Pair] = []
    for key in sorted(base.keys() & arm.keys()):
        b, a = base[key], arm[key]
        out.append(Pair(b.qid, b.round, b.cluster, brier(b.p, b.outcome) - brier(a.p, a.outcome)))
    return out


def oracle_pairs(t: Table, family: str, baseline: str) -> list[Pair]:
    """ORACLE against `baseline`: `p = o`, derived from the outcomes and never recorded."""
    return [Pair(s.qid, s.round, s.cluster, brier(s.p, s.outcome))
            for s in t.scored if s.arm == baseline and s.family == family]


def known_edge(ps: Sequence[Pair], delta: float) -> list[Pair]:
    """KNOWN-EDGE: these pairs' differences centered and moved to a true mean of exactly `delta`
    (pair-weighted, as the statistic is), keeping every cluster and the whole spread."""
    if not ps:
        return []
    mean = sum(p.d for p in ps) / len(ps)
    return [replace(p, d=p.d - mean + delta) for p in ps]


@dataclass(frozen=True)
class Interval:
    n_pairs: int
    n_clusters: int
    mean: float
    lo: float
    hi: float
    p_value: float


def _cluster_sums(ps: Sequence[Pair]) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for p in ps:
        sums[p.cluster] += p.d
        counts[p.cluster] += 1
    keys = sorted(sums)
    return (np.array([sums[k] for k in keys], dtype=np.float64),
            np.array([counts[k] for k in keys], dtype=np.float64))


def cluster_bootstrap(ps: Sequence[Pair], *, resamples: int, seed: int, alpha: float) -> Interval:
    """The pair-weighted mean of `d` with a percentile interval from resampling whole clusters,
    and a two-sided bootstrap p-value for `mean = 0`."""
    if not ps:
        raise ValueError("no pairs to compare")
    sums, counts = _cluster_sums(ps)
    k = len(sums)
    mean = float(sums.sum() / counts.sum())
    if k < 2:
        return Interval(len(ps), k, mean, math.nan, math.nan, math.nan)
    rng = np.random.default_rng(seed)
    boot = np.empty(resamples, dtype=np.float64)
    for start in range(0, resamples, _CHUNK):
        stop = min(start + _CHUNK, resamples)
        idx = rng.integers(0, k, size=(stop - start, k))
        boot[start:stop] = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    p_value = min(1.0, 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean())))
    return Interval(len(ps), k, mean, float(lo), float(hi), p_value)


def holm(p_values: Sequence[float]) -> list[float]:
    """Holm's step-down adjustment: family-wise error at most alpha over the secondary set."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


# -- the sample size, blinded -------------------------------------------------------------------

def cluster_sd(ps: Sequence[Pair]) -> float:
    """The spread of the per-cluster mean of `d`: the planning quantity, which says nothing of
    which arm is ahead."""
    sums, counts = _cluster_sums(ps)
    if len(sums) < 2:
        return math.nan
    return float(np.std(sums / counts, ddof=1))


def required_clusters(sd: float, delta: float, alpha: float, power: float) -> int:
    """Clusters needed to detect a mean difference of `delta`:
    `((z(1 - alpha/2) + z(power)) * sd / delta)^2`, rounded up."""
    if not (sd > 0 and delta > 0):
        raise ValueError("sd and delta must be positive")
    z = NormalDist().inv_cdf
    return max(2, math.ceil(((z(1 - alpha / 2) + z(power)) * sd / delta) ** 2))


@dataclass(frozen=True)
class Pilot:
    """The blinded reading: no mean anywhere in it."""

    comparison: Comparison
    n_pairs: int
    n_clusters: int
    sd: float
    required: int | None
    null_exact: bool | None


def pilot(t: Table) -> Pilot:
    c = t.protocol.primary
    ps = pairs(t, c)
    sd = cluster_sd(ps) if ps else math.nan
    required = (required_clusters(sd, t.protocol.delta, t.protocol.alpha, t.protocol.power)
                if sd > 0 else None)
    return Pilot(c, len(ps), len({p.cluster for p in ps}), sd, required, null_check(t))


def null_check(t: Table) -> bool | None:
    """F-1: the null arm is a copy of the reference arm, so every paired difference is exactly 0.
    None when the protocol names no null arm or the two share no pairs yet."""
    pr = t.protocol
    if pr.null is None or pr.reference is None:
        return None
    ps = pairs(t, Comparison(pr.primary.family, pr.reference, pr.null))
    if not ps:
        return None
    return all(p.d == 0.0 for p in ps)


# -- the growth readout -------------------------------------------------------------------------

STAKES = (1.0, 0.5, 0.25)


def _clip(p: float, clip: float) -> float:
    return min(max(p, clip), 1.0 - clip)


def factor(p: float, r: float, outcome: int, clip: float) -> float:
    """**GRW-1** The proportional stake's factor on one pair: `p / r` on yes and
    `(1 - p) / (1 - r)` on no, on the probabilities the log score reads (clipped to the
    protocol's bound), so that the identity with the ledger's log scores is exact and no factor
    is 0 (GRW-5)."""
    p, r = _clip(p, clip), _clip(r, clip)
    return p / r if outcome == 1 else (1.0 - p) / (1.0 - r)


@dataclass(frozen=True)
class Growth:
    """**GRW-1** One arm's growth against the reference arm on one family, at one stake.

    The thought experiment: a holding of 1 that, on each scored pair in the order the outcomes
    became known, is multiplied by `1 + stake * (F - 1)` for the proportional stake's factor `F`
    (`factor`). At `stake` 1 the growth is the product of the factors, which by GRW-1 equals
    `exp(log_advantage)`, the exponential of the cumulative log-score advantage of the arm over
    the reference: the readout is the ledger's own log scores, read as a holding. GRW-1 holds for
    the stake 1 only; the fractional stakes (0.5, 0.25) are the cautious practice and are read on
    their own terms. `geometric_mean` is the per-pair factor, `worst_factor` the smallest single
    factor, `drawdown` the largest fall of the running product from its peak, and `to_target` the
    number of further pairs, at the realized mean log growth per pair, before the holding reaches
    `target` times its start: 0 when it already has, None when the mean is not positive. Nothing
    here stakes anything."""

    arm: str
    family: str
    reference: str
    stake: float
    n: int
    growth: float
    log_advantage: float
    geometric_mean: float
    worst_factor: float
    drawdown: float
    target: float
    to_target: int | None

    def body(self) -> dict[str, object]:
        return {"arm": self.arm, "family": self.family, "reference": self.reference,
                "stake": self.stake, "pairs": self.n, "growth": self.growth,
                "log_advantage": self.log_advantage, "geometric_mean": self.geometric_mean,
                "worst_factor": self.worst_factor, "drawdown": self.drawdown,
                "target": self.target, "to_target": self.to_target}


def growth_path(factors: Sequence[float], *, stake: float, target: float
                ) -> tuple[float, float, float, float, int | None]:
    """The running product of `1 + stake * (F - 1)` over the factors: its end (the growth), the
    per-pair geometric mean, the worst single factor, the largest drawdown, and the further pairs
    to `target` at the realized mean."""
    if not factors:
        raise ValueError("no factors to compound")
    if not 0 < stake <= 1:
        raise ValueError("the stake must lie in (0, 1]: GRW-5 holds there and nowhere beyond")
    scaled = [1.0 + stake * (f - 1.0) for f in factors]
    running = peak = 1.0
    drawdown = 0.0
    for f in scaled:
        running *= f
        peak = max(peak, running)
        drawdown = max(drawdown, 1.0 - running / peak)
    n = len(scaled)
    mean = math.log(running) / n
    if running >= target:
        to_target: int | None = 0
    elif mean > 0:
        to_target = math.ceil((math.log(target) - math.log(running)) / mean)
    else:
        to_target = None
    return running, math.exp(mean), min(scaled), drawdown, to_target


def growth(t: Table, family: str, arm: str, *, stake: float = 1.0) -> Growth | None:
    """**GRW-1** `arm`'s growth against the protocol's reference arm on `family` at `stake`, over
    the (question, round) pairs both predicted, in the order their outcomes became known; None
    without a reference arm or without pairs."""
    pr = t.protocol
    if pr.reference is None:
        return None
    base = {(s.qid, s.round): s for s in t.scored if s.arm == pr.reference and s.family == family}
    own = {(s.qid, s.round): s for s in t.scored if s.arm == arm and s.family == family}
    keys = sorted(base.keys() & own.keys(), key=lambda k: (base[k].resolved_at, k))
    if not keys:
        return None
    factors = [factor(own[k].p, base[k].p, base[k].outcome, pr.log_clip) for k in keys]
    advantage = sum(log_loss(base[k].p, base[k].outcome, pr.log_clip)
                    - log_loss(own[k].p, own[k].outcome, pr.log_clip) for k in keys)
    end, geometric, worst, drawdown, to_target = growth_path(
        factors, stake=stake, target=pr.growth_target)
    return Growth(arm, family, pr.reference, stake, len(keys), end, advantage, geometric, worst,
                  drawdown, pr.growth_target, to_target)


def _blind(t: Table) -> str | None:
    """Why the comparisons are not readable yet, or None once N is fixed and reached."""
    pr = t.protocol
    clusters = len({p.cluster for p in pairs(t, pr.primary)})
    if pr.n_clusters is None:
        return f"the primary comparison has {clusters} clusters; N is not fixed yet (run the " \
               "blinded pilot)"
    if clusters < pr.n_clusters:
        return f"the primary comparison has {clusters} clusters; N is {pr.n_clusters}"
    return None


def growth_report(t: Table, *, unblind: bool = False) -> dict[str, object]:
    """The growth readout of every arm against the reference arm, on every family, at each of
    `STAKES`. Before N the primary comparison's two arms are withheld on its family, named under
    `withheld` with the reason, unless the caller unblinds on purpose."""
    pr = t.protocol
    reason = None if unblind else _blind(t)
    readouts: list[dict[str, object]] = []
    withheld: list[dict[str, object]] = []
    for family in pr.families if pr.reference is not None else ():
        for arm in pr.arms:
            if arm == pr.reference:
                continue
            if reason is not None and family == pr.primary.family \
                    and arm in (pr.primary.arm, pr.primary.baseline):
                withheld.append({"arm": arm, "family": family})
                continue
            for stake in STAKES:
                g = growth(t, family, arm, stake=stake)
                if g is not None:
                    readouts.append(g.body())
    return {"protocol": pr.name, "reference": pr.reference, "target": pr.growth_target,
            "stakes": list(STAKES), "readouts": readouts, "withheld": withheld,
            "blinded": reason}


# -- the report ---------------------------------------------------------------------------------

def _interval(t: Table, ps: Sequence[Pair]) -> Interval:
    pr = t.protocol
    return cluster_bootstrap(ps, resamples=pr.bootstrap, seed=pr.seed, alpha=pr.alpha)


def _interval_dict(i: Interval) -> dict[str, object]:
    return {"pairs": i.n_pairs, "clusters": i.n_clusters, "mean": i.mean, "lo": i.lo,
            "hi": i.hi, "p_value": i.p_value}


def _verdict(i: Interval, delta: float) -> str:
    if math.isnan(i.lo):
        return "inconclusive (fewer than two clusters)"
    if i.lo > 0:
        return "the arm improves on the baseline"
    if i.hi < delta:
        return "no useful improvement (the interval lies below delta)"
    return "inconclusive"


def report(t: Table, *, unblind: bool = False) -> dict[str, object]:
    """Everything G5 asks for. Refuses (`Blinded`) before N unless `unblind`."""
    pr = t.protocol
    primary_pairs = pairs(t, pr.primary)
    reason = None if unblind else _blind(t)
    if reason is not None:
        raise Blinded(reason)
    out: dict[str, object] = {
        "protocol": pr.name,
        "counts": {"scored": len(t.scored), "late": t.late, "open": t.open, "voided": t.voided},
    }
    arms: list[dict[str, object]] = []
    for family in pr.families:
        for arm in pr.arms:
            s = summarize(t, arm, family)
            if s is not None:
                arms.append({
                    "arm": s.arm, "family": s.family, "n": s.n, "clusters": s.clusters,
                    "brier": s.brier, "log": s.log,
                    "reliability": s.murphy.reliability, "resolution": s.murphy.resolution,
                    "uncertainty": s.murphy.uncertainty, "residual": s.murphy.residual,
                })
    out["arms"] = arms
    if primary_pairs:
        i = _interval(t, primary_pairs)
        out["primary"] = {"comparison": pr.primary.body(), **_interval_dict(i),
                          "verdict": _verdict(i, pr.delta)}
    secondary: list[dict[str, object]] = []
    readable = [(c, _interval(t, ps)) for c in pr.secondary if (ps := pairs(t, c))]
    adjusted = holm([i.p_value if not math.isnan(i.p_value) else 1.0 for _, i in readable])
    for (c, i), p_holm in zip(readable, adjusted, strict=True):
        secondary.append({"comparison": c.body(), **_interval_dict(i), "p_holm": p_holm})
    out["secondary"] = secondary
    controls: dict[str, object] = {"null_exact": null_check(t)}
    edge = known_edge(primary_pairs, pr.delta)
    edge_interval = _interval(t, edge) if edge else None
    controls["known_edge"] = _interval_dict(edge_interval) if edge_interval else None
    # F-3: a null from the primary comparison means something only when this holds.
    controls["powered"] = edge_interval is not None and edge_interval.lo > 0
    oracle = (oracle_pairs(t, pr.primary.family, pr.reference)
              if pr.reference is not None else [])
    controls["oracle"] = _interval_dict(_interval(t, oracle)) if oracle else None
    out["controls"] = controls
    out["growth"] = growth_report(t, unblind=True)
    return out
