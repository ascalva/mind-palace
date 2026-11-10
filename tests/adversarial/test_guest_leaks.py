"""The guest principal does not leak the owner's notes (dn-guest-principal, SCO-9).

A palace on real stores (the ingress's fixture palace: the vault, the plane, the catalog, the
versions, the relation edges, the attestations; the causal store and the chatlog beside them)
holds a note with a canary in its path, title and body, landed by the ingress, an interpreted
relation from it to an authored dialogue turn, and items in every stratum the guest reads: an
authored and an observed dialogue turn, a transcript turn whose causal edge points at the note
and a second at a repo file, a curated paper, a code atom, and the citation graph at a cut. As
the guest, over its MCP surface, every verb of the sentence algebra is asked, the ones that name
the note included, with every adjective and connective, `assume` and every request, then
`overview` and `status`. No output carries the canary: no path, title, text, count or refusal.
The admitted strata answer. And the guest's outputs are the same, byte for byte once the names
the asker typed are normalized, over a second palace whose note, relation and vault edge differ
(noninterference). The Ambassador, asked the same, sees the canary: the fixture is live, and the
withholding is what closes the causal and witness channels.

The causal and citation stores may also hold the note's path as a file system or an action log
spells it (another letter case, another Unicode normal form, a relative path, a URI, a bare file
name), and paths that are not the repo's. Adding such edges to a palace changes no guest output,
and `witness` of each answers nothing; the Ambassador sees every one."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from core.chat_events import _classify_file_write
from core.ingest import ingress
from core.integrator import _WRITE_KIND_TO_DST
from core.kernel.complex_types import EdgeSign
from core.kernel.config import REPO_ROOT
from core.kernel.provenance import Provenance
from core.kernel.scope import Privilege, Stratum, StratumScope, WorldReach
from core.query import AMBASSADOR, GUEST, OPERATOR, QueryEngine
from core.sentence import compile_sentence
from core.sentence.surface import QueryLog
from core.sentence.types import IllScopedSentence
from core.stores.causal_edges import CausalEdge, open_causal_edge_store
from core.stores.chatlog import ChatUtterance, open_chatlog_store
from core.stores.vectorstore import LAYER_CODE_AST
from tests.fixtures.embedding import DIM, FakeEmbedder
from tests.fixtures.ingress import palace_at, write_file
from tests.unit.test_sentence_universe import _Edge, _Refs

EMB = FakeEmbedder()
AUTHORED = "dialogue/tea/2026-11-09T10:00 (user)"
OBSERVED = "dialogue/tea/2026-11-09T10:01 (assistant)"
TURN = "transcript/s1/1"
PAPER = "reference:orchard-paper"
CODE = "core/query.py"
NOT_THE_MIRROR = {Stratum.MIRROR, Stratum.MIRROR_AUTHORED, Stratum.INTERPRETED}


def _canary(seed: str) -> str:
    """A token found in no file: made at run time, the same length for every seed."""
    return "cnry" + hashlib.sha256(seed.encode()).hexdigest()[:16]


def _eid(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:32]


@dataclass
class Fixture:
    canary: str
    engine: QueryEngine
    root: Path
    note: str           # the note's path, under the vault
    title: str          # the note's title
    vault_edge: str     # the causal edge whose endpoint is the note
    repo_edge: str      # the causal edge whose endpoint is a repo file
    attestation: str    # the attestation of the note's landing


def _dialogue(p: Any, path: str, text: str, prov: Provenance) -> str:
    digest, _ = p.stores.raw.add_text(text)
    p.stores.catalog.record(path, digest, text[:24], provenance=prov)
    p.stores.plane.add([{"source_path": path, "digest": digest, "provenance": prov.value,
                         "title": text[:24], "chunk_index": 0, "text": text, "layer": "prose",
                         "vector": EMB.embed_query(text)}])
    return digest


def _edges(f: Fixture) -> list[CausalEdge]:
    """The two proven edges of session s1: the turn's action wrote the note and a repo file (the
    projector stamps an action with the next utterance's index, so turn 1's actions carry
    witness_turn 2)."""
    return [CausalEdge(f.vault_edge, "s1", 1, "C", "file", f.note, "wd1", 2),
            CausalEdge(f.repo_edge, "s1", 2, "C", "file", f"{REPO_ROOT}/{CODE}", "wd1", 2)]


def _palace(base: Path, canary: str) -> Fixture:
    p = palace_at(base, "p")
    root = p.root
    write_file(p.vault, f"{canary}.md",
               f"# {canary} title\n\nThe {canary} body: a walnut orchard, a private plan.\n")
    p.run("do sync_vault")
    (entry,) = p.stores.catalog.active_entries()
    assert canary in entry.source_path and canary in entry.title     # the canary is everywhere
    assert canary in p.stores.raw.get(entry.digest).decode()
    authored = _dialogue(p, AUTHORED, "walnut orchard notes from the chat",
                         Provenance.AUTHORED_DIALOGUE)
    _dialogue(p, OBSERVED, "a summary of the orchard plan", Provenance.OBSERVED)
    # an interpreted relation from the note to the authored turn (a `link`'s product)
    assert p.stores.edges is not None
    p.stores.edges.add(entry.digest, authored, sign=EdgeSign.SUPPORT, rel_type="supports")
    (attestation,) = [a.id for a in p.att.all() if entry.digest in a.output_hashes]

    cfg = replace(p.cfg, embedding=replace(p.cfg.embedding, dim=DIM), paths=replace(
        p.cfg.paths, raw_store=root / "raw", vector_store=root / "vectors",
        derived_store=root / "derived.sqlite", vault_catalog=root / "catalog.sqlite",
        attestation_store=root / "att.sqlite", curated_store=root / "curated.lance",
        telemetry_db=root / "telemetry.sqlite"))
    engine = QueryEngine(cfg)
    engine._cache.update({
        "vectors": p.stores.plane, "catalog": p.stores.catalog, "embedder": p.stores.embedder,
        "edges": p.stores.edges, "versions": p.stores.versions, "attestations": p.att,
        "references": _Refs([_Edge("docs/guide.md", CODE, "c1"),
                             _Edge(CODE, "core/kernel/scope.py", "c1")]),
    })
    # a code atom and a paper, in the indexes `near … over reference` and `over curated` read
    p.stores.plane.add([{"id": "atom-guest", "digest": "dcode", "title": CODE,
                         "source_path": CODE, "chunk_index": 0, "provenance": "code",
                         "text": "GUEST = Grant(...)", "layer": LAYER_CODE_AST,
                         "qualname": "GUEST", "line_start": 1, "line_end": 9, "current": True,
                         "vector": EMB.embed_query("walnut orchard code")}])
    engine._get("curated").add([{"source_path": PAPER, "digest": "dpaper",
                                 "provenance": "curated", "title": "Orchard irrigation",
                                 "chunk_index": 0, "text": "irrigation of walnut orchards",
                                 "layer": "prose",
                                 "vector": EMB.embed_query("irrigation of walnut orchards")}])
    # a transcript turn whose action wrote the note and a repo file
    note = entry.source_path
    f = Fixture(canary, engine, root, note, entry.title, _eid("s1", 1, note), _eid("s1", 2, CODE),
                attestation)
    open_causal_edge_store(cfg).replace_session("s1", _edges(f), "wd1")
    open_chatlog_store(cfg).add_batch([ChatUtterance("s1", 1, "owner", "please write the plan",
                                                     "wd1")])
    return f


@pytest.fixture
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Where a test's palaces stand, the citation graph's cut and the query log fixed."""
    import core.reference_view as rv
    from core.sentence import surface

    monkeypatch.setattr(rv, "_resolve_default_commit", lambda cfg: "c1")
    monkeypatch.setattr(surface, "default_log", lambda: QueryLog(tmp_path / "q.jsonl"))
    return tmp_path


