"""The Ambassador's MCP surface — the palace as a tool server for the local model.

    uv run --project ~/mind-palace python scripts/palace_mcp.py      # MCP over stdio

A harness (OpenCode, or anything that speaks MCP over stdio) spawns this process; it has no
listener and no socket of its own, and it seals itself (Invariant 1) before it opens a store. It is
the Ambassador's client of the core: every read is ONE command, `query` — a sentence of the query
algebra (`core.sentence`, dn-query-sentence-algebra) compiled under the Ambassador's grant, widened
by the hypothetical overlay the owner granted on 2026-11-04 — so an ill-scoped read is refused in
code, not by the prompt, and the plan rides with every answer; writes are only the ones the
grant's W_Σ allows — dialogue capture (provenance fixed by role, never by the text) and
interpreted relation edges. Long operations (dream, relate, sync) wake models and run on demand.

`--role guest` serves an external agent instead (dn-guest-principal): `query` under the read-only
`GUEST` grant, over the dialogue, the repo's code and docs, the papers and the observed records,
never the notes or their interpretations, and `overview`; no write tool, no request, no `status`.

Protocol: JSON-RPC 2.0, one message per line (MCP stdio transport). `initialize`, `ping`,
`tools/list`, `tools/call`; a line that is no request is answered with JSON-RPC's error for it,
and the server reads on (`_answer`). A tool runs with `sys.stdout` pointed at stderr
(`Server.handle`), so what an operation or a library under it prints joins the diagnostics on
stderr and stdout carries protocol messages only. The client that spawned the process holds both
streams.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.query import QueryEngine

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "mind-palace", "version": "0.1.0"}
# The brief (agents/ambassador/brief.md) IS the server's MCP `instructions`: a harness that honours
# them — Open WebUI appends them to the system message whenever the palace tools are on — loads it
# on every chat with no prompt to paste. One text for every client and for eval/ambassador_e2e.py.
INSTRUCTIONS = (Path(__file__).with_name("brief.md")).read_text(encoding="utf-8").strip()
# The guest's surface (`palace_mcp.py --role guest`, dn-guest-principal) has instructions of its
# own: the brief speaks of tools the guest does not have.
GUEST_INSTRUCTIONS = (
    "A read-only view of a mind-palace instance. Ask with query: a sentence of the query algebra, "
    "not keywords, over the strata this grant reads: the dialogue (chat turns, transcripts and the "
    "documents written in them), reference (the repository's code and docs), curated (papers) and "
    "observed. Name them with over, as in near \"<text>\" over dialogue reference curated "
    "observed: near, diffuse S and a causal walk's endpoints read the owner's notes unless over "
    "names other strata, and over is a mask, so a walk from a turn to the files it wrote needs "
    "over reference. A clause over the notes or the interpretations derived from them is "
    "refused. So are assume, the version chains (trace, reach D) and every do request. Verbs: "
    "near, diffuse S from, reach F|C from, walk from <ref> via <regex over S, F, C>, witness, "
    "read \"<ref>\" (a repo path, code/<name>/<path> for a file of a repository the instance "
    "lands, transcript/<session>/<turn>, a dialogue ref, reference:<paper>). overview counts "
    "what this grant reads, shows the grant, and says when the instance embeds nothing: near "
    "then ranks by the lexical index, and S has no edges."
)
# What `overview` says of an instance that embeds nothing (dn-palace-lite), on either surface.
EMBEDDING_OFF = "off: this instance embeds nothing; near ranks by the lexical index"


def _planes(grant: Any) -> list[dict[str, Any]]:
    """A grant's planes as `overview` shows them."""
    return [
        {
            "strata": sorted(s.sigma.strata),
            "edges": sorted(s.edges.fibers),
            "clock": s.time.clock.value,
            "write": bool(s.authority.store_write),
        }
        for s in grant.scopes
    ]


