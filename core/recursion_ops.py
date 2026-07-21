# ── Family 1/5 boundary · dialogue operations (the ingest-operation instantiation of D) ──
# OBJECT:    dialogue reasoning operations — supersede / attach_defeater / record_warrant — that ACT
#            on existing claims rather than entering as peer nodes (dialogue-ingest-and-recursion.md
#            §3–§4; recursive-strata.md; build plan Item 2b).
# INVARIANT: a correction is a RELATION over claims (never a peer assertion); the CONCLUSION is
#            INTERPRETED (γ^d applies, minted via DerivedStore); claim-supersede is a DISTINCT
#            relation in a DISTINCT store from version-supersedes (§4A C3), never the balance graph.
# ENFORCED:  structural — the conclusion is minted through `DerivedStore` (no provenance param ⇒
#            INTERPRETED, γ^d by depth); operations land in `ClaimOpStore`, not Edge/Version.
"""Dialogue operations — corrections that act on claims, not peer nodes (dialogue-ingest §3–§4).

A note is a claim; a dialogue is a *derivation* whose output is a set of OPERATIONS on existing
claims (§3), never a new peer node beside them (the §2 failure — two content-addressed claims
disagreeing, lighting up a false contradiction). The ratified starter vocabulary (§4; build plan
Item 2a) is three operations:

  * `Supersede(C, conclusion, warrant)`   — the dialogue's conclusion C′ replaces C in the ACTIVE
    projection; C is retained in history with the warrant as the reason. C′ is a DERIVED conclusion
    (interpreted, γ^d-damped — never an authored peer), minted through the `DerivedStore`.
  * `AttachDefeater(C, defeater)`         — records that C is contested and how (C stays, marked).
  * `RecordWarrant(warrant, {C, C′})`     — the reasoning linking the initial and final positions.

Three separations keep this honest (all confirmed against code):

  * **Distinct from version-supersedes (§4A C3).** Claim-`supersede` is warrant-bearing reasoning;
    note-`supersedes(v1,v2)` is a file edit (`core/stores/versions.py`). Different relations,
    different stores — never the same rel-type, never the balance-fed `EdgeStore`.
  * **The conclusion is INTERPRETED and grounds on the WARRANT'S anchors (Item 9).** C′ is minted
    via `DerivedStore.add`, carrying `INTERPRETED` provenance (I5) and a derivation depth, so
    `core.recursion` bounds its confidence by γ^d (I10): a dialogue conclusion can never out-rank
    the authored claim it revised without an owner verdict (I1). Its `derived_from` is the warrant's
    K₀ anchors (surviving grounding of C + the dialogue's new evidence). Grounding a revision on a
    *derived* `[C]` is refused — it cites what it discredits and, because the grounding ratio is
    transitive, collapses `g` when C is superseded and builds the cross-stratum tower (§4.2).
    Grounding on an *authored* `[C]` is legitimate: bedrock does not decay, so g=1 and the
    revision is not weightless. The `C→C′` relation is carried by the
    dispositional `ClaimOpStore` edge alone, not a grounding fiber; the γ^{d≥1} "can't out-rank
    authored" guarantee comes from depth ≥ 1.
  * **Budgets floored (PD4).** The recursive-strata I5 population / edge budgets are parked;
    with none enforced these ops are recorded flatly and the Dreamer does not yet consume them
    recursively — exactly the non-recursive floor, recovering current behavior. The hook is named
    here, enforced when recursive-strata unparks.

The dialogue → operations EXTRACTION is a model task (an LLM reads the dialogue and proposes the
operations); it is an injected `DialogueAnalyzer` seam with a deterministic default of NO operations
(document-only ingest, unchanged). This module is the deterministic, INNER core: the pure operation
vocabulary (the op types + the content-id scheme). **bp-089 (S1′):** the sqlite-backed
`ClaimOpStore` and the `DerivedStore`-consuming `apply_operations`/`stale_closure` relocated one
ring outward to `core/stores/claim_ops.py` (inner-ring promotion) — this module now holds no
`sqlite3`, no store, and no `DerivedStore` import; it takes data / injected handles, it does not
acquire them. Zone A, no network.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

DIALOGUE_CONCLUSION = "dialogue_conclusion"   # the DerivedStore artifact kind a Supersede mints


class OpKind(StrEnum):
    SUPERSEDE = "supersede"
    ATTACH_DEFEATER = "attach_defeater"
    RECORD_WARRANT = "record_warrant"


@dataclass(frozen=True)
class Supersede:
    """The dialogue concluded `conclusion`, which replaces `claim` in the active projection; the
    warrant is why. `claim` is an existing claim id (a note digest or an artifact id); `conclusion`
    is the new position's text, minted as a DERIVED interpreted claim on apply (never an authored
    peer).

    `anchors` are the warrant's K₀-reaching authored digests — the grounding `C′` actually rests on
    (Item 9; supersession-lifecycle.md §4.2). A `DialogueAnalyzer` supplies them (surviving
    grounding of C + the dialogue's new evidence). Left empty, apply falls back by C's type: a
    DERIVED C inherits its surviving authored leaves (`leaf_refs`, **never `[C]`** — a derived claim
    decays or is superseded without a verdict, so routing grounding through it is unsafe); an
    AUTHORED (K₀) C grounds on `[C]` itself (bedrock — authored content does not decay, so g=1 and
    the revision is not weightless). The discredited claim is refused as grounding *only* when
    derived."""

    claim: str
    conclusion: str
    warrant: str
    anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class AttachDefeater:
    """`claim` is contested by `defeater`; the claim stays but is marked (not silently dropped)."""

    claim: str
    defeater: str


@dataclass(frozen=True)
class RecordWarrant:
    """The `warrant` links the claims in `links` (typically the initial and final claim)."""

    warrant: str
    links: tuple[str, ...]


DialogueOp = Supersede | AttachDefeater | RecordWarrant


class DialogueAnalyzer(Protocol):
    """Turns a dialogue's text into operations — a MODEL task. Injected; the default emits none."""

    def analyze(self, text: str) -> list[DialogueOp]: ...


def no_op_analyzer(_text: str) -> list[DialogueOp]:
    """The deterministic default (build plan PD4 floor): a dialogue emits NO operations → the
    existing document-only ingest, byte-for-byte unchanged. A real deployment injects a model-backed
    analyzer that proposes operations for owner/verdict review."""
    return []


# --- the claim-operations vocabulary + content-id scheme (the sqlite `ClaimOpStore` and the
#     DerivedStore-consuming `apply_operations`/`stale_closure` live in `core/stores/claim_ops.py`,
#     one ring out — bp-089, S1′). `_op_id`/`_utcnow` stay here as the pure id/timestamp scheme
#     the store keys on (finding-0144's inner-vocabulary split). ------------------------------

def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _op_id(kind: str, claim_id: str, related_id: str, text: str) -> str:
    return hashlib.sha256("\x00".join([kind, claim_id, related_id, text]).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class ClaimOp:
    op_id: str
    kind: OpKind
    claim_id: str
    related_id: str
    text: str
    at: str


@dataclass(frozen=True)
class ApplyReport:
    superseded: tuple[str, ...]     # claim ids superseded this batch
    conclusions: tuple[str, ...]    # the DERIVED conclusion artifact ids minted (γ^d applies)
    defeaters: int
    warrants: int
    stale: tuple[str, ...] = ()     # grounding-descendants of the superseded claims (Stale(C), §5)
                                    # — FLAGGED for re-examination, never cascade-retracted
