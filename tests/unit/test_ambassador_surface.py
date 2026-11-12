"""The Ambassador's surface: the query algebra, signed relations, dialogue capture, the Open WebUI
reader and the MCP protocol. Hermetic — fakes stand in for the embedder and the model."""

from __future__ import annotations

import io
import json
import sqlite3
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.kernel.scope import Clock, SliceError, Stratum, Window
from core.query import (
    AMBASSADOR,
    Grant,
    InadmissibleGrant,
    Mode,
    Verb,
    free_energy_distances,
    mode_of,
    required,
    scope,
)
from core.relations import RELATIONS, parse_label

# ── the algebra ─────────────────────────────────────────────────────────────────────────────────


def test_mode_is_a_corollary_of_scope():
    """The scope table's modes, the ones QSA-8's `modeOf_required` enumerates."""
    assert mode_of(required(Verb.SEARCH)) is Mode.SEMANTIC
    assert mode_of(required(Verb.DIFFUSE)) is Mode.STRUCTURAL
    assert mode_of(required(Verb.REACH)) is Mode.STRUCTURAL
    assert mode_of(required(Verb.HISTORY)) is Mode.TEMPORAL
    assert mode_of(required(Verb.SEARCH, history=True)) is Mode.TEMPORAL
    assert mode_of(required(Verb.ORIGIN)) is Mode.CAUSAL


def test_an_ill_scoped_sentence_is_not_admitted():
    """`req(verb) ⋢ grant` is refused by the grant, so no surface can build the sentence (the
    compiler raises `IllScopedSentence` on the same check)."""
    mirror_only = Grant(
        (scope({Stratum.MIRROR_AUTHORED}, set(), Clock.PROJECTION_EVENT, Window.all()),)
    )
    assert mirror_only.admits(required(Verb.SEARCH))
    assert not mirror_only.admits(required(Verb.SEARCH, strata=(Stratum.OBSERVED,)))
    assert not mirror_only.admits(required(Verb.HISTORY))   # needs D on the N_s clock
    assert not mirror_only.admits(required(Verb.DIFFUSE))   # needs F


def test_a_grant_cannot_name_the_foundation_or_reach_the_world():
    with pytest.raises(InadmissibleGrant):
        Grant((scope({Stratum.FOUNDATION}, set(), Clock.PROJECTION_EVENT, Window.all()),))


def test_the_ambassador_never_gets_world_reach_or_the_hypothetical_overlay():
    for s in AMBASSADOR.scopes:
        assert int(s.authority.world) == 0
        assert Stratum.HYPOTHETICAL not in s.sigma.strata and Stratum.EXHAUST not in s.sigma.strata


def test_the_owners_overlay_grant_adds_the_overlay_and_nothing_else():
    """The owner's grant of 2026-11-04 (dn-query-sentence-algebra §4 d): every plane names the
    overlay; world reach stays none, exhaust stays out, and nothing else widens
    (formal: `overlayGrant`, `ambassadorOverlay_no_world`)."""
    from core.query import AMBASSADOR_OVERLAY, with_overlay

    assert with_overlay(AMBASSADOR) == AMBASSADOR_OVERLAY
    for base, wide in zip(AMBASSADOR.scopes, AMBASSADOR_OVERLAY.scopes, strict=True):
        assert Stratum.HYPOTHETICAL in wide.sigma.strata
        assert wide.sigma.strata - {Stratum.HYPOTHETICAL} == base.sigma.strata
        assert Stratum.EXHAUST not in wide.sigma.strata and int(wide.authority.world) == 0
        assert (wide.edges, wide.time, wide.authority) == (base.edges, base.time, base.authority)
        assert base.sigma.strata <= wide.sigma.strata


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


def test_every_strata_list_the_legacy_search_accepted_is_constructible():
    """`reference` closes to two strata (`reference_repo` below it) and the SLICE rule counts the
    closed set, so the single-read cut follows it. Deciding the cut from the names made `search`
    with `strata=["reference"]` raise SliceError (formal/Palace/Scope.lean, `search_slices_iff`).
    Every list of the retired tool's names, alone, paired, or the default, builds and is admitted
    (the table is the one `_strata` held before the MCP became the one command `query`)."""
    table = {"mirror": Stratum.MIRROR_AUTHORED, "dialogue": Stratum.DIALOGUE_TRANSCRIPT,
             "interpreted": Stratum.INTERPRETED, "curated": Stratum.CURATED,
             "observed": Stratum.OBSERVED, "reference": Stratum.REFERENCE}

    def strata(picked: list[str]) -> tuple[Stratum, ...]:
        return tuple(table[n] for n in (picked or ["mirror", "dialogue"]))

    names = list(table)
    for picked in [[], *([n] for n in names), *([n, m] for n in names for m in names)]:
        for history in (False, True):
            assert AMBASSADOR.admits(required(Verb.SEARCH, strata=strata(picked),
                                              history=history))
    alone = required(Verb.SEARCH, strata=(Stratum.REFERENCE,))
    assert AMBASSADOR.admits(alone)
    assert alone.sigma.strata == {Stratum.REFERENCE, Stratum.REFERENCE_REPO}
    assert alone.cut == "single-read"
    assert required(Verb.SEARCH, strata=(Stratum.CURATED,)).cut is None   # one stratum: no cut