@pytest.fixture
def palaces(base: Path) -> tuple[Fixture, Fixture]:
    return _palace(base / "a", _canary("a")), _palace(base / "b", _canary("b"))


@pytest.fixture
def spelled(base: Path) -> Fixture:
    """A palace under a directory whose name has two Unicode normal forms, so its note's path
    has a second spelling there."""
    return _palace(base / unicodedata.normalize("NFC", "w\u00e9"), _canary("s"))


# ── the surfaces ───────────────────────────────────────────────────────────────────────────────


def _server(f: Fixture, role: str) -> Any:
    from agents.ambassador import mcp

    server = mcp.Server(role)
    tools: Any = mcp.Guest() if role == "guest" else mcp.Ambassador()
    tools.engine = f.engine
    server._amb = tools
    return server


def _call(server: Any, tool: str, **arguments: Any) -> tuple[bool, str]:
    reply = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                           "params": {"name": tool, "arguments": arguments}})
    if "error" in reply:
        return True, json.dumps(reply["error"])
    return reply["result"]["isError"], reply["result"]["content"][0]["text"]


def _battery(f: Fixture) -> list[tuple[str, str]]:
    """Every verb and connective, as (sentence, expected): `answered` (admitted, with hits),
    `admitted` (with or without hits), `empty` (admitted, no hits) or `refused`. Every sentence
    that names the note is refused; the admitted ones never carry the canary in their own words,
    so an answer's echo of its sentence cannot carry it either."""
    n, t = f.note, f.title
    over = "over dialogue reference curated observed"
    return [
        # near, with and without `over`
        ('near "walnut orchard"', "refused"),
        (f'near "walnut orchard" {over}', "answered"),
        ('top 3 near "walnut orchard" over dialogue', "answered"),
        ('near "walnut orchard" over observed', "answered"),
        ('near "walnut orchard" over mirror', "refused"),
        ('near "walnut orchard" over mirror_authored', "refused"),
        ('near "walnut orchard" over interpreted', "refused"),
        # diffuse
        (f'diffuse S from "{AUTHORED}" over dialogue', "answered"),
        (f'diffuse S from "{PAPER}" over curated', "admitted"),
        (f'diffuse S from "{n}"', "refused"),
        (f'diffuse S from "{n}" over dialogue', "refused"),
        (f'diffuse S from "{t}" over dialogue', "refused"),
        (f'diffuse F from "{CODE}"', "answered"),
        # reach F, C and D, forward and back
        (f'reach F from "{CODE}"', "answered"),
        (f'reach F from "{CODE}" forward', "answered"),
        (f'reach F from "{CODE}" depth 2 back', "answered"),
        (f'reach F from "{n}"', "refused"),
        (f'reach C from "{TURN}" over dialogue', "admitted"),     # a mask: no file
        (f'reach C from "{TURN}" over reference', "answered"),
        (f'reach C from "{TURN}" forward over reference', "answered"),
        (f'reach C from "{TURN}" depth 2 over dialogue_transcript reference', "answered"),
        (f'reach C from "{TURN}"', "refused"),
        (f'reach C from "{CODE}" back over dialogue', "answered"),
        (f'reach C from "{n}" back over dialogue', "refused"),
        (f'reach C from "{t}" back over dialogue', "refused"),
        (f'reach D from "{n}"', "refused"),
        (f'reach D from "{n}" back', "refused"),
        (f'reach D from "{AUTHORED}" over dialogue', "refused"),
        # relate, trace
        (f'relate "{n}"', "refused"),
        (f'relate "{AUTHORED}"', "refused"),
        (f'trace "{n}"', "refused"),
        (f'trace "{AUTHORED}" back', "refused"),
        # walk, a regular expression over S, F, D, C
        (f'walk from "{TURN}" via C over dialogue', "admitted"),
        (f'walk from "{TURN}" via C over dialogue reference', "answered"),
        (f'walk from "{TURN}" via CF over reference dialogue_transcript', "answered"),
        (f'walk from "{TURN}" to "{CODE}" via C over reference', "answered"),
        (f'walk from "{CODE}" via F+', "answered"),
        (f'walk from "{AUTHORED}" via S over dialogue', "answered"),
        (f'walk from "{TURN}" via C', "refused"),
        (f'walk from "{TURN}" via CD over dialogue', "refused"),
        (f'walk from "{n}" via S', "refused"),
        (f'walk from "{TURN}" to "{n}" via C over dialogue', "refused"),
        # witness: the vault edge and the note's landing are no record to the guest
        (f'witness "{f.vault_edge}"', "empty"),
        (f'witness "{f.repo_edge}"', "answered"),
        (f'witness "{f.attestation}"', "empty"),
        # read
        (f'read "{n}"', "refused"),
        (f'read "{t}"', "refused"),
        (f'read "~/{Path(n).name}"', "refused"),
        (f'read "{AUTHORED}"', "answered"),
        (f'read "{OBSERVED}"', "answered"),
        (f'read "{TURN}"', "answered"),
        (f'read "{PAPER}"', "answered"),
        (f'read "{CODE}"', "answered"),
        # assume: no overlay
        (f'assume S "{AUTHORED}" "{OBSERVED}" +0.5 in near "walnut" over dialogue', "refused"),
        (f'assume sever F "docs/guide.md" "{CODE}" in reach F from "{CODE}"', "refused"),
        (f'assume contradict "{n}" "{AUTHORED}" in near "walnut" over dialogue', "refused"),
        # the adjectives and connectives
        (f'top 2 near "walnut" over dialogue within reach C from "{TURN}" over dialogue',
         "admitted"),
        ('far near "walnut" over dialogue', "answered"),
        (f'not reach F from "{CODE}"', "admitted"),
        ('atleast 0.1 near "walnut" over curated', "answered"),
        (f'near "walnut" over dialogue and diffuse S from "{AUTHORED}" over dialogue',
         "answered"),
        (f'reach F from "{CODE}" then near "walnut" over reference', "admitted"),
        (f'top 5 near "walnut" over dialogue minus reach C from "{TURN}" over dialogue',
         "answered"),
        ('near "walnut" over dialogue or near "walnut" over curated', "answered"),
        (f'reach F from "{CODE}" as of "c1"', "answered"),
        (f'near "walnut" over dialogue within relate "{n}"', "refused"),
        (f'top 3 near "walnut" over dialogue within reach F from "{n}"', "refused"),
        # requests: none, whatever they name
        ("do dream", "refused"),
        ("do sync_vault", "refused"),
        (f'do capture(text: "{f.canary}", conversation: "x")', "refused"),
        (f'do link(a: "{n}", b: "{AUTHORED}", relation: "supports")', "refused"),
    ]


