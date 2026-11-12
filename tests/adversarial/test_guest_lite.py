"""The guest over an instance that embeds nothing (dn-guest-principal §5, dn-palace-lite).

The guest's intended use is an external coding agent reading the code instance
(`config/instances/code.toml`), which embeds nothing: its items land with their lexical units and
no vector, `near` ranks them by the lexical index and says so, `read` opens a landed repository
file from the raw store, and `overview` says how current each repository is. An instance that
embeds nothing can also hold a vault: its notes land in the same lexical index as the code and the
dialogue, so the index's document frequencies, unit count and mean length would be a function of
the notes if a ranking read them over every class.

A palace that embeds nothing holds a note with a canary in its path, title and body, landed by the
ingress, a repository's files landed by `sync_repository`, a dialogue turn of each kind and a
paper with lexical units and no vector, and the fixture's transcript turn, causal edges and
citation graph. As the guest, the battery of `test_guest_leaks.py` is asked again with the code
source's own refs: no output carries the canary, the admitted strata answer lexically, and over a
second such palace whose note differs in its words and its length every output, `overview`
included, is the same once the names each asker typed are put back to one placeholder. The
Ambassador, asked the same, sees the note and counts its units. Last, the launcher serves the
guest over an overlay made from the code instance's own, its landed repository answering through
the protocol stream and nothing else reaching it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from core.attestation.store import open_attestation_store
from core.ingest import ingress
from core.kernel.config import REPO_ROOT
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance
from core.query import GUEST, QueryEngine
from core.sentence.surface import QueryLog
from core.stores.causal_edges import open_causal_edge_store
from core.stores.chatlog import ChatUtterance, open_chatlog_store
from tests.adversarial.test_guest_leaks import (
    AUTHORED,
    CODE,
    OBSERVED,
    PAPER,
    Fixture,
    _battery,
    _call,
    _canary,
    _edges,
    _eid,
    _meets,
    _outcome,
    _server,
)
from tests.fixtures.ingress import write_file
from tests.integration.test_palace_lite import lite_config
from tests.unit.test_sentence_universe import _Edge, _Refs

REPO = "toy"
FILE = f"code/{REPO}/pkg/orchard.py"
# The note of the first palace says the battery's words often, in over 300 terms; the second's
# says none of them, in four, so a ranking that counted the notes' units would differ between them.
WORDY = "The {c} body: a walnut orchard, a private plan. " + "Walnut orchard rows, walnut " * 80
TERSE = "The {c} body: errands."


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repository on `main` whose three files say the battery's words in different measure."""
    r = tmp_path / "repo"
    (r / "pkg").mkdir(parents=True)
    (r / "docs").mkdir()
    _git(r.parent, "init", "-q", "-b", "main", str(r))
    (r / "pkg" / "orchard.py").write_text(
        'def walnut_orchard(rows):\n    """Irrigate a walnut orchard, row by row."""\n'
        "    return rows\n")
    (r / "pkg" / "plan.py").write_text(
        "from pkg.orchard import walnut_orchard\n\n\ndef plan():\n"
        '    """The plan for the orchard."""\n    return walnut_orchard([])\n')
    (r / "docs" / "guide.md").write_text("# The guide\n\nHow the orchard is planned.\n")
    _git(r, "add", "-A")
    _git(r, "-c", "user.email=t@example.org", "-c", "user.name=t", "commit", "-q", "-m", "one")
    return r


def _land(stores: Any, path: str, text: str, prov: Provenance) -> None:
    """An item as a landing that embeds nothing leaves it: its bytes, its catalog entry and its
    lexical units, and no vector."""
    digest, _ = stores.raw.add_text(text)
    stores.catalog.record(path, digest, text[:24], provenance=prov)
    stores.lexical.land(source_path=path, digest=digest, provenance=prov.value, title=text[:24],
                        chunks=[Chunk(0, text)])