class Ambassador:
    """Tool implementations. Stores and the launcher open lazily, once per process."""

    def __init__(self) -> None:
        from core.query import QueryEngine

        self.engine = QueryEngine()
        self._launcher: Any = None

    @property
    def launcher(self) -> Any:
        if self._launcher is None:
            from ops.lifecycle.launcher import build_launcher

            self._launcher = build_launcher()
        return self._launcher

    # the one read ------------------------------------------------------------------------------
    def query(self, sentence: str, trace: bool = False) -> dict[str, Any]:
        """A sentence of the query algebra (dn-query-sentence-algebra) under `sentence_grant()` —
        the Ambassador's grant with the overlay the owner granted: the plan rides with the answer,
        a refusal names the word that would fix it, a hypothetical answers as a `Hyp` beside the
        actual answer, and `trace` shows the work. Logged as `mcp`/`ambassador` (the query log,
        the sensor)."""
        from core.sentence.surface import ask_logged, sentence_grant

        return ask_logged(sentence, sentence_grant(), surface="mcp", role="ambassador",
                          engine=self.engine, trace=bool(trace)).to_dict()

    def overview(self) -> dict[str, Any]:
        from collections import Counter

        from core.query import AMBASSADOR
        from core.stores.catalog import VaultCatalog

        cfg = self.engine.config
        catalog = Counter(
            e.provenance for e in VaultCatalog(cfg.paths.vault_catalog).active_entries()
        )
        edges = Counter(e.rel_type for e in self.engine._get("edges").all())
        out: dict[str, Any] = {
            "catalog_by_provenance": dict(catalog),
            "vector_rows": self.engine._get("vectors").count(),
            "relation_edges": dict(edges),
            "versions": self.engine._get("versions").count(),
            "your_grant": _planes(AMBASSADOR),
        }
        if not cfg.embedding.enabled:     # the lite profile: say so, and what ranks instead
            out["embedding"] = EMBEDDING_OFF
        lexical = self.engine._get("lexical")
        if lexical is not None:
            out["lexical_units"] = lexical.count()
        code = code_sources(cfg)
        if code:
            out["code"] = code
        return out

    # writes and on-demand work -----------------------------------------------------------------
    def _run(self, fn: Callable[[], int]) -> dict[str, Any]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fn()
        return {"ok": code == 0, "output": buf.getvalue().strip()}

    # The write tools, as aliases of the one command `query` (dn-ingress-language §E8): each calls a
    # library script of the ingress and writes the request the daemon's one writer lands; the
    # receipt rides back as the answer's hit. Nothing is written from this process.
    def _do(self, sentence: str) -> dict[str, Any]:
        return self.query(sentence)

    def sync_dialogue(self) -> dict[str, Any]:
        return self._do("do sync_dialogue")

    def sync_notes(self) -> dict[str, Any]:
        return self._do("do sync_vault")

    def dream(self) -> dict[str, Any]:
        return self._do("do dream")

    def relate(self, max_pairs: int = 12) -> dict[str, Any]:
        from core.ingest.table import JOBS

        most = JOBS["relate"].args["pairs"]
        if not 0 <= int(max_pairs) <= most:
            raise ValueError(f"max_pairs is from 0 to {most}")   # refused here, not at landing
        return self._do(f"do relate(pairs: {int(max_pairs)})")

    def capture(self, text: str, conversation: str = "captures") -> dict[str, Any]:
        """Remember text the MODEL relays (a summary, a decision it was asked to remember) as an
        `observed` dialogue turn, by the ingress, under
        `dialogue/ingress/ambassador/<conversation>/`. Never authored: only the owner's own turns,
        synced from their chat app, carry authored provenance. A conversation is a name, not a
        path."""
        from core.sentence.script import quote

        return self._do(f"do capture(text: {quote(text)}, conversation: {quote(conversation)})")

    def link(self, note_a: str, note_b: str, relation: str) -> dict[str, Any]:
        """Propose a signed relation between two notes, stored as `interpreted`, by the ingress."""
        from core.relations import RELATIONS

        if relation not in RELATIONS:
            raise ValueError(f"relation must be one of {list(RELATIONS)}")
        from core.sentence.script import quote

        return self._do(f"do link(a: {quote(note_a)}, b: {quote(note_b)}, "
                        f"relation: {quote(relation)})")

    # the loop's bookkeeping (docs/brainstorms/ambassador-agent-loop.md, phase 1) ----------------
    def status(self) -> dict[str, Any]:
        """The ecosystem at a glance, read-only and local: jobs (ledger and live processes),
        models, services, store sizes, and what is open or due."""
        from core.stores.tasks import OPEN, now_local, open_task_store
        from ops.heartbeat import chat_key, last_tick, load_policy, model_state, palace_processes

        cfg = self.engine.config
        policy = load_policy()
        store = open_task_store(cfg)
        try:
            running = [j.brief() for j in store.select(kinds=("job",), statuses=("running",))]
            recent = [j.brief() for j in store.finished(limit=20) if j.kind == "job"][:5]
            open_n = len(store.select(kinds=("task", "reminder"), statuses=OPEN, limit=500))
            due = [i.brief() for i in store.due()]
        finally:
            store.close()
        return {
            "now": now_local().isoformat(timespec="minutes"),
            "jobs_running": running,
            "palace_processes": palace_processes(),
            "jobs_recent": recent,
            "tasks_open": open_n,
            "due": due,
            "models": {
                "chat": model_state(cfg.runtime.port_for("routine") or 8080,
                                    key=chat_key(policy)),
                # an instance that embeds nothing has no embedder to ask (dn-palace-lite)
                "embedder": (model_state(cfg.runtime.port_for("embedding") or 8081)
                             if cfg.embedding.enabled else "off"),
            },
            "heartbeat": last_tick(cfg.paths.data_dir, interval_s=policy.interval_s),
            "services": _launch_agents(),
            "stores": {
                "vectors": self.engine._get("vectors").count(),
                "literature_chunks": self.engine._get("curated").count(),
                "relation_edges": len(self.engine._get("edges").all()),
            },
        }

    def task_add(self, title: str, detail: str = "", due: str = "") -> dict[str, Any]:
        """Track a task for the owner, with an optional deadline."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"added": s.add(
            "task", title, detail=detail, due_at=parse_when(due) if due else None).brief()})

    def remind(self, text: str, at: str) -> dict[str, Any]:
        """Bring something up at a moment: it appears among the due items from then on."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"reminder": s.add(
            "reminder", text, due_at=parse_when(at)).brief()})

    def task_list(self, include_done: bool = False) -> dict[str, Any]:
        """Open tasks and reminders, running jobs; recently finished ones on request."""
        from core.stores.tasks import OPEN

        return self._ledger(lambda s: {"items": [
            i.brief() for i in [*s.select(statuses=(*OPEN, "running")),
                                *(s.finished(limit=10) if include_done else [])]]})

    def task_update(self, id: int, status: str = "", note: str = "",
                    due: str = "") -> dict[str, Any]:
        """Change an item's status, add a note, or move its deadline."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"updated": s.update(
            int(id), status=status or None, note=note or None,
            due_at=parse_when(due) if due else None).brief()})

    def _ledger(self, op: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """Run one ledger operation, then refresh the notices the bridge shows the model."""
        from core.stores.tasks import now_local, open_task_store, write_notices

        store = open_task_store(self.engine.config)
        try:
            out = op(store)
            write_notices(store)
        finally:
            store.close()
        return {**out, "now": now_local().isoformat(timespec="minutes")}


def code_sources(cfg: Any) -> list[dict[str, Any]]:
    """Each repository of the lexical code source (dn-palace-lite): the commit whose files it
    last landed whole, when, and how many commits its ref has moved past that since, so a reader
    knows how current the code stratum is before trusting an answer from it."""
    from core.ingest.readers import read_mark
    from core.ingest.repository import behind
    from core.ingest.table import repository_mark
    from core.kernel.config.loader import lexical_code

    if not lexical_code(cfg):
        return []
    out = []
    for repo in cfg.ingestion.code.repositories:
        mark = read_mark(repository_mark(cfg, repo.name))
        landed = str(mark["commit"]) if mark else ""
        out.append({"repository": repo.name, "ref": repo.ref, "landed": landed[:12] or None,
                    "at": mark.get("at") if mark else None,
                    "behind": behind(Path(repo.path), landed, repo.ref) if landed else None})
    return out


# What a scope refusal tells the guest would fix it: the grant's strata, named with `over`.
GUEST_SCOPE_HINT = (
    "; the guest grant reads dialogue, reference, curated and observed (name them with "
    "`over dialogue reference curated observed`, or some of them), never the mirror or the "
    "interpreted stratum, and has no overlay for `assume`, no version plane for `trace` or "
    "`reach D`, and no write bit for `do`"
)


# What a refusal raised while a sentence ran tells the guest, by class: one fixed sentence each.
# The reason raised there may quote what a store holds, so it is never passed on (`_refused`).
GUEST_RAN = {
    "lookup": (
        "a name in the sentence was not found in the strata this grant reads, or what it names "
        "cannot be read as text: spell a ref as an answer's `ref` is spelled (a repo path from "
        "the repository's root such as `core/query.py`, `code/<name>/<path>` for a file of a "
        "repository the instance lands, `transcript/<session>/<turn>`, a dialogue ref, "
        "`reference:<paper>`), name with `over` the strata a title is to be found in, and ask "
        "`near \"<text>\" over dialogue reference curated observed` for refs to start from"
    ),
    "ambiguous": (
        "a name in the sentence fits more than one node of the strata this grant reads, or more "
        "than one commit; write the ref in full in place of a title, and more of the sha after "
        "`as of`"
    ),
    "unsupported": (
        "the sentence compiles and the stores cannot answer it as written: `as of` takes a "
        "commit the citation graph holds a cut at, and a verb walks only the relations recorded "
        "for the nodes it names; drop `as of` or change the relation"
    ),
    "scope": (
        "a ref in the sentence names something outside the strata its clauses read: a transcript "
        "turn is read by walking C or under `over dialogue_transcript`, and `read` returns a "
        "record only of the stratum its ref's spelling names"
    ),
    "sort": "the sentence's sorts did not compose when it ran; give each connective the sorts "
            "its grammar takes",
    "parse": "the sentence could not be read when it ran; write one sentence of the query "
             "algebra",
    "busy": "the instance is busy and took no request; ask again later",
    "error": (
        "the sentence failed while it ran, for a reason this surface does not show; the "
        "instance's query log keeps it for the owner"
    ),
}
# What `overview` tells the guest when it fails, whatever failed.
GUEST_OVERVIEW_FAILED = ("the overview could not be counted on this instance, for a reason this "
                         "surface does not show; `query` may still answer")


class GuestRefusal(PermissionError):
    """A refusal as the guest reads it: its class, then what the surface says of it, one of two
    texts (`_refused` chooses). A sentence the compiler refuses is told the compiler's reason
    with every quoted run replaced by its length (`redact_reason`): compiling reads the sentence
    and the grant and no store, so that reason holds the asker's own words and nothing a store
    holds. A sentence refused while it ran against the stores is told one fixed sentence for its
    class (`GUEST_RAN`), never the reason, which may quote what a store holds and which the
    redaction, pairing quotes by position, does not reliably hide. A scope refusal of either
    kind adds what the grant reads."""

    def __init__(self, kind: str, said: str) -> None:
        super().__init__(f"{kind}: {said}" + (GUEST_SCOPE_HINT if kind == "scope" else ""))


def _refused(sentence: Any, e: BaseException, trace: Any = False) -> GuestRefusal:
    """The refusal the guest reads for `e`, which asking `sentence` raised. The sentence is
    compiled again, alone, with a trace when the call asked for one, as it was compiled the
    first time: that reads the sentence and the grant and no store. If the compiler refuses it,
    the refusal is the compiler's, and the guest reads its class and its reason, redacted. If it
    compiles, `e` came from running it against the stores, and the guest reads `e`'s class and
    that class's fixed sentence; `e`'s own words are never shown. Whatever fails in here is an
    `error`, said in the fixed sentence."""
    kind = "error"
    try:
        from core.query import GUEST
        from core.sentence.plan import compile_sentence
        from core.sentence.surface import is_command, redact_reason, refusal_class
        from core.sentence.trace import Trace

        kind = refusal_class(e) or "error"
        # the trace renders the parse while it compiles, so a sentence can fail to compile with
        # it alone: compiled again without it, that sentence would read as refused in the run
        t = Trace() if bool(trace) else None
        try:
            compile_sentence(sentence, GUEST, role="guest" if is_command(sentence) else None,
                             trace=t)
        except Exception as c:
            return GuestRefusal(refusal_class(c) or "error", redact_reason(str(c)))
    except Exception:
        kind = "error"
    return GuestRefusal(kind, GUEST_RAN.get(kind, GUEST_RAN["error"]))


class Guest:
    """The guest's tools (dn-guest-principal): the one read under `GUEST`, and counts over the
    strata it reads. No write tool, no request, and no `status`, which lists the owner's tasks.
    A tool's body raises `GuestRefusal` and nothing else, whatever fails in it: the engine is
    built on first use, inside the body, so a configuration or a store that cannot be opened is
    a refusal too."""

    def __init__(self) -> None:
        self._engine: QueryEngine | None = None

    @property
    def engine(self) -> QueryEngine:
        if self._engine is None:
            from core.query import QueryEngine

            self._engine = QueryEngine()
        return self._engine

    @engine.setter
    def engine(self, engine: QueryEngine) -> None:
        self._engine = engine

    def query(self, sentence: str, trace: bool = False) -> dict[str, Any]:
        """A sentence under `GUEST`, logged as `mcp`/`guest`. The universe withholds what the
        stores say of the notes (`hide_mirror`); a refusal is a `GuestRefusal`, its text chosen
        by `_refused`."""
        try:
            from core.query import GUEST
            from core.sentence.surface import ask_logged

            return ask_logged(sentence, GUEST, surface="mcp", role="guest", engine=self.engine,
                              trace=bool(trace)).to_dict()
        except Exception as e:
            raise _refused(sentence, e, trace) from None

    def overview(self) -> dict[str, Any]:
        """The catalog's active entries of the classes the grant's strata hold, the curated
        store's chunks, and the grant; then what the Ambassador's overview says of the lite
        profile (dn-palace-lite), over the same classes: that the instance embeds nothing, when
        it is so; the lexical index's current units of those classes; and each repository of a
        lexical code source, with the commit it last landed and how far its ref has moved since.
        Nothing of the mirror or the interpreted stratum is counted, not even in a total. A
        failure is a `GuestRefusal` of one fixed sentence."""
        try:
            from collections import Counter

            from core.kernel.clearance import classes_of
            from core.query import GUEST
            from core.stores.catalog import VaultCatalog

            cfg = self.engine.config
            classes = classes_of(GUEST.strata)
            admitted = {str(p) for p in classes}
            entries = VaultCatalog(cfg.paths.vault_catalog).active_entries()
            catalog = Counter(str(e.provenance) for e in entries if str(e.provenance) in admitted)
            out: dict[str, Any] = {
                "catalog_by_provenance": dict(catalog),
                "literature_chunks": self.engine._get("curated").count(),
                "your_grant": _planes(GUEST),
            }
            if not cfg.embedding.enabled:
                out["embedding"] = EMBEDDING_OFF
            lexical = self.engine._get("lexical")
            if lexical is not None:     # the units of the classes the grant reads, never a total
                out["lexical_units"] = lexical.count(classes=classes)
            code = code_sources(cfg)
            if code:
                out["code"] = code
            return out
        except Exception:
            raise GuestRefusal("error", GUEST_OVERVIEW_FAILED) from None


def _launch_agents() -> list[dict[str, str]]:
    """The stack's LaunchAgents: running (pid) or idle, and the last exit status."""
    import subprocess

    out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
    agents = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2].startswith("com.mind-palace."):
            pid, last_exit, label = parts
            agents.append({"name": label.removeprefix("com.mind-palace."),
                           "state": "running" if pid != "-" else "idle", "last_exit": last_exit})
    return agents