def _outcome(error: bool, text: str) -> str:
    if error:
        return "refused"
    return "answered" if json.loads(text).get("hits") else "empty"


def _meets(seen: str, expected: str) -> bool:
    return seen == expected or (expected == "admitted" and seen != "refused")


# ── the grant ──────────────────────────────────────────────────────────────────────────────────


def test_the_guest_grant_reads_neither_the_mirror_nor_the_interpreted_stratum() -> None:
    """SCO-9, as the code holds it: the closure of the four strata adds their refinements and
    nothing of the mirror (SCO-1); no plane proposes, writes or reaches the world, none names the
    overlay; the role resolves to it and has no spool."""
    assert StratumScope.of(Stratum.DIALOGUE, Stratum.REFERENCE, Stratum.CURATED,
                           Stratum.OBSERVED).strata == GUEST.strata == frozenset({
        Stratum.DIALOGUE, Stratum.DIALOGUE_TRANSCRIPT, Stratum.DIALOGUE_ARTIFACT,
        Stratum.REFERENCE, Stratum.REFERENCE_REPO, Stratum.CURATED, Stratum.OBSERVED})
    assert not GUEST.strata & (NOT_THE_MIRROR | {Stratum.HYPOTHETICAL, Stratum.EXHAUST})
    for plane in GUEST.scopes:
        a = plane.authority
        assert (a.privilege, a.store_write, a.world) == (Privilege.READ, 0, WorldReach.NONE)
    # the Ambassador's planes without the mirror's version plane: same clocks and fibers
    assert [(s.time.clock, s.edges.fibers) for s in GUEST.scopes] == [
        (s.time.clock, s.edges.fibers) for s in AMBASSADOR.scopes[:2]]
    assert ingress.grant_for("guest") is GUEST and "guest" not in ingress.roles()
    assert AMBASSADOR.strata & NOT_THE_MIRROR and OPERATOR.strata & NOT_THE_MIRROR