def _lite(root: Path, canary: str, repo: Path, body: str) -> Fixture:
    """A palace under `root` that embeds nothing: the note landed by `sync_vault`, the
    repository by `sync_repository`, the dialogue and a paper with lexical units alone, and the
    fixture's transcript turn, causal edges and citation graph."""
    cfg = lite_config(root, repo)
    stores = ingress.build_stores(cfg)
    write_file(cfg.ingestion.vault.path, f"{canary}.md",
               f"# {canary} title\n\n{body.format(c=canary)}\n")
    assert ingress.run_library(cfg, "sync_vault", stores=stores)["effects"] == {"landed": 1}
    assert ingress.run_library(cfg, "sync_repository", {"name": REPO},
                               stores=stores)["effects"] == {"landed": 3}
    (entry,) = [e for e in stores.catalog.active_entries()
                if str(e.provenance) == Provenance.AUTHORED_SOLO.value]
    assert canary in entry.source_path and canary in entry.title
    _land(stores, AUTHORED, "walnut orchard notes from the chat", Provenance.AUTHORED_DIALOGUE)
    _land(stores, OBSERVED, "a summary of the orchard plan", Provenance.OBSERVED)
    _land(stores, PAPER, "irrigation of walnut orchards", Provenance.CURATED)
    (attestation,) = [a.id for a in open_attestation_store(cfg).all()
                      if entry.digest in a.output_hashes]
    engine = QueryEngine(config=cfg)
    engine._cache["references"] = _Refs([_Edge("docs/guide.md", CODE, "c1"),
                                         _Edge(CODE, "core/kernel/scope.py", "c1")])
    note = entry.source_path
    f = Fixture(canary, engine, root, note, entry.title, _eid("s1", 1, note),
                _eid("s1", 2, CODE), attestation)
    open_causal_edge_store(cfg).replace_session("s1", _edges(f), "wd1")
    open_chatlog_store(cfg).add_batch([ChatUtterance("s1", 1, "owner", "please write the plan",
                                                     "wd1")])
    return f


@pytest.fixture
def lite(tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Fixture, Fixture]:
    """Two palaces that embed nothing, over one repository, whose notes differ in path, title,
    words and length; the citation graph's cut and the query log fixed."""
    import core.reference_view as rv
    from core.sentence import surface

    monkeypatch.setattr(rv, "_resolve_default_commit", lambda cfg: "c1")
    monkeypatch.setattr(surface, "default_log", lambda: QueryLog(tmp_path / "q.jsonl"))
    return (_lite(tmp_path / "a", _canary("a"), repo, WORDY),
            _lite(tmp_path / "b", _canary("b"), repo, TERSE))


def _lite_battery(f: Fixture) -> list[tuple[str, str]]:
    """The battery as an instance that embeds nothing answers it, then the code source's refs.
    No node keeps a vector, so `S` has no edge and its walks are empty; a paper is ranked by its
    lexical units and read from the curated plane, which such an instance does not have; every
    sentence the battery refuses is refused here too."""
    differs = {
        f'diffuse S from "{AUTHORED}" over dialogue': "empty",
        f'diffuse S from "{PAPER}" over curated': "refused",
        f'walk from "{AUTHORED}" via S over dialogue': "empty",
        f'read "{PAPER}"': "refused",
        f'near "walnut" over dialogue and diffuse S from "{AUTHORED}" over dialogue': "empty",
    }
    battery = [(s, differs.get(s, e)) for s, e in _battery(f)]
    assert set(differs) <= {s for s, _ in battery}
    return battery + [
        ('top 3 near "walnut orchard" over reference', "answered"),
        ('top 5 near "walnut orchard" over dialogue reference curated observed', "answered"),
        ('near "orchard plan" over reference observed', "answered"),
        (f'read "{FILE}"', "answered"),
        (f'read "{FILE}" chunk 1', "answered"),
        (f'diffuse S from "{FILE}" over reference', "empty"),
        (f'reach F from "{FILE}"', "empty"),
        (f'trace "{FILE}"', "refused"),
        (f'near "walnut" over reference within reach F from "{FILE}"', "admitted"),
        ('near "walnut orchard"', "refused"),
        (f'read "code/{REPO}/pkg/absent.py"', "refused"),
    ]