def _schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    """Lean on purpose: every request carries every schema (the fixed cost of a turn), and the
    dispatch already refuses unknown arguments, so `additionalProperties` buys nothing here."""
    return {"type": "object", "properties": props, **({"required": required} if required else {})}


_S = {"type": "string"}
_I = {"type": "integer", "minimum": 1, "maximum": 50}
_WHEN = {"type": "string", "description": "local ISO time (2026-10-30T09:00) or +30m, +2h, +1d"}

TOOLS: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "query",
        "The one read: a sentence of the query algebra, not keywords. Verbs: "
        'near "text" | diffuse S from <note> [beta b] | reach F from <note> [depth n] '
        "[back|forward] | relate <note> | trace <note> | walk from <note> [to <note>] via <regex "
        'over S,F,D,C> | witness "<edge id>" | read "<ref>" [chunk n] (the full text; read before '
        "quoting). Connectives and, or, minus, then; adjectives within <region>, over <strata>; "
        "top k, atleast t, far, not; assume <rel> <a> <b> [+w] in <sentence> (a hypothetical: the "
        "answer is a Hyp, never a fact). A <note> is a quoted path or title. Papers: over curated. "
        'Example: top 5 (near "sleep" and diffuse S from "health.md"), the five best of the '
        "product; top k takes its field with the field's adjectives, so top 5 near \"x\" within "
        "<region> ranks within it. The plan rides with the answer; a refusal names the word that "
        "would fix it; trace: true shows the work: the parse, every rewrite with its law, the "
        "support's census, each clause's arithmetic, the ranking.",
        _schema({"sentence": _S,
                 "trace": {"type": "boolean",
                           "description": "show the work: the parse, the rewrites and their "
                                          "laws, the census, each clause's arithmetic, the "
                                          "ranking"}}, ["sentence"]),
        "query",
    ),
    (
        "overview",
        "Counts per stratum and relation type; your grant.",
        _schema({}, []),
        "overview",
    ),
    (
        "sync_dialogue",
        "Sync new Open WebUI and OpenCode chats into the palace now.",
        _schema({}, []),
        "sync_dialogue",
    ),
    (
        "sync_notes",
        "Re-ingest the owner's changed notes (a `do sync vault` request the daemon lands).",
        _schema({}, []),
        "sync_notes",
    ),
    (
        "capture",
        "Remember text you relay, stored as observed, never as the owner's words (a `do capture` "
        "request the daemon lands).",
        _schema({"text": _S, "conversation": _S}, ["text"]),
        "capture",
    ),
    (
        "status",
        "Palace processes and jobs (ingestion, imports) with progress, models, services, "
        "store sizes, open and due items.",
        _schema({}, []),
        "status",
    ),
    (
        "task_list",
        "The owner's open tasks and reminders, and running jobs.",
        _schema({"include_done": {"type": "boolean"}}, []),
        "task_list",
    ),
    (
        "task_add",
        "Track a task for the owner; due is optional.",
        _schema({"title": _S, "detail": _S, "due": _WHEN}, ["title"]),
        "task_add",
    ),
    (
        "task_update",
        "Change a task or reminder: status open/waiting/done/dropped, a note, or a new due.",
        _schema({"id": _I | {"maximum": 10**9}, "status": {"enum": ["open", "waiting", "done",
                 "dropped"]}, "note": _S, "due": _WHEN}, ["id"]),
        "task_update",
    ),
    (
        "remind",
        "Remind the owner at a time.",
        _schema({"text": _S, "at": _WHEN}, ["text", "at"]),
        "remind",
    ),
    (
        "link",
        "Propose a relation between two notes, stored as interpreted (a `do link` request the "
        "daemon lands).",
        _schema(
            {
                "note_a": _S,
                "note_b": _S,
                "relation": {"enum": ["supports", "contradicts", "contextualizes"]},
            },
            ["note_a", "note_b", "relation"],
        ),
        "link",
    ),
    (
        "dream",
        "Request one dreaming pass (a `do dream` request; minutes, in a trough, wakes the large "
        "model).",
        _schema({}, []),
        "dream",
    ),
    (
        "relate",
        "Request a relation pass among similar notes (a `do relate` request; minutes, wakes the "
        "large model).",
        _schema({"max_pairs": _I}, []),
        "relate",
    ),
]

