"""Ephemeral local-store builders for tests — real stores, throwaway paths, no network.

Each builder takes a tmp directory and returns a freshly-initialized store. These are the
"real local stores" of the integration/metamorphic/adversarial profiles: actual SQLite /
content-addressed files on disk, just rooted somewhere disposable.
"""

from __future__ import annotations

from pathlib import Path

from core.stores.derived import DerivedStore
from core.stores.rawstore import RawStore


def raw_store(tmp_path: Path) -> RawStore:
    """A content-addressed raw store under ``tmp_path/raw``."""
    return RawStore(tmp_path / "raw")


def derived_store(tmp_path: Path) -> DerivedStore:
    """An INTERPRETED-only derived store under ``tmp_path/derived.sqlite``."""
    return DerivedStore(tmp_path / "derived.sqlite")
