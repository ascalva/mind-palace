"""Intent reasoning for the Ambassador (Track B / B2).

The authoritative note (§5) is explicit: the intent step is a **reasoning step, not a bucket
classifier** — but a *deterministic floor* handles the cheap, obvious cases (a clear retrieval,
a clear status query) before the model is earned for the ambiguous/compound rest. "Floor for
the obvious; mind for the rest."

So this module is two separately-testable units:
  * `classify_floor` — pure, deterministic; returns an `Intent` for an unambiguous message, else
    `None` ("not obvious — earn the model").
  * `classify_model` — the model-earned fallback; asks the pinned model to reason about intent,
    parses forgivingly, and degrades to a safe heuristic if the model is unavailable/unparseable.

The five intents map to the conversation loop's paths (ambassador-interpretation-and-flow.md §3),
with retrieval split by which graph it reads — the mirror (authored) vs. the curated
self-knowledge graph — so the firewall (curated ∉ mirror) is honored at the intent boundary.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum


class Intent(StrEnum):
    RETRIEVE = "retrieve"   # recall from the AUTHORED mirror → grounded answer
    EXPLAIN = "explain"     # how the SYSTEM works → the CURATED self-knowledge graph
    STATUS = "status"       # what it's been doing / is it healthy → the ops-view
    DREAMS = "dreams"       # patterns it has noticed across the notes → the INTERPRETED layer
    TASK = "task"           # go do real background work → gate → queue (delegated)
    CAPTURE = "capture"     # a statement/journal entry → store it; acknowledge


# Deterministic floor cues. Order of the checks below is deliberate: stronger, more specific
# signals are tested first so a compound phrase resolves the way a human would read it
# (e.g. "what did I write about my research project" is RETRIEVE, not TASK).
_STATUS_CUES = (
    "what have you been doing", "what have you been up to", "what did you do",
    "what are you doing", "what have you done", "what have you been working on",
    "are you healthy", "are you ok", "are you okay", "are you alright",
    "is everything ok", "is everything okay", "everything alright", "system status",
    "your status", "health check", "how are you doing",
)
_EXPLAIN_CUES = (
    "how do you work", "how does this work", "how are you built", "how were you built",
    "explain yourself", "explain your", "your architecture", "your design",
    "what are you", "who are you", "your constitution", "is my data safe",
    "are you private", "are you secure", "how do you protect", "how do you keep my",
    "how do you store", "what can you do",
)
_RETRIEVE_CUES = (
    "what did i write", "what have i written", "what do my notes say", "find my notes",
    "search my notes", "show me my notes", "did i write", "remind me what",
    "what did i say about", "do i have notes", "what have i said", "pull up my notes",
    "what did i note", "in my notes",
)
_DREAMS_CUES = (
    "what patterns", "any patterns", "patterns in my notes", "patterns across",
    "what have you noticed", "noticed anything", "noticed any", "what have you been dreaming",
    "what are you dreaming", "what insights", "any insights", "what themes", "any themes",
    "what connections", "any connections", "what stood out", "what have you figured out",
    "what have you learned about me", "anything interesting in my notes",
)
_TASK_CUES = (
    "look into", "dig into", "dig through", "investigate", "find out", "figure out",
    "look up whether", "research whether", "do some research", "can you research",
    "go research", "explore whether", "cross-check", "look at whether",
)


def classify_floor(text: str) -> Intent | None:
    """The deterministic floor: an `Intent` for an obvious message, else `None` (escalate)."""
    t = text.strip().lower()
    if not t:
        return Intent.CAPTURE
    if any(c in t for c in _STATUS_CUES):
        return Intent.STATUS
    if any(c in t for c in _EXPLAIN_CUES):
        return Intent.EXPLAIN
    if any(c in t for c in _DREAMS_CUES):     # patterns/insights → the interpreted layer
        return Intent.DREAMS
    if any(c in t for c in _RETRIEVE_CUES):   # before TASK: "what did I write" beats "research"
        return Intent.RETRIEVE
    if any(c in t for c in _TASK_CUES):
        return Intent.TASK
    return None


def heuristic_fallback(text: str) -> Intent:
    """Model-free default for ambiguous messages: a question is a retrieval (blast radius = a
    wrong query, which is read-only and recoverable — note §1b); a statement is a capture."""
    return Intent.RETRIEVE if text.strip().endswith("?") else Intent.CAPTURE


def classify_model(text: str, chat: Callable[[str], str]) -> Intent:
    """The model-earned step. `chat(text) -> reply` asks the pinned model to name the intent;
    parse the first intent word it returns. Forgiving: any unparseable/empty reply degrades to
    the deterministic heuristic, so a missing model never breaks the conversation."""
    try:
        reply = chat(text).lower()
    except Exception:
        return heuristic_fallback(text)
    best: tuple[int, Intent] | None = None
    for intent in Intent:
        pos = reply.find(intent.value)
        if pos != -1 and (best is None or pos < best[0]):
            best = (pos, intent)
    return best[1] if best is not None else heuristic_fallback(text)


def classify(text: str, *, chat: Callable[[str], str] | None = None) -> Intent:
    """Floor first; earn the model only for the ambiguous rest (note §5)."""
    floor = classify_floor(text)
    if floor is not None:
        return floor
    if chat is None:
        return heuristic_fallback(text)
    return classify_model(text, chat)


CLASSIFIER_ROLE = (
    "Classify the owner's message into exactly ONE intent and reply with only that single word.\n"
    "- retrieve: they want to recall or find something from their OWN notes/journals.\n"
    "- explain: they're asking how YOU (the system) work — your design or guarantees.\n"
    "- status: they're asking what you've been doing, or whether you are healthy.\n"
    "- dreams: they're asking what PATTERNS, themes, or insights you've noticed across their "
    "notes.\n"
    "- task: they're asking you to go look into / research / investigate something.\n"
    "- capture: they're telling you something (a thought, a journal entry) rather than asking.\n"
    "Reply with one word: retrieve, explain, status, dreams, task, or capture."
)
