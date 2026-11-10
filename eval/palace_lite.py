"""Lookups through a code instance against ripgrep (docs/design-notes/dn-palace-lite.md).

    MIND_PALACE_OVERLAY=<code overlay> uv run python -m eval.palace_lite \
        --checkout <a checkout of the commit the instance landed> [--runs 5] [--out PATH]
    MIND_PALACE_OVERLAY=<code overlay> uv run python -m eval.palace_lite --mcp [--runs 5]

Each lookup is a question with a known answer, the files that hold it. The palace is asked a
sentence through the sentence engine (`top 5 near "<text>" over reference`, or `trace`), in this
process over the instance's own stores, as the MCP server asks it: the first time (cold, the
engine's stores opened by that call) and then `--runs` more times (warm, the median reported).
Ripgrep is asked the pattern an agent would type, over the checkout, its files sorted by path;
its wall time is the median of `--runs`. A lookup is a hit for the palace when an answer is among
the top 5 files it ranks, and for ripgrep when an answer is among the files it prints; the files
ripgrep prints are how many an agent must open, since ripgrep filters and does not rank. Only
paths, counts and times leave the run.

`--mcp` measures the MCP server over the instance as a client meets it: the command an MCP client
runs is spawned under `/usr/bin/time -l`, and the times from the spawn to the `initialize` answer,
to the first `query` answer and to a second one are taken, then the peak resident memory of the
server's process tree when its input closes; `--runs` spawns, the medians reported.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


@dataclass(frozen=True)
class Lookup:
    id: str
    question: str
    sentence: str               # `{space}` is the repository's item space, `code/<name>/`
    rg: tuple[str, ...]         # ripgrep's arguments after `rg -l --sort path`
    answers: frozenset[str]     # repository-relative paths that answer it


LOOKUPS: tuple[Lookup, ...] = (
    Lookup("define", "where is `embed_fitting` defined",
           'top 5 near "def embed_fitting" over reference', ("def embed_fitting",),
           frozenset({"core/ingest/embed.py"})),
    Lookup("unchanged", "where does the writer's UNCHANGED check live",
           'top 5 near "writer UNCHANGED check" over reference', ("UNCHANGED check",),
           frozenset({"core/ingest/writer.py"})),
    Lookup("note", "which note describes landing without vectors",
           'top 5 near "landing an item without its vector" over reference',
           ("-i", "without (its|a) vector", "docs/design-notes"),
           frozenset({"docs/design-notes/dn-two-phase-ingestion.md"})),
    Lookup("laws", "which laws govern the embed drain",
           'top 5 near "laws of the embed drain" over reference', ("-i", "embed drain"),
           frozenset({"docs/LAWS.md"})),
    Lookup("imports", "which files import core.ingest.writer",
           'top 5 near "from core.ingest.writer import" over reference',
           ("from core.ingest.writer import",),
           frozenset({"core/ingest/ingress.py", "eval/ingress_gas.py", "scheduler/interface.py",
                      "tests/fixtures/ingress.py",
                      "tests/integration/test_ambassador_conversation.py",
                      "tests/integration/test_corpus_ingest.py",
                      "tests/integration/test_ingress_scripts.py", "tests/unit/test_ingress.py"})),
    Lookup("spectral", "which code computes the spectral gap",
           'top 5 near "spectral gap" over reference', ("-i", "spectral gap", "--type", "py"),
           frozenset({"core/graph/influence.py"})),
    Lookup("bm25", "where is the BM25 term weight computed",
           'top 5 near "BM25 term weight" over reference', ("-i", "bm25"),
           frozenset({"core/ingest/lexical.py"})),
    Lookup("root", "where is the instance root resolved",
           'top 5 near "instance root resolution rule" over reference', ("-i", "instance root"),
           frozenset({"core/kernel/config/root.py"})),
    Lookup("lean", "which Lean file proves the script firewall",
           'top 5 near "firewall_store theorem" over reference', ("firewall_store", "formal"),
           frozenset({"formal/Palace/Script.lean"})),
    Lookup("lock", "where is the supervisor lock taken",
           'top 5 near "supervisor lock acquire" over reference', ("SupervisorLock",),
           frozenset({"ops/lifecycle/lock.py"})),
    Lookup("rrf", "which constant does reciprocal rank fusion use",
           'top 5 near "reciprocal rank fusion constant" over reference',
           ("-i", "reciprocal rank"), frozenset({"core/ingest/lexical.py"})),
)
# The file's history: the palace answers with the versions it landed, git with every commit.
HISTORY = ("history", "the commit history of core/ingest/writer.py",
           'trace "{space}core/ingest/writer.py"', "core/ingest/writer.py")


@dataclass
class Result:
    id: str
    question: str
    palace_top: list[str] = field(default_factory=list)
    palace_rank: int | None = None
    palace_cold_ms: float = 0.0
    palace_warm_ms: float = 0.0
    rg_files: int = 0
    rg_hit: bool = False
    rg_rank: int | None = None
    rg_ms: float = 0.0


def _ask(engine: Any, sentence: str, log: Any) -> list[str]:
    from core.sentence.surface import ask_logged, sentence_grant

    answer = ask_logged(sentence, sentence_grant(), surface="eval", role="ambassador",
                        engine=engine, log=log)
    return [h.ref for h in answer.hits]


def _ms(f: Any, runs: int) -> tuple[Any, float]:
    out, times = None, []
    for _ in range(runs):
        t = time.perf_counter()
        out = f()
        times.append((time.perf_counter() - t) * 1000)
    return out, statistics.median(times)


def run(checkout: Path, runs: int) -> dict[str, Any]:
    from core.kernel.config import get_config
    from core.query import QueryEngine
    from core.sentence.surface import QueryLog

    cfg = get_config()
    space = f"code/{cfg.ingestion.code.repositories[0].name}/"
    log = QueryLog(Path(os.devnull))
    engine = QueryEngine(config=cfg)
    results = []
    for lk in LOOKUPS:
        r = Result(lk.id, lk.question)
        t = time.perf_counter()
        refs = _ask(engine, lk.sentence, log)
        r.palace_cold_ms = (time.perf_counter() - t) * 1000
        refs, r.palace_warm_ms = _ms(lambda lk=lk: _ask(engine, lk.sentence, log), runs)
        r.palace_top = [x.removeprefix(space) for x in refs[:5]]
        r.palace_rank = next((i + 1 for i, x in enumerate(r.palace_top) if x in lk.answers),
                             None)
        done, r.rg_ms = _ms(lambda lk=lk: subprocess.run(
            ["rg", "-l", "--sort", "path", *lk.rg], cwd=checkout, capture_output=True,
            text=True), runs)
        files = done.stdout.split()
        r.rg_files = len(files)
        r.rg_hit = any(f in lk.answers for f in files)
        r.rg_rank = next((i + 1 for i, f in enumerate(files) if f in lk.answers), None)
        results.append(r)
    hid, question, sentence, path = HISTORY
    t = time.perf_counter()
    chains = _ask(engine, sentence.format(space=space), log)
    trace_ms = (time.perf_counter() - t) * 1000
    versions = (chains[0].count("→D→") + 1) if chains else 1
    done, git_ms = _ms(lambda: subprocess.run(["git", "log", "--oneline", "--", path],
                                              cwd=checkout, capture_output=True, text=True), runs)
    history = {"id": hid, "question": question, "palace_versions": versions,
               "palace_ms": round(trace_ms, 1), "git_commits": len(done.stdout.splitlines()),
               "git_ms": round(git_ms, 1)}
    hits = sum(1 for r in results if r.palace_rank is not None)
    rg_hits = sum(1 for r in results if r.rg_hit)
    return {"lookups": [asdict(r) for r in results], "history": history,
            "palace_hits_at_5": hits, "rg_hits": rg_hits, "n": len(results),
            "rg_files_median": statistics.median(r.rg_files for r in results),
            "palace_warm_ms_median": round(statistics.median(r.palace_warm_ms
                                                             for r in results), 1),
            "rg_ms_median": round(statistics.median(r.rg_ms for r in results), 1)}


MCP_QUERY = 'top 5 near "writer UNCHANGED check" over reference'


def mcp_once(command: list[str]) -> dict[str, float]:
    """One spawn of the MCP server: seconds to `initialize`, to the first and second `query`
    answers, and the peak resident megabytes of its process tree."""
    def call(i: int, method: str, params: dict[str, Any]) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}) + "\n"

    query: dict[str, Any] = {"name": "query", "arguments": {"sentence": MCP_QUERY}}
    steps: list[tuple[str, str, dict[str, Any]]] = [
        ("initialize", "initialize", {"protocolVersion": "2025-06-18"}),
        ("query_1", "tools/call", query), ("query_2", "tools/call", query)]
    t0 = time.perf_counter()
    p = subprocess.Popen(["/usr/bin/time", "-l", *command], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert p.stdin is not None and p.stdout is not None and p.stderr is not None
    out: dict[str, float] = {}
    for i, (name, method, params) in enumerate(steps, start=1):
        p.stdin.write(call(i, method, params))
        p.stdin.flush()
        reply = json.loads(p.stdout.readline())
        assert "result" in reply and not reply["result"].get("isError"), reply
        out[name] = time.perf_counter() - t0
    p.stdin.close()
    err = p.stderr.read()
    p.wait()
    rss = next(int(line.split()[0]) for line in err.splitlines()
               if "maximum resident set size" in line)
    out["peak_rss_mb"] = rss / 2**20
    return out


def mcp(runs: int) -> dict[str, float]:
    """The MCP server's medians over `runs` spawns, as `uv run` starts it from this checkout."""
    root = Path(__file__).resolve().parent.parent
    command = ["uv", "run", "--project", str(root), "python", str(root / "scripts" /
                                                                   "palace_mcp.py")]
    spawns = [mcp_once(command) for _ in range(runs)]
    return {k: round(statistics.median(s[k] for s in spawns), 3) for k in spawns[0]}


