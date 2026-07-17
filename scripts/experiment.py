#!/usr/bin/env python
"""The σ-sweep experiment CLI (bp-058) — the pre-flight + reporting surfaces run 1 needs. From root:

    uv run scripts/experiment.py controls                                   # V3 — control battery
    uv run scripts/experiment.py blind-sample config/sweeps/dreamer-sigma-ab.toml [--seed N]
    uv run scripts/experiment.py report       config/sweeps/dreamer-sigma-ab.toml [--commit SHA]

Design: `docs/design-notes/sigma-sweep-experiment.md` (RATIFIED, FROZEN @ d932670). This is the
experiment's INSTRUMENT entry — it never fires the run (owner-fired, V5) and moves no lever. Seals
the core first (Invariant 1), then dispatches a subcommand. All heavy lifting lives in the
deterministic, model-free `eval/harness/experiment.py`; this script is the thin CLI + FS wiring +
the run-store resolution over a COMPLETED sweep night (the `scripts/fibers.py` pattern).

Subcommands:
  * `controls`      — V3: bp-057's noise + planted fixtures through the CURRENT pipeline; the three
                      F9 criteria recomputed. GREEN ⇒ exit 0; RED ⇒ exit 1 (run INVALID, §2.1 V3).
  * `blind-sample`  — SE-3: from the completed run's tiering, sample ≤`--cap` claims stratified
                      across tiers, write an UNLABELED presentation + a SEALED labels file.
  * `report`        — §2.3: assemble the composite report (added in Item 3).
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

if TYPE_CHECKING:
    from config.loader import Config
    from eval.harness.fibers import FibersResult
    from eval.harness.gate import TieredClaim
    from eval.harness.sweep import SweepResult, SweepSpec


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _cmd_controls(_args: argparse.Namespace) -> int:
    """V3 — the control battery as one invocation. Returns the exit code (0 GREEN, 1 RED)."""
    from eval.harness.experiment import render_control_markdown, run_control_battery

    outcome = run_control_battery()
    for line in render_control_markdown(outcome):
        print(line)
    if not outcome.green:
        print("CONTROLS RED — the run is INVALID (§2.1 V3): stop, file a finding, read no "
              "hypothesis.", file=sys.stderr)
        return 1
    print("CONTROLS GREEN — instrument integrity holds; the run may proceed to V4/V5.")
    return 0


def _resolve_run_tiering(
    cfg: Config, spec: SweepSpec, *, pipeline: str | None = None
) -> tuple[FibersResult, list[TieredClaim], dict[str, str], int]:
    """Read the COMPLETED sweep night's ledger + eval store, score the fibers (bp-050), and tier the
    `pipeline`'s claims (default = the spec's `select_pipeline` — the σ-driven lane, finding-0089)
    at
    the FROZEN θ defaults (SE-3). Returns `(fibers_result, tiered, content, m)` where `content` maps
    `claim_id → surface_text` (the presentation text, read from the ledger — NEVER the tier).
    Confidence + content are built straight from the ledger columns (no test-fixture helper on the
    real path)."""
    from core.stores.runledger import RunLedger
    from eval.harness.fibers import run_fibers
    from eval.harness.gate import assign_tiers
    from eval.harness.store import open_eval_store

    lane = pipeline or spec.select_pipeline
    grid = tuple(float(v) for v in spec.grid())
    ledger = RunLedger(cfg.paths.derived_store.parent / "dream_runs.sqlite")
    eval_store = open_eval_store(cfg)

    fibers_result = run_fibers(
        ledger=ledger, eval_store=eval_store, base_config=cfg, lever=spec.lever, grid=grid
    )
    fibers = list(fibers_result.fibers.get(lane, ()))

    # confidence + presentation content straight from the ledger's claims for this lane.
    confidence: dict[str, float] = {}
    content: dict[str, str] = {}
    for run in ledger.runs(pipeline=lane):
        for c in ledger.claims(run_id=str(run["run_id"])):
            cid = str(c["claim_id"])
            confidence[cid] = float(c["confidence"])
            content.setdefault(cid, str(c["surface_text"] or ""))

    tiered = assign_tiers(fibers, m=len(grid), confidence=confidence) if fibers else []
    return fibers_result, tiered, content, len(grid)


def _cmd_blind_sample(args: argparse.Namespace) -> int:
    """SE-3 — write the blind presentation + the SEALED labels for the completed run's tiering."""
    from config.loader import get_config
    from eval.harness.experiment import generate_blind_sample, write_blind_sample
    from eval.harness.sweep import parse_spec

    spec = parse_spec(Path(args.spec))
    cfg = get_config()
    _fibers, tiered, content, _m = _resolve_run_tiering(cfg, spec)
    if not tiered:
        print("blind-sample: no tiered claims (empty/absent run ledger for the select pipeline) — "
              "nothing to sample. Run the sweep first (owner-fired).", file=sys.stderr)
        return 1

    topic = args.topic or f"{spec.name}-blind"
    sample = generate_blind_sample(tiered, content, seed=args.seed, cap=args.cap)
    out_dir = write_blind_sample(sample, date=args.date, topic=topic)
    print(f"blind-sample {spec.name}: {len(sample.presentation)} item(s), seed={args.seed}, "
          f"cap={args.cap}")
    print(f"  presentation (UNLABELED): {out_dir / 'presentation.md'}")
    print(f"  labels (SEALED — open only after rating): {out_dir / 'labels.sealed.json'}")
    for note in sample.notes:
        print(f"  - {note}")
    return 0