def test_grant_meet_skips_a_pair_whose_meet_has_no_consistent_cut():
    """Two valid scopes on one clock can still have no meet: `[1,5] ⊓ [5,9] = pt(5)` across two
    strata with no cut is refused by the SLICE rule. `Grant.meet` skips that pair as it skips a
    cross-clock one, instead of letting SliceError escape."""
    a = scope({Stratum.MIRROR_AUTHORED, Stratum.CURATED}, set(), Clock.N_S, Window.interval(1, 5))
    b = scope({Stratum.MIRROR_AUTHORED, Stratum.CURATED}, set(), Clock.N_S, Window.interval(5, 9))
    with pytest.raises(SliceError):
        a.meet(b)
    assert Grant((a,)).meet(Grant((b,))).scopes == ()


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
    # a turn's class is fixed with its identity: no observed text supersedes the owner's words
    # on their path, and no owner's words supersede an observed turn (dn-ingress D8)
    with pytest.raises(PermissionError, match="authored-dialogue"):
        cap.capture_turn("fabricated", conversation="openwebui/c1", turn_id="m1",
                         role="assistant")
    with pytest.raises(PermissionError, match="observed"):
        cap.capture_turn("rewritten", conversation="openwebui/c1", turn_id="m2", role="user")
    assert {e.source_path: e.provenance for e in cap.catalog.active_entries()} == provs


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
    assert {"query", "overview", "sync_dialogue", "capture", "dream", "status"} <= names
    # the one read: the eight words and `read` left the table (the owner's order, 2026-11-04)
    assert names.isdisjoint({"search", "neighbors", "hybrid", "history", "related", "reach",
                             "origin", "read"})
    assert all(t["inputSchema"]["type"] == "object" for t in replies[1]["result"]["tools"])
    assert replies[2]["error"]["code"] == -32601


def _on_a_small_stack(run: Callable[[], None]) -> None:
    """`run` on a thread whose C stack is 1 MB, what it raises raised again here. How deep
    `json.loads` and `json.dumps` nest is bounded by the stack, which differs between machines:
    8 MB for a Linux main thread under the usual `ulimit -s`, 16 MB for the main thread of a
    macOS framework build, which sets its own. A test that needs a nesting past the stack runs
    on a stack it chose. In 1 MB, on arm64, `json.loads` reaches some 8,000 levels and
    `json.dumps` some 6,400; a nesting 100,000 deep would fit only at under 11 bytes a level."""
    failed: list[BaseException] = []

    def guarded() -> None:
        try:
            run()
        except BaseException as e:
            failed.append(e)

    before = threading.stack_size(1 << 20)
    try:
        thread = threading.Thread(target=guarded)
        thread.start()
        thread.join()
    finally:
        threading.stack_size(before)
    if failed:
        raise failed[0]