def test_the_guest_role_is_refused_every_request() -> None:
    """ING-1: no plane carries the write bit, so a request compiled for the role is refused,
    and the spool knows no such role, so one compiled for another could not be spooled."""
    from core.kernel.config import get_config
    from core.sentence.interpret import ScriptError

    for text in ("do dream", "do sync_vault", 'do capture(text: "t")',
                 'do { store "x" in "observed" at "dialogue/x" }'):
        with pytest.raises((IllScopedSentence, ScriptError)):
            compile_sentence(text, ingress.grant_for("guest"), role="guest")
    plan = compile_sentence('do capture(text: "t")', ingress.grant_for("ambassador"),
                            role="ambassador")
    with pytest.raises(IllScopedSentence, match="knows no role"):   # refused before any spool
        ingress.write_request(get_config(), role="guest", plan=plan)


# ── the leak battery ───────────────────────────────────────────────────────────────────────────


def test_no_guest_output_carries_the_canary(palaces: tuple[Fixture, Fixture]) -> None:
    a, b = palaces
    guest = _server(a, "guest")
    seen: dict[str, str] = {}
    for sentence, _ in _battery(a):
        for trace in (False, True):
            error, text = _call(guest, "query", sentence=sentence, trace=trace)
            assert a.canary not in text and b.canary not in text, (sentence, text)
            assert a.note not in text and a.title not in text, sentence
            seen[sentence] = _outcome(error, text)
            if error:
                assert text.startswith("GuestRefusal: "), text
    wrong = {s: (seen[s], e) for s, e in _battery(a) if not _meets(seen[s], e)}
    assert not wrong, wrong


