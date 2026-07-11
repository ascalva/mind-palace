"""Type-level tests for the provenance static shadow (bp-009; type-system-as-core-audit §2.4).

The unit under test is a PROPOSITION, not a behavior: `Authored[T]` / `Derived[T]` make
accidental promotion a TYPE error, and `promote(x: Derived[T], cap: OwnerVerdict) ->
Authored[T]` is callable only from a site that actually holds the capability. So the
assertions here run mypy as a subprocess over fixture snippets and check what the CHECKER
says — a fixture that promotes without the capability must FAIL mypy; with it, PASS.

Mechanics: fixtures are written to tmp_path and checked with cwd=tmp_path plus
`--config-file` pointed at os.devnull, so the repo's `[tool.mypy]` section (whose `files`
list would drag the whole tree into every run) and any user-level config are BOTH ignored;
MYPYPATH points at the repo root so `core.provenance` resolves. Expected errors are declared
inline in each fixture as `# E: <error-code>` markers and asserted line-exactly.

Runtime behavior of core/provenance.py is asserted UNCHANGED at the bottom (the Item-10
invariant): same enum members, same MIRROR_READABLE, and the stub raises.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from core.provenance import (
    MIRROR_READABLE,
    Authored,
    Derived,
    OwnerVerdict,
    Provenance,
    promote,
)

pytest.importorskip("mypy")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_mypy(fixture: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "mypy",
            "--config-file", os.devnull,      # no repo/user config: default flags, fixture only
            "--no-error-summary",
            "--no-incremental",
            "--cache-dir", str(tmp_path / ".mypy_cache"),
            str(fixture),
        ],
        capture_output=True,
        text=True,
        cwd=fixture.parent,
        env={**os.environ, "MYPYPATH": str(REPO_ROOT)},
        check=False,
    )


def _expected_errors(source: str) -> dict[int, str]:
    """Parse `# E: <code>` markers into {line_number: error_code}."""
    out: dict[int, str] = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        if "# E:" in line:
            out[lineno] = line.split("# E:", 1)[1].strip()
    return out


def _check_fixture(tmp_path: Path, source: str) -> None:
    """Assert mypy reports EXACTLY the `# E:` marked errors — no more, no fewer."""
    fixture = tmp_path / "provenance_fixture.py"
    fixture.write_text(source)
    proc = _run_mypy(fixture, tmp_path)
    expected = _expected_errors(source)
    reported = [
        line for line in proc.stdout.splitlines() if ": error:" in line
    ]
    if not expected:
        assert proc.returncode == 0, f"expected a clean run, got:\n{proc.stdout}{proc.stderr}"
        assert reported == []
        return
    assert proc.returncode != 0, f"expected type errors, mypy was green:\n{proc.stdout}"
    assert len(reported) == len(expected), (
        f"expected exactly {len(expected)} errors {sorted(expected)}, got:\n{proc.stdout}"
    )
    for lineno, code in expected.items():
        matches = [ln for ln in reported if f"provenance_fixture.py:{lineno}:" in ln]
        assert matches, f"no error reported at line {lineno} ({code}):\n{proc.stdout}"
        assert f"[{code}]" in matches[0], (
            f"line {lineno}: expected [{code}], got: {matches[0]}"
        )


# ── The acceptance pair (plan §7 Item 10) ────────────────────────────────────────────────


def test_promotion_without_capability_is_a_type_error(tmp_path: Path) -> None:
    """Every accidental route from Derived to Authored is a mypy error: the bare `promote`
    call (no capability), a forged capability, direct assignment, and passing Derived where
    a consumer demands Authored. Payload types thread through the generic."""
    _check_fixture(tmp_path, textwrap.dedent("""\
        from core.provenance import Authored, Derived, OwnerVerdict, promote

        d: Derived[int] = Derived(1)
        cap = OwnerVerdict()

        promote(d)  # E: call-arg
        promote(d, "not a capability")  # E: arg-type
        a1: Authored[int] = d  # E: assignment
        a2: Authored[str] = promote(d, cap)  # E: arg-type

        def takes_authored(x: Authored[int]) -> None: ...

        takes_authored(d)  # E: arg-type
        takes_authored(Derived(2))  # E: arg-type
        """))


def test_promotion_with_capability_passes(tmp_path: Path) -> None:
    """The same call WITH the capability type-checks clean, and the payload type is
    preserved end to end (Derived[int] -> Authored[int] -> int)."""
    _check_fixture(tmp_path, textwrap.dedent("""\
        from core.provenance import Authored, Derived, OwnerVerdict, promote

        def rehearse(d: Derived[int], cap: OwnerVerdict) -> Authored[int]:
            return promote(d, cap)

        a: Authored[int] = rehearse(Derived(1), OwnerVerdict())
        payload: int = a.value
        """))


def test_subclass_laundering_is_a_type_error(tmp_path: Path) -> None:
    """@final closes the deliberate-inheritance hole: a class cannot subclass its way from
    Derived into Authored, and OwnerVerdict cannot be forged by subclassing either."""
    _check_fixture(tmp_path, textwrap.dedent("""\
        from core.provenance import Authored, OwnerVerdict

        class Sneaky(Authored[int]):  # E: misc
            pass

        class ForgedCap(OwnerVerdict):  # E: misc
            pass
        """))


# ── The Item-11 violation class, pinned as a permanent fixture ───────────────────────────


def test_mirror_bypass_is_a_type_error(tmp_path: Path) -> None:
    """The gap the tag closes on the real seam (bp-009 Item 11): an introspective consumer
    typed like `note_centroids` but demanding `Authored[...]` rows cannot be fed raw
    `store.all_rows()` output (which may be OBSERVED/CURATED) — the MirrorView bypass that
    no runtime check catches today becomes a mypy error at authorship time."""
    _check_fixture(tmp_path, textwrap.dedent("""\
        from typing import Any
        from collections.abc import Sequence

        from core.provenance import Authored, Derived

        Row = dict[str, Any]

        def introspective_consumer(rows: Sequence[Authored[Row]]) -> None: ...

        raw_rows: list[Row] = [{"digest": "d0", "provenance": "observed"}]
        derived_rows: list[Derived[Row]] = [Derived({"digest": "d1"})]
        mirror_rows: list[Authored[Row]] = [Authored({"digest": "d2"})]

        introspective_consumer(raw_rows)  # E: arg-type
        introspective_consumer(derived_rows)  # E: arg-type
        introspective_consumer(mirror_rows)
        """))


# ── Runtime invariants: the module's behavior is UNCHANGED (plan §7 Item 10) ─────────────


def test_enum_and_firewall_unchanged() -> None:
    assert [p.value for p in Provenance] == [
        "authored-solo", "authored-dialogue", "curated", "interpreted",
        "derived-stratum", "observed",
    ]
    assert MIRROR_READABLE == frozenset(
        {Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE}
    )


def test_promote_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="verdict-gated promotion"):
        promote(Derived(1), OwnerVerdict())


def test_tags_wrap_their_payload_and_are_frozen() -> None:
    a = Authored({"digest": "d"})
    d = Derived(42)
    assert a.value == {"digest": "d"}
    assert d.value == 42
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.value = 7  # type: ignore[misc]  # warrant: the frozen-ness IS the assertion
