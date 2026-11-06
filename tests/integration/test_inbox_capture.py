"""The Ambassador's inbox on the ingress (dn-ingress-language §E13): the inbox keeps the exchanges
its responder keeps in its own record, the table's `inbox` source labels the owner's text authored
and the reply observed, and `capture_inbox` lands both under the role `inbox` through the one
writer (ING-13, ING-14, ING-7, ING-16).

Proves: the owner's message lands once, as the owner's, at its own path; a re-run lands nothing
new; the reply never lands as authored, whatever it says; no script, the Ambassador's or the
inbox's own, lands model text as the owner's, and a mutation of the source's rule is caught; a
crash between steps converges when the job runs again; a request another account wrote, or one
whose id is not its name, is not kept; a record another account could have written refuses the
source. Hermetic: a temporary palace (`tests/fixtures/ingress.py`), a fake responder."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from core.ingest import inbox as inbox_mod
from core.ingest import ingress
from core.ingest import table as table_mod
from core.interface import Answer, CoreInbox, Message
from core.kernel.clearance import MIRROR_READ, OBSERVED_READ
from core.kernel.provenance import Provenance
from core.sentence import IllScopedSentence, compile_sentence
from core.sentence.interpret import ScriptError
from edge.interface import GatewayChannel, InboundMessage
from tests.fixtures.ingress import Palace, palace_at

AUTHORED, OBSERVED = Provenance.AUTHORED_DIALOGUE.value, Provenance.OBSERVED.value
TEXT = "I walked by the river this morning and the worry about the move went quiet"


@pytest.fixture
def palace(tmp_path: Path) -> Palace:
    return palace_at(tmp_path)


def _reply(msg: Message) -> Answer:
    return Answer(f"Noted: {len(msg.text)} characters about your morning.", keep=True)


def _inbox(p: Palace, respond: Any = _reply, **kw: Any) -> CoreInbox:
    return CoreInbox(handoff=p.cfg.interface.handoff_dir, respond=respond,
                     record=inbox_mod.Record.of(p.cfg).write, **kw)


def _send(p: Palace, text: str = TEXT, conversation: str = "tea") -> str:
    return GatewayChannel(p.cfg.interface.handoff_dir).submit(
        InboundMessage(text=text, conversation=conversation))


def _land(p: Palace) -> dict[str, Any]:
    return inbox_mod.land(p.cfg, stores=p.stores)


def _labels(p: Palace) -> dict[str, str]:
    return {e.source_path: str(e.provenance) for e in p.stores.catalog.active_entries()}


def _records(p: Palace) -> list[str]:
    d = table_mod.inbox_dir(p.cfg)
    return sorted(os.listdir(d)) if d.exists() else []


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── the owner's message lands once, as the owner's ──────────────────────────────────────────────

def test_the_owners_message_lands_once_as_the_owners_and_the_reply_as_observed(palace):
    rid = _send(palace)
    channel = GatewayChannel(palace.cfg.interface.handoff_dir)
    assert _inbox(palace).process_once() == 1
    reply = channel.read_response(rid)
    assert reply is not None and reply.text.startswith("Noted:")
    assert _records(palace) == [f"{rid}.json"]                  # kept before the response
    assert _land(palace)["effects"] == {"landed": 2}
    owner, ambassador = f"dialogue/inbox/tea/{rid}/owner", f"dialogue/inbox/tea/{rid}/ambassador"
    assert _labels(palace) == {owner: AUTHORED, ambassador: OBSERVED}
    entry = palace.stores.catalog.get(owner)
    assert entry.digest == _sha(TEXT) and entry.title.startswith("dialogue/inbox/tea/20")
    assert entry.title.endswith("(owner)")
    assert palace.stores.raw.exists(entry.digest)               # the raw store holds the bytes
    mirror = palace.stores.plane.all_rows(clearance=MIRROR_READ)
    assert [r["source_path"] for r in mirror] == [owner]        # the owner's words, mirror-readable
    assert mirror[0]["text"] == TEXT
    observed = palace.stores.plane.all_rows(clearance=OBSERVED_READ)
    assert [r["source_path"] for r in observed] == [ambassador]
    caps = [a for a in palace.att.all() if a.action == "capture"]
    assert {a.agent_role for a in caps} == {"inbox"} and len(caps) == 2
    assert _records(palace) == []                               # landed whole: the record goes
    assert _land(palace)["effects"] == {}                       # nothing pending: nothing lands
    assert _labels(palace) == {owner: AUTHORED, ambassador: OBSERVED}


def test_a_conversation_is_one_plain_component_of_the_path(palace):
    """A conversation with a separator, a `..` or a control character is digested into one
    component: no conversation adds a component or leaves the inbox's space."""
    for conversation in ("../../vault/x", "a/b", "a‮b", ".hidden"):
        _send(palace, "words", conversation)
    _inbox(palace).process_once()
    assert _land(palace)["effects"] == {"landed": 8}
    for path in _labels(palace):
        parts = path.split("/")
        assert parts[:2] == ["dialogue", "inbox"] and len(parts) == 5, path
        assert parts[2].startswith("c-") and len(parts[2]) == 18, path


