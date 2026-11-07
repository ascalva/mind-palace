"""`python -m eval.predictions`: verify a ledger, print its head, read the blinded pilot, score,
read the growth.

    uv run python -m eval.predictions verify --ledger <file>
    uv run python -m eval.predictions head   --ledger <file>
    uv run python -m eval.predictions power  --ledger <file> [--json]
    uv run python -m eval.predictions score  --ledger <file> [--unblind]
    uv run python -m eval.predictions growth --ledger <file> [--json] [--unblind]

The ledger path is always the caller's: nothing here has a default under `data/`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from eval.predictions.ledger import Ledger, LedgerCorrupt, LedgerError
from eval.predictions.scoring import Blinded, growth_report, pilot, report, table


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m eval.predictions", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("verify", "recompute the hash chain and count the records"),
                       ("head", "print the chain head (sequence and hash) to anchor elsewhere"),
                       ("power", "the blinded pilot: spread and clusters needed, never a mean"),
                       ("score", "the full report; refused before N unless --unblind"),
                       ("growth", "each arm's growth against the reference arm; the primary "
                                  "comparison's arms withheld before N unless --unblind")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--ledger", type=Path, required=True)
        if name in ("power", "growth"):
            p.add_argument("--json", action="store_true")
        if name in ("score", "growth"):
            p.add_argument("--unblind", action="store_true",
                           help="read the comparisons before N: the protocol's bar no longer holds")
    return parser


def _print_growth(out: dict[str, object]) -> None:
    readouts = out["readouts"]
    withheld = out["withheld"]
    assert isinstance(readouts, list) and isinstance(withheld, list)
    print(f"growth against {out['reference']}, target {out['target']}x, the full stake and the "
          f"fractional stakes {out['stakes']}")
    if withheld:
        names = ", ".join(f"{w['arm']} on {w['family']}" for w in withheld)
        print(f"withheld before N: {names} ({out['blinded']})")
    beyond = out["beyond_n"]
    assert isinstance(beyond, dict)
    if beyond["clusters"]:
        print(f"read at N: {beyond['clusters']} clusters beyond N left out "
              f"({beyond['pairs']} pairs of the primary comparison)")
    if out["reference"] is None:
        print("no reference arm in the protocol: nothing to read")
        return
    print(f"{'arm':<16} {'family':<10} {'stake':>5} {'pairs':>5} {'growth':>10} {'per pair':>9} "
          f"{'worst':>8} {'drawdown':>8} {'to target':>9}")
    for g in readouts:
        to_target = g["to_target"]
        print(f"{g['arm']:<16} {g['family']:<10} {g['stake']:>5.2f} {g['pairs']:>5} "
              f"{g['growth']:>10.4f} {g['geometric_mean']:>9.4f} {g['worst_factor']:>8.4f} "
              f"{g['drawdown']:>8.1%} {'none' if to_target is None else to_target:>9}")


def _finite(value: object) -> object:
    """JSON has no NaN: an undefined number (fewer than two clusters) prints as null."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_finite(v) for v in value]
    return value


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ledger = Ledger(args.ledger)
    try:
        if args.command == "verify":
            head = ledger.verify()
            counts = ", ".join(f"{k} {v}" for k, v in head.counts.items())
            print(f"ok: {head.seq + 1} records, head {head.hash}\n{counts}")
        elif args.command == "head":
            head = ledger.verify()
            print(f"{head.seq} {head.hash}")
        elif args.command == "power":
            ledger.verify()
            reading = pilot(table(ledger.entries()))
            if args.json:
                print(json.dumps(_finite({
                    "comparison": reading.comparison.body(), "pairs": reading.n_pairs,
                    "clusters": reading.n_clusters, "sd": reading.sd,
                    "required_clusters": reading.required, "null_exact": reading.null_exact,
                }), indent=2))
            else:
                c = reading.comparison
                print(f"primary: {c.arm} against {c.baseline} on {c.family}")
                print(f"pairs {reading.n_pairs}, clusters {reading.n_clusters}, "
                      f"spread of cluster means {reading.sd:.4f}")
                print(f"clusters needed: {reading.required if reading.required else 'unknown'}")
                print(f"null control exact: {reading.null_exact}")
        elif args.command == "growth":
            ledger.verify()
            out = growth_report(table(ledger.entries()), unblind=args.unblind)
            if args.json:
                print(json.dumps(_finite(out), indent=2))
            else:
                _print_growth(out)
        else:
            ledger.verify()
            out = report(table(ledger.entries()), unblind=args.unblind)
            print(json.dumps(_finite(out), indent=2))
    except LedgerCorrupt as exc:
        print(f"corrupt: {exc}", file=sys.stderr)
        return 1
    except Blinded as exc:
        print(f"blinded: {exc}", file=sys.stderr)
        return 2
    except LedgerError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
