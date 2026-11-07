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
- **Read once, at N.** Once the protocol fixes `n_clusters`, `report` scores the first N clusters
  of the primary comparison, ordered by when each cluster's first pair entered the ledger (the
  ledger's own line order, never a date a caller supplies), in every table it prints: arms,
  primary, secondary and controls. The order is over all the comparison's clusters, resolved or
  not, so a late resolution or void never moves the cut, and the report is read only when every
  question of those N clusters is resolved or voided (`Blinded` otherwise). Waiting past N and
  stopping when the result looks good reads the same N clusters as stopping at N; the clusters
  beyond N are counted in `beyond_n`, not scored.
- **The method** is the protocol's. `percentile` (the default) is the cluster bootstrap above;
  `signflip` is the cluster-level sign-flip randomization test of the pair-weighted mean, with its
  interval made by inverting the test, and the same decision rule on that interval. The protocol's
  `bootstrap` is the number of sign vectors, and all of them are enumerated when there are no more
  than that. Both read the protocol's `alpha`, as `pilot` and `required_clusters` do.
- **Blinding.** `pilot` reports the spread of the primary comparison's cluster means and the
  number of clusters it implies, never a mean. `report` refuses the comparisons until the
  protocol's `n_clusters` is fixed and reached, unless the caller unblinds on purpose.
- **The growth readout** (`growth`, dn-prediction-ledger G8): per arm against the reference arm,
  the growth of a proportional stake over the scored pairs, a thought experiment the scorer
  computes and nothing that stakes anything. By GRW-1 (`formal/Palace/Growth.lean`) its log is
  the cumulative log-score advantage of the arm over the reference, so it reads the ledger's own
  log scores as a holding; the path is kept in log space, and a growth outside the float range
  is reported as its log. Until the comparisons are readable the primary comparison's arms are
  withheld, as `report` withholds the mean, and once N is fixed it reads the first N clusters,
  as `report` does.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
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
    seq: int = 0                      # the line that recorded it: the ledger's own clock


@dataclass(frozen=True)
class Table:
    protocol: Protocol
    scored: tuple[Scored, ...]
    late: int
    open: int
    voided: int
    # The clusters of the primary comparison in the order their first pair entered the ledger
    # (resolved or not, voided or not), and those among them with a question not yet resolved or
    # voided. The cut at N is made on `order`, so a later resolution cannot move it.
    order: tuple[str, ...] = ()
    unsettled: frozenset[str] = frozenset()


def table(entries: Sequence[Entry]) -> Table:
    """The scoreable predictions of a verified chain. The protocol in force is the last one."""
    state = replay(list(entries))
    if state.protocol is None:
        raise LedgerError("the ledger has no protocol")
    scored: list[Scored] = []
    late = open_ = voided = 0
    primary = state.protocol.primary
    # (qid, round) -> arm -> the line that recorded it
    arm_seq: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for entry in entries:
        if entry.kind != "prediction":
            continue
        p = Prediction.parse(entry.body)
        if p.arm in (primary.baseline, primary.arm):
            arm_seq[(p.qid, p.round)][p.arm] = entry.seq
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
                             resolution.resolved_at, entry.seq))
    first: dict[str, int] = {}
    for (qid, _round), seen in arm_seq.items():
        q = state.questions[qid]
        if q.family == primary.family and len(seen) == 2:
            first[q.cluster] = min(max(seen.values()), first.get(q.cluster, max(seen.values())))
    order = tuple(sorted(first, key=lambda c: first[c]))
    unsettled = frozenset(
        q.cluster for q in state.questions.values()
        if q.cluster in first and q.family == primary.family
        and q.qid not in state.resolutions and q.qid not in state.voids)
    return Table(state.protocol, tuple(scored), late, open_, voided, order, unsettled)


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
    seq: int = 0                      # when the pair entered: its later prediction's line