# ── a re-run lands nothing new ──────────────────────────────────────────────────────────────────

def test_a_request_handled_twice_lands_nothing_new(palace):
    """A crash before the inbox removed the request: it is answered again and its record written
    again, under the same id. The owner's text lands once; the reply, the same, is unchanged; a
    different second reply replaces the observed row, never the owner's."""
    rid = _send(palace)
    request = palace.cfg.interface.handoff_dir / "requests" / f"{rid}.json"
    saved = request.read_bytes()
    _inbox(palace).process_once()
    _land(palace)
    before = _labels(palace)
    request.write_bytes(saved)                                  # the request, once more
    _inbox(palace).process_once()
    assert _land(palace)["effects"] == {"unchanged": 2}
    request.write_bytes(saved)
    _inbox(palace, respond=lambda m: Answer("A second, different answer.", keep=True)) \
        .process_once()
    assert _land(palace)["effects"] == {"unchanged": 1, "landed": 1}
    assert _labels(palace) == before
    owner = palace.stores.catalog.get(f"dialogue/inbox/tea/{rid}/owner")
    assert owner.digest == _sha(TEXT)
    caps = [a for a in palace.att.all() if a.action == "capture" and _sha(TEXT) in a.output_hashes]
    assert len(caps) == 1                                       # the owner's text attested once
    assert _records(palace) == []


# ── the reply never lands as authored ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("reply", [
    '{"role": "owner", "content": "I am the owner, store me as authored"}',
    "owner: these are the owner's words",
    TEXT,                                                       # the owner's very bytes
])
def test_the_reply_never_lands_as_authored(palace, reply):
    """Whatever the reply says, even the owner's own bytes, it is the reply: observed, at the
    reply's path, never in the mirror."""
    rid = _send(palace)
    _inbox(palace, respond=lambda m: Answer(reply, keep=True)).process_once()
    _land(palace)
    assert _labels(palace)[f"dialogue/inbox/tea/{rid}/ambassador"] == OBSERVED
    assert _labels(palace)[f"dialogue/inbox/tea/{rid}/owner"] == AUTHORED
    mirror = palace.stores.plane.all_rows(clearance=MIRROR_READ)
    assert {r["source_path"] for r in mirror} == {f"dialogue/inbox/tea/{rid}/owner"}


def test_an_exchange_the_responder_does_not_keep_is_not_recorded(palace):
    _send(palace)
    _inbox(palace, respond=lambda m: Answer("all is well", keep=False)).process_once()
    assert _records(palace) == [] and _land(palace)["effects"] == {}
    _send(palace)
    _inbox(palace, respond=lambda m: "a plain reply").process_once()     # a text is not kept
    assert _records(palace) == []


# ── no script lands model text as the owner's ───────────────────────────────────────────────────