# The guest's table: the one read and the counts, nothing that writes, requests or reads the
# owner's tasks (dn-guest-principal).
GUEST_TOOLS: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "query",
        "The one read, under a read-only grant over dialogue, reference (the repository's code and "
        "docs), curated (papers) and observed: a sentence of the query algebra, not keywords. "
        'Verbs: near "text" | diffuse S from <ref> [beta b] | reach F|C from <ref> [depth n] '
        "[back|forward] | walk from <ref> [to <ref>] via <regex over S,F,C> | witness \"<edge "
        'id>" | read "<ref>" [chunk n]. Connectives and, or, minus, then; adjectives within '
        "<region>, over <strata>; top k, atleast t, far, not. Name the strata with over, "
        'separated by spaces: near "x" over dialogue reference curated observed. A refusal '
        "names what the grant reads; trace: true shows the work.",
        TOOLS[0][2],
        "query",
    ),
    (
        "overview",
        "Counts over the strata this grant reads; your grant.",
        _schema({}, []),
        "overview",
    ),
]

ROLES = ("ambassador", "guest")      # the principals this server can speak for


class Server:
    """The protocol, for one principal: the Ambassador's surface by default, or the guest's
    (`role="guest"`: `GUEST_TOOLS`, `GUEST_INSTRUCTIONS`, the `Guest` tools)."""

    def __init__(self, role: str = "ambassador") -> None:
        if role not in ROLES:
            raise ValueError(f"role is one of {', '.join(ROLES)}, not {role!r}")
        self.role = role
        self.tools = GUEST_TOOLS if role == "guest" else TOOLS
        self.instructions = GUEST_INSTRUCTIONS if role == "guest" else INSTRUCTIONS
        self._amb: Ambassador | Guest | None = None

    @property
    def amb(self) -> Ambassador | Guest:
        if self._amb is None:
            self._amb = Guest() if self.role == "guest" else Ambassador()
        return self._amb

    def handle(self, msg: Any) -> dict[str, Any] | None:
        """The reply to one message, `None` for a notification. A message that is not a request
        object (an array, which this protocol version has no batch for, a number, a string,
        null), an id that is no string or number, and params that are not an object are each
        refused with JSON-RPC's invalid request, the id null when the request's cannot be used."""
        if not isinstance(msg, dict):
            return _err(None, -32600, "invalid request: a message is a JSON object")
        method, mid = msg.get("method"), msg.get("id")
        if mid is None:  # a notification (e.g. notifications/initialized)
            return None
        if not _is_id(mid):
            return _err(None, -32600, "invalid request: an id is a string or a number")
        if not isinstance(msg.get("params") or {}, dict):
            return _err(mid, -32600, "invalid request: params is a JSON object")
        if method == "initialize":
            client = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
            return _ok(
                mid,
                {
                    "protocolVersion": client,
                    "serverInfo": SERVER_INFO,
                    "capabilities": {"tools": {"listChanged": False}},
                    "instructions": self.instructions,
                },
            )
        if method == "ping":
            return _ok(mid, {})
        if method == "tools/list":
            return _ok(
                mid,
                {
                    "tools": [
                        {"name": n, "description": d, "inputSchema": s}
                        for n, d, s, _ in self.tools
                    ]
                },
            )
        if method in ("resources/list", "prompts/list"):
            return _ok(mid, {method.split("/")[0]: []})
        if method == "tools/call":
            params = msg.get("params") or {}
            spec = next((t for t in self.tools if t[0] == params.get("name")), None)
            if spec is None:
                return _err(mid, -32602, f"unknown tool {params.get('name')!r}")
            # The tools are made, and the tool runs, with `sys.stdout` pointed at stderr: a line
            # printed to stdout in there would be read by the client as a protocol message. The
            # diagnostic is printed in here as well, so a process started with no stderr drops
            # it; outside, `print` to a stderr that is None would fall back to stdout.
            with contextlib.redirect_stdout(sys.stderr):
                try:
                    result = getattr(self.amb, spec[3])(**(params.get("arguments") or {}))
                    text = json.dumps(result, ensure_ascii=False, default=str)
                    return _ok(mid, {"content": [{"type": "text", "text": text}],
                                     "isError": False})
                except Exception as e:  # a refused or failed call is a result, not a crash
                    print(traceback.format_exc(), file=sys.stderr)
                    return _ok(
                        mid,
                        {
                            "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                            "isError": True,
                        },
                    )
        return _err(mid, -32601, f"method not found: {method}")


