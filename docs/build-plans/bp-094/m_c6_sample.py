"""bp-094 Item 2 — the M-C6 precision probe (F-CI6).

Opens the L2b gate IN-PROCESS ONLY, computes what each gated pattern would mint at the ledger's
HEAD, draws a seeded stratified sample per pattern, and prints every sampled edge with the
evidence a hand-check needs. A probe, not a tool (bp-011's precedent): it never writes an edge,
and `ops/code_sensor.ENABLED_L2B_PATTERNS` on disk is untouched.

For the code_to_code patterns it also runs mechanical checks that a hand-check would otherwise do
by eye, each one a way the static resolver can be wrong:
  not-defined   the target file does not bind the name at module level (a re-export)
  header-call   the call sits in the function's decorators/defaults, so it runs at definition
                time and is not a call the function makes
  shadowed      the name is bound locally in the enclosing function (params, assignments, ...)
  rebound       the source module binds the name more than once at module level
  hidden-import the only import binding the name lives in a different function
  ambiguous     imports bind the name to more than one module

    uv run python docs/build-plans/bp-094/m_c6_sample.py [--n 30] [--seed 94] [--sha SHA]
"""

from __future__ import annotations

import argparse
import ast
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import ops.code_sensor as cs  # noqa: E402
from ops.code_snapshot import list_py_blobs, read_py_blobs  # noqa: E402

PATTERNS = ("dn-slug", "finding-id", "paired-section", "inherits", "calls")
_OTHER_DOC_IDS = re.compile(r"\b(?:bp-\d{3}|oq-\d{4}|finding-\d{4}|dn-[a-z0-9-]+|[\w./-]+\.md)\b")


def pattern_of(e: Any) -> str:
    return "paired-section" if e.ref_type == "note-citation" else e.ref_type


def stratified(edges: list[Any], n: int, rng: random.Random) -> list[Any]:
    """Proportional allocation over the source's top-level directory, at least one per stratum
    while the budget lasts (largest remainder for the rest)."""
    if len(edges) <= n:
        return list(edges)
    strata: dict[str, list[Any]] = defaultdict(list)
    for e in edges:
        strata[e.source_ref.split("/")[0]].append(e)
    keys = sorted(strata, key=lambda k: (-len(strata[k]), k))
    alloc = {k: 0 for k in keys}
    for k in keys[:n]:
        alloc[k] = 1
    quota = {k: len(strata[k]) / len(edges) * n for k in keys}
    for _ in range(n - sum(alloc.values())):
        k = max((k for k in keys if alloc[k] < len(strata[k])),
                key=lambda k: (quota[k] - alloc[k], k))
        alloc[k] += 1
    out: list[Any] = []
    for k in keys:
        pool = sorted(strata[k], key=lambda e: (e.source_ref, e.source_line, e.target_ref,
                                               e.target_detail))
        out.extend(rng.sample(pool, alloc[k]))
    return out


# ── binding analysis (the mechanical half of the hand-check) ────────────────────────────────


def _targets(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Tuple | ast.List):
        return [n for elt in node.elts for n in _targets(elt)]
    if isinstance(node, ast.Starred):
        return _targets(node.value)
    return []


def scope_bindings(body: list[ast.stmt]) -> list[tuple[str, ast.AST]]:
    """Names bound by these statements in THEIR scope: nested def/class names count, their
    bodies do not; comprehensions have their own scope."""
    out: list[tuple[str, ast.AST]] = []
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            out.append((node.name, node))
            continue
        if isinstance(node, ast.Lambda | ast.ListComp | ast.SetComp | ast.DictComp
                      | ast.GeneratorExp):
            continue
        if isinstance(node, ast.Assign):
            out.extend((n, node) for t in node.targets for n in _targets(t))
        elif isinstance(node, ast.AnnAssign | ast.AugAssign) and node.value is not None:
            out.extend((n, node) for n in _targets(node.target))
        elif isinstance(node, ast.For | ast.AsyncFor):
            out.extend((n, node) for n in _targets(node.target))
        elif isinstance(node, ast.With | ast.AsyncWith):
            out.extend((n, node) for item in node.items if item.optional_vars is not None
                       for n in _targets(item.optional_vars))
        elif isinstance(node, ast.Import | ast.ImportFrom):
            out.extend(((a.asname or a.name).split(".")[0], node) for a in node.names)
        elif isinstance(node, ast.NamedExpr):
            out.extend((n, node) for n in _targets(node.target))
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.append((node.name, node))
        stack.extend(ast.iter_child_nodes(node))
    return out


def params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    a = fn.args
    names = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs]}
    names |= {x.arg for x in (a.vararg, a.kwarg) if x is not None}
    return names