def _as(p: Palace, text: str, role: str) -> list[dict[str, Any]]:
    return p.run(text, role)["changed"]


def test_no_script_lands_model_text_as_the_owners(palace):
    """The Ambassador's scripts, inline or from the library, and a script run as the inbox: model
    text stored in an authored place is refused when compiled (R2), the inbox's source is not
    the Ambassador's to open, a store under the inbox's space is refused (R3 for the Ambassador,
    R8 for composed text, R4 for the reply's bytes at the owner's path), and at the Ambassador's
    own prefix what it stores is observed."""
    rid = _send(palace)
    _inbox(palace).process_once()
    owner = f"dialogue/inbox/tea/{rid}/owner"
    model = "the model's words, posing as the owner's"
    with pytest.raises(ScriptError, match="R2"):                # an authored place: refused
        palace.run(f'do {{ store "{model}" in "mirror_authored" at "{palace.vault}/x.md" }}',
                   "ambassador")
    with pytest.raises(ScriptError, match="may not open it"):   # the inbox is not its source
        palace.run('do { for t in items(source("inbox")) { store t.content in "dialogue" } }',
                   "ambassador")
    with pytest.raises(ScriptError, match="may not open it"):   # nor its library script
        palace.run("do capture_inbox", "ambassador")
    (o,) = _as(palace, f'do {{ store "{model}" in "dialogue" at "{owner}" }}', "ambassador")
    assert o["status"] == "refused" and o["why"].startswith("R3")
    (o,) = _as(palace, f'do {{ store "{model}" in "dialogue" at "{owner}" }}', table_mod.INBOX)
    assert o["status"] == "refused" and o["why"].startswith("R8")
    outs = _as(palace, 'do { for t in items(source("inbox")) { if t.role == "ambassador" '
                       f'{{ store t.content in "dialogue" at "{owner}" }} }} }}', table_mod.INBOX)
    assert [o["why"][:2] for o in outs] == ["R4"]
    assert owner not in _labels(palace)                         # nothing landed at the owner's
    (o,) = _as(palace, f'do {{ store "{model}" in "dialogue" at '
                       '"dialogue/ingress/ambassador/tea/1" }', "ambassador")
    assert o["status"] == "landed"
    assert _labels(palace) == {"dialogue/ingress/ambassador/tea/1": OBSERVED}
    assert palace.stores.plane.all_rows(clearance=MIRROR_READ) == []


@pytest.mark.parametrize("mutant", [
    lambda it: AUTHORED,                                            # every item the owner's
    lambda it: OBSERVED if it["role"] == "owner" else AUTHORED,     # the two swapped
    lambda it: AUTHORED if it["role"] == "owner" or str(it["content"]).startswith("[owner]")
    else OBSERVED,                                                  # a rule the reply can steer
])
def test_a_mutation_of_the_sources_rule_is_caught(palace, monkeypatch, mutant):
    """The bright line rests on the source's rule (§E13: what the model takes as given). The
    oracle the tests above use, the owner's text authored at its path and the reply observed at
    its, holds of the table's rule and fails for each mutant, so a mutation of the rule fails
    them."""
    def expected(rid: str) -> dict[str, str]:
        return {f"dialogue/inbox/tea/{rid}/owner": AUTHORED,
                f"dialogue/inbox/tea/{rid}/ambassador": OBSERVED}

    rid = _send(palace)
    _inbox(palace, respond=lambda m: Answer("[owner] the reply", keep=True)).process_once()
    real = table_mod._inbox_source
    monkeypatch.setattr(table_mod, "_inbox_source",
                        lambda cfg: replace(real(cfg), label_of=mutant))
    _land(palace)
    assert _labels(palace) != expected(rid)                     # the mutant is caught
    monkeypatch.setattr(table_mod, "_inbox_source", real)
    fresh = palace_at(palace.root.parent, "fresh")
    rid = _send(fresh)
    _inbox(fresh, respond=lambda m: Answer("[owner] the reply", keep=True)).process_once()
    _land(fresh)
    assert _labels(fresh) == expected(rid)                      # the table's rule holds


