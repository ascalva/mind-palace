"""The instance root has one resolution rule, and from a checkout it is today's (packaging).

Pins: an in-checkout run resolves every root-derived path exactly as before packaging (the live
instance sees no difference); `MIND_PALACE_ROOT` names the root of an installed copy, and from a
checkout may only restate it; with neither, the refusal is plain and at use.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from core.kernel.config import REPO_ROOT, get_config
from core.kernel.config import loader as L
from core.kernel.config import root as R

CHECKOUT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())


def test_in_checkout_the_root_and_every_derived_path_are_todays() -> None:
    assert R.resolve_root({}) == CHECKOUT
    assert REPO_ROOT == CHECKOUT
    assert R.code_dir() == CHECKOUT
    assert L._DEFAULTS == CHECKOUT / "config" / "defaults.toml"
    from core.kernel.constitution import CONSTITUTION_PATH
    assert CONSTITUTION_PATH == CHECKOUT / "CONSTITUTION.md"
    from core.sentence import script
    assert script.LIBRARY == CHECKOUT / "door"
    p = get_config().paths
    assert p.data_dir == CHECKOUT / "data"
    assert p.derived_store == CHECKOUT / "data" / "derived.sqlite"
    assert p.vector_store == CHECKOUT / "data" / "vectors.lance"


def test_the_overlay_paths_are_todays_in_a_fresh_process() -> None:
    """The conftest redirects the overlays and the config dir (where a named load finds the other
    declared instances) for every test, so read them in a clean interpreter."""
    code = ("from core.kernel.config import loader as L;"
            "print(L._CONFIG_DIR, L.LEVERS_OVERLAY, L._INSTANCE_OVERLAY, L._LEGACY_OVERLAY,"
            " sep='\\n')")
    env = {k: v for k, v in os.environ.items() if k != R.ROOT_ENV}
    out = subprocess.run([sys.executable, "-c", code], cwd=CHECKOUT, env=env, check=True,
                         capture_output=True, text=True).stdout.split("\n")
    assert out[:4] == [str(CHECKOUT / "config"), *(str(CHECKOUT / "config" / n)
                       for n in ("levers.toml", "ouroboros.toml", "local.toml"))]


def test_from_an_installed_copy_the_variable_names_the_root(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(R, "code_dir", lambda: tmp_path / "site-packages")   # no checkout there
    assert R.checkout_root() is None
    assert R.resolve_root({R.ROOT_ENV: str(tmp_path)}) == tmp_path.resolve()


def test_from_a_checkout_the_variable_may_only_restate_the_checkout(tmp_path: Path) -> None:
    """The tools that name Ouroboros's state outside the config reach it by the checkout's path,
    so a checkout's root is the checkout: the variable may restate it, by any name, and no more."""
    with pytest.raises(R.RootNotFound, match="another directory than the checkout"):
        R.resolve_root({R.ROOT_ENV: str(tmp_path)})
    link = tmp_path / "link"
    link.symlink_to(CHECKOUT)
    for name in (str(CHECKOUT), str(link), str(CHECKOUT) + "/"):
        assert R.resolve_root({R.ROOT_ENV: name}) == CHECKOUT


def test_a_relative_variable_is_refused() -> None:
    """It would name a different directory for every working directory a process starts in."""
    with pytest.raises(R.RootNotFound, match="relative"):
        R.resolve_root({R.ROOT_ENV: "."})


def test_a_named_root_that_is_not_a_directory_is_refused(tmp_path: Path) -> None:
    with pytest.raises(R.RootNotFound, match="not a directory"):
        R.resolve_root({R.ROOT_ENV: str(tmp_path / "nope")})


def test_with_no_variable_and_no_checkout_the_refusal_is_plain() -> None:
    with pytest.raises(R.RootNotFound) as e:
        R.resolve_root({}, checkout=None) if False else _no_checkout()
    assert R.ROOT_ENV in str(e.value) and "installed copy" in str(e.value)


def _no_checkout() -> Path:
    orig = R.checkout_root
    R.checkout_root = lambda: None  # type: ignore[assignment]
    try:
        return R.resolve_root({})
    finally:
        R.checkout_root = orig  # type: ignore[assignment]


def test_the_unresolved_root_joins_but_refuses_at_use() -> None:
    p = R._NoRoot("/unset") / "data" / "x.sqlite"
    assert str(p).endswith("data/x.sqlite")
    with pytest.raises(R.RootNotFound):
        p.exists()
