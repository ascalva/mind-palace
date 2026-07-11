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
(document-only ingest, unchanged). This module is the deterministic core: the types, the store, and
`apply_operations` (record + re-project). Zone A, no network.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from config.loader import Config
from core.stores.derived import DerivedStore

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


# --- the claim-operations store (distinct from Edge/Version stores — §4A C3) ---------------------

def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _op_id(kind: str, claim_id: str, related_id: str, text: str) -> str:
    return hashlib.sha256("\x00".join([kind, claim_id, related_id, text]).encode()).hexdigest()[:16]


_DDL = """
CREATE TABLE IF NOT EXISTS claim_ops (
    op_id      TEXT PRIMARY KEY,               -- content id (idempotent re-application)
    kind       TEXT NOT NULL,                  -- supersede | attach_defeater | record_warrant
    claim_id   TEXT NOT NULL,                  -- the primary claim the op acts on
    related_id TEXT NOT NULL DEFAULT '',       -- superseding conclusion's artifact id (supersede)
    text       TEXT NOT NULL,                  -- warrant (supersede/warrant) or defeater text
    at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS claim_ops_claim ON claim_ops(claim_id, kind);
"""


@dataclass(frozen=True)
class ClaimOp:
    op_id: str
    kind: OpKind
    claim_id: str
    related_id: str
    text: str
    at: str


