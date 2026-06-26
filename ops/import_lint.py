"""Static import-graph firewall lint (Invariant 2, BUILD-SPEC §3).

I2 is a property of the *import closure*: if no module under `core/` can reach a
network-capable module, then **no egress path exists regardless of edge behavior** —
composition cannot create one. The Phase-0 runtime egress guard (`core.sealing`) enforces
this at run time; this lint promotes it to the **static** tier — provable without running,
by reading the AST. It is the discharge the formal-properties catalog asks for (I2:
"promote from runtime to static").

Two rules, of different strength:

  1. **Zone non-interference (hard, zero exceptions).** No `core/` module may import
     `edge` (Zone B) or `cloud` (Zone C). This is the load-bearing structural fact: the
     sealed core cannot even *name* the networked zones, so there is no `core → edge → net`
     path to create. There is no audited exception and there never should be — core↔edge is
     a filesystem handoff, never an import (CONVENTIONS).

  2. **Networking primitives (allowlisted).** No `core/` module may import a networking
     module (`socket`, `ssl`, `http`, `urllib`, `requests`, …) EXCEPT the two audited
     loopback/seal modules:
       * `core/sealing.py` — imports `socket` precisely to WRAP and seal it (the guard).
       * `core/models/ollama_client.py` — the single sanctioned loopback IPC channel to the
         local Ollama server (127.0.0.1), which the egress guard permits.
     Every *other* core module is thereby statically proven free of networking imports. We
     state this honestly: the guarantee is "exactly these two audited files touch networking
     primitives, both loopback-only", not "no core file imports http" — overclaiming the
     latter would be dishonest (the Ollama channel is real).

Run: `python -m ops.import_lint` (or `scripts/check_imports.py`); also asserted in
`tests/test_import_firewall.py` and wired into CI.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

# Zone packages the core may never import (hard rule, no exceptions).
FORBIDDEN_ZONES: frozenset[str] = frozenset({"edge", "cloud"})

# Networking-capable top-level modules. Importing any of these is egress-capable, so it is
# forbidden in core outside the audited allowlist below. (stdlib + the usual 3rd-party set.)
NETWORK_MODULES: frozenset[str] = frozenset({
    "socket", "ssl", "http", "urllib", "ftplib", "smtplib", "poplib", "imaplib",
    "nntplib", "telnetlib", "socketserver", "xmlrpc", "asyncore", "asynchat",
    "requests", "httpx", "aiohttp", "urllib3", "websockets", "websocket",
    "boto3", "botocore", "paramiko", "pycurl", "grpc",
})

# The ONLY core modules permitted to import a networking primitive (audited, loopback-only).
# Paths are relative to the repo root, POSIX-style.
NETWORK_ALLOWLIST: frozenset[str] = frozenset({
    "core/sealing.py",                 # wraps socket to seal it
    "core/models/ollama_client.py",    # loopback Ollama IPC channel (127.0.0.1)
})


@dataclass(frozen=True)
class Violation:
    path: str        # repo-relative module path
    lineno: int
    imported: str    # the offending imported name
    rule: str        # "zone" | "network"

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno}: imports {self.imported!r} ({self.rule} firewall)"


def _root(module: str) -> str:
    """Top-level package of a dotted module name (`urllib.request` -> `urllib`)."""
    return module.split(".", 1)[0]


def _imported_names(tree: ast.AST) -> list[tuple[int, str]]:
    """Every imported dotted name in a module, with its line number. Relative imports
    (`from . import x`) stay inside the file's own package and cannot name a sibling
    top-level zone, so they are not network/zone risks; we record absolute imports only."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.lineno, node.module))
    return out


def scan_file(path: Path, *, repo_root: Path) -> list[Violation]:
    rel = path.relative_to(repo_root).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    allow_network = rel in NETWORK_ALLOWLIST
    violations: list[Violation] = []
    for lineno, name in _imported_names(tree):
        root = _root(name)
        if root in FORBIDDEN_ZONES:
            violations.append(Violation(rel, lineno, name, "zone"))
        elif root in NETWORK_MODULES and not allow_network:
            violations.append(Violation(rel, lineno, name, "network"))
    return violations


def scan_core(repo_root: Path | None = None) -> list[Violation]:
    """Scan every module under `core/` for forbidden imports (I2)."""
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    core = repo_root / "core"
    violations: list[Violation] = []
    for path in sorted(core.rglob("*.py")):
        violations.extend(scan_file(path, repo_root=repo_root))
    return violations


def main() -> int:
    violations = scan_core()
    if violations:
        print("Import firewall (I2) VIOLATIONS — sealed core must not reach the network:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("Import firewall (I2): OK — core imports no zone (edge/cloud) or networking module")
    print("  (audited loopback exceptions: " + ", ".join(sorted(NETWORK_ALLOWLIST)) + ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