def _ok(mid: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def _is_id(mid: Any) -> bool:
    """A JSON-RPC id this server echoes: a string or a finite number, never a bool."""
    if isinstance(mid, float):
        return math.isfinite(mid)
    return isinstance(mid, str) or (isinstance(mid, int) and not isinstance(mid, bool))


def _answer(server: Server, line: str) -> dict[str, Any] | None:
    """The reply to one line of the stream, `None` for a notification. A line that is not JSON
    is a parse error; so is a number past Python's limit on the digits it converts, and nesting
    past the stack, which `json.loads` raises as `ValueError` and `RecursionError`. Whatever
    else fails while the message is handled is answered as an internal error, its traceback on
    stderr when the process has one. Either way the server goes on to the next line."""
    try:
        msg = json.loads(line)
    except (ValueError, RecursionError):
        return _err(None, -32700, "parse error")
    try:
        return server.handle(msg)
    except Exception:
        if sys.stderr is not None:      # `print` to a stderr that is None writes to stdout
            with contextlib.suppress(Exception):
                print(traceback.format_exc(), file=sys.stderr)
        mid = msg.get("id") if isinstance(msg, dict) else None
        return _err(mid if _is_id(mid) else None, -32603, "internal error")


def serve(stdin: Any = None, stdout: Any = None, server: Server | None = None) -> None:
    """Speak MCP on stdio for `server`, the Ambassador's surface when none is given."""
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    server = server if server is not None else Server()
    for line in stdin:
        if not line.strip():
            continue
        reply = _answer(server, line)
        if reply is not None:
            line = json.dumps(reply, ensure_ascii=False)
            try:
                # a lone surrogate, which UTF-8 does not encode: a sentence may hold one, and an
                # answer repeats its sentence. Asked here, not left to the stream: one with
                # `surrogateescape`, as Python's UTF-8 mode makes stdout, writes a surrogate from
                # U+DC80 to U+DCFF as a byte that is not UTF-8 instead of refusing it
                line.encode("utf-8")
                stdout.write(line + "\n")
            except UnicodeEncodeError:
                # the same JSON, written as ASCII
                stdout.write(json.dumps(reply, ensure_ascii=True) + "\n")
            stdout.flush()
