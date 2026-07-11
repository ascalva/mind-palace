# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    π_public — the airlock erasure map onto a label that carries no note content
#            (ResearchCriteria).
# INVARIANT: what crosses the airlock outbound is de-identified topical terms only — no
#            names/dates/places/narrative/note content (I11, §16).
# ENFORCED:  structural + runtime guard — the type has no free-text/content field
#            (unrepresentable); assert_clean re-scrubs at the emit boundary (raises on doubt).
"""De-identified research criteria — the one thing allowed to cross the airlock (§16).

THIS IS THE PRIVACY BOUNDARY. The owner's question may be deeply personal ("my migraines
since the divorce in March, ..."). What leaves the sealed core to reach the public internet
must contain **only de-identified topical search terms** — no names, dates, places, free
narrative, or note content (Invariant 11).

Two layers of defense, both structural:

  1. **Type shape.** `ResearchCriteria` has only short, structured fields (a topic label, a
     tuple of terms, coarse filters). It has NO free-text body and NO field that could hold
     the raw query or a note. `to_request()` serializes only these fields, so the payload
     that crosses the airlock cannot carry corpus content — the same way `DerivedStore` has
     no `provenance` parameter, the firewall is in what the type *cannot represent*.

  2. **Validation (`deidentify`).** Even the terms are scrubbed: each must be short, in a
     conservative charset, and free of PII patterns (emails, phone numbers, URLs, handles,
     long digit runs). The policy is **conservative — it raises rather than letting anything
     doubtful through** (`DeidentificationError`). `assert_clean()` re-runs the check at the
     emit boundary so a hand-built criteria object cannot bypass it.

The model only *advises* (proposes candidate terms); this code *acts* — it is the enforcer
(Invariant 2). The richer PII scrubber (corpus proper-noun denylist, NER) is a documented
extension point; the conservative baseline ships now.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

# Conservative bounds on a single search term. A genuine topical term ("systematic review",
# "migraine prophylaxis") is a few short words; anything longer is narrative trying to escape.
_MAX_TERM_CHARS = 64
_MAX_TERM_WORDS = 6
_MAX_TERMS = 12          # a focused query, not a data exfil channel
_MAX_RESULTS_CAP = 100   # the fetcher will not be asked for more than this

# Allowed characters in a term: letters, digits, spaces and a small set of separators that
# appear in real topical phrases. NOT permitted: '@', '#', ':', '/', digits-as-identifiers,
# anything that could encode a contact handle, URL, or path.
_ALLOWED_TERM = re.compile(r"^[A-Za-z][A-Za-z0-9 \-'.()+&]*$")

# PII / non-topical patterns that must never cross. Conservative: any hit rejects the term.
_PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+"),       # email
    re.compile(r"https?://|www\."),                # URL
    re.compile(r"\b\+?\d[\d\-().\s]{6,}\d\b"),     # phone / long number run
    re.compile(r"[@#]\w+"),                         # social handle / hashtag
    re.compile(r"\b\d{5,}\b"),                      # long digit run (ids, SSNs, account #s)
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),  # explicit calendar date
)

# Publication-type filters the fetcher understands. A fixed allowlist — arbitrary strings
# never reach the query layer. Bias toward high-evidence types (§16).
ALLOWED_PUBLICATION_TYPES: frozenset[str] = frozenset({
    "systematic-review", "meta-analysis", "review", "randomized-controlled-trial",
    "clinical-trial", "cohort-study", "case-control-study", "guideline",
})


class DeidentificationError(ValueError):
    """A proposed term/topic could not be safely de-identified, so it is refused.

    Raised rather than silently dropped at the *boundary* (`assert_clean`) so a leak attempt
    is loud. `deidentify()` (the constructor path) drops un-cleanable terms but still raises
    if nothing usable remains — conservative either way."""


@dataclass(frozen=True)
class ResearchCriteria:
    """The de-identified search request. The ONLY object that crosses the airlock outbound.

    By construction it carries no note content: a short topic label, scrubbed terms, and
    coarse filters. `to_request()` is the exact outbound wire payload."""

    topic: str
    terms: tuple[str, ...]
    from_year: int | None = None
    publication_types: tuple[str, ...] = ()
    max_results: int = 50
    id: str = field(default_factory=lambda: uuid4().hex)

    def assert_clean(self) -> None:
        """Re-validate at the trust boundary (defense in depth). Raises on any violation —
        a criteria object built by hand cannot bypass the scrubber on its way out."""
        _clean_term(self.topic)
        if not self.terms:
            raise DeidentificationError("criteria has no terms")
        if len(self.terms) > _MAX_TERMS:
            raise DeidentificationError(f"too many terms ({len(self.terms)} > {_MAX_TERMS})")
        for t in self.terms:
            _clean_term(t)
        for p in self.publication_types:
            if p not in ALLOWED_PUBLICATION_TYPES:
                raise DeidentificationError(f"unknown publication type {p!r}")
        if not (1 <= self.max_results <= _MAX_RESULTS_CAP):
            raise DeidentificationError(f"max_results out of range: {self.max_results}")
        if self.from_year is not None and not (1800 <= self.from_year <= 2100):
            raise DeidentificationError(f"implausible from_year: {self.from_year}")

    def to_request(self) -> dict[str, Any]:
        """The outbound wire payload — de-identified criteria only, no corpus content."""
        return {
            "id": self.id,
            "topic": self.topic,
            "terms": list(self.terms),
            "filters": {
                "from_year": self.from_year,
                "publication_types": list(self.publication_types),
                "max_results": self.max_results,
            },
        }


@dataclass(frozen=True)
class Paper:
    """One public-literature record returned by the fetcher. Public data, not the mirror."""

    source: str          # "openalex" | "europepmc" | "arxiv"
    id: str              # the source's canonical id (OpenAlex id, PMID, arXiv id)
    title: str
    abstract: str
    year: int | None
    venue: str
    type: str            # normalized publication type, e.g. "review", "meta-analysis"
    doi: str
    url: str             # canonical resolvable URL
    is_preprint: bool

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Paper:
        return cls(
            source=str(d.get("source", "")),
            id=str(d.get("id", "")),
            title=str(d.get("title", "")),
            abstract=str(d.get("abstract", "")),
            year=(int(d["year"]) if d.get("year") not in (None, "") else None),
            venue=str(d.get("venue", "")),
            type=str(d.get("type", "")),
            doi=str(d.get("doi", "")),
            url=str(d.get("url", "")),
            is_preprint=bool(d.get("is_preprint", False)),
        )


def clean_term(term: str) -> str:
    """The conservative outbound-term scrubber, public seam. ONE implementation shared by every
    boundary where a term leaves the sealed core (airlock criteria here; sensing requests in
    core/sensing.py) — so the de-identification policy cannot drift between surfaces. Raises
    `DeidentificationError` on anything unsafe."""
    return _clean_term(term)


def _clean_term(term: str) -> str:
    """Validate and normalize one term. Raises `DeidentificationError` on anything unsafe."""
    t = " ".join(term.split())  # collapse whitespace
    if not t:
        raise DeidentificationError("empty term")
    if len(t) > _MAX_TERM_CHARS:
        raise DeidentificationError(f"term too long ({len(t)} chars): {t[:32]!r}…")
    if len(t.split()) > _MAX_TERM_WORDS:
        raise DeidentificationError(f"term has too many words: {t!r}")
    for pat in _PII_PATTERNS:
        if pat.search(t):
            raise DeidentificationError(f"term looks like PII / non-topical: {t!r}")
    if not _ALLOWED_TERM.match(t):
        raise DeidentificationError(f"term has a disallowed character: {t!r}")
    return t


def deidentify(
    topic: str,
    terms: list[str],
    *,
    from_year: int | None = None,
    publication_types: list[str] | tuple[str, ...] = (),
    max_results: int = 50,
) -> ResearchCriteria:
    """Build a `ResearchCriteria` from proposed (possibly model-suggested) topic + terms.

    Conservative: un-cleanable terms are dropped; if nothing usable remains it raises.
    Publication types outside the allowlist are dropped silently. `max_results` is capped."""
    clean_topic = _clean_term(topic)  # the topic must itself be clean (it crosses too)

    seen: dict[str, None] = {}
    for raw in terms:
        try:
            seen.setdefault(_clean_term(raw), None)
        except DeidentificationError:
            continue  # drop the unsafe term, keep going (conservative)
    clean_terms = tuple(seen)[:_MAX_TERMS]
    if not clean_terms:
        raise DeidentificationError("no usable de-identified terms remained")

    pubs = tuple(p for p in publication_types if p in ALLOWED_PUBLICATION_TYPES)
    capped = max(1, min(int(max_results), _MAX_RESULTS_CAP))

    criteria = ResearchCriteria(
        topic=clean_topic,
        terms=clean_terms,
        from_year=from_year,
        publication_types=pubs,
        max_results=capped,
    )
    criteria.assert_clean()  # belt and suspenders
    return criteria
