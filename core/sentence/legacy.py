"""The eight one-word verbs of `core/query.py` as sentences — the compatibility map, and the
demonstration that the old surface is a fragment of the new one (dn-query-sentence-algebra §2.1).

HYBRID is the one verb that was a composition all along: `near "<text>" and diffuse S from <note>`,
ranked. CAPTURE is a write and has no sentence: a sentence is a reading.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.kernel.scope import Stratum
from core.query import Verb


def _quote(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def sentence_of(verb: Verb, *, text: str | None = None, target: str | None = None,
                strata: Iterable[Stratum] = (), k: int = 5, depth: int = 1, beta: float = 1.0,
                direction: str = "forward") -> str:
    """The sentence a legacy `Query` means. Raises `ValueError` for CAPTURE, and when a verb's
    argument is missing."""
    if verb is Verb.CAPTURE:
        raise ValueError("capture is a write; a sentence is a reading")
    strata_t = tuple(strata)
    over = (" over " + " ".join(s.value for s in strata_t)) if strata_t else ""
    if verb is Verb.SEARCH:
        if text is None:
            raise ValueError("search needs text")
        return f"top {k} near {_quote(text)}{over}"
    if target is None:
        raise ValueError(f"{verb.value} needs a target")
    if verb is Verb.REACH:
        return f"reach F from {_quote(target)} depth {depth}"
    if verb is Verb.DIFFUSE:
        return f"top {k} diffuse S from {_quote(target)} beta {beta:g}"
    if verb is Verb.HYBRID:
        if text is None:
            raise ValueError("hybrid needs text")
        return f"top {k} (near {_quote(text)} and diffuse S from {_quote(target)} beta {beta:g})"
    if verb is Verb.HISTORY:
        return f"trace {_quote(target)} {'back' if direction == 'back' else 'forward'}"
    if verb is Verb.RELATED:
        return f"relate {_quote(target)}"
    return f"witness {_quote(target)}"
