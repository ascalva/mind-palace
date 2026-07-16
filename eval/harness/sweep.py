"""The deterministic, model-free grid optimizer (E3a-1b, bp-049).

A declarative sweep spec (§2.6) names ONE registered lever, a grid over its `[lo, hi]`, the
pipelines the runner produces per cell, the objective metric, and `mode = "propose"`. The engine:

  1. **drives** the BUILT `ShadowRunner` once per (grid value × seed) over ONE shared eval store +
     ONE shared run ledger (never reopened per cell — risk (a)), building a modified `Config`
     generically with `dataclasses.replace` (§3 Q1). Each cell's Readings land keyed by the
     runner's own `config_fingerprint` (bp-046 makes it move with the swept value), so a re-run
     dedups for free (§3 Q2 — the engine never re-keys or caches).
  2. **optimizes**: `query`s the eval store for the objective across cells, joins each reading's
     `config_fingerprint` back to its grid value (via the drive-phase map — you cannot read a value
     out of a sha256), builds the per-lever curve aggregated across seeds WITH an interval, filters
     by ADMISSIBILITY (a cell whose stored `golden_recall` regressed below baseline is inadmissible
     — guardrails LEXICOGRAPHICALLY PRIOR, applied BEFORE the argmax), selects a value (§8: widest
     near-optimal plateau center, least-motion tie-break), and emits a `ProposedChange` into the §14
     ledger via `SelfModLoop.propose` — PROPOSED only; the owner blesses the apply.

Model-free by construction: it reads scalar Readings from a DuckDB store and does arithmetic. No
model import, no LLM call; the one model in `dream_v2` (step 8) is never reached — `ShadowRunner`
runs the pipeline STEPS, not the method (§3 Q6). Honors `[selfmod] enabled` — when off, it records
the selection and logs, never forcing the switch (§3 Q5, §11).
"""

from __future__ import annotations

import hashlib
import logging
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean
from typing import TYPE_CHECKING

from eval.harness import registry
from eval.harness.store import EvalKey, EvalResultsStore, Reading
from ops.levers import Lever, ProposedChange, get_lever

if TYPE_CHECKING:
    from config.loader import Config
    from core.complex.temporal import SnapshotStore
    from core.mirror import RowSource
    from core.stores.runledger import RunLedger
    from eval.drift import DriftConfig
    from eval.golden import GoldenQuery, Retriever
    from ops.selfmod import SelfModLoop

_log = logging.getLogger(__name__)

# Metrics that are BETTER SMALLER (§8: the argmax runs in the metric's declared direction). Recall
# and structural quality maximize; the drift gauge minimizes. A spec `direction` overrides this.
_MINIMIZE: frozenset[str] = frozenset({"drift_D"})

# The guardrail the admissibility filter reads per cell (§2.5 always-on; drift_D advisory until Θ).
_GOLDEN_RECALL = "golden_recall"


class SweepSpecError(ValueError):
    """A malformed / disallowed sweep spec. `mode = "auto"` raises this with the 'E3b' banner —
    the autonomy this engine deliberately does NOT build (§9)."""


class ObjectiveNotProducedError(RuntimeError):
    """The objective is registered but NO cell produced it in the store (§10). Refuse to select over
    an empty curve; the objective must be wired into the per-cell run first."""


# --------------------------------------------------------------------------------------------------
# The spec
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SweepSpec:
    """A validated sweep spec (§2.6). `mode` is always `"propose"` (the parser rejects `"auto"`)."""

    name: str
    lever: Lever
    grid_source: str  # "full" | "list"
    resolution: int
    explicit_values: tuple[float, ...] | None
    pipelines: tuple[str, ...]
    corpus: str
    seeds: int
    metrics: tuple[str, ...]
    objective: str
    direction: str  # "maximize" | "minimize"
    epsilon: float
    select_pipeline: str
    guardrails: tuple[str, ...]
    mode: str = "propose"

    def grid(self) -> list[float | int]:
        """The validated grid points for the swept lever, coerced to the lever kind. Each point is
        `lever.validate`-d — an out-of-bounds explicit value raises HERE, before any run (§7)."""
        if self.grid_source == "list":
            assert self.explicit_values is not None
            raw: list[float] = list(self.explicit_values)
        else:  # "full" — [lo, hi] at `resolution` points
            raw = _linspace(self.lever.lo, self.lever.hi, self.resolution)
        out: list[float | int] = []
        seen: set[float | int] = set()
        for v in raw:
            coerced = self.lever.validate(v)  # coerce + hard-bounds check (fail-closed)
            if coerced not in seen:
                seen.add(coerced)
                out.append(coerced)
        return out


