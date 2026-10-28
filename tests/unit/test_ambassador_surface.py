"""The Ambassador's surface: the query algebra, signed relations, dialogue capture, the Open WebUI
reader and the MCP protocol. Hermetic — fakes stand in for the embedder and the model."""

from __future__ import annotations

import io
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.kernel.scope import Clock, Stratum, Window
from core.query import (
    AMBASSADOR,
    Grant,
    IllScopedQuery,
    InadmissibleGrant,
    Mode,
    Query,
    Verb,
    free_energy_distances,
    required,
    scope,
)
from core.relations import RELATIONS, parse_label

# ── the algebra ─────────────────────────────────────────────────────────────────────────────────


def test_mode_is_a_corollary_of_scope():
    assert Query(Verb.SEARCH, AMBASSADOR, text="x").mode is Mode.SEMANTIC
    assert Query(Verb.DIFFUSE, AMBASSADOR, target="n").mode is Mode.STRUCTURAL
    assert Query(Verb.REACH, AMBASSADOR, target="n").mode is Mode.STRUCTURAL
    assert Query(Verb.HISTORY, AMBASSADOR, target="n").mode is Mode.TEMPORAL
    assert Query(Verb.SEARCH, AMBASSADOR, text="x", history=True).mode is Mode.TEMPORAL
    assert Query(Verb.ORIGIN, AMBASSADOR, target="e").mode is Mode.CAUSAL


def test_an_ill_scoped_sentence_cannot_be_constructed():
    mirror_only = Grant(
        (scope({Stratum.MIRROR_AUTHORED}, set(), Clock.PROJECTION_EVENT, Window.all()),)
    )
    Query(Verb.SEARCH, mirror_only, text="x")  # admitted
    with pytest.raises(IllScopedQuery):
        Query(Verb.SEARCH, mirror_only, text="x", strata=(Stratum.OBSERVED,))
    with pytest.raises(IllScopedQuery):
        Query(Verb.HISTORY, mirror_only, target="n")  # needs D on the N_s clock
    with pytest.raises(IllScopedQuery):
        Query(Verb.DIFFUSE, mirror_only, target="n")  # needs F


def test_a_grant_cannot_name_the_foundation_or_reach_the_world():
    with pytest.raises(InadmissibleGrant):
        Grant((scope({Stratum.FOUNDATION}, set(), Clock.PROJECTION_EVENT, Window.all()),))


def test_the_ambassador_never_gets_world_reach_or_the_hypothetical_overlay():
    for s in AMBASSADOR.scopes:
        assert int(s.authority.world) == 0
        assert Stratum.HYPOTHETICAL not in s.sigma.strata and Stratum.EXHAUST not in s.sigma.strata


def test_capture_writes_only_where_the_grant_has_store_write():
    req = required(Verb.CAPTURE)
    assert req.authority.store_write == 1 and AMBASSADOR.admits(req)
    reader = Grant((scope({Stratum.DIALOGUE}, set(), Clock.PROJECTION_EVENT, Window.all()),))
    assert not reader.admits(req)


def test_delegation_never_widens():
    narrow = Grant((scope({Stratum.MIRROR}, set(), Clock.PROJECTION_EVENT, Window.all()),))
    met = AMBASSADOR.meet(narrow)
    assert all(
        any(m <= g for g in AMBASSADOR.scopes) and any(m <= n for n in narrow.scopes)
        for m in met.scopes
    )


# ── the β-curve ─────────────────────────────────────────────────────────────────────────────────


def _path_graph() -> np.ndarray:
    # 0 — 1 — 2 — 3, plus a weak shortcut 0 — 3
    w = np.zeros((4, 4))
    for a, b, x in [(0, 1, 0.9), (1, 2, 0.9), (2, 3, 0.9), (0, 3, 0.2)]:
        w[a, b] = w[b, a] = x
    return w


def test_free_energy_is_a_symmetric_distance_with_zero_diagonal():
    d = free_energy_distances(_path_graph(), beta=1.0)
    assert (
        np.allclose(d, d.T) and np.allclose(np.diag(d), 0) and (d[~np.eye(4, dtype=bool)] > 0).all()
    )


def test_large_beta_follows_the_cheapest_path_small_beta_averages_paths():
    """At large β the distance follows the cheapest path in c = −log w (the chain order 1 < 2 < 3),
    and the dial genuinely changes the geometry between the two ends of the curve."""
    hot, cold = (
        free_energy_distances(_path_graph(), beta=20.0),
        free_energy_distances(_path_graph(), beta=0.05),
    )
    assert hot[0, 1] < hot[0, 2] < hot[0, 3]  # chain order at the tropical end
    assert not np.allclose(hot[0], cold[0])  # the dial changes the geometry