def index_quals(tree: ast.Module) -> dict[str, list[tuple[ast.AST, list[ast.AST]]]]:
    """qualname → [(node, chain of enclosing def/class nodes)] — the extractor's naming."""
    out: dict[str, list[tuple[ast.AST, list[ast.AST]]]] = defaultdict(list)

    def walk(node: ast.AST, prefix: str, chain: list[ast.AST]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                qual = prefix + child.name
                out[qual].append((child, chain))
                walk(child, qual + ".", [*chain, child])
            else:
                walk(child, prefix, chain)

    walk(tree, "", [])
    return out


def _calls_named(nodes: list[ast.AST], name: str, line: int) -> bool:
    for root in nodes:
        for n in ast.walk(root):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name \
                    and n.lineno == line:
                return True
    return False


def _body_only(fn: ast.AST) -> list[ast.AST]:
    """The function's own body, minus nested def/class nodes (their calls are attributed to them
    or dropped by the extractor)."""
    keep: list[ast.AST] = []
    stack = list(getattr(fn, "body", []))
    while stack:
        node = stack.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        keep.append(node)
    return keep


def import_bindings(tree: ast.Module, name: str, src_path: str
                    ) -> list[tuple[str | None, ast.AST | None]]:
    """Every FROM-import binding `name` in the file: (resolved .py path, enclosing function or None
    for module level)."""
    out: list[tuple[str | None, ast.AST | None]] = []

    def walk(node: ast.AST, fn: ast.AST | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ImportFrom):
                for a in child.names:
                    if (a.asname or a.name) == name:
                        out.append((cs._module_to_path(child.module or "", child.level, src_path),
                                    fn))
            inner = child if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else fn
            walk(child, inner)

    walk(tree, None)
    return out


def check_code_edge(e: Any, trees: dict[str, ast.Module]) -> list[str]:
    flags: list[str] = []
    src, tgt = trees.get(e.source_ref), trees.get(e.target_ref)
    if src is None or tgt is None:
        return ["unparsed"]
    name = _name_at(e, src)
    if name is None:
        return ["no-site"]
    tgt_names = {n for n, _ in scope_bindings(tgt.body) if not isinstance(_, ast.Import
                                                                           | ast.ImportFrom)}
    if e.target_detail not in tgt_names:
        flags.append("not-defined")
    module_level = [n for n, node in scope_bindings(src.body)]
    if module_level.count(name) > 1:
        flags.append("rebound")
    sites = index_quals(src).get(e.source_detail, [])
    if e.ref_type == "calls":
        fns = [fn for fn, _ in sites]
        in_body = any(_calls_named(_body_only(fn), name, e.source_line) for fn in fns)
        in_header = any(_calls_named([*fn.decorator_list, fn.args,
                                      *([fn.returns] if fn.returns else [])],
                                     name, e.source_line)
                        for fn in fns if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef))
        if in_header and not in_body:
            flags.append("header-call")
        scopes = fns
    else:
        scopes = [c for _, chain in sites for c in chain
                  if isinstance(c, ast.FunctionDef | ast.AsyncFunctionDef)]
    for fn in scopes:
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        # A local FROM-import is a binding the resolver reads (import_records), not a shadow;
        # two imports leading to different definitions are the resolver's ambiguity drop.
        # A shadow is a NON-import local binding: a parameter, assignment, loop/with target or
        # nested def/class of the same name.
        local = params(fn) | {n for n, node in scope_bindings(fn.body)
                              if not isinstance(node, ast.ImportFrom)}
        globals_ = {g for node in ast.walk(fn) if isinstance(node, ast.Global | ast.Nonlocal)
                    for g in node.names}
        if name in local - globals_:
            flags.append("shadowed")
            break
    if e.target_ref != e.source_ref:                       # resolved through an import
        binds = import_bindings(src, name, e.source_ref)
        if len({p for p, _ in binds}) > 1:
            flags.append("ambiguous")
        enclosing = {id(fn) for fn in scopes} | {
            id(c) for _, chain in sites for c in chain}
        if binds and not any(fn is None or id(fn) in enclosing for _, fn in binds):
            flags.append("hidden-import")
    return flags


def _name_at(e: Any, src: ast.Module) -> str | None:
    """The bare name the edge was minted from (an import may alias the target's real name)."""
    for n in ast.walk(src):
        if e.ref_type == "calls" and isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.lineno == e.source_line:
            if n.func.id == e.target_detail or _aliases(src, n.func.id, e.target_detail):
                return n.func.id
        if e.ref_type == "inherits" and isinstance(n, ast.ClassDef) \
                and n.lineno == e.source_line:
            for b in n.bases:
                if isinstance(b, ast.Name) and (b.id == e.target_detail
                                                or _aliases(src, b.id, e.target_detail)):
                    return b.id
    return None


def _aliases(src: ast.Module, local: str, real: str) -> bool:
    return any(isinstance(n, ast.ImportFrom) and any(a.name == real and a.asname == local
                                                     for a in n.names)
               for n in ast.walk(src))


# ── corpus-side evidence ────────────────────────────────────────────────────────────────────


