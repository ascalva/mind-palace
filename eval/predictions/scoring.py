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
  primary, secondary and controls. Waiting past N and stopping when the result looks good reads
  the same N clusters as stopping at N; the clusters beyond N are counted in `beyond_n`, not scored.
- **The method** is the protocol's. `percentile` (the default) is the cluster bootstrap above;
  `signflip` is the cluster-level sign-flip randomization test of the pair-weighted mean, with its
  interval made by inverting the test, and the same decision rule on that interval. The protocol's
  `bootstrap` is the number of sign vectors, and all of them are enumerated when there are no more
  than that. Both read the protocol's `alpha`, as `pilot` and `required_clusters` do.
- **Blinding.** `pilot` reports the spread of the primary comparison's cluster means and the
  number of clusters it implies, never a mean. `report` refuses the comparisons until the
  protocol's `n_clusters` is fixed and reached, unless the caller unblinds on purpose.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, replace
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
    seq: int = 0                      # the line that recorded it: the ledger's own clock


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
                            entry.seq))
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


def _flip_signs(k: int, flips: int, seed: int) -> tuple[npt.NDArray[np.float64], bool]:
    """The sign vectors the test averages over: all 2^k of them when that is at most `flips`
    (the exact test), otherwise `flips` random ones from the seed. Returns (signs, exact)."""
    if 2 ** k <= flips:
        bits = (np.arange(2 ** k)[:, None] >> np.arange(k)) & 1
        return (bits * 2 - 1).astype(np.float64), True
    rng = np.random.default_rng(seed)
    return (rng.integers(0, 2, size=(flips, k)) * 2 - 1).astype(np.float64), False


def _flip_p(signs: npt.NDArray[np.float64], exact: bool, v: npt.NDArray[np.float64]) -> float:
    """Two-sided p-value of `sum(v)` against the sum of `v` with its signs flipped: the share of
    sign vectors whose |sum| reaches the observed one. Add-one when the flips are a sample."""
    obs = abs(float(v.sum()))
    reach = int(np.count_nonzero(np.abs(signs @ v) >= obs - 1e-12 * float(np.abs(v).sum())))
    return reach / len(signs) if exact else (1 + reach) / (len(signs) + 1)


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
    set an interval around the estimate, found by bisection on each side. With too few clusters
    to ever reject at `alpha` (the smallest attainable p-value, 2 / 2^k, exceeds it) the
    interval is unbounded."""
    if not ps:
        raise ValueError("no pairs to compare")
    sums, counts = _cluster_sums(ps)
    k = len(sums)
    mean = float(sums.sum() / counts.sum())
    if k < 2:
        return Interval(len(ps), k, mean, math.nan, math.nan, math.nan)
    signs, exact = _flip_signs(k, flips, seed)

    def p_at(mu0: float) -> float:
        return _flip_p(signs, exact, sums - mu0 * counts)

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
    their first pair entered the ledger, and what was left out as beyond N. A table with `n` or
    fewer clusters comes back whole. Rows of a cluster that never formed a primary pair, when
    there are clusters beyond N, are left out too: they have no place in the order."""
    first: dict[str, int] = {}
    for p in pairs(t, t.protocol.primary):
        first[p.cluster] = min(p.seq, first.get(p.cluster, p.seq))
    if len(first) <= n:
        return t, {"clusters": 0, "pairs": 0}
    keep = set(sorted(first, key=lambda c: first[c])[:n])
    kept = tuple(s for s in t.scored if s.cluster in keep)
    cut = {s.cluster for s in t.scored if s.cluster not in keep}
    beyond = sum(1 for p in pairs(t, t.protocol.primary) if p.cluster not in keep)
    return replace(t, scored=kept), {"clusters": len(cut), "pairs": beyond}


def report(t: Table, *, unblind: bool = False) -> dict[str, object]:
    """Everything G5 asks for. Refuses (`Blinded`) before N unless `unblind`; reads the first N
    clusters only, however many the ledger holds."""
    pr = t.protocol
    clusters = len({p.cluster for p in pairs(t, pr.primary)})
    if not unblind and (pr.n_clusters is None or clusters < pr.n_clusters):
        need = ("not fixed yet (run the blinded pilot)" if pr.n_clusters is None
                else str(pr.n_clusters))
        raise Blinded(f"the primary comparison has {clusters} clusters; N is {need}")
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
    return out