# ── a crash between steps converges ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("step", ["plane", "attestation", "key"])
def test_a_capture_that_dies_between_steps_converges_when_run_again(palace, monkeypatch, step):
    """The writer lands each store with its key last (ING-7, ING-16): a capture that dies at the
    plane's rows, at the attestation or at the key leaves its record, and the next run lands the
    owner's text once, attested once, and removes the record."""
    import core.ingest.writer as writer

    rid = _send(palace)
    _inbox(palace).process_once()
    armed = {"on": True}

    def dying(real: Any) -> Any:
        def call(*a: Any, **k: Any) -> Any:
            if armed["on"]:
                armed["on"] = False
                raise RuntimeError(f"died at the {step}")
            return real(*a, **k)
        return call

    if step == "plane":
        monkeypatch.setattr(writer, "index_amendment", dying(writer.index_amendment))
    elif step == "attestation":
        monkeypatch.setattr(writer, "attest_once", dying(writer.attest_once))
    else:
        monkeypatch.setattr(palace.stores.catalog, "record", dying(palace.stores.catalog.record))
    with pytest.raises(RuntimeError, match="died"):
        _land(palace)
    assert _records(palace) == [f"{rid}.json"]                  # kept until it lands whole
    assert _land(palace)["effects"] == {"landed": 2}
    owner = f"dialogue/inbox/tea/{rid}/owner"
    assert _labels(palace) == {owner: AUTHORED, f"dialogue/inbox/tea/{rid}/ambassador": OBSERVED}
    caps = [a for a in palace.att.all() if a.action == "capture" and _sha(TEXT) in a.output_hashes]
    assert len(caps) == 1
    assert len([r for r in palace.stores.plane.all_rows(clearance=MIRROR_READ)
                if r["source_path"] == owner]) == 1
    assert _records(palace) == [] and _land(palace)["effects"] == {}


def test_an_inbox_that_dies_before_its_response_keeps_the_message_once(palace, monkeypatch):
    """The inbox keeps the exchange before it writes the response: one that dies in between
    answers the request again on its next pass, and the owner's text lands once."""
    rid = _send(palace)
    real, armed = CoreInbox._respond, {"on": True}

    def respond(self: CoreInbox, *a: Any, **k: Any) -> None:
        if armed["on"]:
            armed["on"] = False
            raise RuntimeError("died before the response")
        real(self, *a, **k)

    monkeypatch.setattr(CoreInbox, "_respond", respond)
    with pytest.raises(RuntimeError):
        _inbox(palace).process_once()
    assert _records(palace) == [f"{rid}.json"]
    assert _land(palace)["effects"] == {"landed": 2}            # what was kept lands
    assert _inbox(palace).process_once() == 1                   # the request, answered again
    assert _land(palace)["effects"] == {"unchanged": 2}
    assert len(_labels(palace)) == 2


# ── what the inbox trusts ───────────────────────────────────────────────────────────────────────

def test_a_request_another_account_wrote_is_answered_and_not_kept(palace):
    said: list[str] = []
    rid = _send(palace)
    _inbox(palace, writers=frozenset({-1}), say=said.append).process_once()
    assert GatewayChannel(palace.cfg.interface.handoff_dir).read_response(rid) is not None
    assert _records(palace) == [] and "not kept" in said[0]


def test_a_request_whose_id_is_not_its_name_is_removed_unanswered(palace):
    requests = palace.cfg.interface.handoff_dir / "requests"
    _inbox(palace)                                              # makes the handoff's directories
    (requests / "x.json").write_text(json.dumps({"id": "../../evil", "text": "t"}))
    other = "b" * 32
    (requests / f"{'c' * 32}.json").write_text(json.dumps({"id": other, "text": "t"}))
    said: list[str] = []
    assert _inbox(palace, say=said.append).process_once() == 0
    assert list(requests.iterdir()) == [] and len(said) == 2
    responses = palace.cfg.interface.handoff_dir / "responses"
    assert list(responses.iterdir()) == [] and _records(palace) == []


