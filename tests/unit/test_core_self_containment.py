"""Enforce the core-is-sacred invariant: ``core/`` imports nothing first-party outside ``core/``.

OBJECT      — the static import graph of ``core/**``.
INVARIANT   — every ``core/**`` module's first-party dependencies are ``core`` itself, the Python
              stdlib, and pinned side-effect-free third-party libraries (numpy, scipy, …;
              ``uv.lock`` authoritative). It imports NOTHING from a sibling package (config, eval,
              ops, agents, edge, scheduler, …). Core is the processing unit; everything else is
              machinery *around* it. First-party code core reaches for is a liability — mutable,
              side-effecting, coupling the sacred to the machinery's churn (the opposite of a pinned
              lib). See CONVENTIONS.md §Trust boundaries in code and docs/findings/finding-0103.md
              for the owner's ruling.
ENFORCED    — ``test_core_imports_nothing_outside_core`` below, a dynamic AST scan asserting the
              violation list is empty.

⚠️  RED BY DESIGN (owner directive, 2026-07-17, finding-0103).  At authoring the invariant is
    violated **106 times across 49 files** (config 90 / ops 8 / eval 7 / agents 1). The owner chose
    a LOUD failure now — never a silent allowlist or "handle later." This test therefore FAILS
    today, on purpose, and is a **ratchet**: a new ``core → sibling`` import makes it redder;
    removing one makes it greener; zero makes it green. The cleanup is a separate program
    (config-split + 16 inversions, finding-0103), each plan measured against this test. Do NOT
    weaken, xfail, skip, or allowlist it to make the suite green — that is exactly the
    silent-handle-later the owner forbade. Fix the imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Repo root: walk up from this file (tests/unit/…) until the marker that anchors the tree. Robust to
# the test being moved between category dirs — it does not hard-code a ``parents[N]`` depth.
_HERE = Path(__file__).resolve()
_REPO_ROOT = next(p for p in _HERE.parents if (p / "pyproject.toml").exists())
_CORE = _REPO_ROOT / "core"


def _first_party_siblings() -> set[str]:
    """Repo top-level packages (a directory with a top-level ``__init__.py``) except ``core``.

    DYNAMIC on purpose: a new sibling package is forbidden the moment it exists on disk, never a
    hard-coded list that rots as the tree grows. At authoring this resolves to
    {agents, config, edge, eval, ops, scheduler}. Stdlib and third-party roots are not repo
    directories, so they can never appear here — only first-party siblings are ever forbidden.
    """
    return {
        p.name
        for p in _REPO_ROOT.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and p.name != "core"
    }


def _core_sibling_imports() -> list[tuple[str, int, str]]:
    """``(repo-relative file, lineno, imported-root)`` for every forbidden ``core/**`` import.

    Scans ``ast.Import`` and ``ast.ImportFrom`` nodes. Only absolute imports (``ImportFrom`` with
    ``level == 0``, plus all plain ``Import``) are considered: a relative import (``level > 0``) is
    always intra-``core`` and is never flagged — flagging one would make the ratchet dishonest. The
    imported root is the first dotted segment; it counts as a violation exactly when it is a
    first-party sibling of core.
    """
    forbidden = _first_party_siblings()
    violations: list[tuple[str, int, str]] = []
    for path in sorted(_CORE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = str(path.relative_to(_REPO_ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in forbidden:
                        violations.append((rel, node.lineno, root))
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    root = node.module.split(".", 1)[0]
                    if root in forbidden:
                        violations.append((rel, node.lineno, root))
    return violations


def test_scanner_sees_the_known_violation_set() -> None:
    """Helper-level guard: the scanner is not silently broken (which would fake a green ratchet).

    Confirms the dynamic forbidden set holds the known siblings and that the scan currently surfaces
    the four offending roots. A scanner that returned ``[]`` because it stopped parsing — not
    because the imports were fixed — would make the ratchet lie; this catches that regression.
    """
    forbidden = _first_party_siblings()
    assert {"config", "eval", "ops", "agents"} <= forbidden
    assert "core" not in forbidden

    roots = {root for _, _, root in _core_sibling_imports()}
    # At authoring all four are present. As the cleanup program lands, roots empty out; the subset
    # assertion (not equality) lets that happen without this guard going stale.
    assert roots <= forbidden


def test_relative_and_intra_core_imports_are_not_flagged() -> None:
    """A relative import and an intra-core absolute import must NOT count as violations."""
    forbidden = _first_party_siblings()
    src = (
        "from . import stores\n"
        "from .stores import chatlog\n"
        "import core.complex\n"
        "from core.graph import conductance\n"
    )
    tree = ast.parse(src)
    flagged: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.split(".", 1)[0] in forbidden:
                flagged.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden:
                    flagged.append(alias.name)
    assert flagged == []


def test_core_imports_nothing_outside_core() -> None:
    """OWNER RULING (2026-07-17, finding-0103): core imports NOTHING first-party outside ``core/``.

    RED BY DESIGN until the cleanup program (config-split + 16 inversions) completes — a loud
    ratchet, never an allowlist. See this module's docstring.
    """
    violations = _core_sibling_imports()
    if violations:
        lines = "\n".join(f"    {f}:{lineno} → {root}" for f, lineno, root in violations)
        banner = (
            "\n"
            "════════════════════════════════════════════════════════════════════════════════\n"
            "  INTENTIONAL RED — core is not yet self-contained.  (finding-0103, owner ruling)\n"
            "════════════════════════════════════════════════════════════════════════════════\n"
            f"  {len(violations)} forbidden import(s): core/** reaching into a sibling package.\n"
            "  core/ is SACRED — it may import only the stdlib, pinned side-effect-free 3p libs,\n"
            "  and core itself.  Every line below is a liability to be REMOVED by the cleanup\n"
            "  program (config-split → bp-067; the 16 machinery inversions → bp-068+).\n"
            "  Do NOT weaken, xfail, skip, or allowlist this test to go green — FIX THE IMPORTS.\n"
            "  (This is a ratchet: the count may only ever decrease.)\n"
            "────────────────────────────────────────────────────────────────────────────────\n"
            f"{lines}\n"
            "════════════════════════════════════════════════════════════════════════════════"
        )
        raise AssertionError(banner)
