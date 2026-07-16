#!/usr/bin/env python
"""The tuning control surface — the owner's hand on the §14 gate (dn-evaluation-harness §2.6, E3a).

    uv run scripts/tune.py show                     # levers: live value, bounds, manifest policy
    uv run scripts/tune.py set <lever> <value> [why]  # PROPOSE a change → awaits owner approval
    uv run scripts/tune.py history                  # every proposal + its outcome
    uv run scripts/tune.py --revert <proposal_id>   # roll an EXECUTED change back to its prior

This is the HUMAN's hand — no model is ever in this path (Invariant 3: the model advises, code
acts). Every apply transits the BUILT §14 loop (`ops/selfmod.SelfModLoop`) and the same proposal
ledger (`ops/ledger.ProposalLedger`); this CLI reimplements no gate.

`set` only PROPOSES — it never auto-approves, executes, or writes the overlay (that is a separate
owner act via `python -m ops.selfmod_cli approve`). `show`/`history` are read-only and work with
`[selfmod] enabled = false`. `--revert` rolls an EXECUTED proposal back through the loop's rollback
primitives; a VALIDATED (kept, terminal) proposal is NOT mutated — the CLI surfaces the inverse
`set` to file instead (Q2: a kept change is undone by a new inverse proposal, not a state
transition).
"""

from __future__ import annotations

import argparse
import sys

from config.loader import Config, get_config, refresh_config
from eval.harness.tuning import TuningManifest, load_manifest
from ops.apply import overlay_restore
from ops.ledger import LedgerStatus, Proposal, ProposalLedger, open_ledger
from ops.levers import LEVERS, ProposedChange, get_lever
from ops.selfmod import SelfModLoop, Validator, _section_value, build_loop

# `set` only proposes; propose never runs the validator. A never-called placeholder guards the seam
# so a mistaken validate() call is a loud AssertionError, never a silent unvalidated apply.
_NO_VALIDATE: Validator = lambda lever, value: (_ for _ in ()).throw(  # noqa: E731
    AssertionError("validator must not run for a `tune.py set`/`--revert` command")
)


# --- show -------------------------------------------------------------------------------------
def cmd_show(cfg: Config, manifest: TuningManifest) -> str:
    """Read-only: each registered lever's live value + hard bounds + resolved manifest policy.

    Live value comes from `_section_value` (Q3) — the config/overlay chain, never the manifest;
    the manifest carries POLICY only, so `show` proves the two channels stay separate."""
    lines = []
    for name in sorted(LEVERS):
        lever = LEVERS[name]
        pol = manifest.policy(name)
        value = _section_value(cfg, lever)
        rendered = str(int(value)) if lever.kind == "int" else f"{value:g}"
        obj = pol.objective or "-"
        lines.append(
            f"{name}: {rendered}  bounds=[{lever.lo:g}, {lever.hi:g}]  kind={lever.kind}\n"
            f"  subsystem={pol.subsystem}  autonomy={pol.autonomy}  objective={obj}\n"
            f"  {lever.description}"
        )
    return "\n".join(lines)


# --- set (PROPOSE only — never approves) ------------------------------------------------------
def cmd_set(loop: SelfModLoop, lever: str, value: float, rationale: str) -> str:
    """PROPOSE a knob change and stop. The CLI never approves its own proposal (falsifier) — the
    owner blesses it separately (`python -m ops.selfmod_cli approve <id>`). Bounds are checked by
    `ProposedChange.resolve` inside `propose`, fail-closed, before any ledger row is written."""
    p = loop.propose(
        ProposedChange(lever=lever, target=value, rationale=rationale), proposer="owner-tune-cli"
    )
    return (
        f"proposed #{p.id}: {p.lever} {p.current_value:g} -> {p.target_value:g}\n"
        "  status=PROPOSED — awaits OWNER APPROVAL; nothing is applied yet.\n"
        f"  approve with:  python -m ops.selfmod_cli approve {p.id}"
    )


# --- history ----------------------------------------------------------------------------------
def _fmt(p: Proposal) -> str:
    line = f"#{p.id} [{p.status}] {p.lever}: {p.current_value:g} -> {p.target_value:g}"
    if p.rationale:
        line += f"  ({p.rationale})"
    if p.status == LedgerStatus.ROLLED_BACK and p.rollback_reason:
        line += f"  ROLLED BACK: {p.rollback_reason}"
    return line