def test_unreachable_nodes_are_infinitely_far():
    w = _path_graph()
    w5 = np.zeros((5, 5))
    w5[:4, :4] = w
    assert np.isinf(free_energy_distances(w5, beta=1.0)[0, 4])


def test_the_walk_needs_the_gamma_ceiling():
    with pytest.raises(ValueError):
        free_energy_distances(_path_graph(), beta=1.0, z=1.0)


# ── relations ───────────────────────────────────────────────────────────────────────────────────


def test_labels_parse_and_unknown_answers_write_nothing():
    assert parse_label("Contradicts — B rejects it") == "contradicts"
    assert parse_label("**supports**") == "supports"
    assert parse_label("I am not sure") == "unrelated"
    assert set(RELATIONS) == {"supports", "contradicts", "contextualizes"}
    assert int(RELATIONS["contradicts"][0]) == -1 and int(RELATIONS["supports"][0]) == 1


def test_the_detector_writes_interpreted_edges_oldest_to_newest(tmp_path: Path):
    from core.kernel.config import loader
    from core.relations import Note, RelationDetector
    from core.stores.edges import EdgeStore

    a = Note("/v/a.md", "a", "da", "2026-07-01T000000")
    b = Note("/v/b.md", "b", "db", "2026-07-02T000000")

    class Fake:
        def __init__(self) -> None:
            self.rows = [
                {"source_path": "/v/a.md", "vector": [1.0, 0.0]},
                {"source_path": "/v/b.md", "vector": [0.8, 0.6]},
            ]

        def all_rows(self, **_: Any) -> list[dict[str, Any]]:
            return self.rows

    edges = EdgeStore(tmp_path / "edges.sqlite")
    det = RelationDetector(
        config=loader.load_config(),
        edges=edges,
        catalog=None,
        vectors=Fake(),
        chat=lambda m: "contradicts",
    )
    det.notes = lambda: [a, b]  # type: ignore[method-assign]
    det.authored = lambda notes: 0  # type: ignore[method-assign]
    report = det.run()
    (e,) = edges.all()
    assert report.written == {"contradicts": 1}
    assert (e.u, e.v, e.rel_type, int(e.sign), e.provenance) == (
        "da",
        "db",
        "contradicts",
        -1,
        "interpreted",
    )
    assert e.w == pytest.approx(0.8)
    assert det.run().skipped_existing == 1  # a related pair is not re-judged


# ── dialogue capture ────────────────────────────────────────────────────────────────────────────


def test_turns_are_idempotent_and_provenance_follows_role(tmp_path: Path):
    from core.ingest.dialogue import DialogueCapture
    from core.ingest.embed import Embedder
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog
    from core.stores.vectorstore import VectorStore

    class Embed:
        dim = 4

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

        def embed_query(self, text: str) -> list[float]:
            return [1.0, 0.0, 0.0, 0.0]

    cap = DialogueCapture(
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=4),
        embedder=cast("Embedder", Embed()),
        catalog=VaultCatalog(tmp_path / "c.sqlite"),
    )
    _, made = cap.capture_turn(
        "hello palace", conversation="openwebui/c1", turn_id="m1", role="user"
    )
    _, again = cap.capture_turn(
        "hello palace", conversation="openwebui/c1", turn_id="m1", role="user"
    )
    cap.capture_turn("hi, owner", conversation="openwebui/c1", turn_id="m2", role="assistant")
    provs = {e.source_path: e.provenance for e in cap.catalog.active_entries()}
    assert made and not again
    assert provs == {
        "dialogue/openwebui/c1/m1": "authored-dialogue",
        "dialogue/openwebui/c1/m2": "observed",
    }


# ── the Open WebUI reader ───────────────────────────────────────────────────────────────────────


def test_the_reader_walks_the_active_branch_only(tmp_path: Path):
    from edge.openwebui import export_chats

    db = tmp_path / "webui.db"
    con = sqlite3.connect(db)
    con.execute("create table chat (id text, title text, updated_at int, chat text, archived int)")
    history = {
        "currentId": "a2",
        "messages": {
            "u1": {
                "id": "u1",
                "parentId": None,
                "role": "user",
                "content": "first",
                "timestamp": 1,
            },
            "a1": {
                "id": "a1",
                "parentId": "u1",
                "role": "assistant",
                "content": "abandoned",
                "timestamp": 2,
            },
            "a2": {
                "id": "a2",
                "parentId": "u1",
                "role": "assistant",
                "content": "kept",
                "timestamp": 3,
            },
        },
    }
    con.execute("insert into chat values ('c1', 't', 5, ?, 0)", (json.dumps({"history": history}),))
    con.execute(
        "insert into chat values ('c2', 'old', 4, ?, 1)", (json.dumps({"history": history}),)
    )
    con.commit()
    (chat,) = export_chats("unused", runner=[sys.executable], db=str(db))
    assert chat["chat_id"] == "c1"  # archived chats skipped
    assert [(t["role"], t["content"]) for t in chat["turns"]] == [
        ("user", "first"),
        ("assistant", "kept"),
    ]