def test_refusals_name_the_fix_and_echo_nothing(palaces: tuple[Fixture, Fixture]) -> None:
    a, _ = palaces
    guest = _server(a, "guest")
    error, text = _call(guest, "query", sentence='near "walnut orchard"')
    assert error and "scope:" in text and "mirror_authored" in text
    assert "`over dialogue reference curated observed`" in text
    error, text = _call(guest, "query", sentence=f'diffuse S from "{a.title}" over dialogue')
    assert error and text.startswith("GuestRefusal: lookup:") and a.title not in text
    assert f'"<{len(a.title)}>"' in text                     # the asker's own words, as a length
    error, text = _call(guest, "query", sentence=f'read "{a.note}"')
    assert error and "scope:" in text and a.note not in text
    error, text = _call(guest, "query", sentence=f'do capture(text: "{a.canary}")')
    assert error and a.canary not in text and "no write bit for `do`" in text


def test_the_admitted_strata_answer(palaces: tuple[Fixture, Fixture]) -> None:
    a, _ = palaces
    guest = _server(a, "guest")

    def hits(sentence: str) -> list[dict[str, Any]]:
        error, text = _call(guest, "query", sentence=sentence)
        assert not error, text
        return list(json.loads(text)["hits"])

    found = hits('top 10 near "walnut orchard" over dialogue reference curated observed')
    assert {h["stratum"] for h in found} == {"dialogue", "reference", "curated"}
    assert {AUTHORED, OBSERVED, PAPER, CODE} <= {h["ref"] for h in found}
    assert "walnut" in hits(f'read "{AUTHORED}"')[0]["text"]
    assert hits(f'read "{CODE}"')[0]["stratum"] == "reference"
    assert hits(f'read "{PAPER}"')[0]["text"] == "irrigation of walnut orchards"
    assert hits(f'read "{TURN}"')[0]["text"] == "please write the plan"
    assert {h["ref"] for h in hits(f'reach F from "{CODE}" back')} >= {"docs/guide.md"}
    # the turn's other action, a repo file, stays visible; the note's is withheld whole
    (end,) = hits(f'reach C from "{TURN}" over reference')
    assert end["ref"] == CODE and end["detail"]["witness"] == a.repo_edge
    assert hits(f'witness "{a.repo_edge}"')[0]["detail"]["transcript"] == TURN
    error, text = _call(guest, "query", sentence=f'reach C from "{TURN}" over reference')
    assert "withheld: the grant names no stratum of the mirror" in text


def test_the_guest_cannot_tell_two_palaces_apart(palaces: tuple[Fixture, Fixture]) -> None:
    """Noninterference: the palaces differ in the note (path, title, body), its relation, its
    landing and the vault edge, and in nothing a guest reads. Every output is the same once the
    names each asker typed are put back to one placeholder."""
    a, b = palaces

    def norm(f: Fixture, text: str) -> str:
        for name, mark in ((f.note, "<note>"), (f.title, "<title>"), (f.canary, "<canary>"),
                           (f.vault_edge, "<edge>"), (f.attestation, "<att>"),
                           (str(f.root), "<root>")):
            text = text.replace(name, mark)
        return text

    ga, gb = _server(a, "guest"), _server(b, "guest")
    for (sa, _), (sb, _) in zip(_battery(a), _battery(b), strict=True):
        for trace in (False, True):
            ea, ta = _call(ga, "query", sentence=sa, trace=trace)
            eb, tb = _call(gb, "query", sentence=sb, trace=trace)
            assert (ea, norm(a, ta)) == (eb, norm(b, tb)), sa
    assert _call(ga, "overview") == _call(gb, "overview")


