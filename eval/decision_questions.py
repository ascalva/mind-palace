"""The decision integrators' questions: every word a decision model is asked, as declared data.

A decision model answers typed questions about supplied state with probabilities: a Choice among
options, a Noul (the probability that a statement is true), a Score on described levels. The
families below are generic, each a judgment a person could make at a glance about any text or any
pair of texts:

- **polarity** (an edge): does a passage support a claim, contradict it, or say nothing about it;
- **relevance** (an edge): does a passage answer a query, is it on the query's subject;
- **kind** (a node): is a text asking a question, and what is it mainly doing;
- **reply** (an edge): does a reply answer a question;
- **equivalence** (an edge): do two texts ask the same question;
- **subject** (a node): which of the options a caller supplies is a text's main subject.

The subject family takes its options from the caller. `ARXIV_ARCHIVES` is a benchmark fixture with
ground truth (dn-decision-integrators §8), never a feature of the palace. `DISCOVERY` holds the
candidate questions of the question-discovery pilot, drafted from the families before any answer
was read.

The wording follows TypeSafe's guidance (docs.typesafe.ai, read 2026-11-08): one judgment per
question; the subject named; option names that describe their content; criteria that describe
each outcome as a situation; a companion Noul beside a Choice whose options may not fit; the
polarity Choice is the citation-check cookbook's, with the cookbook's "section" read as a passage.
Each state field is named the way the questions refer to it. A change of wording is a change of
`VERSION`, and every stored answer is keyed by the digest of the exact question set that produced
it (`digest`), so an answer always names its questions.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

Question = dict[str, Any]  # the wire form: {"type": ..., "instructions": ..., "criteria": ...}

VERSION = "2026-11-08.1"


def digest(questions: dict[str, Question]) -> str:
    """The identity of a question set: sha256 over its questions, ids sorted, each question's own
    order kept (a Choice's option order is part of what the model reads)."""
    canonical = {qid: questions[qid] for qid in sorted(questions)}
    text = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _choice(instructions: str, options: dict[str, str]) -> Question:
    return {"type": "choice", "instructions": instructions, "criteria": dict(options)}


def _noul(instructions: str, true: str | None = None, false: str | None = None) -> Question:
    q: Question = {"type": "noul", "instructions": instructions}
    if true is not None and false is not None:
        q["criteria"] = {"true": true, "false": false}
    return q


def _score(instructions: str, levels: list[str]) -> Question:
    return {"type": "score", "instructions": instructions, "criteria": list(levels)}


# ── polarity: state {"claim": str, "passage": {"title": str, "text": str}} ─────────────────────

POLARITY_OPTIONS = {
    "supports": "The passage states the claim or directly implies that it is true",
    "contradicts": "The passage states the opposite of the claim or implies it is false",
    "says_nothing": "The passage does not address what the claim asserts, either way",
}

POLARITY: dict[str, Question] = {
    "relation": _choice("How does the passage relate to the claim?", POLARITY_OPTIONS),
    # the same Choice with its options in reverse order: the order control (jaggedness #8)
    "relation_reversed": _choice(
        "How does the passage relate to the claim?",
        dict(reversed(list(POLARITY_OPTIONS.items()))),
    ),
    "supports": _noul(
        "Does the passage show the claim to be true?",
        true="The passage states the claim or directly implies that it is true",
        false="The passage shows the claim to be false, or does not address what it asserts",
    ),
    "contradicts": _noul(
        "Does the passage show the claim to be false?",
        true="The passage states the opposite of the claim or implies it is false",
        false="The passage shows the claim to be true, or does not address what it asserts",
    ),
    # the companion Noul: does any polarity option apply at all
    "addresses": _noul(
        "Does the passage report a finding on what the claim asserts?",
        true="The passage reports a result that decides the claim, for it or against it",
        false="The passage is on a related subject but reports nothing that decides the claim",
    ),
}

# ── relevance: state {"query": str, "passage": {"title": str, "text": str}} ────────────────────

RELEVANCE: dict[str, Question] = {
    "answers": _noul(
        "Does the passage contain an answer to the query?",
        true="The passage states information that answers the query",
        false="The passage is on a related subject but does not answer the query",
    ),
    "on_subject": _noul("Does the passage address the subject of the query?"),
}

# ── kind: state {"text": str} ──────────────────────────────────────────────────────────────────

KIND_OPTIONS = {
    "asks_a_question": "The writer asks the reader for an answer, an explanation or help",
    "makes_a_claim": "The writer asserts that something is true",
    "reports_an_observation": "The writer reports something they saw, measured or experienced",
    "gives_an_instruction": "The writer tells the reader what to do or how to do it",
    "records_a_decision": "The writer states a choice that they or others have made",
}

KIND: dict[str, Question] = {
    "asks_question": _noul(
        "Is the writer of the text asking a question?",
        true="The writer asks the reader for an answer, an explanation or help",
        false="The writer answers, explains or reports something, even if the text contains a "
        "question",
    ),
    "kind": _choice("What is the text mainly doing?", KIND_OPTIONS),
}

# ── reply: state {"question": {"title": str, "text": str}, "reply": str} ───────────────────────

REPLY: dict[str, Question] = {
    "answers_question": _noul(
        "Does the reply answer the question?",
        true="The reply addresses the problem the question poses",
        false="The reply addresses a different problem, even one on the same subject",
    ),
}

# ── equivalence: state {"first": {"title", "text"}, "second": {"title", "text"}} ───────────────

EQUIVALENCE: dict[str, Question] = {
    "same_question": _noul(
        "Do the two posts ask the same question?",
        true="An answer to one post would also answer the other",
        false="The posts ask different questions, even if they share a subject",
    ),
}

# ── subject: state {"document": {"title": str, "text": str}}; the options are the caller's ─────


def subject(options: dict[str, str]) -> dict[str, Question]:
    """The subject Choice over the caller's options, and the same Choice in reverse order."""
    return {
        "subject": _choice("Which subject area is the main subject of the document?", options),
        "subject_reversed": _choice(
            "Which subject area is the main subject of the document?",
            dict(reversed(list(options.items()))),
        ),
    }


# A benchmark fixture with ground truth: the arXiv archives with at least 70 items in the sampled
# store, named by arXiv's own archive names. Never a palace feature.
ARXIV_ARCHIVES: dict[str, tuple[str, str]] = {  # option name -> (arXiv archive, description)
    "astrophysics": ("astro-ph", "Astrophysics (arXiv astro-ph)"),
    "computer_science": ("cs", "Computer science (arXiv cs)"),
    "condensed_matter": ("cond-mat", "Condensed matter physics (arXiv cond-mat)"),
    "economics": ("econ", "Economics (arXiv econ)"),
    "electrical_engineering_and_systems_science": (
        "eess",
        "Electrical engineering and systems science (arXiv eess)",
    ),
    "mathematical_physics": ("math-ph", "Mathematical physics (arXiv math-ph)"),
    "mathematics": ("math", "Mathematics (arXiv math)"),
    "nonlinear_sciences": ("nlin", "Nonlinear sciences (arXiv nlin)"),
    "physics": (
        "physics",
        "Physics outside the other physics archives: applied, atomic, biological, chemical, "
        "computational, fluid, optical, plasma, social and general physics (arXiv physics)",
    ),
    "quantitative_biology": ("q-bio", "Quantitative biology (arXiv q-bio)"),
    "quantitative_finance": ("q-fin", "Quantitative finance (arXiv q-fin)"),
    "quantum_physics": ("quant-ph", "Quantum physics (arXiv quant-ph)"),
    "statistics": ("stat", "Statistics (arXiv stat)"),
}

# ── question discovery: candidates on the polarity state, drafted from the generic families ────
# Edge questions read both fields; item questions read one. None was revised after an answer was
# read: the pilot's rule keeps a question only on rows it was not drafted from.

SUPPORT_LEVELS = [
    "The passage shows the claim is false",
    "The passage leans against the claim",
    "The passage says nothing about the claim",
    "The passage leans toward the claim",
    "The passage shows the claim is true",
]

RELATEDNESS_LEVELS = [
    "The passage is on a different subject from the claim",
    "The passage is in the same broad field but on a different topic",
    "The passage is on the same topic but a different question",
    "The passage is on the same question but reports no result on it",
    "The passage is on the same question and reports a result on it",
]

DISCOVERY: dict[str, Question] = {
    # relatedness and evidence (edge)
    "same_subject": _noul("Is the passage about the same subject as the claim?"),
    "reports_on_relationship": _noul(
        "Does the passage report a result about the relationship the claim describes?"
    ),
    "names_claim_entities": _noul("Does the passage mention the main things the claim is about?"),
    "background_only": _noul("Does the passage mention the claim's subject only in passing?"),
    "relatedness_level": _score("How closely is the passage related to the claim?",
                                RELATEDNESS_LEVELS),
    # agreement and disagreement (edge)
    "agrees": _noul("Does the passage report a finding that agrees with the claim?"),
    "disagrees": _noul("Does the passage report a finding that disagrees with the claim?"),
    "denies_part": _noul("Does the passage deny part of what the claim asserts?"),
    "support_level": _score("How does the passage bear on the claim?", SUPPORT_LEVELS),
    # direction and magnitude (edge)
    "same_direction": _noul("Does the passage describe an effect in the same direction as the "
                            "claim?"),
    "opposite_direction": _noul("Does the passage describe an effect in the opposite direction "
                                "to the claim?"),
    "shares_quantity": _noul("Does the passage state a number that the claim also states?"),
    "more_specific": _noul("Does the passage give more detail on the point the claim makes?"),
    # negative results and certainty (passage)
    "null_finding": _noul("Does the passage report that an effect or difference was not found?"),
    "passage_hedged": _noul("Does the passage state its main conclusion with hedging?"),
    "passage_own_data": _noul("Does the passage report a study with its own data?"),
    # the claim's own form (claim)
    "claim_hedged": _noul("Is the claim hedged, with words such as may, might or suggests?"),
    "claim_time_bound": _noul("Does the claim refer to a particular time or period?"),
    "claim_causal": _noul("Does the claim say that one thing causes another?"),
    "claim_negative": _noul("Does the claim say that something does not happen or is not so?"),
}

FAMILIES: dict[str, dict[str, Question]] = {
    "polarity": POLARITY,
    "relevance": RELEVANCE,
    "kind": KIND,
    "reply": REPLY,
    "equivalence": EQUIVALENCE,
    "subject_arxiv": subject({name: desc for name, (_, desc) in ARXIV_ARCHIVES.items()}),
    "discovery": DISCOVERY,
}


def manifest() -> dict[str, Any]:
    """Every family's digest and size, for the record."""
    return {
        "version": VERSION,
        "families": {
            name: {"digest": digest(qs), "questions": sorted(qs)} for name, qs in FAMILIES.items()
        },
    }
