"""The report generator (dn-evaluation-harness §2.7, bp-044 Item 9 + Item 10's appendix).

A **deterministic, model-free** renderer over the harness's settled substrate: the eval-results
store (E1), the run ledger (E2), the telemetry cost ledger (§2.4), and (optional) attestation refs.
It computes ONE report *model* (`Report`, a dataclass tree) and serializes it two ways —
`render_markdown` (human) and `render_json` (machine) — so the two renderings **cannot drift**
(§2.7: "same content, two renderings"). `write_report` drops both into
`data/reports/<date>-<topic>/`.

The load-bearing invariants (plan §6, the whole-plan falsifier):

* **every `Figure` carries its key** `(spec_hash, corpus_ref, config_fingerprint, seed)` — no number
  without provenance. Eval-store figures (curves, drift) anchor on a REAL `Reading.key`;
  ledger/telemetry figures carry a provenance key built from the source row's real identifiers
  (`corpus_ref`, `config_fingerprint`) with a transparent `spec_hash` source-tag and `seed=0` (those
  sources have no seed dimension), plus the `run_id` in `evidence_ref`. Every value stays
  recoverable.
* **model-free + deterministic** — a pure function of the stores + the passed-in `date` (the
  renderer never reads a clock; the CLI/owner stamps it). No model selects or computes here.
* **READ-ONLY over every store** — the renderer queries; it writes only into `data/reports/`.
* **no silent caps** (§2.8) — coverage the renderer could not render (an unregistered metric family,
  a pipeline with no eval readings, an absent cost ledger) is RECORDED in `coverage_notes`, never
  dropped silently.

`structural_axes.*` reconciliation (finding-0086): those metric names are written by the shadow
runner but are NOT registered. Registered metrics resolve their `type_tag` via the fail-closed
`registry.get(...)`; the `structural_axes.*` family is read straight from `query(metric_name=...)`
WITHOUT registry resolution (it would raise `KeyError`), treated as `Inv` as written.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from eval.harness import registry
from eval.harness.sparkline import sparkline
from eval.harness.store import EvalKey, Reading

if TYPE_CHECKING:
    from core.stores.runledger import RunLedger
    from core.stores.telemetry import TelemetryReader


_STRUCTURAL_PREFIX = "structural_axes."
_DRIFT_METRIC = "drift_D"


class FigureKind(StrEnum):
    """The rendered figure families (§2.7). `StrEnum` members are `str`, so a `Figure.kind: str`
    field accepts them directly while the set of legal values stays a closed, named enum."""

    CURVE = "curve"
    TABLE = "table"
    DRIFT = "drift"
    AB = "ab"
    COST = "cost"


class EvalStore(Protocol):
    """The read surface the renderer needs from E1 (`eval/harness/store.EvalResultsStore`)."""

    def query(self, *, metric_name: str | None = ...,
              corpus_ref: str | None = ...) -> list[Reading]: ...


class AttestationRefs(Protocol):
    """The read surface the renderer needs from the attestation store (`core/ops_view`)."""

    def all(self) -> list[Any]: ...


@dataclass(frozen=True)
class Figure:
    """One rendered figure ALWAYS carries its key (§2.7 — no number without provenance)."""

    title: str
    key: EvalKey                    # (spec_hash, corpus_ref, config_fingerprint, seed) — from E1
    kind: str                       # a FigureKind value
    payload: dict[str, Any]         # the rendered data (values, columns, sparkline string)
    evidence_ref: str | None        # the attestation / provenance pointer (§2.4 / §6 Q3)


@dataclass(frozen=True)
class Report:
    topic: str
    date: str                       # passed in (no clock in the renderer; the CLI stamps it)
    figures: tuple[Figure, ...]
    coverage_notes: tuple[str, ...]  # "no silent caps" — dropped/truncated/skipped recorded (§2.8)


# --- assemblers (each pure over its store; every Figure keyed) ----------------------------------


def _curve_figures(eval_store: EvalStore, notes: list[str]) -> list[Figure]:
    """One curve per REGISTERED metric with readings (excluding `drift_D`, which the drift study
    owns, and the `structural_axes.*` family, which the drift study decomposes). Unregistered,
    non-structural metrics are recorded in `notes` (no silent cap), never rendered as a curve."""
    all_readings = eval_store.query()
    names = sorted({r.metric_name for r in all_readings})
    figures: list[Figure] = []
    for name in names:
        if name == _DRIFT_METRIC or name.startswith(_STRUCTURAL_PREFIX):
            continue
        if not registry.is_registered(name):
            notes.append(f"metric {name!r} present in the eval store but UNREGISTERED — "
                         "omitted from curves (no silent cap; §2.5 fail-closed).")
            continue
        spec = registry.get(name)                      # registered → safe to resolve
        readings = eval_store.query(metric_name=name)  # deterministic key order (store contract)
        figures.append(_curve_figure(name, spec.type_tag, readings))
    return figures


def _curve_figure(name: str, type_tag: str, readings: Sequence[Reading]) -> Figure:
    values = [r.value for r in readings]
    anchor = readings[0]
    return Figure(
        title=f"curve · {name}",
        key=anchor.key,
        kind=FigureKind.CURVE,
        payload={
            "metric": name,
            "type_tag": type_tag,
            "sparkline": sparkline(values),
            "points": [_point(r) for r in readings],
        },
        evidence_ref=anchor.evidence_ref,
    )


def _point(r: Reading) -> dict[str, Any]:
    """A single curve point carrying its OWN full key — every value stays independently recoverable.
    """
    return {"key": asdict(r.key), "value": r.value, "evidence_ref": r.evidence_ref}


def _drift_figure(eval_store: EvalStore, notes: list[str]) -> Figure | None:
    """The drift study (§2.7): the `drift_D` trajectory + per-axis `structural_axes.*` decomposition
    (which structural property moved). `structural_axes.*` is read WITHOUT registry resolution
    (finding-0086). Absent both → no figure + a coverage note."""
    drift_readings = eval_store.query(metric_name=_DRIFT_METRIC)
    all_readings = eval_store.query()
    axis_names = sorted({r.metric_name for r in all_readings
                         if r.metric_name.startswith(_STRUCTURAL_PREFIX)})
    if not drift_readings and not axis_names:
        notes.append("drift study: no drift_D readings and no structural_axes.* — omitted "
                     "(no silent cap; §2.8).")
        return None

    axes: list[dict[str, Any]] = []
    anchor: Reading | None = drift_readings[0] if drift_readings else None
    for axis in axis_names:
        readings = eval_store.query(metric_name=axis)   # NOT registry.get (unregistered family)
        if anchor is None:
            anchor = readings[0]
        axes.append({
            "axis": axis.removeprefix(_STRUCTURAL_PREFIX),
            "metric": axis,
            "sparkline": sparkline([r.value for r in readings]),
            "points": [_point(r) for r in readings],
        })
    assert anchor is not None   # guaranteed: one of the two sources is non-empty here
    return Figure(
        title="drift study · D(t) + per-axis decomposition",
        key=anchor.key,
        kind=FigureKind.DRIFT,
        payload={
            "D": {
                "sparkline": sparkline([r.value for r in drift_readings]),
                "points": [_point(r) for r in drift_readings],
            },
            "axes": axes,
        },
        evidence_ref=anchor.evidence_ref,
    )


def _ab_figure(run_ledger: RunLedger, notes: list[str]) -> Figure | None:
    """The A/B table (§2.7): per-pipeline run/claim/novel splits from the run ledger's explicit
    `pipeline` column. The eval store CANNOT be split by pipeline (pipeline lives in an opaque
    `spec_hash`; (corpus_digest, config_fingerprint) are shared across pipelines), so the split is
    ledger-sourced. Keyed by a provenance key from the first run (real corpus_digest +
    config_fingerprint; `spec_hash="ledger:ab"`, `seed=0` — the ledger has no seed dimension)."""
    runs = run_ledger.runs()
    if not runs:
        notes.append("A/B table: the run ledger is empty — omitted (no silent cap).")
        return None
    all_claims = run_ledger.claims()
    pipeline_of = {r["run_id"]: r["pipeline"] for r in runs}
    pipelines = sorted({r["pipeline"] for r in runs})
    rows: list[dict[str, Any]] = []
    for pipe in pipelines:
        pipe_runs = [r for r in runs if r["pipeline"] == pipe]
        pipe_claims = [c for c in all_claims if pipeline_of.get(c["run_id"]) == pipe]
        rows.append({
            "pipeline": pipe,
            "runs": len(pipe_runs),
            "claims": len(pipe_claims),
            "novel": sum(1 for c in pipe_claims if c["novel"]),
        })
    first = runs[0]
    return Figure(
        title="A/B · phase7 vs dream_v2",
        key=EvalKey(spec_hash="ledger:ab", corpus_ref=first["corpus_digest"],
                    config_fingerprint=first["config_fingerprint"], seed=0),
        kind=FigureKind.AB,
        payload={"pipelines": rows},
        evidence_ref=first["run_id"],
    )


def _cost_figure(telemetry: TelemetryReader, run_ledger: RunLedger | None,
                 notes: list[str]) -> Figure | None:
    """The cost appendix (§2.4, Item 10): the harness cost ledger's rows — wall-clock, models
    resident, cells completed/skipped — plus totals. Keyed by a provenance key from the first row
    (its `run_id`, and — when the run is in the ledger — the run's real corpus_digest +
    config_fingerprint). Absent ledger → 'unknown' recorded, never fabricated."""
    costs = telemetry.harness_costs()
    if not costs:
        notes.append("cost appendix: the harness cost ledger is empty — omitted (no silent cap; "
                     "§2.4).")
        return None
    totals = {
        "wall_clock_s": sum(float(c["wall_clock_s"] or 0.0) for c in costs),
        "cells_completed": sum(int(c["cells_completed"] or 0) for c in costs),
        "cells_skipped": sum(int(c["cells_skipped"] or 0) for c in costs),
    }
    first = costs[0]
    run_id = first["run_id"]
    corpus_ref, config_fp = "unknown", "unknown"
    if run_ledger is not None and run_id is not None:
        match = [r for r in run_ledger.runs() if r["run_id"] == run_id]
        if match:
            corpus_ref = match[0]["corpus_digest"]
            config_fp = match[0]["config_fingerprint"]
        else:
            notes.append(f"cost appendix: run_id {run_id!r} not found in the run ledger — "
                         "corpus/config recorded 'unknown' (no fabrication).")
    return Figure(
        title="cost appendix · wall-clock / residency / cells",
        key=EvalKey(spec_hash="telemetry:harness_cost", corpus_ref=corpus_ref,
                    config_fingerprint=config_fp, seed=0),
        kind=FigureKind.COST,
        payload={
            "rows": [_cost_row(c) for c in costs],
            "totals": totals,
        },
        evidence_ref=run_id,
    )


def _cost_row(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": c["run_id"],
        "wall_clock_s": c["wall_clock_s"],
        "models_resident": c["models_resident"],
        "cells_completed": c["cells_completed"],
        "cells_skipped": c["cells_skipped"],
        "note": c["note"],
    }


# --- the one model + its two renderings ---------------------------------------------------------


def build_report(topic: str, date: str, *, eval_store: EvalStore, run_ledger: RunLedger,
                 telemetry: TelemetryReader,
                 attestations: AttestationRefs | None = None) -> Report:
    """Build the ONE report model — pure and READ-ONLY over the stores. `date` is passed in (the
    renderer reads no clock — determinism). Attestation refs, when present, annotate a coverage note
    (the report *displays* refs; it does not verify chains — that is the E8 battery)."""
    notes: list[str] = []
    figures: list[Figure] = []
    figures.extend(_curve_figures(eval_store, notes))
    drift = _drift_figure(eval_store, notes)
    if drift is not None:
        figures.append(drift)
    ab = _ab_figure(run_ledger, notes)
    if ab is not None:
        figures.append(ab)
    cost = _cost_figure(telemetry, run_ledger, notes)
    if cost is not None:
        figures.append(cost)
    if attestations is not None:
        notes.append(f"attestations available: {len(attestations.all())} (refs displayed, chains "
                     "not verified — that is the E8 process battery).")
    return Report(topic=topic, date=date, figures=tuple(figures),
                  coverage_notes=tuple(notes))


def _report_dict(r: Report) -> dict[str, Any]:
    """The single serializable form of the model — both renderings derive from THIS, so they cannot
    disagree on a value (§2.7's anti-drift guarantee)."""
    return asdict(r)


def render_json(r: Report) -> str:
    """`report.json` — the model, machine-rendered. Deterministic (`sort_keys`)."""
    return json.dumps(_report_dict(r), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _key_line(key: EvalKey) -> str:
    return (f"key: spec_hash={key.spec_hash} corpus_ref={key.corpus_ref} "
            f"config_fingerprint={key.config_fingerprint} seed={key.seed}")


def render_markdown(r: Report) -> str:
    """`report.md` — the SAME model, human-rendered. Every figure prints its key line (provenance)
    so `render_markdown` and `render_json` carry identical figures/keys (§2.7)."""
    lines: list[str] = [f"# Harness report · {r.topic}", "", f"_date: {r.date}_", ""]
    if not r.figures:
        lines += ["_No figures — the stores held nothing to render._", ""]
    for fig in r.figures:
        lines += [f"## {fig.title}", "", f"- {_key_line(fig.key)}",
                  f"- evidence_ref: {fig.evidence_ref}", ""]
        lines += _render_payload_md(fig)
        lines.append("")
    lines += ["## Coverage notes", ""]
    if r.coverage_notes:
        lines += [f"- {n}" for n in r.coverage_notes]
    else:
        lines.append("- none — full coverage over the available stores.")
    lines.append("")
    return "\n".join(lines)


def _render_payload_md(fig: Figure) -> list[str]:
    p = fig.payload
    if fig.kind == FigureKind.CURVE:
        return [f"- `{p['metric']}` ({p['type_tag']}): `{p['sparkline']}`  "
                f"({len(p['points'])} points)"]
    if fig.kind == FigureKind.DRIFT:
        out = [f"- D(t): `{p['D']['sparkline']}`  ({len(p['D']['points'])} points)"]
        for ax in p["axes"]:
            out.append(f"- axis `{ax['axis']}`: `{ax['sparkline']}`  ({len(ax['points'])} points)")
        return out
    if fig.kind == FigureKind.AB:
        out = ["| pipeline | runs | claims | novel |", "|---|---|---|---|"]
        out += [f"| {row['pipeline']} | {row['runs']} | {row['claims']} | {row['novel']} |"
                for row in p["pipelines"]]
        return out
    if fig.kind == FigureKind.COST:
        out = ["| run_id | wall_clock_s | models_resident | cells_completed | cells_skipped |",
               "|---|---|---|---|---|"]
        out += [f"| {c['run_id']} | {c['wall_clock_s']} | {c['models_resident']} | "
                f"{c['cells_completed']} | {c['cells_skipped']} |" for c in p["rows"]]
        t = p["totals"]
        out.append(f"- totals: wall_clock_s={t['wall_clock_s']} "
                   f"cells_completed={t['cells_completed']} cells_skipped={t['cells_skipped']}")
        return out
    return [f"- (payload: {sorted(p)})"]


def write_report(r: Report, root: str | Path = "data/reports") -> Path:
    """Write `report.md` + `report.json` into `<root>/<date>-<topic>/` and return that directory.
    The ONLY filesystem write the renderer performs — into `data/reports/`, never a store
    (∉ MIRROR_READABLE; local file, no egress)."""
    slug = f"{r.date}-{r.topic}"
    out_dir = Path(root) / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(render_markdown(r), encoding="utf-8")
    (out_dir / "report.json").write_text(render_json(r), encoding="utf-8")
    return out_dir