# ── the note under other spellings, and endpoints that are not the repo's ──────────────────────


def _spellings(f: Fixture) -> dict[str, tuple[str, str]]:
    """Causal endpoints a guest must not see named, as (dst_type, dst): the note's path as a
    file system may treat it or an action log record it, a path in the checkout that git does
    not track, and a path outside the repo. Each holds the canary."""
    vault = Path(str(f.engine.config.ingestion.vault.path))
    name = Path(f.note).name
    # a vault file under a `docs/design-notes/` folder: the projector keeps its file name alone
    kind, doc = _classify_file_write(str(vault / "docs" / "design-notes" / name))
    out = {
        "case": ("file", f.note.replace(str(vault), str(vault.parent / vault.name.upper()))),
        "nfd": ("file", unicodedata.normalize("NFD", f.note)),
        "relative": ("file", os.path.relpath(f.note)),               # from this directory
        "relative, elsewhere": ("file", f"{vault.parent.name}/{vault.name}/{name}"),
        "uri": ("file", f"file://{f.note}"),
        "doc": (_WRITE_KIND_TO_DST[kind], doc),
        "untracked": ("file", f"{REPO_ROOT}/data/{f.canary}-untracked.md"),
        "outside": ("file", str(f.root.parent / "elsewhere" / f"{f.canary}-outside.txt")),
    }
    assert out["doc"] == ("doc", name) and len({dst for _, dst in out.values()} | {f.note}) == 9
    assert all(f.canary in dst for _, dst in out.values())
    return out


def _answers(server: Any, sentences: list[str]) -> list[tuple[bool, str]]:
    """Each sentence asked without and with its trace, then the overview."""
    asked = [_call(server, "query", sentence=s, trace=t) for s in sentences for t in (False, True)]
    return [*asked, _call(server, "overview")]


def test_an_edge_is_shown_only_when_it_ends_at_a_commit_or_a_tracked_file(
        spelled: Fixture) -> None:
    """The universe's allow list (dn-guest-principal §5). The causal store gains eight edges from
    the fixture's turn, and the citation graph four from a repo file to the note's path, as it
    is and in three spellings that are no repo-relative path. Asked the battery, each new edge's
    id and each new endpoint by its own name, the guest answers what it answered before they
    were added, byte for byte; no answer holds the canary; `witness` of each id is empty. The
    Ambassador is shown all of them."""
    f = spelled
    extra = _spellings(f)
    ids = {name: _eid("s1", 10 + k, dst) for k, (name, (_, dst)) in enumerate(extra.items())}
    cited = [f.note, extra["case"][1], extra["nfd"][1], f"~/{Path(f.note).name}"]
    battery = [s for s, _ in _battery(f)]
    probes = [f'witness "{i}"' for i in ids.values()] + [
        f'reach C from "{dst}" back over dialogue' for _, dst in extra.values()] + [
        f'reach F from "{CODE}" depth 2 over reference']
    guest = _server(f, "guest")
    before = _answers(guest, battery + probes)

    open_causal_edge_store(f.engine.config).replace_session("s1", _edges(f) + [
        CausalEdge(ids[name], "s1", 10 + k, "C", kind, dst, "wd1", 2)
        for k, (name, (kind, dst)) in enumerate(extra.items())], "wd1")
    f.engine._cache["references"].edges += [_Edge(CODE, dst, "c1") for dst in cited]

    after = _answers(guest, battery + probes)
    assert after == before                                   # noninterference, no name normalized
    for _, text in after[:2 * len(battery)]:                 # the battery, each sentence twice
        assert f.canary not in text, text                    # every new endpoint holds it
    for name, edge in ids.items():
        assert _outcome(*_call(guest, "query", sentence=f'witness "{edge}"')) == "empty", name
    (end,) = json.loads(_call(guest, "query",
                              sentence=f'reach C from "{TURN}" over dialogue reference')[1])["hits"]
    assert end["ref"] == CODE and end["detail"]["witness"] == f.repo_edge

    # the control: the edges are in the stores, and a grant that reads the mirror is shown them
    amb = _server(f, "ambassador")
    for name, (_, dst) in extra.items():
        error, text = _call(amb, "query", sentence=f'witness "{ids[name]}"')
        assert not error and json.loads(text)["hits"][0]["detail"]["dst"] == dst, name
    error, text = _call(amb, "query", sentence=f'reach C from "{TURN}" over dialogue reference')
    assert {h["detail"].get("witness") for h in json.loads(text)["hits"]} >= set(ids.values())
    error, text = _call(amb, "query", sentence=f'reach F from "{CODE}"')
    assert {h["ref"] for h in json.loads(text)["hits"]} >= set(cited)