def pairs(t: Table, c: Comparison) -> list[Pair]:
    """The (question, round) pairs both arms predicted, `d = Brier(baseline) - Brier(arm)`."""
    base = {(s.qid, s.round): s for s in t.scored if s.arm == c.baseline and s.family == c.family}
    arm = {(s.qid, s.round): s for s in t.scored if s.arm == c.arm and s.family == c.family}
    out: list[Pair] = []
    for key in sorted(base.keys() & arm.keys()):
        b, a = base[key], arm[key]
        out.append(Pair(b.qid, b.round, b.cluster, brier(b.p, b.outcome) - brier(a.p, a.outcome),
                        max(b.seq, a.seq)))
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


_BISECT = 50


_KEEP = 4_000_000          # sign entries kept in memory between p-values; above it they stream


def _flip_rows(k: int, flips: int) -> tuple[int, bool]:
    """How many sign vectors the test averages over, and whether that is all 2^k of them."""
    exact = 2 ** k <= flips
    return (2 ** k if exact else flips), exact


def _flip_blocks(k: int, flips: int, seed: int) -> Iterator[npt.NDArray[np.float64]]:
    """The sign vectors in blocks of at most `_CHUNK` rows, never all at once: all 2^k of them
    when that is at most `flips` (the exact test), otherwise `flips` random ones from the seed.
    The blocks are the same whatever their size, so memory is `_CHUNK * k`, not `flips * k`."""
    rows, exact = _flip_rows(k, flips)
    rng = None if exact else np.random.default_rng(seed)
    for start in range(0, rows, _CHUNK):
        stop = min(start + _CHUNK, rows)
        if rng is None:
            bits = (np.arange(start, stop)[:, None] >> np.arange(k)) & 1
            yield (bits * 2 - 1).astype(np.float64)
        else:
            yield (rng.integers(0, 2, size=(stop - start, k)) * 2 - 1).astype(np.float64)


def _flip_p(blocks: Iterable[npt.NDArray[np.float64]], rows: int, exact: bool,
            v: npt.NDArray[np.float64]) -> float:
    """Two-sided p-value of `sum(v)` against the sum of `v` with its signs flipped: the share of
    sign vectors whose |sum| reaches the observed one. Add-one when the flips are a sample."""
    obs = abs(float(v.sum()))
    floor = obs - 1e-12 * float(np.abs(v).sum())
    reach = sum(int(np.count_nonzero(np.abs(block @ v) >= floor)) for block in blocks)
    return reach / rows if exact else (1 + reach) / (rows + 1)