def test_no_guest_output_carries_the_canary_where_nothing_is_embedded(
        lite: tuple[Fixture, Fixture]) -> None:
    a, b = lite
    guest = _server(a, "guest")
    seen: dict[str, str] = {}
    for sentence, _ in _lite_battery(a):
        for trace in (False, True):
            error, text = _call(guest, "query", sentence=sentence, trace=trace)
            assert a.canary not in text and b.canary not in text, (sentence, text)
            assert a.note not in text and a.title not in text, sentence
            seen[sentence] = _outcome(error, text)
            if error:
                assert text.startswith("GuestRefusal: "), text
    wrong = {s: (seen[s], e) for s, e in _lite_battery(a) if not _meets(seen[s], e)}
    assert not wrong, wrong
    error, text = _call(guest, "overview")
    assert not error and a.canary not in text


def test_the_guest_cannot_tell_two_palaces_that_embed_nothing_apart(
        lite: tuple[Fixture, Fixture]) -> None:
    """Noninterference over the lexical index: the notes differ in their words and their length,
    and nothing the guest receives does, its ranks and scores and `overview`'s counts included.
    The Ambassador's answers and counts tell the two apart: the difference is in the stores."""
    a, b = lite

    def norm(f: Fixture, text: str) -> str:
        for name, mark in ((f.note, "<note>"), (f.title, "<title>"), (f.canary, "<canary>"),
                           (f.vault_edge, "<edge>"), (f.attestation, "<att>"),
                           (str(f.root), "<root>")):
            text = text.replace(name, mark)
        return text

    ga, gb = _server(a, "guest"), _server(b, "guest")
    for (sa, _), (sb, _) in zip(_lite_battery(a), _lite_battery(b), strict=True):
        for trace in (False, True):
            ea, ta = _call(ga, "query", sentence=sa, trace=trace)
            eb, tb = _call(gb, "query", sentence=sb, trace=trace)
            assert (ea, norm(a, ta)) == (eb, norm(b, tb)), sa
    assert _call(ga, "overview") == _call(gb, "overview")

    # the control: a grant that reads the mirror ranks the wordy note first and counts its units
    aa, ab = _server(a, "ambassador"), _server(b, "ambassador")
    error, text = _call(aa, "query", sentence='top 1 near "walnut orchard"')
    assert not error and json.loads(text)["hits"][0]["ref"] == a.note
    error, text = _call(ab, "query", sentence='top 1 near "walnut orchard"')
    assert not error and b.canary not in text
    units = [json.loads(_call(s, "overview")[1])["lexical_units"] for s in (aa, ab)]
    assert units[0] > units[1]


def test_every_lexical_read_the_guest_causes_names_classes_its_grant_reads(
        lite: tuple[Fixture, Fixture], monkeypatch: pytest.MonkeyPatch) -> None:
    """The mechanism under the noninterference test. A ranking's statistics are read over the
    classes it names, and over the whole index when it names none; a count likewise. While the
    guest asks the battery, the code source's refs and the overview, every score and every count
    the lexical index makes names its classes, and each is a class the grant reads. The
    Ambassador's `near` over the notes names the notes' class: the recorder sees it."""
    from core.kernel.clearance import classes_of
    from core.stores.lexical import LexicalStore

    asked: list[frozenset[str] | None] = []
    score, count = LexicalStore._score_units, LexicalStore.count

    def named(classes: Any) -> frozenset[str] | None:
        return None if classes is None else frozenset(str(c) for c in classes)

    def scored(self: LexicalStore, query: str, *, classes: Any, paths: Any) -> dict[int, float]:
        asked.append(named(classes))
        return score(self, query, classes=classes, paths=paths)

    def counted(self: LexicalStore, *, classes: Any = None) -> int:
        asked.append(named(classes))
        return count(self, classes=classes)

    monkeypatch.setattr(LexicalStore, "_score_units", scored)
    monkeypatch.setattr(LexicalStore, "count", counted)
    a, _ = lite
    guest = _server(a, "guest")
    for sentence, _ in _lite_battery(a):
        _call(guest, "query", sentence=sentence)
    _call(guest, "overview")
    readable = {p.value for p in classes_of(GUEST.strata)}
    assert len(asked) > 10
    assert all(c is not None and c <= readable for c in asked), asked
    asked.clear()
    _call(_server(a, "ambassador"), "query", sentence='near "walnut orchard"')
    assert any(c is not None and Provenance.AUTHORED_SOLO.value in c for c in asked), asked


