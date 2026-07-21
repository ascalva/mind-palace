"""The inner-ring ratchet — born green (dn-inner-outer-core §2.4-B).

Recomputes the strict-v2 inner-ring fixed point over ``core/**`` at test time and forces the
declared map (``core.rings.INNER``) to equal it. The inner ring is the maximal import-closed subset
of ``core/**`` over the admissible base

    (stdlib ∖ ops.import_lint.NETWORK_MODULES ∖ core.rings.PLUMBING_STDLIB) ∪ core.rings.MATH_3P

under STRICT closure semantics: importing ``core.a.b`` executes ``core/a/__init__.py`` and
``core/__init__.py``, so a module also depends on every ancestor package of everything it imports
(§2.3). ``core/__init__.py`` is import-free, so the fixed point does not collapse — verified here.

**A deliberate, named DRY exception (§2.4-B).** The AST-scanning pattern below is a *second,
independent copy* of the outer scanner in ``tests/unit/test_core_self_containment.py`` — which
pillar 2 pins UNCHANGED — extended with relative-import resolution + third-party classification +
closure iteration. It is NOT refactored into a shared helper: two independent scanners cross-check
each other (a bug in one cannot silently blind both — the redundant-sensor argument). The audited
``NETWORK_MODULES`` constant *is* reused (one home for "network-capable"); the ~30-line scanner is
intentionally not. The fixed-point computation lives IN this module (P4: not extracted to ``ops/``
until a second consumer exists).

**Falsifier F6 (§2.7):** if ``test_inner_ring_is_the_computed_fixed_point`` lands red, the MAP is
stale (computed at an older tree), never the test — recompute at HEAD and edit ``core.rings.INNER``
to match; never hand-edit the map toward green. **Falsifier F4 (§2.4):** an inner→outer import
observed with assertion 1 green means the scanner lies — the direction-law tooth (assertion 2) and
the honesty guard (assertion 3) exist to catch that; extend them, never relax.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from core.rings import INNER, MATH_3P, PLUMBING_STDLIB
from ops.import_lint import NETWORK_MODULES

# Repo root: walk up from this file until the marker that anchors the tree (robust to the test being
# moved between category dirs — mirrors the outer scanner's marker walk, does not hard-code depth).
_HERE = Path(__file__).resolve()
_REPO_ROOT = next(p for p in _HERE.parents if (p / "pyproject.toml").exists())
_CORE = _REPO_ROOT / "core"


def _module_name(path: Path) -> str:
    """``core/complex/hodge.py`` → ``core.complex.hodge``; ``core/__init__.py`` → ``core``."""
    parts = list(path.relative_to(_REPO_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _package_of(name: str, path: Path) -> str:
    """The package a module lives in, for relative-import resolution.

    A package (``__init__.py``) is its own package context; a plain module's package is its parent.
    """
    if path.name == "__init__.py":
        return name
    return name.rsplit(".", 1)[0] if "." in name else name


def _proper_ancestors(name: str) -> list[str]:
    """Every ancestor package module of a dotted name: ``core.a.b`` → ``[core, core.a]``."""
    parts = name.split(".")
    return [".".join(parts[:i]) for i in range(1, len(parts))]


def _admissible_root(root: str) -> bool:
    """Is a non-core import root inside the admissible base?

    stdlib minus the audited network set minus the plumbing subtraction, plus the pinned pure-math
    third-party libs. Everything else (other third-party, sqlite3, any NETWORK_MODULE) is
    inadmissible and makes its importer outer.
    """
    if root in MATH_3P:
        return True
    return (
        root in sys.stdlib_module_names
        and root not in NETWORK_MODULES
        and root not in PLUMBING_STDLIB
    )


def _scan() -> tuple[frozenset[str], dict[str, bool], dict[str, frozenset[str]]]:
    """Scan ``core/**`` → (all core module names, direct-inadmissible flag, direct core deps).

    ``direct_core_deps[m]`` is the set of core modules ``m`` strictly pulls in: every core module it
    imports (relative imports resolved; ``from core.pkg import sub`` resolved to the submodule when
    it exists), plus every ancestor package of ``m`` and of each such import (strict semantics).
    ``direct_inadmissible[m]`` is True iff ``m`` directly imports an inadmissible non-core root.
    ``ast.walk`` sees lazy in-function and ``TYPE_CHECKING`` imports — both count, per §2.1.
    """
    modules: dict[str, Path] = {
        _module_name(p): p for p in sorted(_CORE.rglob("*.py"))
    }
    known = frozenset(modules)
    direct_inadmissible: dict[str, bool] = {}
    direct_core_deps: dict[str, frozenset[str]] = {}

    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        pkg = _package_of(name, path)
        bad = False
        cdeps: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] == "core":
                        cdeps.add(alias.name)
                    elif not _admissible_root(alias.name.split(".", 1)[0]):
                        bad = True
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    base = node.module or ""
                else:  # resolve a relative import to its absolute base module
                    anc = pkg.split(".")
                    cut = len(anc) - (node.level - 1)
                    parts = anc[:cut] if cut > 0 else []
                    if node.module:
                        parts = parts + node.module.split(".")
                    base = ".".join(parts)
                if not base:
                    continue
                if base.split(".", 1)[0] == "core":
                    cdeps.add(base)
                    for alias in node.names:  # resolve `from core.pkg import sub` to a submodule
                        cand = f"{base}.{alias.name}"
                        if cand in modules:
                            cdeps.add(cand)
                elif not _admissible_root(base.split(".", 1)[0]):
                    bad = True

        # Strict semantics: add ancestor packages of the module and of every core import.
        full: set[str] = set(cdeps)
        for d in cdeps:
            full.update(_proper_ancestors(d))
        full.update(_proper_ancestors(name))
        full.discard(name)
        direct_inadmissible[name] = bad
        direct_core_deps[name] = frozenset(d for d in full if d in known)

    return known, direct_inadmissible, direct_core_deps


def _fixed_point() -> frozenset[str]:
    """The maximal import-closed subset: iteratively drop any module that is directly inadmissible
    or reaches a dropped module, until stable."""
    known, bad, deps = _scan()
    inner = set(known)
    changed = True
    while changed:
        changed = False
        for m in list(inner):
            if bad[m] or not deps[m] <= inner:
                inner.discard(m)
                changed = True
    return frozenset(inner)


def test_core_init_is_import_free() -> None:
    """Strict-semantics precondition (§2.3): a single impure import in ``core/__init__.py`` would
    make ``core`` outer and collapse the fixed point to near-empty. Guarded structurally here."""
    tree = ast.parse((_CORE / "__init__.py").read_text(encoding="utf-8"))
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert imports == [], (
        "core/__init__.py must stay import-free — an impure import there collapses the strict "
        "inner-ring fixed point (a real regression, not a test bug)."
    )


def test_inner_ring_is_the_computed_fixed_point() -> None:
    """Assertion 1 (§2.4-B1): computed == declared, BOTH directions.

    A new inadmissible import in an inner module drops it from the computed set → red until the map
    is edited (a demotion). A module that becomes pure enters the computed set → red until the map
    adds it (a promotion). Every membership change is thereby forced to be an explicit
    ``core/rings.py`` diff. If this lands red, the MAP is stale — recompute, never edit toward
    green (falsifier F6).
    """
    computed = _fixed_point()
    missing = computed - INNER   # computed inner, not declared → an un-recorded promotion
    extra = INNER - computed     # declared inner, not computed → a stale/over-claimed member
    assert not missing, (
        "modules compute INNER but are absent from core.rings.INNER (add them — a promotion is an "
        f"explicit map diff): {sorted(missing)}"
    )
    assert not extra, (
        "modules are declared in core.rings.INNER but no longer compute inner (stale map — "
        f"recompute at HEAD, never hand-edit toward green, F6): {sorted(extra)}"
    )
    assert computed == INNER


def test_outer_never_imported_by_inner() -> None:
    """Assertion 2 (§2.4-B2): the direction law, asserted per member with its own message.

    An inner module may reach only inner ∪ admissible-base — never an outer core module. This is a
    corollary of assertion 1 (an import-closed set cannot reach its complement), but it gets its own
    named tooth so a scanner regression cannot silently retire it (falsifier F4).
    """
    _, _, deps = _scan()
    computed = _fixed_point()
    for member in sorted(computed):
        reach_out = deps[member] - computed
        assert not reach_out, (
            f"inner module {member!r} imports outer core module(s) {sorted(reach_out)} — the "
            "direction law (outer never imported by inner) is violated; scanner or map lies."
        )


def test_scanner_sees_known_impurities() -> None:
    """Assertion 3 (§2.4-B3): the honesty guard — a scanner that stopped parsing cannot fake a green
    ring. The computed EXCLUSIONS must include known-outer modules for their known reasons, and the
    computed set must be non-trivially large.
    """
    known, _, _ = _scan()
    computed = _fixed_point()
    excluded = known - computed

    known_impure = {
        "core.sealing",              # socket (network stdlib — NETWORK_ALLOWLIST)
        "core.stores.chatlog",       # sqlite3 (the v2 plumbing subtraction)
        "core.stores.vectorstore",   # pyarrow (non-pure third-party)
        "core.temporal.spine",       # eval (a finding-0103 sibling violation) + sqlite stores
        "core.complex.spectral",     # sknetwork (shimmed third-party)
    }
    assert known_impure <= known, (
        "the honesty guard names modules that no longer exist under core/ — re-ground the guard "
        f"against HEAD: {sorted(known_impure - known)}"
    )
    assert known_impure <= excluded, (
        "known-impure modules computed INNER — the scanner is under-counting impurities (F4); do "
        f"NOT relax the guard: {sorted(known_impure - excluded)}"
    )
    # Non-trivially large: a scanner that stopped parsing would collapse the ring toward empty.
    assert len(computed) >= 20, (
        f"computed inner ring implausibly small ({len(computed)}) — scanner broken?"
    )
