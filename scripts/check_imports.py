#!/usr/bin/env python3
"""CLI for the static import-graph firewall lints. Wired into CI and the local gate.

Two scans, both "promote a runtime property to a static one, provable by reading the AST":

  1. **I2, the core firewall** (Invariant 2) — no module under `core/` imports a networked zone
     (edge/cloud) or a networking primitive outside the audited loopback allowlist. Rules and
     implementation live in `ops/import_lint.py`; also asserted in `tests/test_import_firewall.py`.

  2. **The worker boundary** (bp-110 Item 5, `dn-supervision-and-liveness` §2.3) — the compute
     worker's transitive import graph contains no store-opening constructor.

⚑ **The worker-boundary scan is TIER 4 on the note's enforcement ladder (§2, "ratchet: a
test/scan proves the property in CI") and this comment must not claim otherwise.** The property
it backs — "the worker cannot write a store" — is *tier 2* (capability: a worker process holds no
store object, and a compute half is handed only a `ReadOnlyRows`). This scan is the tier-4 backing
that re-derives the tier-2 claim from the AST instead of trusting a docstring. It is NOT tier 1
(the stores are files on a shared disk; nothing makes a write unrepresentable) and NOT tier 2
itself (a scan is not a capability). §2 names overclaiming a tier as the foot-gun in miniature:
"unrepresentable delivered as a tier-5 check is shooting ourselves in the foot, one level up."

Run: `python scripts/check_imports.py` (or `uv run python scripts/check_imports.py`).
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # repo root on path

from ops.import_lint import Violation, _imported_names  # noqa: E402
from ops.import_lint import main as core_firewall_main  # noqa: E402

# The worker entrypoint whose graph is scanned. `python -m scheduler.worker` (bp-110 §3 Q4): a
# DEDICATED entrypoint is what gives the worker a scoped import graph at all — under
# `multiprocessing` the worker's graph is the parent's and this scan would assert nothing.
WORKER_ENTRY = "scheduler/worker.py"

# Top-level packages we own. The walk follows only these: a third-party library cannot import our
# stores, so its graph is irrelevant, and following it would make the scan slow and noisy.
FIRST_PARTY: frozenset[str] = frozenset({
    "core", "scheduler", "ops", "config", "agents", "edge", "cloud", "eval", "scripts",
})

# Packages whose whole point is opening a durable store. A module under one of these appearing
# anywhere in the worker's graph is a violation on its own — no symbol analysis needed.
#
# Stated as PACKAGES rather than as a list of class names deliberately. A name list is exactly the
# thing that rots: the next store lands in `core/stores/` and a name list silently stops covering
# it, which is the "N ad-hoc detectors, each with its own rot" failure the note's §1.2 forbids.
# A package rule covers every store that exists today and every one added tomorrow.
FORBIDDEN_STORE_PACKAGES: tuple[str, ...] = (
    "core.stores",           # the corpus stores: vectorstore, derived, catalog, versions, …
    "core.kernel.stores",    # rawstore (the blob substrate) + sourceset
    "ops.effect_ledger",     # the Track-G durable effect ledger
    "ops.ledger",            # the propose/approve/validate gate ledger
)

# Belt and braces for a store that lives OUTSIDE those packages. `scheduler.queue.JobQueue` is the
# one that matters most: the worker imports `Job` (a frozen, stdlib-only record) from that module,
# which is safe and necessary, but importing the QUEUE WRITER would hand the worker the single-
# writer capability the whole compute/land split exists to keep in the supervisor. Name SHAPES,
# again so the rule does not rot: `core/complex/temporal.py:SnapshotStore` and
# `core/stores/runledger.py:RunLedger` are both caught without being enumerated.
FORBIDDEN_SYMBOL_EXACT: frozenset[str] = frozenset({"JobQueue", "open_store"})
FORBIDDEN_SYMBOL_SUFFIXES: tuple[str, ...] = ("Store", "Catalog", "Ledger")
FORBIDDEN_SYMBOL_PREFIXES: tuple[str, ...] = ("open_",)


def _is_forbidden_module(module: str) -> bool:
    return any(module == pkg or module.startswith(pkg + ".")
               for pkg in FORBIDDEN_STORE_PACKAGES)


def _is_forbidden_symbol(name: str) -> bool:
    if name in FORBIDDEN_SYMBOL_EXACT:
        return True
    if name.endswith(FORBIDDEN_SYMBOL_SUFFIXES):
        return True
    return name.startswith(FORBIDDEN_SYMBOL_PREFIXES) and name.endswith("store")


def _module_file(module: str, repo_root: Path) -> Path | None:
    """Resolve a dotted first-party module name to its file, or None if it is not ours.

    None also covers a first-party module with no file on disk, which is what lets a test point
    the scan at a small synthetic tree instead of reproducing the whole repo: an unresolvable
    edge is still CHECKED for forbidden-ness, it is simply not descended into.
    """
    if module.split(".", 1)[0] not in FIRST_PARTY:
        return None
    base = repo_root / Path(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _imported_symbols(tree: ast.AST) -> list[tuple[int, str, str]]:
    """(lineno, module, symbol) for every `from M import S`, at ANY nesting depth.

    ⚑ This is a second PROJECTION over the same AST, never a second walker. The graph traversal,
    the parse, the module-edge extraction (`_imported_names`) and the `Violation` record all come
    from `ops/import_lint.py` — bp-110 §2 makes writing a second import walker a DRY defect, and
    the reuse is the point of putting this rule here rather than in a new script. What that
    function cannot give us is the *bound name*: for `from core.stores.vectorstore import
    open_vector_store` it returns the MODULE, which is all the I2 firewall ever needed. The
    worker rule needs the symbol too, because `from scheduler.queue import Job` must pass while
    `from scheduler.queue import JobQueue` must fail — a distinction module granularity cannot
    draw.

    `ast.walk` (the same idiom `_imported_names` uses) descends into function bodies, so a
    FUNCTION-LOCAL import is caught exactly like a module-level one. That is not incidental:
    bp-105's raw `import psutil` was function-local and passed every gate in the repo
    (finding-0198 / bp-106 Item 4 record it as the exact hole), so a rule that only saw
    module-level imports would reproduce a hole we have already been bitten by.
    """
    out: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.extend((node.lineno, node.module, alias.name) for alias in node.names)
    return out


def scan_worker_boundary(repo_root: Path | None = None,
                         entry: str = WORKER_ENTRY) -> list[Violation]:
    """Walk the worker entrypoint's transitive first-party import graph; report store reaches.

    `repo_root`/`entry` are parameters so the rule's own falsifiers can be PLANTED against a
    synthetic tree in a test (`tests/unit/test_worker_protocol.py`) rather than by editing the
    real worker and hoping someone re-runs the scan. A ratchet nobody has watched go red is an
    assertion, not a ratchet — finding-0187's standing lesson (deleting bp-105's sweep call left
    85/85 green).
    """
    root = repo_root or REPO_ROOT
    violations: list[Violation] = []
    seen: set[str] = set()
    entry_module = entry[:-3].replace("/", ".")
    queue: list[tuple[str, Path]] = [(entry_module, root / entry)]

    while queue:
        module, path = queue.pop()
        if module in seen:
            continue
        seen.add(module)
        rel = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for lineno, imported in _imported_names(tree):          # reused walker — module edges
            if _is_forbidden_module(imported):
                violations.append(Violation(rel, lineno, imported, "worker-store-module"))
            child = _module_file(imported, root)
            if child is not None:
                queue.append((imported, child))

        for lineno, mod, symbol in _imported_symbols(tree):     # the symbol projection
            if _is_forbidden_symbol(symbol):
                violations.append(
                    Violation(rel, lineno, f"{mod}.{symbol}", "worker-store-symbol")
                )
    return violations


def main() -> int:
    rc = core_firewall_main()

    violations = scan_worker_boundary()
    if violations:
        print()
        print("Worker boundary (tier 4) VIOLATIONS — the compute worker must open no store:")
        for v in violations:
            print(f"  {v}")
        print("  The worker holds NO store handle by construction (dn-supervision-and-liveness")
        print("  §2.3). A compute half that needs to READ takes a `ReadOnlyRows` — served over")
        print("  the wire by the supervisor — never a store it opened itself.")
        return 1
    print(f"Worker boundary (tier 4): OK — `python -m {WORKER_ENTRY[:-3].replace('/', '.')}`'s "
          "import graph opens no store")
    print("  (scanned transitively; module-level AND function-local imports)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
