"""Apply the `emergent` marker to every test collected under this directory.

Directory-level marking (test-organization.md §3): a test's *location* declares its
execution profile, so `-m emergent` selects this whole category without per-file decoration.
The path filter is load-bearing — pytest calls every conftest's
`pytest_collection_modifyitems` with the *global* item list, so we must only mark items
that actually live beneath this directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        try:
            item.path.relative_to(_HERE)
        except ValueError:
            continue  # not under this category dir — another conftest owns it
        item.add_marker(pytest.mark.emergent)