def cluster_signflip(ps: Sequence[Pair], *, flips: int, seed: int, alpha: float) -> Interval:
    """The cluster-level sign-flip randomization test of the pair-weighted mean of `d`.

    With cluster sums S_c and pair counts n_c the statistic is `sum(S_c) / sum(n_c)`, the same
    pair-weighted mean the bootstrap reports (a cluster counts as many times as it has pairs).
    The denominator is fixed, so a flip of cluster c's sign changes only `S_c`. The test is exact
    under the null that the two arms are exchangeable within each cluster (flipping a cluster's
    sign is swapping the arms in it) and the clusters are independent: it needs no resampling
    approximation, and with at most `flips` sign vectors it enumerates all of them. It does not
    protect against dependence across clusters, which makes the effective N smaller than the
    cluster count.

    The reported p-value tests mean = 0. The interval inverts the test: the set of mu0 at which
    flipping the signs of `S_c - mu0 * n_c` does not reject at `alpha`. With the sign vectors held
    fixed, p(mu0) is nonincreasing as mu0 moves away from the estimate on either side: the
    observed |sum(S - mu0 n)| grows at slope sum(n) while a flipped sum changes at slope at most
    |eps . n| <= sum(n), so each sign vector's reach indicator can only switch off. That makes the
    set an interval around the estimate, found by bisection on each side. Inverting the test
    shifts every pair's `d` by mu0, so the interval assumes a location shift: that the arms'
    difference moves the whole distribution by a constant. The test of mean = 0 alone does not
    need that. The sign vectors are made in blocks of `_CHUNK` rows (kept between p-values when
    they are few, regenerated from the seed when many), so memory does not grow with the flip
    count. With too few clusters to ever reject at `alpha` (the smallest attainable p-value,
    2 / 2^k, exceeds it) the interval is unbounded."""
    if not ps:
        raise ValueError("no pairs to compare")
    sums, counts = _cluster_sums(ps)
    k = len(sums)
    mean = float(sums.sum() / counts.sum())
    if k < 2:
        return Interval(len(ps), k, mean, math.nan, math.nan, math.nan)
    rows, exact = _flip_rows(k, flips)
    kept = list(_flip_blocks(k, flips, seed)) if rows * k <= _KEEP else None

    def p_at(mu0: float) -> float:
        blocks = kept if kept is not None else _flip_blocks(k, flips, seed)
        return _flip_p(blocks, rows, exact, sums - mu0 * counts)

    def edge(direction: float) -> float:
        step = max(1e-3, float(np.abs(sums / counts).max()))
        inside, outside = mean, mean + direction * step
        for _ in range(60):
            if p_at(outside) <= alpha:
                break
            inside = outside
            step *= 2.0
            outside = mean + direction * step
        else:
            return direction * math.inf
        for _ in range(_BISECT):
            mid = (inside + outside) / 2.0
            if p_at(mid) > alpha:
                inside = mid
            else:
                outside = mid
        return inside

    return Interval(len(ps), k, mean, edge(-1.0), edge(1.0), p_at(0.0))


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
    is 0 (GRW-5). The readout never multiplies factors: it sums their logs (`log_factor`)."""
    p, r = _clip(p, clip), _clip(r, clip)
    return p / r if outcome == 1 else (1.0 - p) / (1.0 - r)


def log_factor(p: float, r: float, outcome: int, clip: float, *, stake: float = 1.0) -> float:
    """**GRW-1** The log of the stake's factor `1 + stake * (F - 1)` on one pair. At the full
    stake it is the arm's log-score advantage over the reference, the difference of the two
    clipped log scores the ledger reads, so the log growth is their sum. Below the full stake it
    is `log1p(stake * (F - 1))`, with `F - 1 = (L(p) - L(r)) / L(r)` taken from the clipped
    probabilities, never a product: it stays below `1 / clip`, and log1p keeps a small edge's
    digits."""
    if not 0 < stake <= 1:
        raise ValueError("the stake must lie in (0, 1]: GRW-5 holds there and nowhere beyond")
    if stake == 1.0:
        return log_loss(r, outcome, clip) - log_loss(p, outcome, clip)
    p, r = _clip(p, clip), _clip(r, clip)
    lp, lr = (p, r) if outcome == 1 else (1.0 - p, 1.0 - r)
    return math.log1p(stake * (lp - lr) / lr)


def _from_log(x: float) -> tuple[float, bool]:
    """`(exp(x), False)` when that is a normal float, else `(x, True)`: a growth outside the
    float range is held as its log."""
    try:
        value = math.exp(x)
    except OverflowError:
        return x, True
    return (value, False) if value >= sys.float_info.min else (x, True)


@dataclass(frozen=True)
class Growth:
    """**GRW-1** One arm's growth against the reference arm on one family, at one stake.

    The thought experiment: a holding of 1 that, on each scored pair in the order the outcomes
    became known, is multiplied by `1 + stake * (F - 1)` for the proportional stake's factor `F`
    (`factor`). The path is computed in log space (`growth_path`) from the log factors
    (`log_factor`), so no run of factors overflows or underflows. At `stake` 1 they are the
    differences of the ledger's clipped log scores, so `log_growth` is `log_advantage`, the
    cumulative log-score advantage of the arm over the reference, exactly (GRW-1): the readout
    is the ledger's own log scores, read as a holding. `growth` is `exp(log_growth)` when that is
    a normal float; otherwise it holds `log_growth` itself, and `growth_is_log` says so. GRW-1
    holds for the stake 1 only; the fractional stakes (0.5, 0.25) are the cautious practice and
    are read on their own terms. `geometric_mean` is the per-pair factor, `worst_factor` the
    smallest single factor, `drawdown` the largest fall of the holding from its running peak, as
    a fraction of the peak, and `to_target` the number of further pairs, at the realized mean log
    growth per pair, before the holding reaches `target` times its start: 0 when it already has,
    None when the mean is not positive. Nothing here stakes anything."""

    arm: str
    family: str
    reference: str
    stake: float
    n: int
    growth: float
    growth_is_log: bool
    log_growth: float
    log_advantage: float
    geometric_mean: float
    worst_factor: float
    drawdown: float
    target: float
    to_target: int | None

    def body(self) -> dict[str, object]:
        return {"arm": self.arm, "family": self.family, "reference": self.reference,
                "stake": self.stake, "pairs": self.n, "growth": self.growth,
                "growth_is_log": self.growth_is_log, "log_growth": self.log_growth,
                "log_advantage": self.log_advantage, "geometric_mean": self.geometric_mean,
                "worst_factor": self.worst_factor, "drawdown": self.drawdown,
                "target": self.target, "to_target": self.to_target}


@dataclass(frozen=True)
class GrowthPath:
    """A holding's path over a sequence of log factors (`growth_path`)."""

    log_growth: float
    growth: float
    growth_is_log: bool
    geometric_mean: float
    worst_factor: float
    drawdown: float
    to_target: int | None


