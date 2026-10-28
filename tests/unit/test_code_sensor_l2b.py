"""bp-094/CI-3 — the L2b shorthand resolvers + the code_to_code inherits/calls AST edges.

Hermetic tmp git repo. Proves (§6, plan Item 1 acceptance):
  • the existence check drops a corpus-target `note-citation` absent from the tree (the `x.md`
    false-positive class) — and thereby the references_out worldview change behind the bump;
  • `dn-<slug>`/`finding-NNNN` resolve deterministically, tree-existence-checked, unresolved
    dropped — and mint NOTHING while their pattern is disabled (precision-first, F-CI6);
  • a `§N` binds only when PAIRED to exactly one cited note (ambiguous/unpaired dropped, PD-F);
  • `inherits`/`calls` resolve module-internal + explicit-import targets, drop attribute-chain /
    dynamic / unresolved / self edges (PD-I), and are disabled by default.
Deterministic — no model anywhere in the path.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.sensing import CodeSensingHandoff
from core.stores.code_observations import CodeObservationStore
from core.stores.reference_edges import ReferenceEdgeStore
from ops import code_sensor as cs
from ops.code_sensor import CodeSensor, _module_to_path, extract_references
from ops.code_snapshot import open_snapshot_db


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


_REFS_PY = (
    '"""Cites dn-foo and finding-0001 and dn-ghost; see docs/design-notes/absent.md and §2.4."""\n'
)
_PAIRED_PY = '"""Only dn-foo here — see §2.4 and §3.1 (paired to the one cited note)."""\n'
_BASE_PY = (
    "class Base:\n    pass\n\n\n"
    "class Sub(Base):\n    pass\n\n\n"
    "def helper():\n    pass\n\n\n"
    "def caller():\n    helper()\n\n\n"
    "def rec():\n    rec()\n"
)
_CHILD_PY = (
    "from base import Base, helper\n\n\n"
    "class Child(Base):\n    def m(self):\n        helper()\n\n\n"
    "def outer():\n    import os\n    os.getcwd()\n    unknown()\n"
)


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    (r / "docs" / "design-notes").mkdir(parents=True)
    (r / "docs" / "findings").mkdir(parents=True)
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "docs" / "design-notes" / "foo.md").write_text("# foo\n")          # dn-foo resolves here
    (r / "docs" / "findings" / "finding-0001.md").write_text("# f1\n")      # finding-0001 resolves
    (r / "refs.py").write_text(_REFS_PY)
    (r / "paired.py").write_text(_PAIRED_PY)
    (r / "base.py").write_text(_BASE_PY)
    (r / "child.py").write_text(_CHILD_PY)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "feat: plant L2b fixtures")
    return r


def _sensor(repo: Path, tmp_path) -> CodeSensor:
    return CodeSensor(
        repo=repo, db=open_snapshot_db(tmp_path / "snap.sqlite"), attestor=None,
        observations=CodeObservationStore(tmp_path / "obs.sqlite"),
        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
        reference_edges=ReferenceEdgeStore(tmp_path / "refs.sqlite"),
    )


# --- the existence check on references_out (the bump's justification, §2.4-3) -----------------
def test_extract_references_existence_check_drops_absent_corpus_target():
    doc = "See docs/design-notes/present.md and docs/design-notes/absent.md."
    known = {"docs/design-notes/present.md"}
    got = {(r["type"], r["target"]) for r in
           extract_references(doc, source_line=1, known_corpus=known)}
    assert got == {("note-citation", "docs/design-notes/present.md")}   # absent.md dropped
    # None (a pure probe with no tree) keeps the pre-CI-3 behavior: no check, both present.
    both = {r["target"] for r in extract_references(doc, source_line=1)}
    assert both == {"docs/design-notes/present.md", "docs/design-notes/absent.md"}


def test_projection_drops_absent_note_citation_from_observations(repo, tmp_path):
    sensor = _sensor(repo, tmp_path)
    sensor.sync()
    obs = sensor.observations
    assert obs is not None
    sha = _git(repo, "rev-list", "main").strip()
    refs_out = {(r["type"], r["target"]) for row in obs.rows_for(sha)
                if row["path"] == "refs.py" and row["qualname"] == ""
                for r in row["references_out"]}
    assert ("note-citation", "docs/design-notes/absent.md") not in refs_out   # existence-checked
    assert sensor.reference_edges is not None
    assert not any(e.target_ref == "docs/design-notes/absent.md"
                   for e in sensor.reference_edges.all())


# --- shorthand resolvers: gated OFF by default, resolve+drop when enabled --------------------
def test_shorthand_mints_nothing_while_disabled(repo, tmp_path):
    assert cs.ENABLED_L2B_PATTERNS == frozenset()          # the shipped default: all off
    sensor = _sensor(repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    minted_types = {e.ref_type for e in sensor.reference_edges.all()}
    assert minted_types.isdisjoint({"dn-slug", "finding-id", "inherits", "calls"})


def test_shorthand_resolves_and_existence_checks(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "ENABLED_L2B_PATTERNS", frozenset({"dn-slug", "finding-id"}))
    sensor = _sensor(repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    got = {(e.ref_type, e.source_ref, e.target_ref)
           for e in sensor.reference_edges.all()
           if e.ref_type in ("dn-slug", "finding-id")}
    assert got == {
        ("dn-slug", "refs.py", "docs/design-notes/foo.md"),        # dn-foo → foo.md (exists)
        ("dn-slug", "paired.py", "docs/design-notes/foo.md"),      # paired.py cites dn-foo too
        ("finding-id", "refs.py", "docs/findings/finding-0001.md"),  # finding-0001 (exists)
    }
    # dn-ghost resolves to docs/design-notes/ghost.md — absent from the tree ⇒ dropped.
    assert not any("ghost" in e.target_ref for e in sensor.reference_edges.all())


def test_paired_section_binds_only_the_unambiguous_note(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "ENABLED_L2B_PATTERNS", frozenset({"dn-slug", "paired-section"}))
    sensor = _sensor(repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    paired = {(e.source_ref, e.target_ref, e.target_detail)
              for e in sensor.reference_edges.all()
              if e.ref_type == "note-citation" and e.target_detail}
    # paired.py cites exactly ONE note (dn-foo → foo.md) and two sections → two anchored edges.
    assert paired == {
        ("paired.py", "docs/design-notes/foo.md", "§2.4"),
        ("paired.py", "docs/design-notes/foo.md", "§3.1"),
    }
    # refs.py cites TWO notes (dn-foo + finding-0001) → its §2.4 is ambiguous ⇒ dropped (PD-F).
    assert not any(e.source_ref == "refs.py" and e.target_detail
                   for e in sensor.reference_edges.all())


# --- code_to_code inherits/calls: static resolution, precision-first drops -------------------
def test_code_to_code_edges_resolve_static_targets(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "ENABLED_L2B_PATTERNS", frozenset({"inherits", "calls"}))
    sensor = _sensor(repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    got = {(e.ref_type, e.source_ref, e.source_detail, e.target_ref, e.target_detail)
           for e in sensor.reference_edges.all() if e.direction == "code_to_code"}
    assert got == {
        ("inherits", "base.py", "Sub", "base.py", "Base"),        # module-internal
        ("inherits", "child.py", "Child", "base.py", "Base"),     # explicit-import cross-module
        ("calls", "base.py", "caller", "base.py", "helper"),      # module-internal
        ("calls", "child.py", "Child.m", "base.py", "helper"),    # explicit-import cross-module
    }
    # DROPPED, never guessed: os.getcwd() (attribute chain), unknown() (unresolved),
    # rec()→rec (self-edge). None may appear.
    assert not any("getcwd" in e.target_detail or "unknown" in e.target_detail or
                   (e.source_ref == e.target_ref and e.source_detail == e.target_detail)
                   for e in sensor.reference_edges.all() if e.direction == "code_to_code")


# --- the M-C6 census fixes (bp-094 Item 2): definition-time calls, re-exports, ambiguity ------
_RESOLVE_FILES = {
    "impl.py": "def work():\n    pass\n\n\nclass Thing:\n    pass\n",
    "other.py": "def work():\n    pass\n",
    "facade.py": "from impl import Thing, work\n",            # re-exports only, defines nothing
    "pkg/__init__.py": "from pkg.mod import task\n",          # a package re-export
    "pkg/mod.py": "def task():\n    pass\n",
    "outside.py": "from os.path import join\n",               # re-exports from outside the tree
    "user.py": (
        "from facade import Thing, work\n"
        "from pkg import task\n"
        "from outside import join\n\n\n"
        "def gate():\n    return True\n\n\n"
        "def deco(flag):\n    return lambda f: f\n\n\n"
        "class Sub(Thing):\n    pass\n\n\n"
        "def use():\n    work()\n    task()\n    join()\n\n\n"
        "@deco(gate())\n"
        "def decorated():\n    pass\n\n\n"
        "def outer():\n"
        "    def inner(flag=gate()):\n        pass\n"
        "    return inner\n"
    ),
    "two.py": (                                               # one name, two definitions
        "def first():\n    from impl import work\n    work()\n\n\n"
        "def second():\n    from other import work\n    work()\n"
    ),
    "same.py": (                                              # two routes, one definition
        "def first():\n    from impl import work\n    work()\n\n\n"
        "def second():\n    from facade import work\n    work()\n"
    ),
}


@pytest.fixture
def resolve_repo(tmp_path) -> Path:
    r = tmp_path / "resolve"
    (r / "pkg").mkdir(parents=True)
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    for rel, text in _RESOLVE_FILES.items():
        (r / rel).write_text(text)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "feat: plant resolver fixtures")
    return r


def test_code_to_code_follows_reexports_and_keeps_header_calls_out(resolve_repo, tmp_path,
                                                                   monkeypatch):
    monkeypatch.setattr(cs, "ENABLED_L2B_PATTERNS", frozenset({"inherits", "calls"}))
    sensor = _sensor(resolve_repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    got = {(e.ref_type, e.source_ref, e.source_detail, e.target_ref, e.target_detail)
           for e in sensor.reference_edges.all() if e.direction == "code_to_code"}
    assert got == {
        ("inherits", "user.py", "Sub", "impl.py", "Thing"),     # through the facade
        ("calls", "user.py", "use", "impl.py", "work"),         # through the facade
        ("calls", "user.py", "use", "pkg/mod.py", "task"),      # through the package __init__
        ("calls", "user.py", "outer", "user.py", "gate"),       # inner's default runs in outer
        ("calls", "same.py", "first", "impl.py", "work"),       # two routes, one definition
        ("calls", "same.py", "second", "impl.py", "work"),
    }
    # DROPPED: the decorator's calls (definition time, module scope — not `decorated`'s),
    # `inner`'s default as inner's own call, join() (the chain leaves the tree), and two.py's
    # `work` (one name, two definitions in one file).


def test_module_to_path_absolute_and_relative():
    assert _module_to_path("a.b.c", 0, "x/y.py") == "a/b/c.py"
    assert _module_to_path("", 0, "x/y.py") is None                # `import a` binds via attribute
    assert _module_to_path("mod", 1, "a/b/c.py") == "a/b/mod.py"   # from .mod import X
    assert _module_to_path("pkg.mod", 2, "a/b/c.py") == "a/pkg/mod.py"  # from ..pkg.mod import X
    assert _module_to_path("x", 9, "a/b.py") is None               # ascent past the repo root
