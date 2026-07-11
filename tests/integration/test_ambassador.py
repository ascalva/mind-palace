"""The Ambassador's five paths end to end with fakes (Track B / B2–B5).

Proves: each intent routes to its path; RETRIEVE reads the authored mirror and EXPLAIN reads the
curated graph (the firewall holds at the conversational layer); STATUS narrates plainly with no
model; TASK delegates + narrates effort; the owner's messages on mind-turns are captured as
authored-dialogue; every step is attested; earned interruptions respect the policy.
"""

from pathlib import Path

from agents.ambassador import Ambassador, DeliveredResult, Intent, InterruptionPolicy, Sensitivity
from agents.ambassador.policy import LEAKY_NOUNS
from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.dreams_view import DreamsView
from core.ingest.dialogue import DialogueCapture
from core.librarian import Librarian
from core.ops_view import OpsView
from core.provenance import Provenance
from core.stores.catalog import VaultCatalog
from core.stores.derived import DREAM, DerivedStore
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from ops.ledger import ProposalLedger
from scheduler.budget import Budgeter
from tests.fixtures.fakes import HashingEmbedder, ReplyServer

DIM = 32


def _row(digest, title, text, provenance, emb):
    return {"id": f"{digest}:0", "digest": digest, "title": title, "source_path": f"/{title}",
            "chunk_index": 0, "provenance": provenance, "text": text,
            "vector": emb.embed_documents([text])[0]}


class _FakeDrift:
    def __init__(self, within):
        self.within_tolerance = within
        self.constitution_intact = True


def _amb(tmp_path, *, server=None, drift=None, sensitivity=Sensitivity.EARNED_ONLY,
         delegate=None, pending=None, derived=None):
    emb = HashingEmbedder(DIM)
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    store.add([
        _row("sleep1", "sleep", "racing thoughts at night, slow breathing helps me sleep",
             "authored-solo", emb),
        _row("budget1", "budget", "monthly budget and emergency fund", "authored-solo", emb),
        _row("cur1", "docs/design",
             "The Ambassador is a reasoning agent that is computationally light", "curated", emb),
    ])
    att_store = AttestationStore(Path(":memory:"))
    attestor = StoreAttestor(att_store)
    capture = DialogueCapture(raw=RawStore(tmp_path / "raw"), store=store, embedder=emb,
                              catalog=VaultCatalog(tmp_path / "c.sqlite"), attestor=attestor)
    ops_view = OpsView.over(att_store, ProposalLedger(Path(":memory:")),
                            drift=(lambda: drift) if drift is not None else None)
    amb = Ambassador(
        server=server or ReplyServer("Here's what I see."),
        librarian=Librarian(server=server or ReplyServer(), embedder=emb, store=store, k=5),
        ops_view=ops_view,
        dreams_view=DreamsView.over(derived) if derived is not None else None,
        budgeter=Budgeter(window=8192),
        tier="router",
        capture_sink=capture,
        attestor=attestor,
        delegate=delegate,
        pending_results=pending,
        interruption=InterruptionPolicy(sensitivity),
    )
    return amb, att_store, store


def test_retrieve_reads_the_mirror_and_captures_the_turn(tmp_path):
    seen = {}

    def fn(_tier, messages):
        seen["ctx"] = " ".join(m["content"] for m in messages)
        return "Based on your notes, slow breathing helps."

    amb, att_store, store = _amb(tmp_path, server=ReplyServer(fn=fn))
    turn = amb.respond("what did I write about sleep")

    assert turn.intent is Intent.RETRIEVE
    assert "slow breathing" in seen["ctx"]                  # mirror chunk reached the model
    assert "computationally light" not in seen["ctx"]       # curated did NOT (firewall)
    # the owner's message landed as authored-dialogue (the capture loop)
    dialogue = store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE})
    assert any("what did I write about sleep" in r["text"] for r in dialogue)
    # attested: a read (the retrieval) + a capture (the dialogue)
    actions = {a.action for a in att_store.all()}
    assert {"read", "capture"} <= actions


def test_explain_reads_the_curated_graph_not_the_mirror(tmp_path):
    seen = {}

    def fn(_tier, messages):
        seen["ctx"] = " ".join(m["content"] for m in messages)
        return "I'm a reasoning agent that stays light."

    amb, _att, _store = _amb(tmp_path, server=ReplyServer(fn=fn))
    turn = amb.respond("how do you work")

    assert turn.intent is Intent.EXPLAIN
    assert "computationally light" in seen["ctx"]           # curated reached the model
    assert "slow breathing" not in seen["ctx"]              # mirror did NOT (firewall, reversed)