def _linspace(lo: float, hi: float, n: int) -> list[float]:
    if n <= 1:
        return [lo]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _default_direction(metric: str) -> str:
    return "minimize" if metric in _MINIMIZE else "maximize"


def parse_spec_text(text: str) -> SweepSpec:
    """Parse a `[sweep.<name>]` TOML body into a validated `SweepSpec` (fail-closed)."""
    raw = tomllib.loads(text)
    sweep = raw.get("sweep")
    if not isinstance(sweep, dict) or len(sweep) != 1:
        raise SweepSpecError("a sweep spec must contain exactly one [sweep.<name>] table")
    name, body = next(iter(sweep.items()))
    if not isinstance(body, dict):
        raise SweepSpecError(f"[sweep.{name}] must be a table")

    # mode — E3b: `auto` is the autonomy this engine refuses to build (§9).
    mode = str(body.get("mode", "propose"))
    if mode == "auto":
        raise SweepSpecError(
            "E3b: mode = \"auto\" is not supported by the sweep engine — it PROPOSES only; the "
            "owner blesses the apply. Set mode = \"propose\"."
        )
    if mode != "propose":
        raise SweepSpecError(f"E3b: unknown mode {mode!r}; only \"propose\" is supported")

    # lever — exactly one, resolved fail-closed against the registry.
    levers = body.get("levers")
    if not isinstance(levers, dict) or len(levers) != 1:
        raise SweepSpecError(
            "levers must be a table with exactly one { lever_name = <grid> } entry"
        )
    lever_name, grid_spec = next(iter(levers.items()))
    lever = get_lever(str(lever_name))  # raises on an unknown lever

    if isinstance(grid_spec, str):
        if grid_spec != "full":
            raise SweepSpecError(f"lever grid string must be \"full\", got {grid_spec!r}")
        grid_source, explicit_values = "full", None
    elif isinstance(grid_spec, list):
        grid_source = "list"
        explicit_values = tuple(float(x) for x in grid_spec)
    else:
        raise SweepSpecError("a lever grid must be \"full\" or an explicit list of values")

    objective = str(body.get("objective", ""))
    if not registry.is_registered(objective):
        raise SweepSpecError(
            f"objective {objective!r} is not a registered metric (§2.5) — sweeps may reference "
            f"only registered metrics; register it in eval/harness/registry.py first"
        )

    pipelines = tuple(str(p) for p in body.get("pipelines", []))
    if not pipelines:
        raise SweepSpecError("pipelines must list at least one pipeline")
    # select_pipeline (finding-0089): which lane the optimizer selects on. Default = the LAST
    # pipeline (the dream_v2 lane the σ lever drives). Never silent — recorded in the result.
    select_pipeline = str(body.get("select_pipeline", pipelines[-1]))
    if select_pipeline not in pipelines:
        raise SweepSpecError(
            f"select_pipeline {select_pipeline!r} is not one of pipelines {list(pipelines)}"
        )

    seeds = int(body.get("seeds", 1))
    if seeds < 1:
        raise SweepSpecError("seeds must be >= 1")

    return SweepSpec(
        name=str(name),
        lever=lever,
        grid_source=grid_source,
        resolution=int(body.get("resolution", 0)),
        explicit_values=explicit_values,
        pipelines=pipelines,
        corpus=str(body.get("corpus", "")),
        seeds=seeds,
        metrics=tuple(str(m) for m in body.get("metrics", [])),
        objective=objective,
        direction=str(body.get("direction", _default_direction(objective))),
        epsilon=float(body.get("epsilon", 0.0)),
        select_pipeline=select_pipeline,
        guardrails=tuple(str(g) for g in body.get("guardrails", [])),
        mode=mode,
    )


