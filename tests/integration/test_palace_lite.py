"""The lite profile (docs/design-notes/dn-palace-lite.md): an instance that embeds nothing, a code
source that keeps no vectors, and a repository read as a source through git.

What is pinned: in an instance with `[embedding] enabled = false` no embedder and no vector plane
is ever constructed, while a repository's files land, re-land as nothing, change, retire, and are
found by `near`, `read`, `trace` and `reach`; the per-source switch keeps a note's vector and the
code's lack of one side by side in an instance that embeds; and the default instance's
configuration and table are what they were.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.ingest import ingress
from core.ingest.readers import read_mark
from core.ingest.repository import behind, itemizable
from core.ingest.table import build_table, repository_mark
from core.kernel.config import get_config
from core.kernel.config.loader import (
    InstanceOverlayError,
    RepositoryConfig,
    _repositories,
    lexical_code,
    load_config,
    needs_lexical,
)
from core.kernel.provenance import Provenance
from core.query import QueryEngine
from core.sentence.surface import QueryLog, ask_logged, sentence_grant
from core.stores.noplane import EmbeddingOff, NoPlane
from tests.fixtures.ingress import EVERY, palace_at, write_file

REPO = "toy"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@example.org", "-c", "user.name=t", "commit", "-q", "-m",
         message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repository on `main` with code, a note, a foundation path, a binary and a symlink."""
    r = tmp_path / "repo"
    (r / "pkg").mkdir(parents=True)
    (r / "docs").mkdir()
    _git(r.parent, "init", "-q", "-b", "main", str(r))
    (r / "pkg" / "embed.py").write_text(
        'def embed_fitting(texts):\n    """Cut a text to fit the embedder."""\n    return texts\n')
    (r / "pkg" / "derive.py").write_text(
        "from pkg.embed import embed_fitting\n\n\ndef drain():\n    return embed_fitting([])\n")
    (r / "docs" / "landing.md").write_text(
        "# Landing without vectors\n\nAn item lands complete without its vector.\n")
    (r / "CONSTITUTION.md").write_text("the foundation is never an item\n")
    (r / "pkg" / "blob.bin").write_bytes(b"bin\0ary")
    (r / "link.py").symlink_to("pkg/embed.py")
    _commit(r, "one")
    return r


def lite_config(root: Path, repo: Path, *, embedding: bool = False, embed: bool = False) -> Any:
    """A palace under `root` reading `repo` as its code: every path the instance writes is under
    `root`, embedding as asked, the code keeping no vectors unless `embed`."""
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (root / "vault").mkdir(exist_ok=True)
    base = get_config()
    paths = replace(base.paths, data_dir=data, raw_store=data / "raw",
                    vector_store=data / "vectors.lance", curated_store=data / "curated.lance",
                    vault_catalog=data / "vault_catalog.sqlite",
                    derived_store=data / "derived.sqlite", telemetry_db=data / "telemetry.duckdb",
                    attestation_store=data / "attestations.sqlite")
    code = replace(base.ingestion.code, enabled=True, embed=embed,
                   repositories=(RepositoryConfig(REPO, repo, "main"),))
    return replace(base, paths=paths,
                   ingestion=replace(base.ingestion, code=code,
                                     vault=replace(base.ingestion.vault, path=root / "vault")),
                   interface=replace(base.interface, handoff_dir=data / "handoff"),
                   embedding=replace(base.embedding, enabled=embedding, lazy=False))


