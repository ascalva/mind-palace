"""bp-067 falsifiers — the config loader moved into `core.config` (finding-0103, the core-is-sacred
cleanup). These pin the three guarantees of the move: config VALUES are unchanged, `core.config` is
network-free (the security win of landing inside `import_lint`'s perimeter), and the trust boundary
held — core's `get_secret` is env-only while the outside facade stays token-capable.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from ops.import_lint import NETWORK_MODULES, scan_file

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
_CORE_CONFIG = _REPO_ROOT / "core" / "kernel" / "config"   # K1 (bp-090): config moved


def test_config_values_resolve_under_repo_root() -> None:
    """The move must not drift any config value. REPO_ROOT re-anchors to the real repo root (not
    `core/`), and the tomls (which stay in `config/`) still drive the same resolved paths."""
    from core.kernel.config import REPO_ROOT, get_config, load_config
    from core.kernel.config.loader import _DEFAULTS

    assert REPO_ROOT == _REPO_ROOT                               # re-anchored correctly (not core/)
    cfg = get_config()
    assert cfg.paths.data_dir == _REPO_ROOT / "data"            # defaults.toml data_dir="data"
    assert cfg.paths.derived_store == _REPO_ROOT / "data" / "derived.sqlite"
    assert cfg.paths.derived_store.parent == cfg.paths.data_dir
    # against the COMMITTED defaults (bypassing an owner's overlay, which may enable it):
    assert load_config(_DEFAULTS).secrets.enabled is False      # shipped-safe default preserved


def test_core_config_is_network_free() -> None:
    """The security win: `core/config/**` now falls under `import_lint`'s core ban, so config
    loading is STRUCTURALLY network-free — no file imports a networking primitive or a bad zone."""
    for py in _CORE_CONFIG.rglob("*.py"):
        violations = scan_file(py, repo_root=_REPO_ROOT)
        assert violations == [], f"{py} imports a banned module: {violations}"


def test_core_config_imports_no_first_party_sibling() -> None:
    """core.config is self-contained: nothing under it imports a first-party sibling of core
    (config/eval/ops/agents/edge/scheduler) — the whole point of moving the loader IN."""
    forbidden = {"config", "eval", "ops", "agents", "edge", "scheduler"}
    for py in _CORE_CONFIG.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots = [node.module]
            elif isinstance(node, ast.Import):
                roots = [a.name for a in node.names]
            else:
                continue
            for r in roots:
                assert r.split(".", 1)[0] not in forbidden, f"{py}:{node.lineno} {r}"


def test_core_get_secret_is_env_only() -> None:
    """The trust boundary held: core's `get_secret` is the ENV path only — no `token` parameter, and
    the module imports neither `secrets_backend` nor `hvac`, so the Vault path cannot leak in."""
    from core.kernel.config import get_secret

    params = inspect.signature(get_secret).parameters
    assert "token" not in params                                # env-only signature
    assert list(params) == ["name"]

    # No IMPORT of the network Vault wiring anywhere in the moved module (a docstring may NAME
    # build_secrets_backend in prose — an import is the leak, not a mention). AST, not substring.
    tree = ast.parse((_CORE_CONFIG / "loader.py").read_text(encoding="utf-8"))
    imported_roots = {
        (n.module.split(".", 1)[0] if isinstance(n, ast.ImportFrom) and n.module else
         (n.names[0].name.split(".", 1)[0] if isinstance(n, ast.Import) else ""))
        for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)
    }
    imported_full = {
        n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
    } | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert "config" not in imported_roots                       # no secrets_backend / config reach
    assert not any("secrets_backend" in m or "hvac" in m for m in imported_full)
    assert not (NETWORK_MODULES & imported_roots)               # no networking primitive imported


def test_outside_facade_stays_token_capable() -> None:
    """The outside `config.loader` facade preserves the FULL public surface for the ~147 non-core
    importers, including the token-capable `get_secret` (the machinery/Vault form) and the privates
    a couple of callers name."""
    import config.loader as facade

    params = inspect.signature(facade.get_secret).parameters
    assert "token" in params                                    # token-capable out here
    # the pure public API is re-exported (one source of truth — defined in core.config.loader)
    for name in ("get_config", "load_config", "Config", "REPO_ROOT", "LEVERS_OVERLAY"):
        assert hasattr(facade, name), f"facade missing {name}"


# --- bp-123: the local.toml -> ouroboros.toml migration guard ------------------------------------
#
# The per-machine overlay was renamed on 2026-07-26 (owner ruling: mind-palace is the framework,
# Ouroboros is the live instance). The rename itself is one line; the RISK is that a machine still
# holding a `local.toml` would come up on committed defaults with every owner-enabled flag off and
# σ reverted — a silent config reversion nobody would notice until behaviour drifted. So the loader
# refuses. These cases pin both refusal branches, and the invariant that a tree with NEITHER file
# (a fresh clone, CI) still loads cleanly — a guard that breaks a fresh clone is worse than the
# problem it solves.


def _isolated_config_dir(monkeypatch, tmp_path: Path):
    """Redirect every PER-MACHINE config path into `tmp_path`, and hand back the loader module.

    ⚑ The three overlay constants are derived from `_CONFIG_DIR` at IMPORT time, so patching
    `_CONFIG_DIR` alone would be a no-op — the derived constants would still point at the real
    `config/`. All four are patched, and that is what makes these cases hermetic: the guard must
    never be exercised against the owner's live overlay (plan §6/§10 — the file is gitignored,
    exists in one copy, and carries an owner ruling).

    `_DEFAULTS` is deliberately NOT redirected: the committed defaults are the baseline being
    overlaid, and every assertion here is about the overlay chain, not about the defaults.
    """
    from core.kernel.config import loader

    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")
    return loader


def test_legacy_overlay_alone_refuses_and_names_the_move(monkeypatch, tmp_path: Path) -> None:
    """Branch 1 — legacy present, current absent: the overlay would be silently ignored.

    ⚑ REFUSES, does not warn. A warning would be a false green one level down: the process comes up
    on defaults with the wrong σ and the owner learns from behaviour, not from an error. The message
    is the owner's only instruction at that moment, so it must name BOTH files and the exact `mv`.
    """
    from core.kernel.config.loader import ConfigMigrationError

    loader = _isolated_config_dir(monkeypatch, tmp_path)
    (tmp_path / "local.toml").write_text("[dreaming]\nsimilarity_threshold = 0.58\n")

    with pytest.raises(ConfigMigrationError) as excinfo:
        loader.load_config()

    message = str(excinfo.value)
    assert "local.toml" in message                    # the file the owner has
    assert "ouroboros.toml" in message                # the file the loader wants
    assert f"mv {tmp_path / 'local.toml'} {tmp_path / 'ouroboros.toml'}" in message


def test_both_overlays_present_refuses_as_ambiguous(monkeypatch, tmp_path: Path) -> None:
    """Branch 2 — both present: authority is ambiguous, so the loader must not guess a winner.

    Picking one silently is the same failure mode as branch 1 with an extra coin flip: whichever
    file lost would have its owner-authored settings discarded without a word.
    """
    from core.kernel.config.loader import ConfigMigrationError

    loader = _isolated_config_dir(monkeypatch, tmp_path)
    (tmp_path / "local.toml").write_text("[dreaming]\nsimilarity_threshold = 0.58\n")
    (tmp_path / "ouroboros.toml").write_text("[dreaming]\nsimilarity_threshold = 0.61\n")

    with pytest.raises(ConfigMigrationError) as excinfo:
        loader.load_config()

    message = str(excinfo.value)
    assert "local.toml" in message and "ouroboros.toml" in message
    assert "ambiguous" in message


def test_neither_overlay_present_loads_committed_defaults(monkeypatch, tmp_path: Path) -> None:
    """⚑ Item 1's named invariant: a tree with NEITHER file must still load cleanly.

    That is CI and every fresh clone. The guard exists for a one-time migration and must be
    completely silent on a machine that has nothing to migrate.
    """
    loader = _isolated_config_dir(monkeypatch, tmp_path)

    cfg = loader.load_config()                              # no overlay files exist in tmp_path
    assert cfg.dreaming.similarity_threshold == 0.62        # the committed default, untouched
    assert cfg.secrets.enabled is False                     # shipped-safe flags stay off


def test_renaming_the_overlay_away_refuses_instead_of_reverting(
    monkeypatch, tmp_path: Path
) -> None:
    """§7 Item 1's falsifier, run entirely against a COPY in tmp_path (never the real overlay).

    First prove the overlay is genuinely being read (σ = 0.58, the owner's retune under oq-0024),
    then put the file back under its legacy name and prove the loader REFUSES rather than quietly
    handing back σ = 0.62. If it returned 0.62 here the guard would be decorative and the silent
    reversion risk would still be live.
    """
    from core.kernel.config.loader import ConfigMigrationError

    loader = _isolated_config_dir(monkeypatch, tmp_path)
    overlay = tmp_path / "ouroboros.toml"
    overlay.write_text("[dreaming]\nsimilarity_threshold = 0.58\n")

    assert loader.load_config().dreaming.similarity_threshold == 0.58   # the overlay IS read

    overlay.rename(tmp_path / "local.toml")                 # the un-migrated machine's state
    with pytest.raises(ConfigMigrationError):
        loader.load_config()                                # refuses; does NOT return 0.62
