"""The sentence shell's completion, measured: latency and coverage over the sentences the test suite
holds (papers/2026-11-08-sentence-shell). `uv run python eval/shell_completion.py`.

Coverage: every valid read sentence written as a string literal in tests/unit/test_sentence_*.py
is replayed token by token; at each token the completer is asked for the prefix before it, and
the token counts as offered when the completer offers it (a keyword, a symbol, a stratum, a note
the catalog holds) or recognizes its slot (a number, whose default it offers, a free text, whose
opening quote it offers, a path word, whose letters it offers, or a path's count). A literal
counts only when it compiles: the suite's refused sentences are not examples of the language.
Latency: the completer is called on every character prefix of the same sentences, with an empty
catalog and with one of 20,000 paths.
"""

from __future__ import annotations

import ast
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.sentence.grammar import KEYWORDS, is_request, quote, tokenize  # noqa: E402
from core.sentence.plan import compile_sentence  # noqa: E402
from scripts.shell import RELATIONS, Catalog, Completer, slot  # noqa: E402


def corpus() -> list[str]:
    out: set[str] = set()
    for path in sorted((ROOT / "tests" / "unit").glob("test_sentence_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value.strip()
                if not text or is_request(text) or "\n" in text:
                    continue
                try:
                    compile_sentence(text)          # well-formed, well-sorted, within bounds
                except Exception:  # noqa: BLE001 - a refused sentence is no example
                    continue
                if len(tokenize(text)) > 2:
                    out.add(text)
    return sorted(out)


def atoms_of(sentences: list[str]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for s in sentences:
        for t in tokenize(s):
            if t.kind == "STRING" or (t.kind == "WORD" and t.text not in KEYWORDS):
                seen[t.text] = None
    return tuple(seen)


def coverage(sentences: list[str], completer: Completer) -> dict[str, tuple[int, int]]:
    tally: dict[str, list[int]] = {}
    for s in sentences:
        for t in tokenize(s)[:-1]:
            prefix = s[:t.pos]
            cands = set(completer.sentence(prefix))
            kind = slot(prefix).kind
            if t.kind == "WORD" and t.text in KEYWORDS:
                cls, ok = "keyword", t.text in cands
            elif t.kind == "SYM":
                cls, ok = "symbol", t.text in cands
            elif kind == "path":                 # a path's letters, or the count in `{m,n}`
                cls, ok = "path", t.kind == "NUMBER" or all(ch in RELATIONS for ch in t.text)
            elif t.kind == "NUMBER":
                cls, ok = "number", kind == "number"
            elif kind == "strata":
                cls, ok = "stratum", t.text in cands
            elif kind == "string":
                cls, ok = "text", '"' in cands
            else:
                cls = "note"
                ok = (quote(t.text) if t.kind == "STRING" else t.text) in cands
            tally.setdefault(cls, [0, 0])
            tally[cls][0] += int(ok)
            tally[cls][1] += 1
    return {k: (v[0], v[1]) for k, v in sorted(tally.items())}


def latency(sentences: list[str], completer: Completer) -> list[float]:
    times = []
    for s in sentences:
        for k in range(len(s) + 1):
            t0 = time.perf_counter()
            completer.complete(s[:k])
            times.append((time.perf_counter() - t0) * 1000)
    return times


def main() -> None:
    sentences = corpus()
    print(f"sentences: {len(sentences)}, tokens: "
          f"{sum(len(tokenize(s)) - 1 for s in sentences)}")
    full = Completer(Catalog(atoms=atoms_of(sentences)))
    empty = Completer(Catalog())
    for name, c in (("catalog holding the atoms", full), ("empty catalog", empty)):
        cov = coverage(sentences, c)
        ok, n = sum(v[0] for v in cov.values()), sum(v[1] for v in cov.values())
        print(f"coverage, {name}: {ok}/{n} = {100 * ok / n:.1f}%  " +
              ", ".join(f"{k} {a}/{b}" for k, (a, b) in cov.items()))
    sizes = sorted(len(empty.sentence(s[:t.pos])) for s in sentences for t in tokenize(s)[:-1])
    print(f"candidates offered per position, empty catalog: median {statistics.median(sizes)}, "
          f"max {sizes[-1]}, out of {len(KEYWORDS) - 1} keywords")
    big = Completer(Catalog(atoms=tuple(f"notes/area{i % 97}/note{i}.md" for i in range(20_000))))
    for name, c in (("empty catalog", empty), ("20,000 paths", big)):
        latency(sentences[:5], c)                       # warm
        ts = sorted(latency(sentences, c))
        print(f"latency, {name}: n={len(ts)} median {statistics.median(ts):.2f} ms, "
              f"p95 {ts[int(0.95 * len(ts))]:.2f} ms, max {ts[-1]:.2f} ms")


if __name__ == "__main__":
    main()
