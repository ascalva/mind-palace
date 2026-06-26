"""Static import-graph firewall (Invariant 2, BUILD-SPEC §3) — the promote-to-static check.

I2 ("no path Core ->* Net") is discharged here without running the system: the AST of every
core module is scanned for forbidden imports. This is strictly stronger than the runtime
egress guard (`core.sealing`) — it proves *no import path exists* rather than catching a
connect() at run time. See ops/import_lint.py for the two rules (zone non-interference,
networking-primitive allowlist).
"""

import ast
from pathlib import Path

from ops.import_lint import (
    NETWORK_ALLOWLIST,
    Violation,
    scan_core,
    scan_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_core_has_no_forbidden_imports():
    """The live invariant: core/ imports no zone (edge/cloud) and no networking primitive
    outside the audited loopback allowlist."""
    violations = scan_core(REPO_ROOT)
    assert violations == [], "I2 firewall violations:\n" + "\n".join(str(v) for v in violations)


def test_allowlist_files_exist_and_are_the_only_network_importers():
    """The allowlist is exactly the set of core files that import a networking module — no
    more (an unaudited importer would fail above), no stale entries (a dead allowlist entry
    would silently widen the exception)."""
    importers = set()
    for path in (REPO_ROOT / "core").rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        # Re-scan with the file treated as NOT allowlisted to see if it imports networking.
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.append(node.module)
        from ops.import_lint import NETWORK_MODULES, _root
        if any(_root(n) in NETWORK_MODULES for n in names):
            importers.add(rel)
    assert importers == set(NETWORK_ALLOWLIST), (
        f"network-importing core files {importers} != allowlist {set(NETWORK_ALLOWLIST)}"
    )


def test_lint_flags_a_zone_import(tmp_path):
    """Negative control: a core file importing edge/ is caught as a zone violation."""
    f = tmp_path / "core" / "bad.py"
    f.parent.mkdir(parents=True)
    f.write_text("from edge.interface import gateway\n")
    violations = scan_file(f, repo_root=tmp_path)
    assert violations == [Violation("core/bad.py", 1, "edge.interface", "zone")]


def test_lint_flags_an_unaudited_network_import(tmp_path):
    """Negative control: a non-allowlisted core file importing socket is a network violation."""
    f = tmp_path / "core" / "leak.py"
    f.parent.mkdir(parents=True)
    f.write_text("import socket\nimport urllib.request\n")
    rules = {v.rule for v in scan_file(f, repo_root=tmp_path)}
    assert rules == {"network"}
