"""`python -m eval.predictions`: verify a ledger, print its head, read the blinded pilot, score.

    uv run python -m eval.predictions verify --ledger <file>
    uv run python -m eval.predictions head   --ledger <file>
    uv run python -m eval.predictions power  --ledger <file> [--json]
    uv run python -m eval.predictions score  --ledger <file> [--unblind]

The ledger path is always the caller's: nothing here has a default under `data/`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from eval.predictions.ledger import Ledger, LedgerCorrupt, LedgerError
from eval.predictions.scoring import Blinded, pilot, report, table


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m eval.predictions", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("verify", "recompute the hash chain and count the records"),
                       ("head", "print the chain head (sequence and hash) to anchor elsewhere"),
                       ("power", "the blinded pilot: spread and clusters needed, never a mean"),
                       ("score", "the full report; refused before N unless --unblind")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--ledger", type=Path, required=True)
        if name == "power":
            p.add_argument("--json", action="store_true")
        if name == "score":
            p.add_argument("--unblind", action="store_true",
                           help="read the comparisons before N: the protocol's bar no longer holds")
    return parser


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