@pytest.fixture
def no_vectors(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Constructing an embedder or a vector store fails the test: each attempt is recorded and
    refused, so a pass proves none was made."""
    made: list[str] = []

    def refuse(what: str) -> Any:
        def boom(*_a: Any, **_k: Any) -> None:
            made.append(what)
            raise AssertionError(f"{what} was constructed")
        return boom

    from core.ingest import embed
    from core.models import inference
    from core.stores import vectorstore
    monkeypatch.setattr(vectorstore.VectorStore, "__post_init__", refuse("a vector store"))
    monkeypatch.setattr(embed.Embedder, "__init__", refuse("an embedder"))
    monkeypatch.setattr(inference, "build_inference_client", refuse("an inference client"))
    return made


def _sync(cfg: Any, stores: Any) -> dict[str, Any]:
    return ingress.run_library(cfg, "sync_repository", {"name": REPO}, stores=stores)


def _ask(engine: QueryEngine, sentence: str, log: Path) -> dict[str, Any]:
    return ask_logged(sentence, sentence_grant(), surface="test", role="ambassador",
                      engine=engine, log=QueryLog(log)).to_dict()


# ── an instance that embeds nothing ────────────────────────────────────────────────────────────


def test_an_instance_that_embeds_nothing_never_builds_an_embedder_or_opens_a_plane(
        tmp_path: Path, repo: Path, no_vectors: list[str]) -> None:
    cfg = lite_config(tmp_path / "lite", repo)
    stores = ingress.build_stores(cfg)
    assert isinstance(stores.plane, NoPlane) and stores.embedder is None
    assert stores.lexical is not None
    landed = _sync(cfg, stores)
    assert landed["effects"] == {"landed": 3}
    assert sorted(c["path"] for c in landed["changed"]) == [
        "code/toy/docs/landing.md", "code/toy/pkg/derive.py", "code/toy/pkg/embed.py"]
    engine = QueryEngine(config=cfg)
    log = tmp_path / "log.jsonl"
    near = _ask(engine, 'top 3 near "embed fitting" over reference', log)
    refs = [h["ref"] for h in near["hits"]]
    assert "code/toy/pkg/embed.py" in refs
    assert all(h["detail"]["ranked_by"] == "lexical: the item keeps no vector"
               for h in near["hits"])
    assert any("the instance embeds nothing" in n for n in near["notes"])
    read = _ask(engine, 'read "code/toy/pkg/embed.py"', log)
    assert "def embed_fitting" in read["hits"][0]["text"]
    assert read["hits"][0]["stratum"] == "reference"
    assert _ask(engine, 'reach F from "code/toy/pkg/derive.py"', log)["hits"] == []
    diffuse = _ask(engine, 'diffuse S from "code/toy/pkg/derive.py" over reference', log)
    assert diffuse["hits"] == [] and any("S has no edge" in n for n in diffuse["notes"])
    assert no_vectors == []
    assert not list((tmp_path / "lite").rglob("*.lance"))


def test_notes_land_and_rank_lexically_in_an_instance_that_embeds_nothing(
        tmp_path: Path, repo: Path, no_vectors: list[str]) -> None:
    """The profile is not the code's alone: a vault note lands with its lexical units and no
    vector, and `near` over the mirror ranks it by the index and says why."""
    cfg = lite_config(tmp_path / "lite", repo)
    write_file(cfg.ingestion.vault.path, "drain.md", "the embed drain derives vectors later\n")
    write_file(cfg.ingestion.vault.path, "other.md", "a note about something else\n")
    stores = ingress.build_stores(cfg)
    assert ingress.run_library(cfg, "sync_vault", stores=stores)["effects"] == {"landed": 2}
    near = _ask(QueryEngine(config=cfg), 'near "embed drain"', tmp_path / "log.jsonl")
    assert near["hits"][0]["ref"] == str(cfg.ingestion.vault.path / "drain.md")
    assert near["hits"][0]["detail"]["ranked_by"] == "lexical: the item keeps no vector"
    assert near["hits"][0]["detail"]["vector"] == "none: the instance embeds nothing"
    assert no_vectors == []


def test_the_factories_refuse_an_embedder_and_a_plane_by_name(tmp_path: Path,
                                                              repo: Path) -> None:
    from core.ingest.embed import build_embedder
    from core.stores.curated_store import open_curated_store
    from core.stores.vectorstore import open_vector_store

    cfg = lite_config(tmp_path / "lite", repo)
    for factory in (build_embedder, open_vector_store, open_curated_store):
        with pytest.raises(EmbeddingOff, match="embeds nothing"):
            factory(cfg)
    plane = NoPlane()
    assert plane.count() == 0 and plane.all_rows() == [] and plane.search([0.0]) == []
    assert plane.current_versions() == set() and not plane.holds_current("a", "b")
    plane.delete_source("a")                                 # a retire's step: nothing to take
    with pytest.raises(EmbeddingOff):
        plane.add([{"id": "x"}])
    with pytest.raises(EmbeddingOff):
        plane.reset()


def test_a_repository_lands_once_changes_retire_and_its_commit_is_marked(
        tmp_path: Path, repo: Path) -> None:
    cfg = lite_config(tmp_path / "lite", repo)
    stores = ingress.build_stores(cfg)
    first = _sync(cfg, stores)
    assert first["effects"] == {"landed": 3}
    mark = read_mark(repository_mark(cfg, REPO))
    assert mark is not None and mark["commit"] == _git(repo, "rev-parse", "main")
    assert mark["files"] == 3
    assert _sync(cfg, stores)["effects"] == {"unchanged": 3}          # a re-run lands nothing
    labels = {str(e.provenance) for e in stores.catalog.active_entries()}
    assert labels == {Provenance.CODE.value}
    (repo / "pkg" / "embed.py").write_text(
        'def embed_fitting(texts):\n    """Cut a text by bisection."""\n    return texts\n')
    (repo / "docs" / "landing.md").unlink()
    head = _commit(repo, "two")
    assert behind(repo, mark["commit"], "main") == 1
    second = _sync(cfg, stores)
    assert second["effects"] == {"unchanged": 1, "landed": 1, "retired": 1}
    assert {c["path"]: c["status"] for c in second["changed"]} == {
        "code/toy/pkg/embed.py": "landed", "code/toy/docs/landing.md": "retired"}
    assert read_mark(repository_mark(cfg, REPO))["commit"] == head          # type: ignore[index]
    assert behind(repo, head, "main") == 0
    assert stores.versions is not None
    assert len(stores.versions.history("code/toy/pkg/embed.py")) == 2
    assert stores.lexical.units_of("code/toy/docs/landing.md") == 0       # retired: not current
    trace = _ask(QueryEngine(config=cfg), 'trace "code/toy/pkg/embed.py"', tmp_path / "log")
    assert [h["stratum"] for h in trace["hits"]] == ["reference"]
    assert trace["hits"][0]["ref"] == "code/toy/pkg/embed.py@1 →D→ code/toy/pkg/embed.py@2"


def test_a_repository_source_reads_the_ref_never_the_working_tree(tmp_path: Path,
                                                                 repo: Path) -> None:
    (repo / "pkg" / "embed.py").write_text("an uncommitted edit\n")
    (repo / "untracked.py").write_text("never committed\n")
    cfg = lite_config(tmp_path / "lite", repo)
    stores = ingress.build_stores(cfg)
    _sync(cfg, stores)
    paths = {e.source_path for e in stores.catalog.active_entries()}
    assert "code/toy/untracked.py" not in paths
    assert "code/toy/CONSTITUTION.md" not in paths and "code/toy/pkg/blob.bin" not in paths
    assert "code/toy/link.py" not in paths                          # a symlink is no file
    entry = stores.catalog.get("code/toy/pkg/embed.py")
    assert b"def embed_fitting" in stores.raw.get(entry.digest)
    assert not itemizable("CONSTITUTION.md") and not itemizable("eval/golden/x.md")
    assert not itemizable(".claude/settings.json") and itemizable("docs/LAWS.md")


# ── a source that keeps no vectors in an instance that embeds ──────────────────────────────────


def test_the_code_keeps_no_vectors_while_the_notes_keep_theirs(tmp_path: Path,
                                                              repo: Path) -> None:
    p = palace_at(tmp_path, lexical=True)
    code = replace(p.cfg.ingestion.code, enabled=True, embed=False,
                   repositories=(RepositoryConfig(REPO, repo, "main"),))
    p.cfg = replace(p.cfg, ingestion=replace(p.cfg.ingestion, code=code))
    assert p.cfg.embedding.enabled and lexical_code(p.cfg) and needs_lexical(p.cfg)
    calls: list[int] = []
    embed_documents = p.stores.embedder.embed_documents

    def counted(texts: list[str]) -> list[list[float]]:
        calls.append(len(texts))
        return embed_documents(texts)
    p.stores.embedder.embed_documents = counted          # type: ignore[method-assign]
    write_file(p.vault, "a.md", "a note about the drain")
    assert p.run("do sync_vault")["effects"] == {"landed": 1}
    assert calls                                              # the note was embedded
    embedded = sum(calls)
    assert p.run(f'do sync_repository(name: "{REPO}")')["effects"] == {"landed": 3}
    assert sum(calls) == embedded                             # the code was not
    held = {str(r["source_path"]) for r in p.stores.plane.all_rows(clearance=EVERY)}
    assert held == {str(p.vault / "a.md")}
    assert p.stores.lexical is not None
    assert p.stores.lexical.units_of("code/toy/pkg/embed.py") > 0
    assert p.run(f'do sync_repository(name: "{REPO}")')["effects"] == {"unchanged": 3}


def test_a_lazy_instance_asks_no_drain_for_code_that_keeps_no_vectors(tmp_path: Path,
                                                                      repo: Path) -> None:
    p = palace_at(tmp_path, lazy=True)
    code = replace(p.cfg.ingestion.code, enabled=True, embed=False,
                   repositories=(RepositoryConfig(REPO, repo, "main"),))
    p.cfg = replace(p.cfg, ingestion=replace(p.cfg.ingestion, code=code))
    assert p.run(f'do sync_repository(name: "{REPO}")')["effects"] == {"landed": 3}
    assert p.jobs == []                                       # the code's landing asks nothing
    write_file(p.vault, "a.md", "a note")
    assert p.run("do sync_vault")["effects"] == {"landed": 1}
    assert [kind for kind, _ in p.jobs] == ["embed"]          # the note's asks for its vector


# ── the configuration ─────────────────────────────────────────────────────────────────────────


def test_the_default_instance_is_what_it_was() -> None:
    cfg = load_config()
    assert cfg.embedding.enabled and cfg.ingestion.code.embed
    assert not lexical_code(cfg) and not needs_lexical(cfg)
    assert not any(s.kind == "repository" for s in build_table(cfg).sources.values())
    assert "reference" in build_table(cfg).places          # a place no default role writes into
    assert build_table(cfg).roles["ambassador"].prefixes.get("reference") is None


def test_the_code_instance_lives_outside_every_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.kernel.config import loader

    monkeypatch.setenv("MIND_PALACE_OVERLAY", "config/instances/code.toml")
    cfg = load_config()
    assert cfg.instance.id == "code" and not cfg.embedding.enabled
    assert cfg.instance.root == Path("~/.mind-palace/instances/code").expanduser()
    assert loader._working_tree_of(cfg.instance.root) is None
    assert cfg.paths.data_dir == cfg.instance.root / "data"
    assert lexical_code(cfg) and [r.name for r in cfg.ingestion.code.repositories] == [
        "mind-palace"]
    assert not cfg.secrets.enabled and not cfg.effectors.enabled
    assert not cfg.dreaming.scheduled and not cfg.integrate.enabled


@pytest.mark.parametrize("root, why", [
    ("instances/x", "relative"),
    ("", "names no directory"),
])
def test_a_declared_root_is_absolute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                     root: str, why: str) -> None:
    overlay = tmp_path / "x.toml"
    overlay.write_text(f'[instance]\nid = "lite-x"\nroot = "{root}"\n')
    monkeypatch.setenv("MIND_PALACE_OVERLAY", str(overlay))
    with pytest.raises(InstanceOverlayError, match=why):
        load_config()


def test_a_declared_root_inside_a_working_tree_refuses(tmp_path: Path, repo: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    overlay = tmp_path / "x.toml"
    overlay.write_text(f'[instance]\nid = "lite-x"\nroot = "{repo / "state"}"\n')
    monkeypatch.setenv("MIND_PALACE_OVERLAY", str(overlay))
    with pytest.raises(InstanceOverlayError, match="inside the git working tree"):
        load_config()
    outside = tmp_path / "home" / "lite-x"
    overlay.write_text(f'[instance]\nid = "lite-x"\nroot = "{outside}"\n')
    cfg = load_config()
    assert cfg.instance.root == outside and cfg.paths.data_dir == outside / "data"


def test_the_default_chain_refuses_a_root(tmp_path: Path) -> None:
    from core.kernel.config.loader import _ouroboros_instance

    with pytest.raises(InstanceOverlayError, match="named instance's"):
        _ouroboros_instance({"instance": {"root": str(tmp_path)}}, "x")


def test_repositories_are_named_once_with_known_keys(tmp_path: Path) -> None:
    got = _repositories({"repositories": [{"name": "a", "path": "~/a"},
                                          {"name": "b", "path": "rel", "ref": "dev"}]}, tmp_path)
    assert [(r.name, r.ref) for r in got] == [("a", "main"), ("b", "dev")]
    assert got[0].path == Path("~/a").expanduser() and got[1].path == tmp_path / "rel"
    assert len(_repositories({}, tmp_path)) == 1                         # the checkout
    for bad, why in ([{"name": "a", "path": "x"}, {"name": "a", "path": "y"}], "repeat"), \
                    ([{"name": "A b", "path": "x"}], "not a source name"), \
                    ([{"name": "a", "path": "x", "branch": "y"}], "unknown key"), \
                    ([{"name": "a"}], "names no path"), \
                    ([{"name": "a", "path": "x", "ref": "-x"}], "not a ref"):
        with pytest.raises(ValueError, match=why):
            _repositories({"repositories": bad}, tmp_path)


def test_the_mark_is_json_with_the_time(tmp_path: Path, repo: Path) -> None:
    cfg = lite_config(tmp_path / "lite", repo)
    _sync(cfg, ingress.build_stores(cfg))
    doc = json.loads(repository_mark(cfg, REPO).read_text())
    assert set(doc) == {"commit", "ref", "files", "at"} and doc["ref"] == "main"