def growth_path(log_factors: Sequence[float], *, target: float) -> GrowthPath:
    """The path of a holding of 1 whose log moves by each log factor in turn, kept in log space
    so that no run of factors overflows or underflows. The log growth is the sum, correctly
    rounded (`math.fsum`), at the full stake the cumulative log-score advantage (GRW-1); the
    growth is its exponential when that is a normal float, else the log itself with
    `growth_is_log`; the geometric mean and the worst factor are the exponentials of the mean and
    the least log factor; the drawdown is the largest fall of the log path below its running
    maximum, reported as `1 - exp(-fall)`; and the further pairs to `target` are `log target` less
    the log growth over the realized mean log factor."""
    if not log_factors:
        raise ValueError("no factors to compound")
    running = peak = fall = 0.0
    for x in log_factors:
        running += x
        peak = max(peak, running)
        fall = max(fall, peak - running)
    log_growth = math.fsum(log_factors)
    mean = log_growth / len(log_factors)
    if log_growth >= math.log(target):
        to_target: int | None = 0
    elif mean > 0:
        to_target = math.ceil((math.log(target) - log_growth) / mean)
    else:
        to_target = None
    value, is_log = _from_log(log_growth)
    return GrowthPath(log_growth, value, is_log, math.exp(mean), math.exp(min(log_factors)),
                      -math.expm1(-fall), to_target)


def growth(t: Table, family: str, arm: str, *, stake: float = 1.0) -> Growth | None:
    """**GRW-1** `arm`'s growth against the protocol's reference arm on `family` at `stake`, over
    the (question, round) pairs both predicted, in the order their outcomes became known; None
    without a reference arm or without pairs. At the full stake the log factors are the pairs'
    log-score advantages themselves, so the log growth is their sum, `log_advantage`, both
    correctly rounded."""
    pr = t.protocol
    if pr.reference is None:
        return None
    base = {(s.qid, s.round): s for s in t.scored if s.arm == pr.reference and s.family == family}
    own = {(s.qid, s.round): s for s in t.scored if s.arm == arm and s.family == family}
    keys = sorted(base.keys() & own.keys(), key=lambda k: (base[k].resolved_at, k))
    if not keys:
        return None
    advantages = [log_factor(own[k].p, base[k].p, base[k].outcome, pr.log_clip) for k in keys]
    logs = advantages if stake == 1.0 else [
        log_factor(own[k].p, base[k].p, base[k].outcome, pr.log_clip, stake=stake) for k in keys]
    path = growth_path(logs, target=pr.growth_target)
    return Growth(arm, family, pr.reference, stake, len(keys), path.growth, path.growth_is_log,
                  path.log_growth, math.fsum(advantages), path.geometric_mean, path.worst_factor,
                  path.drawdown, pr.growth_target, path.to_target)