def cmd_history(ledger: ProposalLedger) -> str:
    rows = ledger.all()
    return "\n".join(_fmt(p) for p in rows) if rows else "no proposals yet."


# --- revert -----------------------------------------------------------------------------------
def cmd_revert(loop: SelfModLoop, pid: int) -> str:
    """Roll an EXECUTED proposal back to its exact prior overlay value, through the SAME primitives
    the loop's `validate` uses on a gate-deny (`overlay_restore` + `mark_rolled_back` +
    `refresh_config`) — a deliberate, unconditional reversal, not a gate decision, and not a
    reimplementation of the gate (the gate is the admit predicate, not invoked here).

    Only an EXECUTED proposal is directly revertible (EXECUTED→ROLLED_BACK is the sole legal
    successor edge, ops/ledger._TRANSITIONS). A VALIDATED (kept, terminal) proposal has no
    successor: the CLI REFUSES the transition and surfaces the inverse `set` to file instead
    (Q2). Any other state is not revertible."""
    loop._require_enabled()  # writing the overlay is a self-mod act; honor the master switch
    p = loop.ledger.get(pid)
    if p is None:
        return f"no proposal #{pid}"

    if p.status is LedgerStatus.EXECUTED:
        lever = get_lever(p.lever)
        overlay_restore(lever, p.prior_overlay, loop.overlay_path)
        refresh_config()
        final = loop.ledger.mark_rolled_back(
            pid, reason=f"reverted by owner via tune.py --revert (was {p.target_value:g})"
        )
        restored = "removed (knob back to its committed default)" if p.prior_overlay is None \
            else f"restored to {p.prior_overlay:g}"
        return f"reverted #{pid}: {final.lever} overlay {restored}; status now ROLLED_BACK."

    if p.status is LedgerStatus.VALIDATED:
        # Kept + terminal — do NOT fake a transition (falsifier). Offer the inverse proposal.
        return (
            f"proposal #{pid} is VALIDATED (kept, terminal) — its status cannot be reverted.\n"
            f"  To undo a kept change, file the INVERSE proposal (a new owner-blessed change):\n"
            f"    uv run scripts/tune.py set {p.lever} {p.current_value:g} 'revert #{pid}'"
        )

    return (
        f"proposal #{pid} is {p.status} — only an EXECUTED proposal can be --reverted "
        f"(a VALIDATED one is undone via an inverse `set`)."
    )


# --- entrypoint -------------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tune.py", description="tuning control surface (§14)")
    parser.add_argument(
        "--revert", type=int, metavar="PROPOSAL_ID", default=None,
        help="roll an EXECUTED proposal back to its prior overlay value",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="levers: live value, bounds, manifest policy")
    p_set = sub.add_parser("set", help="propose a knob change (awaits owner approval)")
    p_set.add_argument("lever")
    p_set.add_argument("value", type=float)
    p_set.add_argument("rationale", nargs="*", default=[])
    sub.add_parser("history", help="every proposal and its outcome")
    return parser


def main(argv: list[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --revert is a state change through the loop (which enforces [selfmod] enabled, fail-closed).
    if args.revert is not None:
        try:
            loop = build_loop(_NO_VALIDATE, ledger=open_ledger())
            print(cmd_revert(loop, args.revert))
            return 0
        except Exception as exc:  # surface gate refusals (disabled, illegal transition) plainly
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.command == "show":
        print(cmd_show(get_config(), load_manifest()))
        return 0
    if args.command == "history":
        print(cmd_history(open_ledger()))
        return 0
    if args.command == "set":
        lever = args.lever
        if lever not in LEVERS:
            print(f"unknown lever {lever!r}; registered: {sorted(LEVERS)}", file=sys.stderr)
            return 2
        try:
            loop = build_loop(_NO_VALIDATE, ledger=open_ledger())
            print(cmd_set(loop, lever, args.value, " ".join(args.rationale)))
            return 0
        except Exception as exc:  # bounds / [selfmod] disabled — refuse plainly, no ledger write
            print(f"error: {exc}", file=sys.stderr)
            return 1

    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
