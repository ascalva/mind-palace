"""V4 reference inventory probe (bp-011 Item 2) — read-only, deterministic, both directions.

A PROBE, not a tool (plan §7 Item 2) — lives under docs/build-plans/bp-011/, not scripts/.
Read-only over the corpus and code (Item 2 invariant); writes only inventory.json in this
same directory. Scans docstrings (code -> corpus) and design notes/findings (corpus ->
code) for deterministic cross-reference patterns per the design note's §2.3
`references_out` typed candidates and the brainstorm's warrant capsule (Q3). Run from the
repo root: `python3 docs/build-plans/bp-011/v4_reference_scan.py`.

Precision notes baked in from the bp-011 hand-check (~30-sample, see journal for the full
table): `wikilink` scores 0% in code docstrings specifically (prose ABOUT `[[...]]`
syntax, not real links — the corpus's real wikilinks live in dialogue/logseq content, not
code comments) and `symbol-mention` scores low (~20%) on plain dotted-token regexes
(false-positive on stdlib calls, filenames with dots, and compound `path.py.symbol`
mentions that need a different pattern shape). `path-mention` and `note-citation` score
high (100% in-sample) in both directions.
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]     # docs/build-plans/bp-011/ -> repo root
OUT_PATH = Path(__file__).resolve().parent / "inventory.json"

CODE_DIRS = ["ops", "core", "agents", "eval", "scheduler", "scripts", "config"]
CORPUS_DIRS = ["docs/design-notes", "docs/findings", "docs/brainstorms"]

# --- direction (a): code -> corpus, patterns found INSIDE docstrings -------------------
RE_NOTE_CITATION = re.compile(r"docs/(?:design-notes|findings|brainstorms)/[\w.\-]+\.md")
RE_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
RE_BACKTICK_PATH = re.compile(r"`([\w./\-]+\.(?:py|md|toml|yml|yaml|sh))(:\d+)?`")

# --- direction (b): corpus -> code, patterns found INSIDE design notes/findings ---------
RE_PATH_MENTION = re.compile(r"`([\w./\-]+\.py)(:(\d+))?`")
RE_BACKTICK_SYMBOL = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)`")
# NOTE: an earlier draft also matched design-notes/*.md <-> design-notes/*.md citations
# under this label ("design-ref") -- verified ALL 129 hits were note-to-note citations
# (0 pointed at non-.md/code targets), i.e. corpus-to-corpus, not corpus-to-code. Out of
# V4's scope (code<->corpus entanglement specifically) -- dropped from the corpus_to_code
# scan entirely rather than mislabeled as a code-citing pattern (see inventory.json notes).


@dataclass
class RefEdge:
    direction: str          # code_to_corpus | corpus_to_code
    pattern: str            # note-citation | wikilink | path-mention | symbol-mention | design-ref
    source_file: str
    source_line: int
    target: str
    context: str


def iter_py_files(root: Path, dirs: list[str]):
    for d in dirs:
        base = root / d
        if not base.exists():
            continue
        yield from sorted(base.rglob("*.py"))


def iter_md_files(root: Path, dirs: list[str]):
    for d in dirs:
        base = root / d
        if not base.exists():
            continue
        yield from sorted(base.glob("*.md"))


def scan_code_to_corpus(root: Path) -> list[RefEdge]:
    """Docstrings mentioning corpus artifacts: note citations, [[wikilinks]], backticked paths."""
    edges: list[RefEdge] = []
    for f in iter_py_files(root, CODE_DIRS):
        try:
            source = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        rel = str(f.relative_to(root))

        docstrings: list[tuple[str, int]] = []
        mod_doc = ast.get_docstring(tree)
        if mod_doc:
            docstrings.append((mod_doc, 1))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docstrings.append((doc, node.lineno))

        for doc, lineno in docstrings:
            for m in RE_NOTE_CITATION.finditer(doc):
                edges.append(RefEdge("code_to_corpus", "note-citation", rel, lineno,
                                      m.group(0), doc[max(0, m.start() - 40):m.end() + 20]))
            for m in RE_WIKILINK.finditer(doc):
                edges.append(RefEdge("code_to_corpus", "wikilink", rel, lineno,
                                      m.group(1), doc[max(0, m.start() - 40):m.end() + 20]))
            for m in RE_BACKTICK_PATH.finditer(doc):
                target = m.group(1)
                edges.append(RefEdge("code_to_corpus", "path-mention", rel, lineno,
                                      target, doc[max(0, m.start() - 40):m.end() + 20]))
    return edges


def scan_corpus_to_code(root: Path) -> list[RefEdge]:
    """Design notes/findings citing code paths, path:line, or backticked dotted symbols."""
    edges: list[RefEdge] = []
    for f in iter_md_files(root, CORPUS_DIRS):
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        rel = str(f.relative_to(root))
        for i, line in enumerate(lines, start=1):
            for m in RE_PATH_MENTION.finditer(line):
                target = m.group(1) + (f":{m.group(3)}" if m.group(3) else "")
                edges.append(RefEdge("corpus_to_code", "path-mention", rel, i,
                                      target, line.strip()[:100]))
            for m in RE_BACKTICK_SYMBOL.finditer(line):
                sym = m.group(1)
                if re.search(r"\.(py|md|toml|yml|yaml|sh|json)$", sym):
                    continue
                edges.append(RefEdge("corpus_to_code", "symbol-mention", rel, i,
                                      sym, line.strip()[:100]))
    return edges


def main() -> None:
    code_edges = scan_code_to_corpus(REPO)
    corpus_edges = scan_corpus_to_code(REPO)
    all_edges = code_edges + corpus_edges

    by_pattern: dict[str, int] = {}
    for e in all_edges:
        by_pattern[e.pattern] = by_pattern.get(e.pattern, 0) + 1

    out = {
        "scanned_at": "2026-07-11",
        "code_dirs": CODE_DIRS,
        "corpus_dirs": CORPUS_DIRS,
        "counts": {
            "code_to_corpus_total": len(code_edges),
            "corpus_to_code_total": len(corpus_edges),
            "total": len(all_edges),
            "by_pattern": by_pattern,
        },
        "precision_sample": {
            "note": ("38-item stratified hand-check, seed=11 (see journal.md for the full "
                     "per-item table + verdicts); NOT re-embedded here to keep this file a "
                     "clean re-runnable probe -- the journal is the precision record of truth."),
            "overall_precision": 0.763,
            "by_pattern": {
                "code_to_corpus/note-citation": {"hits": 4, "n": 4, "precision": 1.0},
                "code_to_corpus/path-mention": {"hits": 7, "n": 7, "precision": 1.0},
                "code_to_corpus/wikilink": {"hits": 0, "n": 5, "precision": 0.0},
                "corpus_to_code/path-mention": {"hits": 17, "n": 17, "precision": 1.0},
                "corpus_to_code/symbol-mention": {"hits": 1, "n": 5, "precision": 0.2},
            },
            "judgment_call_rate": 0.132,
        },
        "verdict": "keep",
        "verdict_rationale": (
            "364 total deterministic edges over the real corpus (98 code_to_corpus, 266 "
            "corpus_to_code) -- not near-empty. Two patterns (note-citation, path-mention, "
            "both directions) score 100% precision in-sample and account for the large "
            "majority of edges; the ledger falsifier (V4, note Sec2.7 clause 3) is RULED "
            "OUT for those patterns. wikilink (0%) and symbol-mention (20%) are noise-"
            "dominated IN CODE DOCSTRINGS SPECIFICALLY and should be dropped or substantially "
            "reworked before bp-013 uses them -- this is itself useful signal (per-pattern "
            "quality, exactly what V4 asks for), not a reason to call the whole probe "
            "no-signal. Judgment-call rate 13.2% is well under the 20% stop-and-raise "
            "threshold (plan Sec10), so precision IS determinable, cleanly."
        ),
        "ranked_patterns_for_bp013": [
            {"pattern": "note-citation", "direction": "code_to_corpus", "precision": 1.0,
             "recommendation": "use as-is"},
            {"pattern": "path-mention", "direction": "corpus_to_code", "precision": 1.0,
             "recommendation": "use as-is; add basename-lookup fallback for bare filenames "
                                "(ambiguous e.g. policy.py, apply.py, _lib.py -- 3/17 sampled "
                                "needed directory-proximity context to disambiguate, all "
                                "resolvable)"},
            {"pattern": "path-mention", "direction": "code_to_corpus", "precision": 1.0,
             "recommendation": "use as-is; same bare-filename caveat as above"},
            {"pattern": "symbol-mention", "direction": "corpus_to_code", "precision": 0.2,
             "recommendation": ("rework before use: exclude stdlib-shaped dotted tokens "
                                 "(os.fsync, select.kqueue), filenames with dots mistaken "
                                 "for module.attr (python.wasm, sensor_readings.ts), and add "
                                 "a SEPARATE compound path.symbol pattern (e.g. `_lib.py."
                                 "cmd_stop_audit`) instead of forcing it through the plain "
                                 "dotted-symbol regex")},
            {"pattern": "wikilink", "direction": "code_to_corpus", "precision": 0.0,
             "recommendation": ("drop for code docstrings -- every sampled hit was prose "
                                 "describing [[...]] SYNTAX, not a real link; the corpus's "
                                 "genuine wikilinks live in dialogue/logseq content (core/"
                                 "ingest/logseq.py's own domain), not code comments")},
        ],
        "edges": [asdict(e) for e in all_edges],
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"wrote {OUT_PATH}")
    print(json.dumps(out["counts"], indent=2))
    print(json.dumps(out["verdict"], indent=2))


if __name__ == "__main__":
    main()
