"""The claim-operations persistence — `ClaimOpStore` + `apply_operations` (bp-089, S1′).

The inner-ring promotion (dn-inner-outer-core §2.6b) moves the sqlite-backed `ClaimOpStore` and the
`DerivedStore`-consuming application logic (`apply_operations`, `stale_closure`) OFF
`core/recursion_ops.py` — so that module keeps only the pure dialogue-operations vocabulary and
becomes inner. Item 3's DRY audit (finding-0144) confirmed NO existing `core/stores/*` covers
`claim_ops`: `authored_supersession` is a distinct owner-declared K₀↔K₀ edge type; `versions` is
note-version supersession. A new store is genuinely needed — this one.

Claim-`supersede` is a DISTINCT relation in a DISTINCT store from version-`supersedes` (§4A C3):
warrant-bearing reasoning, never a note edit and never a semantic ± edge. Byte-identical behavior:
the store DDL, the record/query methods, and the `apply_operations`/`stale_closure` bodies are
relocated verbatim from `recursion_ops.py`; the pure vocabulary (`OpKind`, `ClaimOp`, `Supersede`,
…, `_op_id`, `_utcnow`) is imported from its inner home. Zone A: reads/writes the claim-ops sqlite +
reads/writes the `DerivedStore`; no model, no network.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from core.kernel.config import Config
from core.kernel.recursion_ops import (
    DIALOGUE_CONCLUSION,
    ApplyReport,
    AttachDefeater,
    ClaimOp,
    DialogueOp,
    OpKind,
    RecordWarrant,
    Supersede,
    _op_id,
    _utcnow,
)
from core.stores.derived import DerivedStore

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
    from core.kernel.config import get_config

    cfg = config or get_config()
    return ClaimOpStore(cfg.paths.derived_store.parent / "claim_ops.sqlite")