# ── the MCP protocol ────────────────────────────────────────────────────────────────────────────


def _talk(lines: list[dict[str, Any]], server: Any = None) -> list[dict[str, Any]]:
    from agents.ambassador import mcp

    out = io.StringIO()
    if server is not None:
        mcp.Server = lambda: server  # type: ignore[assignment,misc]
    mcp.serve(io.StringIO("\n".join(json.dumps(m) for m in lines) + "\n"), out)
    return [json.loads(x) for x in out.getvalue().splitlines()]


def test_mcp_handshake_lists_tools_and_ignores_notifications():
    replies = _talk(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "nope"},
        ]
    )
    assert [r["id"] for r in replies] == [1, 2, 3]
    assert replies[0]["result"]["capabilities"] == {"tools": {"listChanged": False}}
    names = {t["name"] for t in replies[1]["result"]["tools"]}
    assert {"search", "read", "history", "related", "sync_dialogue", "capture", "dream"} <= names
    assert all(t["inputSchema"]["type"] == "object" for t in replies[1]["result"]["tools"])
    assert replies[2]["error"]["code"] == -32601


def test_a_failing_tool_is_an_error_result_not_a_crash(monkeypatch: pytest.MonkeyPatch):
    from agents.ambassador import mcp

    class Boom:
        def search(self, **_: Any) -> None:
            raise PermissionError("refused")

    server = mcp.Server()
    server._amb = Boom()  # type: ignore[assignment]
    (reply,) = [
        server.handle(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": "search", "arguments": {"query": "x"}},
            }
        )
    ]
    assert reply is not None
    assert reply["result"]["isError"] is True
    assert "refused" in reply["result"]["content"][0]["text"]


def test_the_opencode_reader_keeps_text_parts_of_top_level_sessions(tmp_path: Path) -> None:
    from edge.opencode_sessions import export_sessions

    db = tmp_path / "opencode.db"
    con = sqlite3.connect(db)
    con.execute(
        "create table session (id text, parent_id text, title text, time_updated int, "
        "time_archived int)"
    )
    con.execute("create table message (id text, session_id text, data text, time_created int)")
    con.execute(
        "create table part (id text, message_id text, session_id text, data text, time_created int)"
    )
    con.execute("insert into session values ('s1', null, 'talk', 3, null)")
    con.execute("insert into session values ('s2', 's1', 'subagent', 3, null)")
    con.execute("insert into message values ('m1', 's1', ?, 1000)", (json.dumps({"role": "user"}),))
    con.execute(
        "insert into message values ('m2', 's1', ?, 2000)", (json.dumps({"role": "assistant"}),)
    )
    for pid, mid, data in [
        ("p1", "m1", {"type": "text", "text": "what did I write?"}),
        ("p2", "m2", {"type": "reasoning", "text": "hidden thoughts"}),
        ("p3", "m2", {"type": "tool", "tool": "palace_search"}),
        ("p4", "m2", {"type": "text", "text": "you wrote about recursion"}),
    ]:
        con.execute("insert into part values (?, ?, 's1', ?, 1)", (pid, mid, json.dumps(data)))
    con.commit()
    (session,) = export_sessions(db)
    assert session["chat_id"] == "s1"
    assert [(t["role"], t["content"]) for t in session["turns"]] == [
        ("user", "what did I write?"),
        ("assistant", "you wrote about recursion"),
    ]
    assert export_sessions(tmp_path / "missing.db") == []


def test_embedder_templates_follow_the_model_family() -> None:
    import dataclasses

    from core.ingest.embed import Embedder
    from core.kernel.config import loader

    sent: list[list[str]] = []

    class Client:
        def embed(self, model: str, inputs: list[str], **_: Any) -> list[list[float]]:
            sent.append(inputs)
            return [[0.0] for _ in inputs]

    base = loader.load_config().embedding
    Embedder(client=cast("Any", Client()), config=base).embed_query("q")
    gemma = dataclasses.replace(
        base,
        query_template="task: search result | query: {text}",
        document_template="title: none | text: {text}",
    )
    e = Embedder(client=cast("Any", Client()), config=gemma)
    e.embed_query("q")
    e.embed_documents(["d"])
    assert sent[0] == [f"Instruct: {base.query_instruction}\nQuery: q"]  # today's default
    assert sent[1:] == [["task: search result | query: q"], ["title: none | text: d"]]
