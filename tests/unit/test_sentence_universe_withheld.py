"""What the universe names to a reader whose grant holds no stratum of the mirror
(`core/sentence/universe.py` under `hide_mirror`, dn-guest-principal §5): a causal edge only when
it ends at a commit or at a file git tracks in the repo at HEAD, a citation neighbour only when it
is a repo-relative path outside the vault, and a vault path in whatever spelling it was recorded.
A reader whose grant holds the mirror is shown what it was shown before. Hermetic: the store fakes
of test_sentence_universe, a vault under tmp_path and a scratch git repo standing for the
checkout."""

from __future__ import annotations

import subprocess
import unicodedata
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from core.kernel.config import get_config
from core.query import AMBASSADOR_OVERLAY, GUEST, QueryEngine
from core.sentence import compile_sentence, execute
from core.sentence.precedents import DEFAULT
from core.sentence.universe import _Builder, _doc_path, build
from tests.unit.test_sentence_universe import (
    _Causal,
    _cedge,
    _Chatlog,
    _Curated,
    _Edge,
    _Engine,
    _Memberships,
    _Refs,
    _vec,
    _Vectors,
)

SHA = "0123456789abcdef0123456789abcdef01234567"
WITHHELD = "withheld: the grant names no stratum of the mirror"


def _config(vault: Path) -> Any:
    base = get_config()
    return replace(base, ingestion=replace(base.ingestion,
                                           vault=replace(base.ingestion.vault, path=vault)))


