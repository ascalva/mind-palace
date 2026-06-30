"""The Ambassador's intent step (Track B / B2) — floor + model-earned, separately testable.

The authoritative note §5: a deterministic floor for the obvious cases; the model earned for the
ambiguous rest. These test the two units independently and their composition.
"""

from agents.ambassador.intent import (
    Intent,
    classify,
    classify_floor,
    classify_model,
    heuristic_fallback,
)


def test_floor_buckets_the_obvious_cases():
    assert classify_floor("what have you been doing?") is Intent.STATUS
    assert classify_floor("are you healthy?") is Intent.STATUS
    assert classify_floor("how do you work?") is Intent.EXPLAIN
    assert classify_floor("is my data safe?") is Intent.EXPLAIN
    assert classify_floor("what did I write about my father") is Intent.RETRIEVE
    assert classify_floor("find my notes on sleep") is Intent.RETRIEVE
    assert classify_floor("look into whether I've been more anxious lately") is Intent.TASK
    assert classify_floor("can you research treatments for migraines") is Intent.TASK


def test_floor_buckets_dreams_questions():
    assert classify_floor("what patterns have you noticed?") is Intent.DREAMS
    assert classify_floor("any insights from my notes lately?") is Intent.DREAMS
    assert classify_floor("what have you been dreaming about") is Intent.DREAMS
    # dreams (patterns) is distinct from status (activity/health) and retrieve (a specific recall)
    assert classify_floor("what have you been doing?") is Intent.STATUS
    assert classify_floor("what did I write about sleep") is Intent.RETRIEVE


def test_floor_returns_none_for_ambiguous():
    assert classify_floor("I've been thinking about my father a lot") is None
    assert classify_floor("tell me something interesting") is None


def test_floor_empty_is_capture():
    assert classify_floor("") is Intent.CAPTURE
    assert classify_floor("   ") is Intent.CAPTURE


def test_retrieve_beats_task_when_both_cues_present():
    # "what did I write" (retrieve) must win over "research" — it's a recall, not a delegation.
    assert classify_floor("what did I write about my research project") is Intent.RETRIEVE


def test_heuristic_fallback():
    assert heuristic_fallback("what's the weather?") is Intent.RETRIEVE   # a question → recall
    assert heuristic_fallback("I felt calm today") is Intent.CAPTURE      # a statement → store


def test_classify_model_parses_first_intent_word():
    assert classify_model("x", lambda _t: "task") is Intent.TASK
    assert classify_model("x", lambda _t: "Intent: explain (about the system)") is Intent.EXPLAIN
    # garbage → heuristic fallback (here, a statement → capture)
    assert classify_model("a quiet thought", lambda _t: "i have no idea") is Intent.CAPTURE


def test_classify_model_degrades_when_the_model_raises():
    def boom(_t):
        raise RuntimeError("no ollama")

    assert classify_model("what did the model do?", boom) is Intent.RETRIEVE   # "?" → retrieve


def test_classify_uses_floor_first_and_skips_the_model():
    calls = []

    def chat(text):
        calls.append(text)
        return "task"

    # An obvious retrieval resolves at the floor; the model is never consulted.
    assert classify("what did I write about sleep", chat=chat) is Intent.RETRIEVE
    assert calls == []
    # An ambiguous message earns the model.
    assert classify("I keep coming back to this", chat=chat) is Intent.TASK
    assert calls == ["I keep coming back to this"]


def test_classify_without_a_model_uses_the_heuristic():
    assert classify("what should I do?") is Intent.RETRIEVE     # ambiguous + "?" → retrieve
    assert classify("just a passing note") is Intent.CAPTURE    # ambiguous statement → capture
