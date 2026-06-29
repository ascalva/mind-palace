#!/usr/bin/env python
"""Run code in the powerless sandbox, with data piped IN. From the repo root:

    ./.venv/bin/python scripts/sandbox.py analysis.py --input series.csv=~/data/series.csv
    echo 'import numpy as np; print(np.arange(5).sum())' | ./.venv/bin/python scripts/sandbox.py -

The code runs network-off, vault-less, non-root, resource-limited, wall-clock-bounded (Invariant
4) — DATA in, DATA out, never actions. Each `--input NAME=PATH` loads a host file as text and makes
it readable inside at `/tmp/input/NAME` (no host mount — the data rides stdin; the vault stays
unreachable). It returns stdout/stderr/exit.

Needs the podman machine running. For numpy/scipy/pandas/scikit, build + select the libs image
first: `./scripts/build_sandbox_image.sh` then `[sandbox] image = "mind-palace-sandbox:latest"` in
config/local.toml. (This is exactly the seam a future correlator / data_analyst agent uses to find
patterns in observed/IoT data and cross-check against the knowledge graph.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1); the sandbox itself is network-off
    from core.sandbox import ExecSpec
    from core.sandbox.broker import build_broker

    if not argv or argv[0] in {"-h", "--help"}:
        print("usage: sandbox.py <code.py|-> [--input NAME=PATH ...] [--timeout N]")
        return 0

    code = sys.stdin.read() if argv[0] == "-" else Path(argv[0]).expanduser().read_text()
    inputs: dict[str, str] = {}
    timeout = 10
    i = 1
    while i < len(argv):
        if argv[i] == "--input" and i + 1 < len(argv):
            name, _, path = argv[i + 1].partition("=")
            inputs[name] = Path(path).expanduser().read_text()
            i += 2
        elif argv[i] == "--timeout" and i + 1 < len(argv):
            timeout = int(argv[i + 1])
            i += 2
        else:
            print(f"unknown arg {argv[i]!r}")
            return 2

    broker = build_broker()
    res = broker.run(ExecSpec(code=code, inputs=inputs, timeout_s=timeout))
    if res.stdout:
        print(res.stdout, end="" if res.stdout.endswith("\n") else "\n")
    if res.stderr:
        print(f"[stderr]\n{res.stderr}", file=sys.stderr)
    print(f"[exit={res.exit_code} timed_out={res.timed_out} {res.duration_s:.2f}s]",
          file=sys.stderr)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
