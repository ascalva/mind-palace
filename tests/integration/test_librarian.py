"""Librarian wiring (BUILD-SPEC §9) — deterministic, with fakes for the model + stores.

Proves: retrieval defaults to the AUTHORED mirror; context is Constitution-first with the
retrieved grounding injected and the query last; the grounding self-check passes a grounded
answer and flags a fabricated citation. The live end-to-end run is test_librarian_live.py.
"""

from core.constitution import load_constitution
from core.librarian import Librarian
from core.provenance import MIRROR_READABLE
from core.selfcheck import FAIL

ROWS = [
    {"title": "sleep-and-racing-thoughts", "source_path": "/x/sleep.md",
     "text": "slow breathing helps", "provenance": "authored-solo", "_distance": 0.4},
    {"title": "monthly-budget", "source_path": "/x/budget.md",
     "text": "emergency fund", "provenance": "authored-solo", "_distance": 0.6},
]


class FakeEmbedder:
    def embed_query(self, text):
        return [0.0, 0.0]

    def embed_documents(self, texts):
        return [[0.0, 0.0] for _ in texts]


class FakeStore:
    def __init__(self, rows):
        self.rows = rows
        self.last_provenances = "unset"

    def search(self, vector, *, k=5, provenances=None):
        self.last_provenances = provenances
        return self.rows[:k]


class FakeServer:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def chat(self, tier, messages, *, think=None):
        self.calls.append((tier, messages))
        return self.reply


def _lib(reply, rows=ROWS):
    return Librarian(server=FakeServer(reply), embedder=FakeEmbedder(),
                     store=FakeStore(list(rows)), k=2)


def test_retrieve_defaults_to_the_authored_mirror():
    lib = _lib("ans")
    rs = lib.retrieve("how to sleep")
    assert [r.title for r in rs] == ["sleep-and-racing-thoughts", "monthly-budget"]
    assert lib.store.last_provenances == MIRROR_READABLE   # authored-only firewall, structural
    assert rs[0].distance == 0.4


def test_context_is_constitution_first_with_grounding_and_query_last():
    lib = _lib("ans")
    ctx = lib.context_for("how to sleep", lib.retrieve("how to sleep"))
    assert ctx[0]["content"] == load_constitution()                   # Constitution outermost
    assert any("Librarian" in m["content"] for m in ctx)             # role present
    assert any("[[sleep-and-racing-thoughts]]" in m["content"] for m in ctx)  # grounding block
    assert ctx[-1] == {"role": "user", "content": "how to sleep"}    # query last


def test_answer_with_grounded_citation_passes_and_uses_routine_tier():
    lib = _lib("Per [[sleep-and-racing-thoughts]], slow breathing helps.")
    ans = lib.answer("how to sleep")
    assert ans.check.passed
    assert ans.sources
    assert lib.server.calls[0][0] == "routine"   # foreground RAG runs on the routine model


def test_answer_flags_a_fabricated_citation():
    lib = _lib("According to [[Made Up Note]], do X.")
    ans = lib.answer("how to sleep")
    assert not ans.check.passed
    assert any(f.status == FAIL for f in ans.check.findings)


def test_empty_retrieval_yields_no_context_marker():
    lib = _lib("I don't have notes on that.", rows=[])
    ctx = lib.context_for("obscure", lib.retrieve("obscure"))
    assert any("No notes were retrieved" in m["content"] for m in ctx)