def _builder(vault: Path, *, hide: bool = True) -> _Builder:
    """A builder with a configuration alone: enough for the tests of a path, which open no store."""
    engine = SimpleNamespace(config=_config(vault))
    return _Builder(cast(QueryEngine, engine), DEFAULT, hide_mirror=hide)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git repo standing for the checkout: two files, a design note and a finding committed;
    a file and a design note written after the commit, which git does not track."""
    import core.kernel.config as config

    root = tmp_path / "repo"
    for d in ("core", "docs/design-notes", "docs/findings"):
        (root / d).mkdir(parents=True)
    (root / "core" / "x.py").write_text("x = 1\n")
    (root / "docs" / "a.md").write_text("a\n")
    (root / "docs" / "design-notes" / "dn-kept.md").write_text("kept\n")
    (root / "docs" / "findings" / "finding-0007-seven.md").write_text("seven\n")
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True, capture_output=True)
    subprocess.run([*git, "add", "core", "docs"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-q", "-m", "tree"], check=True, capture_output=True)
    (root / "core" / "new.py").write_text("y = 2\n")
    (root / "docs" / "design-notes" / "dn-draft.md").write_text("draft\n")
    monkeypatch.setattr(config, "REPO_ROOT", root)
    return root


# ── the tracked paths ──────────────────────────────────────────────────────────────────────────


def test_tracked_paths_are_the_tree_at_head_and_none_when_git_cannot_answer(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    ex = importlib.import_module("core.sentence.execute")   # the package exports `execute`
    assert ex.tracked_paths(repo) == {"core/x.py", "docs/a.md", "docs/design-notes/dn-kept.md",
                                      "docs/findings/finding-0007-seven.md"}
    subprocess.run(["git", "-C", str(repo), "add", "core/new.py"], check=True, capture_output=True)
    assert "core/new.py" not in ex.tracked_paths(repo)        # staged is not yet at HEAD
    bare = tmp_path / "not-a-repo"
    bare.mkdir()
    assert ex.tracked_paths(bare) == frozenset()
    assert ex.tracked_paths(tmp_path / "absent") == frozenset()
    # a name that is not UTF-8 is spelled by no string, so it is left out, not approximated
    monkeypatch.setattr(ex, "_git", lambda root, *args: b"docs/a.md\0docs/\xff.md\0")
    assert ex.tracked_paths(repo) == {"docs/a.md"}
    monkeypatch.setattr(ex, "_git", lambda root, *args: None)
    assert ex.tracked_paths(repo) == frozenset()
    for sha in ("0123abc", SHA, "a" * 64):
        assert ex.is_commit_sha(sha)
    for text in ("", "0123ab", "0123ABC", "0123abc\n", "g123abc", f"{SHA}/x", "a" * 65,
                 "docs/a.md"):
        assert not ex.is_commit_sha(text), text


# ── the vault, in every spelling ───────────────────────────────────────────────────────────────


def test_a_vault_path_is_recognised_in_every_spelling(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """The spellings a file system may treat as one file, whether or not this one does: another
    letter case, another Unicode normal form, `..`, a symlink, `~`, a path relative to the
    working directory. The comparison is by component, so a sibling whose name starts with the
    vault's is outside."""
    home = tmp_path / unicodedata.normalize("NFC", "w\u00e9")
    vault = home / "vault"
    (vault / "sub").mkdir(parents=True)
    (tmp_path / "link").symlink_to(vault)
    (tmp_path / "deep" / "er").mkdir(parents=True)
    (home / "hop").symlink_to(tmp_path / "deep" / "er")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(home)
    b = _builder(vault)
    note = str(vault / "sub" / "n.md")
    nfd = unicodedata.normalize("NFD", note)
    assert nfd != note
    inside = [note, str(vault), f"{vault}/", str(home / "VAULT" / "Sub" / "N.md"), nfd,
              nfd.replace("/vault/", "/VAULT/"), f"{home}/other/../vault/n.md",
              f"{vault}/../vault/n.md", f"/{note}", f"{vault}/./n.md",
              str(tmp_path / "link" / "n.md"), "~/vault/n.md", "~/Vault/n.md", "vault/n.md",
              "./vault/sub/../n.md", "../" + home.name + "/vault/n.md",
              str(home / "\uff56ault" / "n.md"),        # a compatibility form of the name
              # in the vault by its normal form alone: resolved, the link is followed before the
              # `..` and the path leaves; the three forms are each asked, so it is withheld
              f"{home}/hop/../vault/n.md"]
    for ref in inside:
        assert b._in_vault(ref), ref
    assert (home / "hop" / ".." / "vault").resolve() == (tmp_path / "deep" / "vault").resolve()
    outside = [str(home / "vault-2" / "n.md"), f"{vault}.md", str(home), str(home / "n.md"),
               "/srv/repo/core/x.py", "core/x.py", "~/n.md", "dn-kept.md",
               f"file://{note}"]                         # a URI is no path: named by no rule
    for ref in outside:
        assert not b._in_vault(ref), ref
    # a path that cannot be read counts as inside
    for ref in (f"{vault}\0/n.md", "a\0b", "~no-such-user-of-this-test/n.md"):
        assert b._in_vault(ref), ref
    unset = _Builder(cast(QueryEngine, SimpleNamespace(config=None)), DEFAULT, hide_mirror=True)
    assert unset._in_vault("/srv/repo/core/x.py")            # any failure: inside


# ── a causal edge's endpoint ───────────────────────────────────────────────────────────────────