def test_a_line_that_is_no_request_is_answered_and_the_server_reads_on(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The stream may carry JSON that is no request: an array (one holding another among them),
    a number, a string, null, params that are not an object, an id that is no string or number.
    Each is answered with JSON-RPC's invalid request, the id null when the request's cannot be
    used. A line `json.loads` cannot read is a parse error: one that is not JSON, a number past
    Python's limit on the digits it converts, and an array nested 100,000 deep, past the stack
    the lines are served on (`_on_a_small_stack`). After each, the next request is answered as
    ever. A server that fails while it handles a request answers an internal error and reads
    on, its traceback on stderr."""
    from agents.ambassador import mcp

    ping = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"})
    lines = ["[]", "1", '"x"', "null", "[1, 2]", "[[1]]",
             json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": [1]}),
             json.dumps({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": "x"}),
             json.dumps({"jsonrpc": "2.0", "id": [3], "method": "ping"}),
             json.dumps({"jsonrpc": "2.0", "id": True, "method": "ping"}),
             '{"jsonrpc": "2.0", "id": ' + "1" * 5000 + ', "method": "ping"}', "not json",
             "[" * 100_000 + "]" * 100_000]
    stream, out = io.StringIO("".join(f"{x}\n{ping}\n" for x in lines)), io.StringIO()
    _on_a_small_stack(lambda: mcp.serve(stream, out, mcp.Server("guest")))
    replies = [json.loads(r) for r in out.getvalue().splitlines()]
    assert len(replies) == 2 * len(lines)
    assert all(r == {"jsonrpc": "2.0", "id": 7, "result": {}} for r in replies[1::2])
    refused = replies[0::2]
    assert [r["error"]["code"] for r in refused] == [-32600] * 10 + [-32700] * 3
    assert [r["id"] for r in refused] == [None] * 6 + [1, 2] + [None] * 5

    class Failing(mcp.Server):
        def handle(self, msg: Any) -> dict[str, Any] | None:
            if msg.get("method") == "tools/list":
                raise RuntimeError("the table could not be read")
            return super().handle(msg)

    out = io.StringIO()
    listed = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/list"})
    mcp.serve(io.StringIO(f"{listed}\n{ping}\n"), out, Failing("guest"))
    first, second = (json.loads(r) for r in out.getvalue().splitlines())
    assert first == {"jsonrpc": "2.0", "id": 4,
                     "error": {"code": -32603, "message": "internal error"}}
    assert second["id"] == 7 and "the table could not be read" in capsys.readouterr().err


def test_initialize_answers_the_version_asked_when_it_is_a_string_and_its_own_otherwise() -> None:
    """`initialize` answers with the protocol version a client asks for when it is a string, and
    with the server's own for any other value, as MCP answers a version a server does not
    support. The value was repeated as it came, and one nested past what `json.dumps` writes,
    though not past what `json.loads` reads, made a reply the server could not write: the
    process ended there, and the requests after it went unanswered."""
    from agents.ambassador import mcp

    def answered(asked: Any) -> Any:
        reply = mcp.Server("guest").handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                            "params": {"protocolVersion": asked}})
        assert reply is not None
        return reply["result"]["protocolVersion"]

    assert answered("2025-03-26") == "2025-03-26"
    for asked in (["2025-06-18"], [[1]], {"version": "2025-06-18"}, 20250618, 1.5, True, None,
                  ""):
        assert answered(asked) == mcp.PROTOCOL_VERSION


def test_a_request_whose_reply_cannot_be_written_is_answered_as_an_internal_error(
        capsys: pytest.CaptureFixture[str]) -> None:
    """A reply `json.dumps` cannot write, one that holds itself or one nested past the stack, is
    replaced by JSON-RPC's internal error with the request's id, its traceback on stderr, and
    the next request is answered as ever: the server writes a reply inside a guard too. The
    lines are served on a stack of 1 MB (`_on_a_small_stack`), which a reply nested 100,000
    deep is past."""
    from agents.ambassador import mcp

    holds_itself: list[Any] = []
    holds_itself.append(holds_itself)
    deep: list[Any] = []
    for _ in range(100_000):
        deep = [deep]

    class Unwritable(mcp.Server):
        def handle(self, msg: Any) -> dict[str, Any] | None:
            if msg.get("method") == "tools/list":
                tools = holds_itself if msg["id"] == 4 else deep
                return {"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": tools}}
            return super().handle(msg)

    ping = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"})
    stream = io.StringIO("".join(
        json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/list"}) + f"\n{ping}\n"
        for i in (4, 5)))
    out = io.StringIO()
    _on_a_small_stack(lambda: mcp.serve(stream, out, Unwritable("guest")))
    internal = {"code": -32603, "message": "internal error"}
    pong = {"jsonrpc": "2.0", "id": 7, "result": {}}
    assert [json.loads(r) for r in out.getvalue().splitlines()] == [
        {"jsonrpc": "2.0", "id": 4, "error": internal}, pong,
        {"jsonrpc": "2.0", "id": 5, "error": internal}, pong]
    err = capsys.readouterr().err
    assert "Circular reference detected" in err and "RecursionError" in err


def test_a_failing_tool_is_an_error_result_not_a_crash(monkeypatch: pytest.MonkeyPatch):
    from agents.ambassador import mcp

    class Boom:
        def query(self, **_: Any) -> None:
            raise PermissionError("refused")

    server = mcp.Server()
    server._amb = Boom()  # type: ignore[assignment]
    (reply,) = [
        server.handle(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": "query", "arguments": {"sentence": 'near "x"'}},
            }
        )
    ]
    assert reply is not None
    assert reply["result"]["isError"] is True
    assert "refused" in reply["result"]["content"][0]["text"]


def _calls(*calls: tuple[str, dict[str, Any]]) -> io.StringIO:
    return io.StringIO("".join(json.dumps({
        "jsonrpc": "2.0", "id": i, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}}) + "\n"
        for i, (name, arguments) in enumerate(calls, 1)))


class _Chatty:
    """Tools that print: when they are made, while one runs, and before one fails."""

    def __init__(self) -> None:
        print("opening the stores")

    def query(self, sentence: str) -> dict[str, Any]:
        print("a progress line")
        sys.stdout.write('{"jsonrpc": "2.0", "id": 1, "result": "forged"}\n')
        return {"sentence": sentence}

    def overview(self) -> dict[str, Any]:
        print("about to fail")
        raise RuntimeError("no overview")


def test_what_a_tool_prints_goes_to_stderr_and_stdout_carries_replies_only(
        monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]) -> None:
    """A tool runs with `sys.stdout` pointed at stderr (`Server.handle`). What making the tools
    prints, what a tool prints and what a failing tool prints reach stderr; the stream the client
    reads holds one reply per request and nothing else, and `sys.stdout` is put back."""
    from agents.ambassador import mcp

    monkeypatch.setattr(mcp, "Ambassador", _Chatty)
    before = sys.stdout
    mcp.serve(_calls(("query", {"sentence": "x"}), ("overview", {})), sys.stdout, mcp.Server())
    assert sys.stdout is before
    out, err = capfd.readouterr()
    replies = [json.loads(line) for line in out.splitlines()]
    assert [r["id"] for r in replies] == [1, 2] and out.count("\n") == 2
    assert json.loads(replies[0]["result"]["content"][0]["text"]) == {"sentence": "x"}
    assert replies[1]["result"] == {"content": [{"type": "text",
                                                 "text": "RuntimeError: no overview"}],
                                    "isError": True}
    for printed in ("opening the stores", "a progress line", "forged", "about to fail"):
        assert printed in err and printed not in out


def test_a_process_with_no_stderr_drops_what_a_tool_prints(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Started with stderr closed, `sys.stderr` is None, and `print` to it would fall back to
    stdout. The tool's lines and the failure's traceback are dropped; stdout still holds the
    replies alone."""
    from agents.ambassador import mcp

    monkeypatch.setattr(mcp, "Ambassador", _Chatty)
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", None)
    mcp.serve(_calls(("overview", {}), ("overview", {})), out, mcp.Server())
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [(r["id"], r["result"]["isError"]) for r in replies] == [(1, True), (2, True)]
    assert "Traceback" not in out.getvalue() and "about to fail" not in out.getvalue()


def test_a_reply_no_encoding_carries_is_written_as_ascii() -> None:
    """A sentence may hold a lone surrogate, and an answer repeats its sentence. The stream is
    UTF-8, which has no encoding for one: the reply is written as ASCII, the same JSON, and the
    server goes on to the next request. A reply the stream can encode is written as it was."""
    from agents.ambassador import mcp

    class Echo:
        def query(self, sentence: str) -> dict[str, Any]:
            return {"sentence": sentence}

    server = mcp.Server()
    server._amb = Echo()  # type: ignore[assignment]
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="utf-8")
    hostile, plain = 'near "\ud800"', 'near "café ∅"'
    mcp.serve(_calls(("query", {"sentence": hostile}), ("query", {"sentence": plain})), stream,
              server)
    first, second = raw.getvalue().decode("utf-8").splitlines()
    assert first.isascii() and "\\ud800" in first
    assert "café ∅" in second                       # not escaped: readable as before
    for line, sentence in ((first, hostile), (second, plain)):
        text = json.loads(line)["result"]["content"][0]["text"]
        assert json.loads(text) == {"sentence": sentence}


