"""The two cross-cutting build deltas (authoritative note §5): effort narration + the
earned-interruption policy.

Both follow "model advises, code acts": the *judgment* ("is this worth raising?", "what to
say") may be model-advised, but the *policy* (whether to deliver an unprompted message at all,
the default-off knob) and the *register* (plain language, never internals) are plain, testable
code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# Internal nouns the plain-language registers must NEVER leak (authoritative note §4's contrast
# example). Asserted by the unit tests, so an edit can't quietly reintroduce jargon.
LEAKY_NOUNS = (
    "synthesis", "tier", "queue", "job", "token", "accessor", "signature", "sqlite",
    "lancedb", "embedding", "vector", "attestation", "ledger", "podman", "ollama", "qwen",
)


# Delegation verbs to strip when extracting the topic of a "go do this" request.
TASK_PREFIXES = (
    "look into whether", "look into", "dig into", "dig through", "investigate",
    "find out whether", "find out", "figure out", "research whether", "do some research on",
    "do some research", "can you research", "go research", "explore whether", "look at whether",
    "cross-check",
)


def topic_of(text: str) -> str:
    """A short topic for a delegated request — strip the delegation verb, cap the length. Shared
    by the effort narration and the delegated-result surfacing so they read consistently."""
    t = text.strip().rstrip("?.!")
    low = t.lower()
    for cue in TASK_PREFIXES:
        if low.startswith(cue):
            t = t[len(cue):].strip(" ,:")
            break
    return t[:60].strip()


# External-literature cues that mark a TASK as *research* (the airlock path) rather than a dig
# through the owner's OWN notes (the existing librarian.answer path). Deliberately CONSERVATIVE
# (external-grounding.md §2.5 parked decision): a request must explicitly invoke the literature
# to route to the airlock; anything ambiguous defaults to the mirror path (blast radius of a
# wrong route: a read-only mirror answer, fully recoverable). Precision is revisitable with a
# classifier if it proves poor in use.
RESEARCH_CUES = (
    "research on", "research about", "research into", "the research on", "recent research",
    "papers", "literature", "studies on", "the studies", "publications", "scientific",
    "clinical trial", "clinical trials", "meta-analysis", "meta analysis",
    "systematic review", "peer-reviewed", "peer reviewed", "academic", "the evidence on",
    "what does the science", "what does the research",
)


def is_research_request(text: str) -> bool:
    """True when a TASK message asks for EXTERNAL literature grounding (the airlock), not a dig
    through the owner's own notes. Conservative: an explicit literature cue is required, else the
    request stays on the mirror path (the safe default — external-grounding.md §2.5)."""
    low = text.lower()
    return any(cue in low for cue in RESEARCH_CUES)


def narrate_effort(topic: str = "") -> str:
    """Plain-language "I need to go work on this" — the RIGHT register (note §4): honest about
    the wait + the rough plan, never the plumbing. A pure function from "what was delegated" to
    one plain sentence (unit-tested to leak no internal noun)."""
    topic = topic.strip()
    if topic:
        return (f"That's a bigger question — let me dig through your notes on {topic} and "
                "cross-check a few things. I'll come back to you with what I find.")
    return ("That's a bigger question — let me dig through your notes and cross-check a few "
            "things. Give me a bit and I'll come back to you.")


class Sensitivity(StrEnum):
    OFF = "off"                  # never surface anything unprompted (the owner opted out)
    EARNED_ONLY = "earned_only"  # surface only what's judged worth raising (the default)
    VERBOSE = "verbose"          # surface freely


@dataclass(frozen=True)
class InterruptionPolicy:
    """Whether the Ambassador may speak UNPROMPTED. The "would the owner want this raised?"
    judgment is the model-advised part; this policy is the code that acts on it, and the
    owner-tunable default is `EARNED_ONLY` (note §3 — "not a silent oracle, not a nag").

    A single dial (off / earned-only / verbose) is shipped; per-category sensitivity is left a
    documented future extension (note §7 leaves it genuinely open — avoid the premature-
    abstraction trap on an axis nothing uses yet). Expected updates (a result the owner asked
    for) are NOT governed by this — those are always delivered; this gates only the unprompted."""

    sensitivity: Sensitivity = Sensitivity.EARNED_ONLY

    def admits(self, worth_raising: bool) -> bool:
        if self.sensitivity is Sensitivity.OFF:
            return False
        if self.sensitivity is Sensitivity.VERBOSE:
            return True
        return worth_raising


def parse_sensitivity(value: str) -> Sensitivity:
    """Tolerant config parse — an unknown value degrades to the safe default (earned-only)."""
    try:
        return Sensitivity(value.strip().lower())
    except ValueError:
        return Sensitivity.EARNED_ONLY