def test_only_a_commit_or_a_tracked_file_is_named(repo: Path, tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    vault = tmp_path / "vault"
    vault.mkdir()
    (repo / "into-vault").symlink_to(vault)
    b = _builder(vault)
    named = [(SHA, "commit"), ("0123abc", "commit"),
             (f"{repo}/core/x.py", "file"), (f"{repo}/docs/a.md", "file"),
             (f"{repo}//core/x.py", "file"), (f"{repo}/core/x.py/", "file"),
             (f"{repo}/.claude/worktrees/wt/core/x.py", "file"),      # a worktree's copy of it
             (f"{repo}/docs/design-notes/dn-kept.md", "doc"),
             ("dn-kept.md", "doc"), ("dn-kept", "doc"), ("finding-0007", "doc")]
    for dst, kind in named:
        assert b._named(dst, kind), (dst, kind)
    withheld = [
        ("not-a-sha", "commit"), ("", "commit"), (f"{SHA}\n", "commit"), ("core/x.py", "commit"),
        (f"{vault}/n.md", "file"), (f"{tmp_path}/VAULT/n.md", "file"),
        (f"{repo}/into-vault/n.md", "file"),                # under the checkout, in the vault
        (f"{repo}/core/new.py", "file"),                    # in the checkout, not tracked
        (f"{repo}/core/gone.py", "file"),                   # no such file
        (f"{repo}/CORE/x.py", "file"),                      # not as git spells it
        (f"{repo}/core/../core/x.py", "file"), (f"{repo}/core", "file"), (str(repo), "file"),
        ("/private/tmp/scratch/out.txt", "file"), ("/elsewhere/.claude/worktrees/w/core/x.py",
                                                   "file"),
        ("core/x.py", "file"), ("./core/x.py", "file"), ("~/core/x.py", "file"),
        (f"file://{repo}/core/x.py", "file"), ("", "file"),
        ("dn-draft.md", "doc"), ("dn-none", "doc"), ("plan.md", "doc"), ("finding-0008", "doc"),
        ("docs/design-notes/dn-kept.md", "doc"),
        (f"{repo}/core/x.py", "artifact"), (f"{repo}/core/x.py", ""), ("dn-kept.md", "file"),
    ]
    for dst, kind in withheld:
        assert not b._named(dst, kind), (dst, kind)
    # a doc's id is read as a name, never as a pattern. The projector records a file under any
    # `docs/design-notes/` folder by its file name, and a file name may hold a glob's characters:
    # each of these, looked up as the glob it is, finds the one tracked finding, and is not named
    for pattern in ("finding-*", "finding-000?.md", "finding-0007[-]seven.md",
                    "finding-0007*[the private plan].md"):
        assert _doc_path(pattern) == "docs/findings/finding-0007-seven.md"
        assert not b._named(pattern, "doc"), pattern
    assert b._named_of[(f"{repo}/core/x.py", "file")] is True      # judged once per endpoint
    # the vault is asked first: a file git tracks is not named when it lies in the vault
    inner = _builder(repo / "docs")
    assert not inner._named(f"{repo}/docs/a.md", "file")
    assert inner._named(f"{repo}/core/x.py", "file")


def test_nothing_but_a_commit_is_named_when_the_tree_cannot_be_read(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed: git absent or failing, or any error while an endpoint is judged, withholds
    the edge; it never raises into the sentence."""
    import core.sentence.universe as universe

    vault = tmp_path / "vault"
    assert _builder(vault)._named(f"{repo}/core/x.py", "file")      # the control
    failing = _builder(vault)
    monkeypatch.setattr(failing, "_endpoint", lambda dst, dst_type: 1 / 0)
    assert not failing._named(f"{repo}/core/x.py", "file")

    def no_git(root: Path) -> frozenset[str]:
        raise OSError("git: not found")

    monkeypatch.setattr(universe, "tracked_paths", no_git)
    b = _builder(vault)
    assert not b._named(f"{repo}/core/x.py", "file") and not b._named("dn-kept.md", "doc")
    assert b._named(SHA, "commit") and b._tracked() == frozenset()


def _engine(repo: Path, vault: Path, monkeypatch: pytest.MonkeyPatch, causal: list[dict[str, Any]],
            refs: list[_Edge]) -> _Engine:
    import core.reference_view as rv

    monkeypatch.setattr(rv, "_resolve_default_commit", lambda cfg: "c1")
    e = _Engine(
        refs=_Refs(refs),
        vectors=_Vectors(dialogue=[{"source_path": "dialogue/c/t1", "title": "turn 1",
                                    "digest": "dt1", "provenance": "observed",
                                    "vector": _vec(2)}], atoms=[]),
        curated=_Curated([]), memberships=_Memberships({}), embed={},
        causal=_Causal(causal),
        chatlog=_Chatlog([{"session_id": "s1", "turn_index": 3, "speaker": "owner",
                           "text": "please write x", "transcript_digest": "td1",
                           "provenance": "observed"}]))
    e.config = _config(vault)
    return e


def test_the_universe_shows_the_named_edges_and_withholds_the_rest_whole(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One turn with fifteen proven edges. The reader without the mirror is shown the four that
    end at a tracked file, a tracked doc or a commit: as hits, in the counts and by `witness`.
    The others are not counted, and `witness` of their ids answers as for an id the store does
    not hold. The reader with the mirror is shown all fifteen, as before."""
    vault = tmp_path / "vault"
    vault.mkdir()
    shown = {"e-file": ("file", f"{repo}/core/x.py"), "e-doc": ("doc", "dn-kept.md"),
             "e-finding": ("doc", "finding-0007"), "e-commit": ("commit", SHA)}
    hidden = {"h-untracked": ("file", f"{repo}/core/new.py"),
              "h-outside": ("file", "/private/tmp/scratch/out.txt"),
              "h-note": ("file", f"{vault}/n.md"),
              "h-case": ("file", f"{tmp_path}/VAULT/n.md"),
              "h-relative": ("file", "core/x.py"),
              "h-uri": ("file", f"file://{repo}/core/x.py"),
              "h-draft": ("doc", "dn-draft.md"),
              "h-name": ("doc", "plan-0.md"),
              "h-pattern": ("doc", "finding-0007*[the private plan].md"),
              "h-word": ("commit", "not-a-sha"),
              "h-kind": ("artifact", f"{repo}/core/x.py")}
    edges = [_cedge(eid, "s1", 3, dst, dst_type=kind, order=i)
             for i, (eid, (kind, dst)) in enumerate({**shown, **hidden}.items())]
    engine = _engine(repo, vault, monkeypatch, edges, [_Edge("docs/a.md", "core/x.py", "c1")])
    sentence = 'reach C from "transcript/s1/3" depth 1 over dialogue_transcript reference'

    plan = compile_sentence(sentence, GUEST)
    u = build(cast(QueryEngine, engine), plan, hide_mirror=True)
    hits = {h.ref: h for h in execute(plan, u).hits}
    assert set(hits) == {"core/x.py", "docs/design-notes/dn-kept.md",
                         "docs/findings/finding-0007-seven.md", SHA}
    assert hits["core/x.py"].detail["witness"] == "e-file"
    assert hits["docs/design-notes/dn-kept.md"].detail["id"] == "dn-kept.md"
    assert any("causal: 4 proven edges from 1 transcript turns to 4 endpoints" in m
               for m in u.missing)
    assert sum(m.startswith(WITHHELD) for m in u.missing) == 1
    for eid, (_kind, dst) in shown.items():
        record = u.witness(eid)
        assert record is not None and record["dst"] == dst
    for eid in hidden:
        assert u.witness(eid) is None, eid
    assert u.witness("no-such-edge") is None

    # the same store with every hidden edge taken out: the same universe, word for word
    bare = _engine(repo, vault, monkeypatch, edges[:len(shown)],
                   [_Edge("docs/a.md", "core/x.py", "c1")])
    v = build(cast(QueryEngine, bare), plan, hide_mirror=True)
    assert (u.notes, u.missing, u.edges) == (v.notes, v.missing, v.edges)

    # a grant that reads the mirror builds what it built before: every edge, every record
    wide = compile_sentence(sentence, AMBASSADOR_OVERLAY)
    w = build(cast(QueryEngine, engine), wide)
    assert any("causal: 15 proven edges from 1 transcript turns" in m for m in w.missing)
    assert not any(m.startswith(WITHHELD) for m in w.missing)
    for eid, (_kind, dst) in {**shown, **hidden}.items():
        record = w.witness(eid)
        assert record is not None and record["dst"] == dst


def test_a_turn_whose_edges_are_all_withheld_is_no_turn_to_the_reader(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The lookup refusal for a turn with only withheld edges is the one for a turn no edge names,
    and an endpoint asked for by name has no turn behind it."""
    vault = tmp_path / "vault"
    vault.mkdir()
    edges = [_cedge("h1", "s9", 1, f"{vault}/n.md"), _cedge("h2", "s9", 1, "notes/n.md"),
             _cedge("h3", "s9", 1, f"{repo}/core/new.py")]
    engine = _engine(repo, vault, monkeypatch, edges, [])
    plan = compile_sentence('reach C from "transcript/s9/1" over dialogue_transcript', GUEST)
    with pytest.raises(LookupError) as with_edges:
        build(cast(QueryEngine, engine), plan, hide_mirror=True)
    with pytest.raises(LookupError) as without:
        build(cast(QueryEngine, _engine(repo, vault, monkeypatch, [], [])), plan,
              hide_mirror=True)
    assert str(with_edges.value) == str(without.value)
    back = compile_sentence('reach C from "notes/n.md" back over dialogue', GUEST)
    assert execute(back, build(cast(QueryEngine, engine), back, hide_mirror=True)).hits == ()
    back_new = compile_sentence('reach C from "core/new.py" back over dialogue', GUEST)
    assert execute(back_new, build(cast(QueryEngine, engine), back_new,
                                   hide_mirror=True)).hits == ()


class _Minted(_Refs):
    """A reference store whose edges are found by id: each id names the commit that minted it."""

    def __init__(self, minted: dict[str, str]) -> None:
        super().__init__([])
        self.minted = minted

    def edge(self, edge_id: str) -> _Edge | None:
        sha = self.minted.get(edge_id)
        return None if sha is None else _Edge("docs/a.md", "core/x.py", sha)


def test_the_witness_of_a_reference_edge_is_judged_like_any_other(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`witness` of a reference edge's id answers the causal edge keyed to the commit that
    minted it (`origin`). The reader without the mirror is answered only when that edge is one
    it may see named, a commit by its sha; a row keyed to a commit whose endpoint is anything
    else is no record to it, as an id the stores do not hold. The reader with the mirror is
    answered both."""
    vault = tmp_path / "vault"
    vault.mkdir()
    other = "f" * 40
    engine = _engine(repo, vault, monkeypatch, [
        {**_cedge("c-commit", "s1", 3, SHA, dst_type="commit", order=2), "pair_cut_sha": SHA},
        {**_cedge("c-note", "s1", 3, f"{vault}/n.md", order=1), "pair_cut_sha": other}], [])
    engine._cache["references"] = _Minted({"r-commit": SHA, "r-note": other})
    plan = compile_sentence('witness "r-commit"', GUEST)
    u = build(cast(QueryEngine, engine), plan, hide_mirror=True)
    record = u.witness("r-commit")
    assert record is not None and (record["edge_id"], record["dst"]) == ("c-commit", SHA)
    assert u.witness("r-note") is None and u.witness("r-none") is None
    assert execute(compile_sentence('witness "r-note"', GUEST), u).hits == ()
    w = build(cast(QueryEngine, engine), compile_sentence('witness "r-note"', AMBASSADOR_OVERLAY))
    record = w.witness("r-note")
    assert record is not None and record["dst"] == f"{vault}/n.md"


def test_a_withheld_edge_keyed_to_a_commit_stands_in_front_of_no_named_one(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two causal edges keyed to the commit that minted a reference edge: one ends at a vault
    path and comes first, the other ends at the commit. `origin` answers the first of the edges
    it may choose from. The reader without the mirror may not choose the withheld one, so it is
    answered the commit's edge, in whatever order the store holds the two: the answer of a store
    without the withheld edge. The reader with the mirror is answered the first, as before."""
    vault = tmp_path / "vault"
    vault.mkdir()
    shown = {**_cedge("c-commit", "s1", 3, SHA, dst_type="commit", order=2), "pair_cut_sha": SHA}
    hidden = {**_cedge("c-note", "s1", 3, f"{vault}/n.md", order=1), "pair_cut_sha": SHA}
    plan = compile_sentence('witness "r"', GUEST)
    seen = []
    for causal in ([shown], [shown, hidden], [hidden, shown]):
        engine = _engine(repo, vault, monkeypatch, causal, [])
        engine._cache["references"] = _Minted({"r": SHA})
        u = build(cast(QueryEngine, engine), plan, hide_mirror=True)
        record = u.witness("r")
        assert record is not None and (record["edge_id"], record["dst"]) == ("c-commit", SHA)
        seen.append((record, [h.__dict__ for h in execute(plan, u).hits], u.missing))
    assert seen[1] == seen[2] == seen[0]
    wide = build(cast(QueryEngine, engine), compile_sentence('witness "r"', AMBASSADOR_OVERLAY))
    record = wide.witness("r")
    assert record is not None and (record["edge_id"], record["dst"]) == ("c-note", f"{vault}/n.md")


def test_the_withheld_note_is_one_sentence_whatever_the_store_holds(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The note that says what is withheld rides with every sentence that walks C or asks a
    witness, in the same words over a store with no edge, with edges that are shown, and with
    edges that are withheld: its presence and its words tell nothing of the store. A sentence
    that does neither carries no such note."""
    vault = tmp_path / "vault"
    vault.mkdir()
    edges = [_cedge("e1", "s1", 3, f"{repo}/core/x.py"),
             _cedge("h1", "s1", 3, f"{vault}/n.md", order=1)]
    said = set()
    for causal in ([], edges[:1], edges[1:], edges):
        engine = _engine(repo, vault, monkeypatch, causal, [])
        for sentence in ('reach C from "core/x.py" back over dialogue', 'witness "e1"',
                         'witness "h1"',
                         'walk from "core/x.py" via (C|F) over reference dialogue_transcript'):
            plan = compile_sentence(sentence, GUEST)
            u = build(cast(QueryEngine, engine), plan, hide_mirror=True)
            (note,) = [m for m in u.missing if m.startswith(WITHHELD)]
            said.add(note)
        quiet = compile_sentence('reach F from "core/x.py"', GUEST)
        assert not any(m.startswith(WITHHELD) for m in build(
            cast(QueryEngine, engine), quiet, hide_mirror=True).missing)
    assert len(said) == 1 and "at a commit or at a file git tracks" in said.pop()


# ── a citation neighbour ───────────────────────────────────────────────────────────────────────


def test_a_citation_neighbour_is_named_only_as_a_repo_path_outside_the_vault(
        repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The citation graph's refs are repo-relative paths. A neighbour spelled any other way, or
    one that lies in the vault under the checkout, is not named; one that git does not track at
    HEAD is, since the graph is read at other cuts too."""
    vault = repo / "private"                  # a vault kept inside the checkout
    plain = ["core/y.py", "docs/b.md", "README.md", "docs/design-notes/dn-kept.md"]
    other = [f"{tmp_path}/vault/n.md", "/srv/notes/n.md", "~/notes/n.md", "file:///srv/n.md",
             "docs/../../notes/n.md", "../notes/n.md", "private/n.md", "PRIVATE/sub/n.md",
             "docs/../private/n.md"]
    refs = [_Edge("core/x.py", t, "c1") for t in plain + other]
    engine = _engine(repo, vault, monkeypatch, [], refs)
    sentence = 'reach F from "core/x.py" depth 1'

    plan = compile_sentence(sentence, GUEST)
    u = build(cast(QueryEngine, engine), plan, hide_mirror=True)
    assert sorted(h.ref for h in execute(plan, u).hits) == sorted(plain)
    assert not {n["source_path"] for n in u.notes} & set(other)
    hidden = _builder(vault)
    assert all(hidden._citable(t) for t in plain)
    assert not any(hidden._citable(t) for t in other)

    # a grant that reads the mirror is shown every neighbour, as before
    wide = compile_sentence(sentence, AMBASSADOR_OVERLAY)
    w = build(cast(QueryEngine, engine), wide)
    assert sorted(h.ref for h in execute(wide, w).hits) == sorted(plain + other)
    assert all(_builder(vault, hide=False)._citable(t) for t in plain + other)