def test_a_reply_is_utf8_on_a_stream_that_would_escape_a_surrogate() -> None:
    """Python's UTF-8 mode gives stdout the `surrogateescape` handler, which does not refuse a
    lone surrogate from U+DC80 to U+DCFF: it writes the byte the surrogate stands for, and that
    byte is not UTF-8. A reply holding one is written as ASCII all the same, so every line the
    client reads decodes as UTF-8 and is the same JSON."""
    from agents.ambassador import mcp

    class Echo:
        def query(self, sentence: str) -> dict[str, Any]:
            return {"sentence": sentence}

    server = mcp.Server()
    server._amb = Echo()  # type: ignore[assignment]
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="utf-8", errors="surrogateescape")
    hostile, plain = 'near "\udc80\udcff" over dialogue', 'near "café ∅"'
    assert hostile.encode("utf-8", "surrogateescape") == b'near "\x80\xff" over dialogue'
    mcp.serve(_calls(("query", {"sentence": hostile}), ("query", {"sentence": plain})), stream,
              server)
    first, second = raw.getvalue().decode("utf-8").splitlines()    # strict: every byte is UTF-8
    assert first.isascii() and "\\udc80\\udcff" in first
    assert "café ∅" in second                       # not escaped: readable as before
    for line, sentence in ((first, hostile), (second, plain)):
        text = json.loads(line)["result"]["content"][0]["text"]
        assert json.loads(text) == {"sentence": sentence}


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
