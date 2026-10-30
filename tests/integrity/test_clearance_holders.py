"""Who may mint clearances and hold the deliberate grants (dn-vector-membership-store A3.4) —
integrity tier.

Owner ruling 2026-10-29: "accessible records without the correct permission should be
unrepresentable". In Python, "only an authority can mint" is object-capability discipline made
mechanical: the private mint and the deliberate grants live in `core.kernel.clearance`, and THIS
test pins every non-test module that imports them — both directions, so a new holder is a red
test (add it here with its reason, in a reviewable diff) and a stale entry is a red test too.

`MIRROR_READ` (the safest read), the types and `narrow_*` are free to import. Tests are the
verifier and may mint anything (`tests/fixtures/clearances.py`). The negative control proves the
scanner sees both spellings: `from core.kernel.clearance import X` and attribute access through
an imported module.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = "core.kernel.clearance"
ROOTS = ("core", "agents", "edge", "ops", "scripts", "eval", "scheduler", "config", "bin")
RESTRICTED = frozenset({"_mint", "_MINT", "_Mint", "clearance_of", "MAINTENANCE_READ",
                        "CODE_READ", "CURATED_READ", "DIALOGUE_READ", "OBSERVED_READ"})

#: name -> {module path: why it holds that authority}
HOLDERS: dict[str, dict[str, str]] = {
    "_MINT": {
        "core/stores/plane.py": "mints the occupancies, hits and rows it holds",
        "core/stores/vectorstore.py": "mints rows for the physical (code / pre-plane) records",
        "core/stores/chatlog.py": "mints its observed rows",
        "core/stores/code_observations.py": "mints its observed rows",
        "core/stores/agent_observations.py": "mints its observed rows",
    },
    "_Mint": {},                         # the token's type: nothing outside the kernel names it
    "_mint": {
        "eval/harness/code_retrieval.py": "the measurement harness reads the class set a "
                                          "battery names (eval is a verifier, like tests)",
    },
    "clearance_of": {
        "core/query.py": "mints from an ADMITTED sentence's required scope — admission is the "
                         "permission",
        "core/dreaming/evaluate.py": "mints from the grant `force` has just checked",
    },
    "MAINTENANCE_READ": {
        "core/curator/curator.py": "prune: orphaned derived weight is dead in every class",
        "core/ingest/index.py": "the Item-1c re-key reads and rewrites every row",
        "core/stores/vectorstore.py": "`count()` totals the plane's occupancies",
        "core/temporal/spine.py": "the structural spine walks every store's chains",
        "eval/embedder_bench.py": "re-embeds the whole corpus to compare models",
        "eval/storage_census.py": "the storage census measures every stratum",
        "ops/plane_migrate.py": "the A3 migration converts and verifies every row",
        "scripts/migrate_provenance_split.py": "the §1 relabel migration counts every row",
    },
    "CODE_READ": {
        "core/stores/memberships.py": "the code lane's own atom repair and drift ratchet",
        "eval/harness/code_retrieval.py": "the code-retrieval battery reads the code lane",
        "ops/code_rebuild.py": "the code rebuild's seed and baseline read the code lane",
    },
    "CURATED_READ": {
        "agents/ambassador/agent.py": "the EXPLAIN intent answers from the curated corpus",
        "agents/ambassador/mcp.py": "palace_read of a `reference:` paper",
        "core/research/curate.py": "the manifest check that an embedded paper is stored",
        "scripts/curate_local.py": "the paper importer dedupes against stored digests",
    },
    "DIALOGUE_READ": {},
    "OBSERVED_READ": {},
}


def _holders(root: Path, roots: tuple[str, ...] = ROOTS) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {name: set() for name in RESTRICTED}
    for top in roots:
        for path in sorted((root / top).rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            if rel == "core/kernel/clearance.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            aliases: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == MODULE:
                    for a in node.names:
                        if a.name in RESTRICTED:
                            found[a.name].add(rel)
                elif isinstance(node, ast.ImportFrom) and node.module == "core.kernel":
                    aliases |= {a.asname or a.name for a in node.names if a.name == "clearance"}
                elif isinstance(node, ast.Import):
                    aliases |= {a.asname or a.name for a in node.names if a.name == MODULE}
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id in aliases and node.attr in RESTRICTED):
                    found[node.attr].add(rel)
    return found


def test_every_holder_of_a_restricted_authority_is_pinned_with_its_reason() -> None:
    found = _holders(REPO_ROOT)
    unlisted = {name: sorted(paths - set(HOLDERS[name])) for name, paths in found.items()
                if paths - set(HOLDERS[name])}
    assert unlisted == {}, (
        "a module took a clearance authority it is not pinned to hold — route the read through "
        f"an existing holder, or add it to HOLDERS with its reason: {unlisted}")


def test_no_stale_holder_widens_the_allowlist() -> None:
    found = _holders(REPO_ROOT)
    stale = {name: sorted(set(allowed) - found[name]) for name, allowed in HOLDERS.items()
             if set(allowed) - found[name]}
    assert stale == {}, f"pinned holders that no longer hold the authority — remove them: {stale}"


def test_negative_control_the_scanner_sees_both_spellings(tmp_path: Path) -> None:
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / "a.py").write_text(
        "from core.kernel.clearance import MAINTENANCE_READ, MIRROR_READ\n")
    (tmp_path / "ops" / "b.py").write_text(
        "from core.kernel import clearance as cl\nx = cl._mint({'observed'}, 'sneaky')\n")
    (tmp_path / "ops" / "c.py").write_text("from core.kernel.clearance import MIRROR_READ\n")
    found = _holders(tmp_path, roots=("ops",))
    assert found["MAINTENANCE_READ"] == {"ops/a.py"}
    assert found["_mint"] == {"ops/b.py"}
    assert all("ops/c.py" not in paths for paths in found.values())