def test_overview_counts_only_what_the_grant_reads_and_status_is_absent(
        palaces: tuple[Fixture, Fixture]) -> None:
    a, _ = palaces
    guest = _server(a, "guest")
    error, text = _call(guest, "overview")
    assert not error and a.canary not in text
    body = json.loads(text)
    assert set(body) == {"catalog_by_provenance", "literature_chunks", "your_grant"}
    assert body["catalog_by_provenance"] == {"authored-dialogue": 1, "observed": 1}
    assert body["literature_chunks"] == 1
    assert all(not set(p["strata"]) & {s.value for s in NOT_THE_MIRROR} and not p["write"]
               for p in body["your_grant"])
    # the Ambassador's overview counts the note and its relation: what the guest's leaves out
    error, amb = _call(_server(a, "ambassador"), "overview")
    assert json.loads(amb)["catalog_by_provenance"]["authored-solo"] == 1
    assert json.loads(amb)["relation_edges"] == {"supports": 1}
    for tool in ("status", "capture", "task_list", "task_add", "remind", "link", "dream",
                 "relate", "sync_dialogue", "sync_notes", "task_update"):
        error, text = _call(guest, tool)
        assert error and "unknown tool" in text


def test_the_ambassador_sees_what_the_guest_is_denied(palaces: tuple[Fixture, Fixture]) -> None:
    """The positive control: the same palace, asked by the Ambassador, carries the canary in
    the channels the guest's battery tried, so the battery would have caught a leak."""
    a, _ = palaces
    amb = _server(a, "ambassador")
    for sentence in ('near "walnut orchard"', f'reach C from "{TURN}" over dialogue',
                     f'witness "{a.vault_edge}"', f'relate "{a.note}"', f'read "{a.note}"'):
        error, text = _call(amb, "query", sentence=sentence)
        assert not error and a.canary in text, (sentence, text)


def test_the_default_server_is_the_ambassadors() -> None:
    from agents.ambassador import mcp

    default, guest = mcp.Server(), mcp.Server("guest")
    assert default.tools is mcp.TOOLS and default.instructions == mcp.INSTRUCTIONS
    assert [t[0] for t in guest.tools] == ["query", "overview"]
    assert guest.instructions == mcp.GUEST_INSTRUCTIONS != mcp.INSTRUCTIONS
    with pytest.raises(ValueError, match="role is one of"):
        mcp.Server("intruder")


def test_the_launcher_serves_the_guest_on_stdio() -> None:
    """The command line an MCP client spawns: `palace_mcp.py --role guest` seals, then lists
    the guest's two tools; an unknown role is refused before anything is served."""
    script = str(Path(REPO_ROOT) / "scripts" / "palace_mcp.py")
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    out = subprocess.run([sys.executable, script, "--role", "guest"], capture_output=True,
                         text=True, input="\n".join(map(json.dumps, lines)) + "\n", timeout=60)
    replies = [json.loads(x) for x in out.stdout.splitlines()]
    assert [t["name"] for t in replies[1]["result"]["tools"]] == ["query", "overview"]
    bad = subprocess.run([sys.executable, script, "--role", "intruder"], capture_output=True,
                         text=True, input="", timeout=60)
    assert bad.returncode == 1 and "--role is one of ambassador, guest" in bad.stderr