def git_show(sha: str, path: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def heading_has(note: str, anchor: str) -> bool:
    num = anchor.lstrip("§").strip()
    pat = re.compile(rf"^#{{1,6}}\s+(?:§\s?)?{re.escape(num)}(?:[.\s)—:-]|$)")
    return any(pat.match(line) for line in note.splitlines())


def snippet(doc: str, token: str, width: int = 90) -> str:
    i = doc.find(token)
    if i < 0:
        return doc[: 2 * width].replace("\n", " ")
    lo, hi = max(0, i - width), min(len(doc), i + len(token) + width)
    return ("…" if lo else "") + doc[lo:hi].replace("\n", " ") + ("…" if hi < len(doc) else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=94)
    ap.add_argument("--sha", default=None)
    ap.add_argument("--census", action="store_true",
                    help="run the mechanical checks over EVERY code_to_code edge instead")
    ap.add_argument("--examples", type=int, default=6)
    args = ap.parse_args()

    sensor = cs.build_code_sensor()
    sha = args.sha or sensor.db.execute(
        "SELECT commit_sha FROM snapshots ORDER BY committed_at DESC LIMIT 1").fetchone()[0]
    cs.ENABLED_L2B_PATTERNS = frozenset(cs.L2B_PATTERNS)   # in-process only; never written
    known = set(sensor._known_corpus_docs(sha))
    edges = sensor._shorthand_reference_edges(sha, known) + sensor._code_to_code_edges(sha)

    by: dict[str, dict[str, Any]] = {p: {} for p in PATTERNS}
    for e in edges:
        by[pattern_of(e)].setdefault(e.edge_id, e)
    print(f"HEAD {sha[:12]}  candidates: "
          + ", ".join(f"{p} {len(by[p])}" for p in PATTERNS))

    docs = {(p, q): d for p, q, d, _ in sensor._docstrings_for(sha)}
    py = list_py_blobs(sensor.repo, sha)
    blobs = read_py_blobs(sensor.repo, sorted({b for _, b in py}))
    texts = {p: blobs.get(b, "") for p, b in py}
    trees: dict[str, ast.Module] = {}
    for p, t in texts.items():
        try:
            trees[p] = ast.parse(t)
        except SyntaxError:
            pass

    if args.census:                                        # every code edge, not a sample
        for p in ("inherits", "calls"):
            flagged: dict[str, list[Any]] = defaultdict(list)
            for e in by[p].values():
                for f in check_code_edge(e, trees):
                    flagged[f].append(e)
            print(f"\n== census {p}: {len(by[p])} edges; flagged: "
                  + (", ".join(f"{f} {len(v)}" for f, v in sorted(flagged.items())) or "none"))
            for f, es in sorted(flagged.items()):
                for e in sorted(es, key=lambda e: (e.source_ref, e.source_line))[:args.examples]:
                    line = texts.get(e.source_ref, "").splitlines()[e.source_line - 1:
                                                                    e.source_line]
                    print(f"  {f}: {e.source_ref}:{e.source_line} {e.source_detail} → "
                          f"{e.target_ref}::{e.target_detail}")
                    print(f"      {line[0].strip()[:150] if line else ''}")
        return 0

    rng = random.Random(args.seed)
    for p in PATTERNS:
        sample = stratified(list(by[p].values()), args.n, rng)
        print(f"\n== {p}: sample {len(sample)} of {len(by[p])} (seed {args.seed})")
        for i, e in enumerate(sample, 1):
            where = f"{e.source_ref}:{e.source_line} {e.source_detail or '<module>'}"
            if e.target_kind == "code":
                flags = check_code_edge(e, trees)
                line = texts.get(e.source_ref, "").splitlines()[e.source_line - 1:e.source_line]
                print(f"{i:2}. {where} → {e.target_ref}::{e.target_detail}"
                      f"  [{', '.join(flags) or 'clean'}]")
                print(f"      {line[0].strip()[:150] if line else ''}")
            else:
                doc = docs.get((e.source_ref, e.source_detail), "")
                if p == "paired-section":
                    note = git_show(sha, e.target_ref)
                    others = sorted(set(_OTHER_DOC_IDS.findall(doc)))
                    head = "heading" if heading_has(note, e.target_detail) else "NO-HEADING"
                    print(f"{i:2}. {where} → {e.target_ref} {e.target_detail}  [{head}]")
                    print(f"      ids in docstring: {', '.join(others)[:200]}")
                    token = e.target_detail if e.target_detail in doc \
                        else e.target_detail.replace("§", "§ ")
                    print(f"      {snippet(doc, token, 110)}")
                else:
                    token = ("dn-" + Path(e.target_ref).stem if p == "dn-slug"
                             else Path(e.target_ref).stem)
                    print(f"{i:2}. {where} → {e.target_ref}")
                    print(f"      {snippet(doc, token)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
