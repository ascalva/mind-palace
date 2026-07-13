"""The interpreter-version ratchet (bp-018 Item 1; dn-self-sensing §3.2 V2, plan §6(a)).

Every interpreter over the repo instrument declares a semantic version (its worldview
coordinate) AND pins the sha256 of its source files here. The ratchet (the
argless-mypy==69 pattern): change the interpreter source and this suite reds until you
EITHER bump the version and pin the new pair (a worldview change — re-projection will
supersede; run `backfill_observations()`) OR re-pin the hash at the same version (a
declared refactor — no worldview change, no re-projection). Both are reviewed,
deliberate acts — an unbumped source change is never silent (V2's rejected alternative:
a bare declared constant, where a forgotten bump reproduces the exact silent no-op B-a
exists to fix; the other rejection, pure content-hash identity, would make every
refactor re-project and fill the supersession chain with non-worldview noise).
"""

from __future__ import annotations

import hashlib
import importlib
from dataclasses import dataclass

import pytest

from config.loader import REPO_ROOT


@dataclass(frozen=True)
class Interp:
    version_attr: tuple[str, str]   # (module, attribute) declaring the version
    sources: tuple[str, ...]        # repo-relative files whose bytes ARE the worldview
    version: str                    # the pinned declared version
    sha256: str                     # the pinned source fingerprint at that version


def source_fingerprint(sources: tuple[str, ...]) -> str:
    """sha256 over (path, NUL, bytes, NUL) per file, in declaration order — filename-
    delimited so file boundaries cannot alias; raw bytes, so no newline/encoding
    normalization can drift the pin between machines."""
    h = hashlib.sha256()
    for rel in sources:
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update((REPO_ROOT / rel).read_bytes())
        h.update(b"\0")
    return h.hexdigest()


INTERPRETERS: dict[str, Interp] = {
    "phi_code": Interp(version_attr=("ops.code_sensor", "INTERPRETER_VERSION"),
                       sources=("ops/code_sensor.py", "ops/code_snapshot.py"),
                       version="1.0.0",
                       sha256="8832e5b369763049dad5a0ea384eaaff04672265eb3170e1ee1a6cbccd365d5c"),
    # bp-019 Item 7: phi_self over the cost stream (dn-self-sensing.md §2.2/§2.4).
    # Re-pinned same-version once in-session (orchestrator scrutiny catch: §6(f) warning
    # path was unimplemented) — a DECLARED REFACTOR, not a worldview change: the projection
    # map is byte-identical (unparseable non-null yielded no observation before and after);
    # only report-side warnings were added, and batch content hashes are untouched.
    "phi_self": Interp(version_attr=("ops.self_sensor", "INTERPRETER_VERSION"),
                       sources=("ops/self_sensor.py",),
                       version="1.0.0",
                       sha256="6a5a75347f5c469361e147744ffcb1457baa0f3bda663d60bf5995e04529ddeb"),
}


@pytest.mark.parametrize("name", sorted(INTERPRETERS))
def test_declared_version_matches_the_pin(name: str) -> None:
    interp = INTERPRETERS[name]
    module, attr = interp.version_attr
    assert getattr(importlib.import_module(module), attr) == interp.version, (
        f"{name}: the declared {module}.{attr} disagrees with the pinned pair — "
        f"update INTERPRETERS deliberately (bump or re-pin), never casually")


@pytest.mark.parametrize("name", sorted(INTERPRETERS))
def test_source_hash_matches_the_pin(name: str) -> None:
    interp = INTERPRETERS[name]
    actual = source_fingerprint(interp.sources)
    assert actual == interp.sha256, (
        f"{name}: interpreter source changed without a deliberate act. EITHER bump "
        f"{interp.version_attr[0]}.{interp.version_attr[1]} and pin the new "
        f"(version, sha256) pair (a worldview change — re-projection supersedes; run "
        f"backfill_observations()) OR re-pin sha256='{actual}' at version "
        f"'{interp.version}' (a declared refactor — no re-projection). "
        f"Never silence this test any other way.")