@dataclass
class ClaimOpStore:
    """Append-only store of dialogue operations over claims. A DISTINCT structure from the version
    store and the balance-fed edge store (§4A C3): claim-supersede is warrant-bearing reasoning, not
    a note edit and not a semantic ± edge, so it shares no rel-type or store with either."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def record(self, kind: OpKind, claim_id: str, *,
               related_id: str = "", text: str = "") -> ClaimOp:
        op = ClaimOp(op_id=_op_id(kind.value, claim_id, related_id, text), kind=OpKind(kind),
                     claim_id=claim_id, related_id=related_id, text=text, at=_utcnow())
        self._conn.execute("INSERT OR REPLACE INTO claim_ops VALUES (?, ?, ?, ?, ?, ?)",
                           [op.op_id, op.kind.value, op.claim_id, op.related_id, op.text, op.at])
        self._conn.commit()
        return op

    def superseded(self) -> set[str]:
        """Claim ids with a SUPERSEDE op — the active-projection filter (a consumer excludes these,
        exactly as `DispositionStore.retracted` does for verdicts; the superseded claim lives on in
        history)."""
        return {r["claim_id"] for r in self._conn.execute(
            "SELECT claim_id FROM claim_ops WHERE kind = ?", [OpKind.SUPERSEDE.value])}

    def defeaters(self, claim_id: str) -> list[str]:
        return [r["text"] for r in self._conn.execute(
            "SELECT text FROM claim_ops WHERE claim_id = ? AND kind = ? ORDER BY at",
            [claim_id, OpKind.ATTACH_DEFEATER.value])]

    def all(self) -> list[ClaimOp]:
        return [ClaimOp(op_id=r["op_id"], kind=OpKind(r["kind"]), claim_id=r["claim_id"],
                        related_id=r["related_id"], text=r["text"], at=r["at"])
                for r in self._conn.execute("SELECT * FROM claim_ops ORDER BY at, op_id")]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM claim_ops").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._conn.close()


@dataclass(frozen=True)
class ApplyReport:
    superseded: tuple[str, ...]     # claim ids superseded this batch
    conclusions: tuple[str, ...]    # the DERIVED conclusion artifact ids minted (γ^d applies)
    defeaters: int
    warrants: int
    stale: tuple[str, ...] = ()     # grounding-descendants of the superseded claims (Stale(C), §5)
                                    # — FLAGGED for re-examination, never cascade-retracted


def stale_closure(derived: DerivedStore, claim: str) -> set[str]:
    """`Stale(C) = { x : C is reachable from x along grounding fibers }` — C's grounding-descendant
    closure (supersession-lifecycle.md §5). When C is superseded, every x that transitively grounds
    on C routes its support through a dead node, so its grounding ratio `g` will fall; this names
    them at the moment of supersession — the PROACTIVE complement to the detective grounding gauge.

    These are **flagged for re-examination, not resolved**: whether a derived claim survives its
    parent's revision is a semantic judgment the Dreamer proposes later (terminating in proposals,
    never silent edits). Read-only; walks the `derived_from` DAG (`x → … → C`). Note the Item 9
    grounding correction keeps a *revision chain* from self-generating this set — C′ grounds on
    warrant anchors, not on its predecessor, so the closure holds only genuine dependents (§5)."""
    children_of: dict[str, set[str]] = {}     # parent → the artifacts that derive_from it
    for art in derived.all():
        for parent in art.derived_from:
            children_of.setdefault(parent, set()).add(art.id)
    out: set[str] = set()
    stack = [claim]
    while stack:
        for child in children_of.get(stack.pop(), ()):
            if child not in out:
                out.add(child)
                stack.append(child)
    return out


def apply_operations(ops: Iterable[DialogueOp], *, ops_store: ClaimOpStore,
                     derived: DerivedStore) -> ApplyReport:
    """Apply dialogue operations: record each as a claim relation and re-project.

    A `Supersede` mints its conclusion C′ as a DERIVED artifact grounded on the WARRANT'S K₀
    anchors (Item 9; supersession-lifecycle.md §4.2), so γ^d bounds it (I10/I5) and C leaves the
    active projection without C′ entering as an authored peer (the §2 failure avoided). Explicit
    `op.anchors` win; empty falls back by C's type — a DERIVED C inherits its `leaf_refs` (never
    `[C]`, which decays); an AUTHORED C grounds on `[C]` (bedrock, g=1, so the revision is not
    weightless). On supersession we also compute `Stale(C)` (§5) — grounding-descendants to flag for
    re-examination — surfaced in the report for the digest; nothing is cascade-retracted. Budgets
    floored (PD4)."""
    superseded: list[str] = []
    conclusions: list[str] = []
    defeaters = warrants = 0
    for op in ops:
        if isinstance(op, Supersede):
            # Item 9: ground C′ on the warrant's K₀ anchors. Explicit anchors always win; else the
            # fallback depends on whether C is authored or derived, because the [C] prohibition only
            # targets grounding through something that DECAYS / is superseded without a verdict:
            #   * C DERIVED → inherit its authored leaves (leaf_refs), NEVER [C]: a derived C decays
            #     / can be superseded silently, so routing g through it is self-staleness
            #     (supersession-lifecycle §4.2). An ungrounded derived C ⇒ ∅ (honestly ungrounded).
            #   * C AUTHORED (K₀) → ground on [C]: authored content is bedrock — it does not decay
            #     (I2 is derived-only) and persists, so g=1 is legitimate and C′ is not weightless.
            #     If C is later demoted by verdict, C′ lands in Stale(C) and is re-examined — not a
            #     reason to refuse grounding on it.
            if op.anchors:
                anchors: tuple[str, ...] = tuple(op.anchors)
            elif derived.is_artifact(op.claim):
                anchors = tuple(sorted(derived.leaf_refs(op.claim)))     # derived C: never [C]
            else:
                anchors = (op.claim,)                                    # authored C: bedrock, g=1
            art = derived.add(kind=DIALOGUE_CONCLUSION, summary=op.conclusion,
                              subjects=(op.claim,), derived_from=list(anchors))
            ops_store.record(OpKind.SUPERSEDE, op.claim, related_id=art.id, text=op.warrant)
            superseded.append(op.claim)
            conclusions.append(art.id)
        elif isinstance(op, AttachDefeater):
            ops_store.record(OpKind.ATTACH_DEFEATER, op.claim, text=op.defeater)
            defeaters += 1
        elif isinstance(op, RecordWarrant):
            for claim in op.links:
                ops_store.record(OpKind.RECORD_WARRANT, claim, text=op.warrant)
            warrants += 1
    # Stale(C) over every claim superseded this batch — flagged, not resolved (§5).
    stale: set[str] = set()
    for c in superseded:
        stale |= stale_closure(derived, c)
    return ApplyReport(superseded=tuple(superseded), conclusions=tuple(conclusions),
                       defeaters=defeaters, warrants=warrants, stale=tuple(sorted(stale)))


def open_claim_op_store(config: Config | None = None) -> ClaimOpStore:
    from config.loader import get_config

    cfg = config or get_config()
    return ClaimOpStore(cfg.paths.derived_store.parent / "claim_ops.sqlite")