def parse_spec(path: Path | str) -> SweepSpec:
    return parse_spec_text(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------------
# The curve + the selection instrument (§8)
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CurvePoint:
    """One aggregated cell of the objective curve: a grid value, its seed-mean, the seed-interval
    half-width, admissibility (guardrails lexicographically prior), and its position in the full
    grid (adjacency is grid-adjacency, not list-adjacency — a removed cell breaks a plateau)."""

    value: float | int
    mean: float
    halfwidth: float
    admissible: bool
    grid_index: int
    n_seeds: int


def _argbest(points: Sequence[CurvePoint], direction: str) -> list[CurvePoint]:
    best = (min if direction == "minimize" else max)(p.mean for p in points)
    return [p for p in points if abs(p.mean - best) <= 1e-12]


def _tiebreak_nearest(values: Sequence[float | int], current: float) -> float | int:
    """Least motion from `current`; the value itself is the deterministic secondary key."""
    return min(values, key=lambda v: (abs(float(v) - current), float(v)))


def _run_center(run: Sequence[CurvePoint]) -> float | int:
    """A plateau's CENTER = its median grid point. `run[len//2]` is the exact middle for an odd run
    (the shape the falsifier test uses) and the upper-middle for an even run — deterministic."""
    return run[len(run) // 2].value


def select(
    points: Sequence[CurvePoint],
    *,
    current: float,
    epsilon: float,
    direction: str,
    grid_size: int,
) -> float | int | None:
    """§8 — return the robustly near-optimal lever value, or None if nothing is admissible.

    Guardrails are lexicographically prior: inadmissible points are dropped BEFORE `M` is computed,
    so an inadmissible cell can never win even if it holds the objective extremum. `M` is the best
    seed-mean in the metric's declared `direction`; the near-optimal set `P` is every admissible
    point within `epsilon` of `M`. `P` is partitioned into maximal runs of grid-ADJACENT points;
    the LONGEST run's center wins, tie-broken toward the current value. THE CARDINAL FALSIFIER: this
    must never return a knife-edge singleton max when a strictly wider near-optimal plateau exists.
    """
    admissible = [p for p in points if p.admissible]
    if not admissible:
        return None

    # A sparse grid has no meaningful notion of "adjacent" (§8 validity) — degenerate to argmax.
    if grid_size <= 3:
        return _tiebreak_nearest([p.value for p in _argbest(admissible, direction)], current)

    if direction == "minimize":
        m = min(p.mean for p in admissible)
        near = [p for p in admissible if p.mean <= m + epsilon]
    else:
        m = max(p.mean for p in admissible)
        near = [p for p in admissible if p.mean >= m - epsilon]

    # Maximal runs of grid-adjacent near-optimal points (consecutive grid_index).
    near_sorted = sorted(near, key=lambda p: p.grid_index)
    runs: list[list[CurvePoint]] = []
    cur: list[CurvePoint] = []
    for p in near_sorted:
        if cur and p.grid_index == cur[-1].grid_index + 1:
            cur.append(p)
        else:
            if cur:
                runs.append(cur)
            cur = [p]
    if cur:
        runs.append(cur)

    longest = max(len(r) for r in runs)
    centers = [_run_center(r) for r in runs if len(r) == longest]
    return _tiebreak_nearest(centers, current)


# --------------------------------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DriveResult:
    """What the drive phase recorded: the grid, and the map from each cell's `config_fingerprint`
    back to its grid value (you cannot read a value out of a sha256 — §3 Q2)."""

    grid: tuple[float | int, ...]
    fp_to_value: dict[str, float | int]


@dataclass(frozen=True)
class SweepResult:
    """The optimizer's verdict. `proposal_id` is set only when `[selfmod] enabled` and a value was
    selected on a guardrail-captured curve; otherwise `None` with a note explaining why."""

    spec_name: str
    lever: str
    grid: tuple[float | int, ...]
    curve: tuple[CurvePoint, ...]
    select_pipeline: str
    current: float
    selected: float | int | None
    epsilon: float
    direction: str
    degenerate_argmax: bool
    guardrails_captured: bool
    proposal_emitted: bool
    proposal_id: int | None
    evidence_keys: tuple[str, ...]
    notes: tuple[str, ...]


def _modify_config(cfg: Config, lever: Lever, value: float | int) -> Config:
    """Build the per-cell modified config GENERICALLY (§3 Q1/§6): frozen dataclasses -> replace."""
    section = getattr(cfg, lever.section)
    return replace(cfg, **{lever.section: replace(section, **{lever.key: lever.coerce(value)})})


def _spec_hash(pipeline: str) -> str:
    """Reconstruct the runner's per-pipeline spec_hash (shadow encodes the pipeline into it) so the
    engine can partition objective readings by pipeline. The prefix is imported from shadow (single
    source); the two-line formula mirrors `ShadowRunner._key`."""
    from core.dreaming.shadow import _SPEC_PREFIX

    return hashlib.sha256(f"{_SPEC_PREFIX}‖{pipeline}".encode()).hexdigest()


def _key_text(k: EvalKey) -> str:
    return f"{k.spec_hash[:8]}/{k.corpus_ref[:8]}/{k.config_fingerprint[:8]}/seed{k.seed}"


@dataclass
class SweepEngine:
    """Drives the grid (Item 13) and optimizes the curve (Item 14) over ONE shared eval store + ONE
    shared run ledger. The seams mirror `ShadowRunner`'s: inject them for tests; `scripts/sweep.py`
    resolves them from config for a real overnight run."""

    spec: SweepSpec
    base_config: Config
    eval_store: EvalResultsStore
    ledger: RunLedger
    store: RowSource | None = None
    retriever: Retriever | None = None
    golden: Sequence[GoldenQuery] | None = None
    baseline: dict[str, float] | None = None
    drift_cfg: DriftConfig | None = None
    snapshots: SnapshotStore | None = None

    def drive(self) -> DriveResult:
        """Item 13 — one shared-store `ShadowRunner.run` per (grid value × seed). No re-keying: the
        store dedups a re-run for free (§3 Q2). The SAME eval store + run ledger are reused across
        every cell (risk (a)); the seed varies the runner (risk (c))."""
        from core.dreaming.shadow import ShadowRunner, _config_fingerprint

        grid = self.spec.grid()  # validates every point BEFORE any run (out-of-bounds raises here)
        fp_to_value: dict[str, float | int] = {}
        for value in grid:
            modified = _modify_config(self.base_config, self.spec.lever, value)
            fp_to_value[_config_fingerprint(modified)] = value
            for seed in range(self.spec.seeds):
                runner = ShadowRunner(
                    ledger=self.ledger,
                    store=self.store,
                    eval_store=self.eval_store,   # ONE shared store — never reopened per cell
                    snapshots=self.snapshots,
                    retriever=self.retriever,
                    golden=self.golden,
                    baseline=self.baseline,
                    drift_cfg=self.drift_cfg,
                    seed=seed,
                )
                runner.run(config=modified)
        return DriveResult(grid=tuple(grid), fp_to_value=fp_to_value)

    def _baseline_recall(self) -> float:
        if self.baseline is not None:
            return float(self.baseline["recall_at_k"])
        from eval.golden import load_baseline

        return float(load_baseline()["recall_at_k"])

    def optimize(
        self, drive: DriveResult, *, selfmod_loop: SelfModLoop | None = None
    ) -> SweepResult:
        """Item 14 — curve → admissibility → selection → §14 proposal (PROPOSED only)."""
        fp_to_value = drive.fp_to_value
        grid = list(drive.grid)
        notes: list[str] = [f"cells={len(grid)}×{self.spec.seeds}seeds (no cap applied)"]

        objective_readings = self.eval_store.query(metric_name=self.spec.objective)
        cells = [r for r in objective_readings if r.key.config_fingerprint in fp_to_value]
        if not cells:
            # §10: registered but produced no readings — refuse to select over an empty curve.
            raise ObjectiveNotProducedError(
                f"objective {self.spec.objective!r} produced no readings for this sweep's cells; "
                f"wire it into the per-cell run first (it is registered but not written per cell)"
            )

        primary_spec = _spec_hash(self.spec.select_pipeline)
        prim = [r for r in cells if r.key.spec_hash == primary_spec]
        if not prim:
            raise ObjectiveNotProducedError(
                f"objective {self.spec.objective!r} produced no readings for select_pipeline "
                f"{self.spec.select_pipeline!r}"
            )

        baseline_recall = self._baseline_recall()
        by_value: dict[float | int, list[Reading]] = {}
        for r in prim:
            by_value.setdefault(fp_to_value[r.key.config_fingerprint], []).append(r)

        curve: list[CurvePoint] = []
        evidence: list[str] = []
        guardrails_captured = True
        for value, seed_readings in by_value.items():
            ys = [r.value for r in seed_readings]
            ybar = mean(ys)
            halfwidth = (max(ys) - min(ys)) / 2 if len(ys) > 1 else 0.0
            captured = True
            recalls: list[float] = []
            for r in seed_readings:
                gr = self.eval_store.get(r.key, _GOLDEN_RECALL)
                if gr is None:
                    captured = False
                    break
                recalls.append(gr.value)
                evidence.append(_key_text(r.key))
            if not captured:
                guardrails_captured = False
                admissible = False
            else:
                # Guardrail: a cell whose golden_recall regressed below baseline is inadmissible.
                admissible = all(rc + 1e-9 >= baseline_recall for rc in recalls)
            curve.append(
                CurvePoint(
                    value=value,
                    mean=ybar,
                    halfwidth=halfwidth,
                    admissible=admissible,
                    grid_index=grid.index(value),
                    n_seeds=len(ys),
                )
            )

        curve.sort(key=lambda p: p.grid_index)
        current = float(getattr(getattr(self.base_config, self.spec.lever.section),
                                self.spec.lever.key))
        # ε ≥ the seed-interval half-width (§8) so plateau membership is not seed noise.
        max_half = max((p.halfwidth for p in curve if p.admissible), default=0.0)
        epsilon = max(self.spec.epsilon, max_half)
        degenerate = len(grid) <= 3

        if not guardrails_captured:
            # §10: guardrails not-captured (no retriever) → an unguarded selection is inadmissible
            # by construction → refuse to emit.
            notes.append("admissibility not-captured (no golden_recall/cell); refusing to emit")
            return SweepResult(
                spec_name=self.spec.name, lever=self.spec.lever.name, grid=tuple(grid),
                curve=tuple(curve), select_pipeline=self.spec.select_pipeline, current=current,
                selected=None, epsilon=epsilon, direction=self.spec.direction,
                degenerate_argmax=degenerate, guardrails_captured=False, proposal_emitted=False,
                proposal_id=None, evidence_keys=tuple(dict.fromkeys(evidence)), notes=tuple(notes),
            )

        selected = select(curve, current=current, epsilon=epsilon,
                          direction=self.spec.direction, grid_size=len(grid))
        if degenerate:
            notes.append("degenerate grid (≤3 points) — selection is argmax, not a plateau center")

        if selected is None:
            notes.append("no admissible cell — no proposal emitted")
            return SweepResult(
                spec_name=self.spec.name, lever=self.spec.lever.name, grid=tuple(grid),
                curve=tuple(curve), select_pipeline=self.spec.select_pipeline, current=current,
                selected=None, epsilon=epsilon, direction=self.spec.direction,
                degenerate_argmax=degenerate, guardrails_captured=True, proposal_emitted=False,
                proposal_id=None, evidence_keys=tuple(dict.fromkeys(evidence)), notes=tuple(notes),
            )

        rationale = self._rationale(curve, selected, current, epsilon, evidence)
        proposal_id: int | None = None
        emitted = False
        loop_enabled = selfmod_loop is not None and selfmod_loop.config.selfmod.enabled
        if loop_enabled:
            assert selfmod_loop is not None
            proposal = selfmod_loop.propose(
                ProposedChange(lever=self.spec.lever.name, target=float(selected),
                               rationale=rationale),
                proposer="sweep-engine",
            )
            proposal_id = proposal.id
            emitted = True
            notes.append(f"emitted PROPOSED proposal #{proposal.id} (owner blesses the apply)")
        else:
            notes.append("proposal not emitted (selfmod disabled)")
            _log.info("sweep %s: proposal not emitted (selfmod disabled); selected=%s",
                      self.spec.name, selected)

        return SweepResult(
            spec_name=self.spec.name, lever=self.spec.lever.name, grid=tuple(grid),
            curve=tuple(curve), select_pipeline=self.spec.select_pipeline, current=current,
            selected=selected, epsilon=epsilon, direction=self.spec.direction,
            degenerate_argmax=degenerate, guardrails_captured=True, proposal_emitted=emitted,
            proposal_id=proposal_id, evidence_keys=tuple(dict.fromkeys(evidence)),
            notes=tuple(notes),
        )

    def _rationale(self, curve: Sequence[CurvePoint], selected: float | int, current: float,
                   epsilon: float, evidence: Sequence[str]) -> str:
        pts = ", ".join(f"{p.value}:{p.mean:.4f}{'' if p.admissible else '*'}" for p in curve)
        keys = "; ".join(dict.fromkeys(evidence))
        return (
            f"sweep {self.spec.name} lever={self.spec.lever.name} objective={self.spec.objective} "
            f"({self.spec.direction}) pipeline={self.spec.select_pipeline} ε={epsilon:.4f} "
            f"current={current} selected={selected} (widest near-optimal plateau center); "
            f"curve[{pts}] (*=inadmissible); evidence[{keys}]"
        )


def run_sweep(
    spec: SweepSpec,
    *,
    base_config: Config,
    eval_store: EvalResultsStore,
    ledger: RunLedger,
    store: RowSource | None = None,
    retriever: Retriever | None = None,
    golden: Sequence[GoldenQuery] | None = None,
    baseline: dict[str, float] | None = None,
    drift_cfg: DriftConfig | None = None,
    snapshots: SnapshotStore | None = None,
    selfmod_loop: SelfModLoop | None = None,
) -> SweepResult:
    """Drive the grid then optimize — the one-call entry the script and integration test use."""
    engine = SweepEngine(
        spec=spec, base_config=base_config, eval_store=eval_store, ledger=ledger, store=store,
        retriever=retriever, golden=golden, baseline=baseline, drift_cfg=drift_cfg,
        snapshots=snapshots,
    )
    drive = engine.drive()
    return engine.optimize(drive, selfmod_loop=selfmod_loop)