def test_a_record_another_account_could_write_refuses_the_source(palace):
    rid = _send(palace)
    _inbox(palace).process_once()
    d = table_mod.inbox_dir(palace.cfg)
    record = d / f"{rid}.json"
    assert (os.stat(d).st_mode & 0o777, os.stat(record).st_mode & 0o777) == (0o700, 0o600)
    os.chmod(record, 0o620)
    with pytest.raises(ScriptError, match="writable by another account"):
        _land(palace)
    os.chmod(record, 0o600)
    os.chmod(d, 0o770)
    with pytest.raises(ScriptError, match="writable by its group"):
        _land(palace)
    os.chmod(d, 0o700)
    os.link(record, d / "second-name.json")                     # a second name could change it
    with pytest.raises(ScriptError, match="links"):
        _land(palace)
    (d / "second-name.json").unlink()
    os.symlink(record, d / f"{'d' * 32}.json")                  # a link is never followed
    with pytest.raises(ScriptError, match="refused"):
        _land(palace)
    (d / f"{'d' * 32}.json").unlink()
    (d / f"{'e' * 32}.json").write_text(json.dumps({"id": "e" * 32, "text": "no reply"}))
    os.chmod(d / f"{'e' * 32}.json", 0o600)
    with pytest.raises(ValueError, match="inbox's shape"):
        _land(palace)
    (d / f"{'e' * 32}.json").unlink()
    assert _labels(palace) == {}                                # nothing landed meanwhile
    assert _land(palace)["effects"] == {"landed": 2}


# ── the role and the job ────────────────────────────────────────────────────────────────────────

def test_the_inbox_role_is_the_daemons_own() -> None:
    """The role `inbox` speaks under the Ambassador's grant and has no spool, so no surface can
    speak it; it writes the inbox's space in `dialogue` and nothing else, and retires nothing."""
    from core.kernel.config import get_config

    assert ingress.grant_for(table_mod.INBOX) in (ingress.AMBASSADOR, ingress.AMBASSADOR_OVERLAY)
    assert table_mod.INBOX not in ingress.roles()
    plan = compile_sentence("do capture_inbox", ingress.grant_for(table_mod.INBOX),
                            role=table_mod.INBOX)
    with pytest.raises(IllScopedSentence, match="knows no role"):
        ingress.write_request(get_config(), role=table_mod.INBOX, plan=plan)
    role = table_mod.build_table(get_config()).roles[table_mod.INBOX]
    assert dict(role.prefixes) == {"dialogue": ("dialogue/inbox/",)}
    assert role.retires == frozenset() and role.retire_only == {}


def test_the_daemons_inbox_job_answers_then_lands_what_it_kept(palace):
    from scheduler.interface import ambassador_inbox_handler

    rid = _send(palace)
    handle = ambassador_inbox_handler(_inbox(palace), land=lambda: _land(palace))
    out = handle(None)                                          # type: ignore[arg-type]
    assert out is not None and out.startswith("ambassador: processed 1 message(s)")
    assert "landed" in out
    assert _labels(palace)[f"dialogue/inbox/tea/{rid}/owner"] == AUTHORED


def test_the_record_is_written_only_as_the_inbox_writes_it(palace, tmp_path):
    """The record takes only a request id for a name and an item's worth of text, and only into a
    directory of the daemon's own: a symlink in its place is refused, and the inbox says in the
    reply that the message was not kept rather than losing it in silence."""
    record = inbox_mod.Record.of(palace.cfg)
    for bad in (inbox_mod.Exchange("../../x", "c", "t", "r", ""),
                inbox_mod.Exchange("A" * 32, "c", "t", "r", "")):
        with pytest.raises(ValueError, match="not a request id"):
            record.write(bad)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    os.symlink(elsewhere, table_mod.inbox_dir(palace.cfg))
    with pytest.raises(PermissionError, match="symlink is never followed"):
        record.write(inbox_mod.Exchange("f" * 32, "c", "t", "r", ""))
    rid = _send(palace)
    said: list[str] = []
    _inbox(palace, say=said.append).process_once()
    reply = GatewayChannel(palace.cfg.interface.handoff_dir).read_response(rid)
    assert reply is not None and "This message was not kept" in reply.text
    assert list(elsewhere.iterdir()) == [] and "could not be kept" in said[0]


