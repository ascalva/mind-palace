# ── Family 1 boundary (labelings & information-flow) · the inbound verdict channel, apply half ──
# OBJECT:    the disposition ledger — what each owner verdict DID to its subject claim
#            (design-notes/verdict-authority.md; ingest-identity-and-amendment.md §6 active/hist).
# INVARIANT: append-only + latest-wins by subject; a RETRACT drops a claim from the ACTIVE
#            projection but never from history (the claim is superseded, not deleted).
# ENFORCED:  append-only (no update/delete); `retracted()` is the active-projection filter readers
#            apply. WEIGHT promotion (recursive-strata I1) is a separate, parked mechanism — absent.
"""Verdict dispositions — the buildable half of verdict 'apply' (verdict-authority.md).

A verdict labels an interpreted claim; its EFFECT is a disposition on that claim. The half that is
buildable WITHOUT the parked recursive-strata weight machinery is **supersession**: a
`wrong`/`noise` verdict RETRACTS the claim from the *active projection* — the reasoning complex and
the surfaced dreams stop showing it — while it stays in the historical log (ingest-identity §6: two
views over one log, applied to the interpreted layer). Endorsement / record are noted, for later.

Append-only, latest-wins by `subject_id`: a newer verdict supersedes an earlier disposition (the
owner may change their mind) and the full history stays queryable. WEIGHT promotion (recursive-
strata I1 — a derived node's edge weights rising) is deliberately NOT here; parked. No network.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from config.loader import Config


class VerdictEffect(StrEnum):
    """What a verdict does to its subject claim in the ACTIVE projection.

    RETRACT — drop from the active view (kept in history): a `wrong`/`noise` claim.
    ENDORSE — the owner affirmed it (a `novel_useful` claim); surfaced, but weight promotion (I1)
              stays parked, so this is a label, not yet a weight change.
    RECORD  — noted only (`true_known` / `plausible`): no change to what is shown.
    """

    RETRACT = "retract"
    ENDORSE = "endorse"
    RECORD = "record"


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Disposition:
    verdict_seq: int
    subject_id: str
    effect: VerdictEffect
    at: str


_DDL = """
CREATE TABLE IF NOT EXISTS dispositions (
    verdict_seq INTEGER PRIMARY KEY,   -- the verdict (monotonic seq) that set this disposition
    subject_id  TEXT NOT NULL,         -- the interpreted claim/artifact the verdict applied to
    effect      TEXT NOT NULL,         -- retract | endorse | record
    at          TEXT NOT NULL          -- when applied (audit)
);
CREATE INDEX IF NOT EXISTS dispositions_subject ON dispositions(subject_id, verdict_seq);
"""


@dataclass
class DispositionStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def record(self, subject_id: str, effect: VerdictEffect, verdict_seq: int) -> Disposition:
        """Append the disposition a verdict set. Keyed by `verdict_seq` (one disposition per
        verdict), so re-applying the same verdict is idempotent (INSERT OR REPLACE on the seq)."""
        d = Disposition(verdict_seq=verdict_seq, subject_id=subject_id,
                        effect=VerdictEffect(effect), at=_utcnow())
        self._conn.execute("INSERT OR REPLACE INTO dispositions VALUES (?, ?, ?, ?)",
                           [d.verdict_seq, d.subject_id, d.effect.value, d.at])
        self._conn.commit()
        return d

    def effect_for(self, subject_id: str) -> VerdictEffect | None:
        """The subject's CURRENT disposition — the effect of its highest-seq verdict (latest wins),
        or None if never verdicted."""
        row = self._conn.execute(
            "SELECT effect FROM dispositions WHERE subject_id = ? "
            "ORDER BY verdict_seq DESC LIMIT 1",
            [subject_id],
        ).fetchone()
        return VerdictEffect(row["effect"]) if row else None

    def retracted(self) -> set[str]:
        """Every subject whose CURRENT disposition is RETRACT — the active-projection filter a
        reader applies to exclude owner-superseded claims (ingest-identity §6)."""
        latest: dict[str, VerdictEffect] = {}
        for r in self._conn.execute(
            "SELECT subject_id, effect FROM dispositions ORDER BY verdict_seq"
        ).fetchall():
            latest[r["subject_id"]] = VerdictEffect(r["effect"])   # later seq overwrites
        return {s for s, e in latest.items() if e is VerdictEffect.RETRACT}

    def all(self) -> list[Disposition]:
        return [Disposition(verdict_seq=r["verdict_seq"], subject_id=r["subject_id"],
                            effect=VerdictEffect(r["effect"]), at=r["at"])
                for r in self._conn.execute(
                    "SELECT * FROM dispositions ORDER BY verdict_seq").fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM dispositions").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._conn.close()


def open_disposition_store(config: Config | None = None) -> DispositionStore:
    from config.loader import get_config

    cfg = config or get_config()
    return DispositionStore(cfg.paths.derived_store.parent / "verdict_dispositions.sqlite")