def table(report: dict[str, Any]) -> str:
    rows = ["| lookup | palace rank (top 5) | palace warm ms | palace cold ms | rg files | "
            "rg holds it | rg ms |", "|---|---|---|---|---|---|---|"]
    for r in report["lookups"]:
        rows.append(f"| {r['question']} | {r['palace_rank'] or 'miss'} | "
                    f"{r['palace_warm_ms']:.0f} | {r['palace_cold_ms']:.0f} | {r['rg_files']} | "
                    f"{'yes' if r['rg_hit'] else 'no'} | {r['rg_ms']:.0f} |")
    h = report["history"]
    rows.append(f"| {h['question']} | {h['palace_versions']} version(s) | {h['palace_ms']:.0f} | "
                f"| {h['git_commits']} commits (git log) | | {h['git_ms']:.0f} |")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkout", type=Path)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--mcp", action="store_true")
    args = ap.parse_args()
    if args.mcp:
        print(json.dumps(mcp(args.runs)))
        return 0
    if args.checkout is None:
        ap.error("--checkout is required for the lookups")
    report = run(args.checkout, args.runs)
    if args.out:
        args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(table(report))
    print(f"\npalace hits at 5: {report['palace_hits_at_5']}/{report['n']}; ripgrep holds the "
          f"answer: {report['rg_hits']}/{report['n']}; median files ripgrep prints: "
          f"{report['rg_files_median']}; median warm ms: palace "
          f"{report['palace_warm_ms_median']}, ripgrep {report['rg_ms_median']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