def test_the_guest_reads_the_code_source_lexically(lite: tuple[Fixture, Fixture]) -> None:
    """What the code instance is for: `near` over reference ranks the repository's files by the
    lexical index and labels each hit, its notes say the instance embeds nothing, `read` opens a
    landed file from the raw store, `trace` is refused with the grant's hint, and `overview` says
    the profile, the units of the classes the grant reads and the commit each repository landed."""
    from agents.ambassador import mcp
    from core.kernel.clearance import classes_of
    from core.stores.lexical import open_lexical_store

    a, _ = lite
    guest = _server(a, "guest")

    def answer(sentence: str) -> dict[str, Any]:
        error, text = _call(guest, "query", sentence=sentence)
        assert not error, text
        return dict(json.loads(text))

    near = answer('top 3 near "walnut orchard" over reference')
    assert near["hits"][0]["ref"] == FILE
    assert {h["ref"] for h in near["hits"]} <= {FILE, f"code/{REPO}/pkg/plan.py",
                                                 f"code/{REPO}/docs/guide.md"}
    assert all(h["detail"]["ranked_by"] == "lexical: the item keeps no vector"
               for h in near["hits"])
    assert any("the instance embeds nothing" in n for n in near["notes"])
    (read,) = answer(f'read "{FILE}"')["hits"]
    assert read["stratum"] == "reference" and "def walnut_orchard" in read["text"]
    dialogue = answer('near "walnut orchard" over dialogue')["hits"]
    assert [h["ref"] for h in dialogue][:1] == [AUTHORED]
    error, text = _call(guest, "query", sentence=f'trace "{FILE}"')
    assert error and text.endswith(mcp.GUEST_SCOPE_HINT) and "no version plane" in text
    error, text = _call(guest, "query", sentence=f'read "code/{REPO}/pkg/absent.py"')
    assert (error, text) == (True, "GuestRefusal: lookup: " + mcp.GUEST_RAN["lookup"])
    assert "code/<name>/<path>" in text

    error, text = _call(guest, "overview")
    assert not error
    body = json.loads(text)
    head = _git(Path(a.engine.config.ingestion.code.repositories[0].path), "rev-parse", "main")
    assert body["embedding"] == mcp.EMBEDDING_OFF
    assert body["code"] == [{"repository": REPO, "ref": "main", "landed": head[:12],
                             "at": body["code"][0]["at"], "behind": 0}]
    assert body["catalog_by_provenance"] == {"code": 3, "authored-dialogue": 1, "observed": 1,
                                             "curated": 1}
    assert body["literature_chunks"] == 0
    lexical = open_lexical_store(a.engine.config)
    assert body["lexical_units"] == lexical.count(classes=classes_of(GUEST.strata)) \
        < lexical.count()


# ── the launcher over the code instance's overlay ──────────────────────────────────────────────


def _code_overlay(tmp_path: Path, repo: Path) -> Path:
    """The code instance's overlay (`config/instances/code.toml`) as a test runs it: every
    setting the same but the id, which one overlay may declare, the root, which is the owner's,
    and the repository, which is the fixture's."""
    declared = tomllib.loads((Path(REPO_ROOT) / "config" / "instances" / "code.toml").read_text())
    assert declared["embedding"] == {"enabled": False}
    assert declared["ingestion"]["vault"] == {"enabled": False}
    root = tmp_path / "home" / "code-guest"
    lines = ["[instance]", 'id = "code-guest"', f'root = "{root}"', ""]
    for section, values in declared.items():
        if section == "instance":
            continue
        for name, table in ([(f"{section}.{k}", v) for k, v in values.items()]
                            if section == "ingestion" else [(section, values)]):
            lines.append(f"[{name}]")
            lines += [f"{k} = {json.dumps(v)}" for k, v in table.items()
                      if k != "repositories"]
            lines.append("")
    lines += ["[[ingestion.code.repositories]]", f'name = "{REPO}"', f'path = "{repo}"',
              'ref = "main"', ""]
    overlay = tmp_path / "code-guest.toml"
    overlay.write_text("\n".join(lines))
    return overlay