def _blind(t: Table) -> str | None:
    """Why the comparisons are not readable yet, or None once they are: N is fixed, the primary
    comparison has that many clusters (counted in the ledger's order, resolved or not), and every
    question of the first N is resolved or voided. `report` refuses with this reason, and
    `growth_report` withholds the primary comparison's arms with it."""
    pr = t.protocol
    clusters = len(t.order)
    if pr.n_clusters is None or clusters < pr.n_clusters:
        need = ("not fixed yet (run the blinded pilot)" if pr.n_clusters is None
                else str(pr.n_clusters))
        return f"the primary comparison has {clusters} clusters; N is {need}"
    open_ = sorted(c for c in t.order[:pr.n_clusters] if c in t.unsettled)
    if open_:
        return (f"{len(open_)} of the first {pr.n_clusters} clusters still have a question "
                f"neither resolved nor voided (first: {open_[0]})")
    return None


def growth_report(t: Table, *, unblind: bool = False) -> dict[str, object]:
    """The growth readout of every arm against the reference arm, on every family, at each of
    `STAKES`. Until the comparisons are readable (`_blind`) the primary comparison's two arms are
    withheld on its family, named under `withheld` with the reason, unless the caller unblinds on
    purpose. Once N is fixed it reads the first N clusters only, the cut `report` makes
    (`first_n`), and says in `beyond_n` what it left out."""
    pr = t.protocol
    reason = None if unblind else _blind(t)
    beyond = {"clusters": 0, "pairs": 0}
    if pr.n_clusters is not None:
        t, beyond = first_n(t, pr.n_clusters)
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
            "blinded": reason, "beyond_n": beyond}


# -- the report ---------------------------------------------------------------------------------

def _interval(t: Table, ps: Sequence[Pair]) -> Interval:
    pr = t.protocol
    if pr.method == "signflip":
        return cluster_signflip(ps, flips=pr.bootstrap, seed=pr.seed, alpha=pr.alpha)
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


def first_n(t: Table, n: int) -> tuple[Table, dict[str, int]]:
    """The table restricted to the first `n` clusters of the primary comparison, in the order
    their first pair entered the ledger (all clusters, resolved or not), and what was left out as
    beyond N. A table with `n` or fewer clusters comes back whole. Rows of a cluster that never
    formed a primary pair, when there are clusters beyond N, are left out too: they have no place
    in the order."""
    if len(t.order) <= n:
        return t, {"clusters": 0, "pairs": 0}
    keep = set(t.order[:n])
    kept = tuple(s for s in t.scored if s.cluster in keep)
    beyond = sum(1 for p in pairs(t, t.protocol.primary) if p.cluster not in keep)
    return replace(t, scored=kept), {"clusters": len(t.order) - n, "pairs": beyond}


def report(t: Table, *, unblind: bool = False) -> dict[str, object]:
    """Everything G5 asks for. Refuses (`Blinded`) before N unless `unblind`; reads the first N
    clusters only, however many the ledger holds."""
    pr = t.protocol
    reason = None if unblind else _blind(t)
    if reason is not None:
        raise Blinded(reason)
    readout = growth_report(t, unblind=True)
    beyond = {"clusters": 0, "pairs": 0}
    if pr.n_clusters is not None:
        t, beyond = first_n(t, pr.n_clusters)
    primary_pairs = pairs(t, pr.primary)
    out: dict[str, object] = {
        "protocol": pr.name,
        "counts": {"scored": len(t.scored), "late": t.late, "open": t.open, "voided": t.voided},
        "beyond_n": beyond,
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
    out["growth"] = readout
    return out
