"""Research airlock — the sealed-core (Zone A) side of the one-way research flow (§16).

The owner asks a health/research question; the core must NOT leak the question or any note
content to the network. Instead it emits **de-identified research criteria** (short topical
terms only), which the Zone-B bridge carries to the cloud fetcher; public literature comes
back and is ranked **inside the walls** against the private corpus.

This package is sealed-core code: it has NO network, NO S3, NO `boto3`, and never imports
`edge`/`cloud`. It only reads and writes a filesystem handoff directory (mirroring the §12
interface handoff). The structural firewall (Invariant 11, §16):

  * `criteria.py` — only a `ResearchCriteria` (de-identified terms + filters) can be
    constructed, and `deidentify()` rejects anything that looks like PII or free narrative.
    The type that crosses the airlock has **no field that could carry note content**.
  * `airlock.py` — the core writes criteria requests / reads literature results on disk; it
    never touches S3 or the network. The corpus never crosses.
  * `rank.py` — public literature is ranked against the private corpus **transiently**,
    inside the core. It is NEVER ingested into the AUTHORED mirror (it is public, external,
    not the owner's own writing).
"""

from core.research.airlock import ResearchAirlock, ResearchResult, build_airlock
from core.research.criteria import (
    DeidentificationError,
    Paper,
    ResearchCriteria,
    deidentify,
)
from core.research.rank import RankedPaper, rank_literature

__all__ = [
    "DeidentificationError",
    "Paper",
    "RankedPaper",
    "ResearchAirlock",
    "ResearchCriteria",
    "ResearchResult",
    "build_airlock",
    "deidentify",
    "rank_literature",
]