def test_dreams_reflects_the_interpreted_layer_mirror_not_oracle(tmp_path):
    derived = DerivedStore(Path(":memory:"))
    derived.add(kind=DREAM, summary="a pull toward solitude when work intensifies",
                subjects=["overwork", "weekend alone"])
    server = ReplyServer("SHOULD NOT BE CALLED")
    amb, att_store, store = _amb(tmp_path, server=server, derived=derived)
    turn = amb.respond("what patterns have you noticed in my notes?")

    assert turn.intent is Intent.DREAMS
    assert server.calls == []                               # deterministic narration, no model
    low = turn.reply.lower()
    assert "pull toward solitude" in low                    # the synthesis is reflected
    assert "[[overwork]]" in turn.reply                     # the spanned notes are cited
    assert "not anything you wrote" in low                  # framed as interpretation (§III.2)
    # DREAMS is about the SYSTEM's read, not the owner's mind — not added to the corpus
    assert store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE}) == []
    assert any(a.action == "read" for a in att_store.all())  # attested as a read


def test_dreams_without_a_view_is_honest(tmp_path):
    amb, _att, _store = _amb(tmp_path)                      # no derived store wired
    turn = amb.respond("any insights from my notes?")
    assert turn.intent is Intent.DREAMS
    assert "haven't started looking for patterns" in turn.reply.lower()


def test_status_is_plain_language_and_uses_no_model(tmp_path):
    server = ReplyServer("SHOULD NOT BE CALLED")
    amb, _att, _store = _amb(tmp_path, server=server)
    turn = amb.respond("what have you been doing?")

    assert turn.intent is Intent.STATUS
    assert server.calls == []                               # status renders deterministically
    low = turn.reply.lower()
    for noun in LEAKY_NOUNS:
        assert noun not in low                              # no internal nouns leak


def test_task_delegates_and_narrates_effort(tmp_path):
    delegated: list[tuple[str, str]] = []

    def _delegate(q: str, c: str) -> str:
        delegated.append((q, c))
        return "task-1"

    amb, att_store, _store = _amb(tmp_path, delegate=_delegate)
    turn = amb.respond("look into whether I've been more anxious lately")

    assert turn.intent is Intent.TASK
    assert delegated == [("look into whether I've been more anxious lately", "default")]
    low = turn.reply.lower()
    assert "dig" in low                                     # plain effort narration
    for noun in LEAKY_NOUNS:
        assert noun not in low
    assert any(a.action == "propose" for a in att_store.all())


def test_capture_intent_stores_and_acknowledges(tmp_path):
    amb, _att, store = _amb(tmp_path)
    turn = amb.respond("I felt really steady and clear after the run today")

    assert turn.intent is Intent.CAPTURE
    assert "saved" in turn.reply.lower() or "noted" in turn.reply.lower()
    dialogue = store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE})
    assert any("steady and clear" in r["text"] for r in dialogue)


def test_status_turn_is_not_captured(tmp_path):
    # STATUS/EXPLAIN are about the SYSTEM, not the owner's mind — not added to the corpus.
    amb, _att, store = _amb(tmp_path)
    amb.respond("are you healthy?")
    assert store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE}) == []


def test_ungrounded_answer_is_flagged_not_hidden(tmp_path):
    # A fabricated citation fails the grounding self-check → the reply carries an honest caveat.
    amb, _att, _store = _amb(tmp_path, server=ReplyServer("According to [[Made Up Note]], do X."))
    turn = amb.respond("what did I write about sleep")
    assert turn.check is not None and not turn.check.passed
    assert "grain of salt" in turn.reply.lower()


def test_earned_interruption_surfaces_a_drift_alarm_per_policy(tmp_path):
    # On an UNPROMPTED turn (not a status question), earned_only + a real alarm (drift out of
    # tolerance) surfaces the alarm as a prefix.
    amb, _att, _store = _amb(tmp_path, drift=_FakeDrift(within=False),
                             sensitivity=Sensitivity.EARNED_ONLY)
    assert "drifted" in amb.respond("I had a productive day").reply.lower()

    # OFF → the owner opted out of unprompted messages; even a real alarm stays silent.
    amb_off, _a, _s = _amb(tmp_path, drift=_FakeDrift(within=False), sensitivity=Sensitivity.OFF)
    assert "drifted" not in amb_off.respond("I had a productive day").reply.lower()


def test_status_reports_health_even_with_interruptions_off(tmp_path):
    # The interruption policy gates UNPROMPTED messages — a direct "are you healthy?" is asked,
    # so the drift health is reported regardless of the dial.
    amb, _att, _store = _amb(tmp_path, drift=_FakeDrift(within=False), sensitivity=Sensitivity.OFF)
    assert "drift" in amb.respond("are you healthy?").reply.lower()


def test_expected_results_are_delivered_regardless_of_sensitivity(tmp_path):
    # A result the owner ASKED for is an expected update — delivered even with interruptions OFF.
    result = DeliveredResult(ref="task-1", topic="my sleep", text="You wrote about it 4 times.")
    amb, _att, _store = _amb(tmp_path, sensitivity=Sensitivity.OFF,
                             pending=lambda _conv: [result])
    turn = amb.respond("hi")
    assert "here's what i found" in turn.reply.lower()
    assert "4 times" in turn.reply
    # not re-surfaced on the next turn
    assert "here's what i found" not in amb.respond("ok thanks").reply.lower()