def test_the_launcher_serves_the_guest_over_the_code_instances_overlay(
        tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`MIND_PALACE_OVERLAY=<the code overlay> palace_mcp.py --role guest`, as an MCP client
    spawns it, after the repository landed: one reply per request on stdout and nothing else,
    the landed files found and read, the refusals in their fixed words, the instance's own query
    log written with the guest's role, and no vector store made."""
    from agents.ambassador import mcp
    from core.kernel.config.loader import load_config

    overlay = _code_overlay(tmp_path, repo)
    monkeypatch.setenv("MIND_PALACE_OVERLAY", str(overlay))
    cfg = load_config()
    assert cfg.instance.id == "code-guest" and not cfg.embedding.enabled
    assert ingress.run_library(cfg, "sync_repository", {"name": REPO},
                               stores=ingress.build_stores(cfg))["effects"] == {"landed": 3}
    asked = [("initialize", {}), ("tools/list", {}),
             ("tools/call", {"name": "overview", "arguments": {}}),
             ("tools/call", {"name": "query", "arguments": {
                 "sentence": 'top 3 near "walnut orchard" over reference'}}),
             ("tools/call", {"name": "query", "arguments": {"sentence": f'read "{FILE}"'}}),
             ("tools/call", {"name": "query", "arguments": {"sentence": 'near "walnut"'}}),
             ("tools/call", {"name": "query", "arguments": {"sentence": f'trace "{FILE}"'}}),
             ("tools/call", {"name": "query", "arguments": {
                 "sentence": f'read "code/{REPO}/pkg/absent.py"'}}),
             ("tools/call", {"name": "status", "arguments": {}})]
    requests = "".join(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
                       + "\n" for i, (method, params) in enumerate(asked, 1))
    out = subprocess.run([sys.executable, str(Path(REPO_ROOT) / "scripts" / "palace_mcp.py"),
                          "--role", "guest"], capture_output=True, text=True, input=requests,
                         timeout=120, env={**os.environ, "MIND_PALACE_OVERLAY": str(overlay)})
    assert out.returncode == 0, out.stderr
    replies = [json.loads(line) for line in out.stdout.splitlines()]
    assert [r["id"] for r in replies] == list(range(1, len(asked) + 1))
    assert out.stdout.count("\n") == len(asked)
    assert replies[0]["result"]["instructions"] == mcp.GUEST_INSTRUCTIONS
    assert [t["name"] for t in replies[1]["result"]["tools"]] == ["query", "overview"]

    def text(i: int) -> tuple[bool, str]:
        result = replies[i]["result"]
        return result["isError"], result["content"][0]["text"]

    error, body = text(2)
    overview = json.loads(body)
    assert not error and overview["embedding"] == mcp.EMBEDDING_OFF
    assert overview["catalog_by_provenance"] == {"code": 3}
    assert [(c["repository"], c["behind"]) for c in overview["code"]] == [(REPO, 0)]
    error, body = text(3)
    assert not error and json.loads(body)["hits"][0]["ref"] == FILE
    error, body = text(4)
    assert not error and "def walnut_orchard" in json.loads(body)["hits"][0]["text"]
    error, body = text(5)
    assert error and body.startswith("GuestRefusal: scope: ")
    error, body = text(6)
    assert error and body.endswith(mcp.GUEST_SCOPE_HINT)
    assert text(7) == (True, "GuestRefusal: lookup: " + mcp.GUEST_RAN["lookup"])
    assert "unknown tool" in replies[8]["error"]["message"]
    logged = QueryLog(cfg.paths.data_dir / "query_log.jsonl").entries()
    assert [e.role for e in logged] == ["guest"] * 5
    assert not list(cfg.instance.root.rglob("*.lance"))