def _reoptimize(cfg: Config, spec: SweepSpec, eval_store: object,
                ledger: object) -> SweepResult | None:
    """Reconstruct SE-1's verdict over the COMPLETED run's readings WITHOUT re-driving (the
    optimizer is deterministic + model-free — it reads the eval store and does arithmetic). Returns
    a `SweepResult`, or None (+ the caller notes it) when the store holds no objective readings."""
    from dataclasses import replace

    from core.dreaming.shadow import _config_fingerprint
    from eval.harness.sweep import DriveResult, SweepEngine

    grid = spec.grid()
    fp_to_value: dict[str, float | int] = {}
    for value in grid:
        section = getattr(cfg, spec.lever.section)
        modified = replace(cfg, **{spec.lever.section: replace(
            section, **{spec.lever.key: spec.lever.coerce(value)})})
        fp_to_value[_config_fingerprint(modified)] = value

    engine = SweepEngine(spec=spec, base_config=cfg, eval_store=eval_store, ledger=ledger)  # type: ignore[arg-type]
    try:
        return engine.optimize(DriveResult(grid=tuple(grid), fp_to_value=fp_to_value),
                               selfmod_loop=None)
    except Exception as exc:  # noqa: BLE001 — ObjectiveNotProducedError (empty store) degrades to None
        print(f"  (SE-1 selection unavailable: {exc})", file=sys.stderr)
        return None


def _cmd_report(args: argparse.Namespace) -> int:
    """§2.3 — assemble the composite report over the completed run's stores. V2 cut / V4 determinism
    default to preview (they are pre-flight/run artifacts recorded separately; the report
    re-assembles
    with them once available). Writes `composite.{md,json}` under data/reports/."""
    from config.loader import get_config
    from core.stores.runledger import RunLedger
    from core.stores.telemetry import open_store as open_telemetry
    from eval.harness.experiment import (
        SelfmodPosture,
        assemble_composite,
        run_control_battery,
        write_composite,
    )
    from eval.harness.report import build_report
    from eval.harness.store import open_eval_store
    from eval.harness.sweep import parse_spec

    spec = parse_spec(Path(args.spec))
    cfg = get_config()
    fibers_result, tiered, _content, _m = _resolve_run_tiering(cfg, spec)

    ledger = RunLedger(cfg.paths.derived_store.parent / "dream_runs.sqlite")
    eval_store = open_eval_store(cfg)
    # The E4 A/B report reads the telemetry store for its cost appendix. If that store is
    # unavailable
    # (e.g. the live daemon holds the duckdb lock), degrade to a preview A/B — the assembler records
    # the absence as a coverage note; never a crash, never a fabricated cost.
    ab_report = None
    try:
        telemetry = open_telemetry(cfg).reader()
        ab_report = build_report(f"{spec.name}-ab", args.date, eval_store=eval_store,
                                 run_ledger=ledger, telemetry=telemetry)
    except Exception as exc:  # noqa: BLE001 — a locked/absent store degrades the A/B, not the run
        print(f"  (E4 A/B unavailable — {exc}; assembling without the cost appendix)",
              file=sys.stderr)
    sweep_result = _reoptimize(cfg, spec, eval_store, ledger)
    control = run_control_battery()
    posture = SelfmodPosture(
        enabled=cfg.selfmod.enabled,
        unattended_enabled=cfg.selfmod.unattended_enabled,
        proposal_emitted=bool(getattr(sweep_result, "proposal_emitted", False)),
        proposal_id=getattr(sweep_result, "proposal_id", None),
    )

    report = assemble_composite(
        topic=args.topic or f"{spec.name}", date=args.date, commit_sha=args.commit,
        sweep_result=sweep_result, fibers_result=fibers_result, tiered=tiered, control=control,
        cut=None, determinism=None, selfmod_posture=posture, ab_report=ab_report,
    )
    out_dir = write_composite(report)
    print(f"report {spec.name}: {len(report.sections)} section(s) → {out_dir / 'composite.md'}")
    for note in report.coverage_notes:
        print(f"  - {note}")
    return 0


def _git_head() -> str:
    """Best-effort HEAD SHA for the report's commit_sha (V1). Falls back to 'unknown' — the renderer
    reads no clock/VCS; this is a convenience default the caller may override with --commit."""
    import subprocess

    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             cwd=str(Path(__file__).resolve().parent.parent), timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(prog="experiment", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_controls = sub.add_parser("controls", help="V3 — the control battery (GREEN/RED pre-flight)")
    p_controls.set_defaults(func=_cmd_controls)

    p_blind = sub.add_parser("blind-sample", help="SE-3 — blind presentation + sealed labels")
    p_blind.add_argument("spec", help="the frozen sweep spec (for the grid + lever)")
    p_blind.add_argument("--seed", type=int, default=20260717, help="blinding seed (deterministic)")
    p_blind.add_argument("--cap", type=int, default=24, help="max claims sampled (stratified)")
    p_blind.add_argument("--date", default=_today(), help="YYYY-MM-DD stamp (no clock read)")
    p_blind.add_argument("--topic", default=None, help="report topic slug (default <spec>-blind)")
    p_blind.set_defaults(func=_cmd_blind_sample)

    p_report = sub.add_parser("report", help="§2.3 — assemble the composite report")
    p_report.add_argument("spec", help="the frozen sweep spec (for the grid + lever)")
    p_report.add_argument("--date", default=_today(), help="YYYY-MM-DD stamp (no clock read)")
    p_report.add_argument("--commit", default=_git_head(), help="commit SHA for V1 evidence")
    p_report.add_argument("--topic", default=None, help="report topic slug (default <spec>)")
    p_report.set_defaults(func=_cmd_report)

    args = parser.parse_args()

    from core.sealing import seal

    seal()  # structural egress guard first (Invariant 1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
