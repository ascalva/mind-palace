"""Where the instance's root is: the one resolution rule (packaging; stdlib only).

The root is the directory holding what an instance owns and the code does not ship: `data/`, the
per-machine overlays in `config/`, the overlays of the other instances declared on the host
(`config/instances/`), the named instances' state (`instances/<id>/`), the vault-relative paths,
the Constitution. From a checkout it is the checkout, as it always was. From an installed wheel
there is no checkout, so the root is named by `MIND_PALACE_ROOT`. One rule, in this order:

    1. `MIND_PALACE_ROOT`, when set: an absolute path to an existing directory, which from a
       checkout must be that checkout (the same directory, by `os.path.samefile`);
    2. the checkout this code is running from, when it is one;
    3. otherwise refuse, in plain words, at the first use of a path under the root.

Refusal is at use, not at import, so `import core` works anywhere: a consumer that reads only the
ledger needs no root. `REPO_ROOT` is then a `Path` whose every filesystem use raises
`RootNotFound`, so a stray join cannot quietly land in the working directory.

The committed defaults (`config/defaults.toml`, `config/tuning.toml`) and the sentence library
(`door/`) ship inside the wheel beside the code, so they are found from `code_dir()` whether or not
a root is set. Only the instance's own state moves with the root.

Instance identity (DI-2, `core/kernel/config/loader.py`) composes below the root. The root says
where a host's instances live; an instance's id says which of them a process is; every namespace
derives from the pair. Ouroboros, the default chain, holds the root itself, so from a checkout its
paths are exactly what they were. A named instance holds `<root>/instances/<id>`, and the loader's
checks (no namespace shared, locations compared by real path, a root linked into another's state
refused) run against the instances declared under the same root. Where the two rules could
disagree, the stricter holds: from a checkout the variable may only restate the checkout, because
the tools that name Ouroboros's state outside the config reach it by the checkout's path
(`ouroboros_only`); those tools refuse in an installed copy, which has no checkout; and a relative
variable is refused, because it would name a different directory for each working directory.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import NoReturn

ROOT_ENV = "MIND_PALACE_ROOT"


class RootNotFound(RuntimeError):
    """No usable instance root: `MIND_PALACE_ROOT` is unset and this is not a checkout, or the
    variable is relative, names no directory, or names another directory than the checkout."""


def code_dir() -> Path:
    """The directory holding the packages and the shipped `config/` and `door/`: the checkout
    root from a checkout, `site-packages` from a wheel. `core/kernel/config/root.py` is 3 deep."""
    return Path(__file__).resolve().parents[3]


def checkout_root() -> Path | None:
    """The checkout this code runs from, or None when it is an installed copy."""
    here = code_dir()
    return here if (here / "pyproject.toml").is_file() and (here / "core" / "kernel").is_dir() \
        else None


def resolve_root(env: Mapping[str, str] | None = None, *, checkout: Path | None = None) -> Path:
    """The instance root by the rule above. `checkout` defaults to `checkout_root()`."""
    named = (os.environ if env is None else env).get(ROOT_ENV, "").strip()
    found = checkout_root() if checkout is None else checkout
    if named:
        given = Path(named).expanduser()
        if not given.is_absolute():
            raise RootNotFound(
                f"{ROOT_ENV}={named!r} is relative, so it would name a different directory for "
                f"each working directory. Give the root as an absolute path.")
        p = given.resolve()
        if not p.is_dir():
            raise RootNotFound(f"{ROOT_ENV}={named!r} is not a directory")
        if found is None:
            return p
        if not os.path.samefile(p, found):
            raise RootNotFound(
                f"{ROOT_ENV}={named!r} names another directory than the checkout this code runs "
                f"from, {found}. A checkout's root is the checkout: the tools that reach "
                f"Ouroboros's state by the checkout's path would act on it while the configuration "
                f"acted on {p}. Unset {ROOT_ENV} here, or run an installed copy.")
        return found
    if found is not None:
        return found
    raise RootNotFound(
        f"mind-palace has no instance root: this is an installed copy, not a checkout, and "
        f"{ROOT_ENV} is not set. Set {ROOT_ENV} to the directory holding the instance's data/ "
        f"and config/ overlays."
    )


class _NoRoot(Path):
    """The `REPO_ROOT` when the rule has no root (an installed copy with no variable, or a variable
    the rule refuses): it joins like a path and refuses at any filesystem use. Reading `str()` of
    it is allowed (messages), opening or testing is not."""

    def __fspath__(self) -> NoReturn:
        resolve_root()      # raises the full message while the rule still has no answer
        raise RootNotFound(f"{ROOT_ENV} was set after import; restart to use {str(self)!r}")


def _module_root() -> Path:
    try:
        return resolve_root()
    except RootNotFound:
        return _NoRoot("/mind-palace-root-unset")


REPO_ROOT: Path = _module_root()