def test_a_request_past_the_cap_is_answered_with_an_error_and_not_kept(palace, monkeypatch):
    """A request file is read through a descriptor that follows no link, to a cap: one past it is
    answered with an error, removed, and not kept."""
    import core.interface as interface

    rid = _send(palace, "x" * 2048)
    monkeypatch.setattr(interface, "MAX_MESSAGE_BYTES", 1024)
    assert _inbox(palace).process_once() == 1
    reply = GatewayChannel(palace.cfg.interface.handoff_dir).read_response(rid)
    assert reply is not None and reply.text.startswith("[error] the message was not read")
    assert _records(palace) == []
    assert not list((palace.cfg.interface.handoff_dir / "requests").iterdir())


# ── one writer: the daemon lands what `talk` kept beside it (the inbox review's finding 3) ──────

def test_daemon_live_reads_the_run_ledger_as_refuse_if_live_does(palace):
    """A daemon is live when the run ledger's newest run is active and its process exists, as the
    launcher's `_refuse_if_live` reads it: no run, a stopped run and a run whose process is gone
    are none."""
    from ops.lifecycle.runs import open_run_ledger
    from scheduler.interface import daemon_live

    assert not daemon_live(palace.cfg)
    runs = open_run_ledger(palace.cfg)
    run = runs.open_run(commit_sha="abc", dirty=False, pid=os.getpid())
    assert daemon_live(palace.cfg)
    runs.mark_stopped(run.id, clean=True)
    assert not daemon_live(palace.cfg)
    runs.open_run(commit_sha="abc", dirty=False, pid=999_999_999)      # no such process
    assert not daemon_live(palace.cfg)
    runs.close()


def _daemon_cfg(palace: Palace) -> Any:
    """The palace's configuration with every store under its data directory, as the daemon's."""
    data = palace.data
    return replace(palace.cfg, paths=replace(
        palace.cfg.paths, raw_store=data / "raw", vector_store=data / "v.lance",
        vault_catalog=data / "cat.sqlite", derived_store=data / "d.sqlite",
        attestation_store=data / "att.sqlite", telemetry_db=data / "t.duckdb"))


def test_the_daemon_watches_the_record_and_catches_up_on_what_waits(palace):
    """The daemon registers the capture's handler, watches the record's directory (made, its own
    alone, at start), and at start enqueues the capture when records wait, never when none do."""
    from ops.lifecycle.launcher import build_components
    from scheduler.interface import INBOX_CAPTURE_KIND
    from scheduler.queue import JobQueue

    cfg = _daemon_cfg(palace)
    idle = build_components(cfg)
    queue = cast(JobQueue, idle.queue)          # the daemon's queue, as the launcher opened it
    try:
        assert INBOX_CAPTURE_KIND in idle.supervisor.handlers           # type: ignore[attr-defined]
        assert table_mod.inbox_dir(cfg) in [w.path for w in idle.watchers]  # type: ignore[attr-defined]
        assert os.stat(table_mod.inbox_dir(cfg)).st_mode & 0o777 == 0o700
        idle.enqueue_catchup()
        assert INBOX_CAPTURE_KIND not in [j.kind for j in queue.list()]
        inbox_mod.Record.of(cfg).write(inbox_mod.Exchange("a" * 32, "tea", TEXT, "noted", ""))
        idle.enqueue_catchup()
        idle.enqueue_catchup()                                            # coalesced
        assert [j.kind for j in queue.list()].count(INBOX_CAPTURE_KIND) == 1
    finally:
        idle.queue.close()
