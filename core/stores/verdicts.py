# ── Family 1 boundary (labelings & information-flow) · the inbound verdict channel ──
# OBJECT:    the append-only signed verdict store — owner authorizations persisted under a
#            monotonic sequence (design-notes/verdict-authority.md §3–§4; build plan Item 4b).
# INVARIANT: append-only (no update/delete); every stored verdict carries a VERIFIED owner
#            Ed25519 signature; seq is strictly increasing, so a replay/reorder is refused and a
#            DROP is a detectable gap (censorship visible, never forgeable).
# ENFORCED:  structural — the class exposes only append + reads; append verifies the signature and
#            the strict-increase BEFORE insert (fail closed); no mutation API exists.
"""Append-only signed verdict store (design-notes/verdict-authority.md; live-adoption §3, L2).

Persists owner verdicts as the labeled ground truth the longitudinal apparatus is missing, with
the sacred-boundary upgrade the plain L2 `claim_verdicts` schema lacked: each row carries the
owner's Ed25519 signature (VERIFIED before it is stored) and a monotonic sequence number. A
compromised transport (a tampered Ambassador) can DROP or REORDER — both refused or made visible
here — but can never FORGE a verdict, because the store holds only the owner PUBLIC key
(verdict-authority.md §4: the Ambassador degrades to transport).

APPEND-ONLY IS STRUCTURAL, like the attestation store (`core/attestation/store.py`): this class
exposes `append` + reads and NO update/delete. Corrections are new verdicts at a higher seq
(supersession by sequence), never in-place edits — the same discipline the ingestion boundary
uses. Verdicts are operational ground truth, NOT mirror content (they label interpreted-tier
output; they never enter `MIRROR_READABLE`). Zone A, no network.

The APPLY half — what `promote` / `supersede` DO to the graph — is deliberately NOT here: it
depends on the promotion mechanism (recursive-strata I1), which is parked. This store is the
buildable, lower-blast-radius half of Item 4b; apply lands when the promotion mechanism does.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config
from core.verdict.payload import SignedVerdict, VerdictPayload

_DDL = """
CREATE TABLE IF NOT EXISTS verdicts (
    seq          INTEGER PRIMARY KEY,   -- monotonic sequence number (ordering + gap detection)
    subject_id   TEXT NOT NULL,         -- the insight/cluster the verdict applies to
    verdict      TEXT NOT NULL,         -- category; ratified taxonomy, checked on append
    timestamp    TEXT NOT NULL,         -- ISO-8601, from the signed payload
    signature    TEXT NOT NULL,         -- base64 Ed25519 over the canonical payload
    signer       TEXT NOT NULL,         -- "owner"
    recorded_at  TEXT NOT NULL          -- when the store appended it (audit; unsigned)
);
"""


class VerdictSignatureError(ValueError):
    """A verdict was offered whose signature did not verify under the owner public key — the
    illegal state the boundary deletes (fail closed): an unsigned or forged verdict is never
    stored, so no compromised transport can inject an owner authorization."""


class VerdictSequenceError(ValueError):
    """A verdict's seq did not strictly exceed the stored maximum — a replay, a reorder, or a
    reused number. Refused so the sequence is monotone; a genuine DROP shows up as a forward gap
    (detectable via `gaps()`), never as a silently-accepted lower number."""


class VerdictCategoryError(ValueError):
    """A verdict category outside the configured ratified taxonomy (when one is set). Absent a
    ratified set (`allowed_verdicts=None`) any category is accepted — the taxonomy is an owner
    decision (build plan R3), and this store must not hard-code it."""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class VerdictRecord:
    """One stored, signature-verified owner verdict."""

    seq: int
    subject_id: str
    verdict: str
    timestamp: str
    signature: str
    signer: str
    recorded_at: str

    def as_signed(self) -> SignedVerdict:
        """Reconstruct the `SignedVerdict` for re-verification (tamper-evidence over the store)."""
        return SignedVerdict(
            payload=VerdictPayload(subject_id=self.subject_id, verdict=self.verdict,
                                   seq=self.seq, timestamp=self.timestamp),
            signature=self.signature, signer=self.signer,
        )


@dataclass
class VerdictStore:
    path: Path
    # The ratified verdict taxonomy, if the owner has decided one (build plan R3). None = accept any
    # category (the honest default until ratification — never a hard-coded set).
    allowed_verdicts: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_DDL)
            self._conn.commit()

    def append(self, signed: SignedVerdict, *, public_b64: str) -> VerdictRecord:
        """Verify + persist one owner verdict. Fail closed, in order:

          1. category ∈ the ratified taxonomy (when configured), else `VerdictCategoryError`;
          2. the signature verifies under `public_b64`, else `VerdictSignatureError`;
          3. seq strictly exceeds the stored maximum, else `VerdictSequenceError`.

        Only if all three hold is the row appended. The whole check+insert is under the lock, so a
        concurrent append cannot race the monotonic-seq guard."""
        p = signed.payload
        if self.allowed_verdicts is not None and p.verdict not in self.allowed_verdicts:
            raise VerdictCategoryError(
                f"verdict category {p.verdict!r} not in the ratified taxonomy "
                f"{sorted(self.allowed_verdicts)!r}"
            )
        if not signed.verify(public_b64):
            raise VerdictSignatureError(
                f"verdict seq={p.seq} subject={p.subject_id!r} failed signature verification — "
                "refused (an unsigned or forged verdict is never stored)"
            )
        with self._lock:
            latest = self._latest_seq_locked()
            if latest is not None and p.seq <= latest:
                raise VerdictSequenceError(
                    f"verdict seq={p.seq} does not exceed the stored maximum {latest} — "
                    "replay/reorder refused (a real drop is a forward gap, see gaps())"
                )
            rec = VerdictRecord(seq=p.seq, subject_id=p.subject_id, verdict=p.verdict,
                                timestamp=p.timestamp, signature=signed.signature,
                                signer=signed.signer, recorded_at=_utcnow())
            self._conn.execute(
                "INSERT INTO verdicts VALUES (?, ?, ?, ?, ?, ?, ?)",
                [rec.seq, rec.subject_id, rec.verdict, rec.timestamp, rec.signature,
                 rec.signer, rec.recorded_at],
            )
            self._conn.commit()
            return rec

    def _latest_seq_locked(self) -> int | None:
        row = self._conn.execute("SELECT max(seq) AS m FROM verdicts").fetchone()
        return row["m"] if row and row["m"] is not None else None

    def latest_seq(self) -> int | None:
        """The highest stored seq, or None if empty — what the next verdict must exceed."""
        with self._lock:
            return self._latest_seq_locked()

    def all(self) -> list[VerdictRecord]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM verdicts ORDER BY seq").fetchall()
        return [_row(r) for r in rows]

    def get(self, seq: int) -> VerdictRecord | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM verdicts WHERE seq = ?", [seq]).fetchone()
        return _row(row) if row else None

    def gaps(self) -> list[int]:
        """The missing sequence numbers between the smallest and largest stored seq — the
        censorship signal (verdict-authority.md §4: a dropped verdict is a visible gap). Empty
        when the stored sequence is contiguous."""
        with self._lock:
            rows = self._conn.execute("SELECT seq FROM verdicts ORDER BY seq").fetchall()
        seqs = [r["seq"] for r in rows]
        if not seqs:
            return []
        present = set(seqs)
        return [n for n in range(seqs[0], seqs[-1] + 1) if n not in present]

    def verify_all(self, public_b64: str) -> bool:
        """Re-verify every stored verdict's signature under `public_b64` — tamper-evidence over
        the store as a whole (a mutated row fails). True iff all rows verify (or the store is
        empty)."""
        return all(r.as_signed().verify(public_b64) for r in self.all())

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT count(*) FROM verdicts").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def _row(r: sqlite3.Row) -> VerdictRecord:
    return VerdictRecord(
        seq=r["seq"], subject_id=r["subject_id"], verdict=r["verdict"], timestamp=r["timestamp"],
        signature=r["signature"], signer=r["signer"], recorded_at=r["recorded_at"],
    )


def open_verdict_store(config: Config | None = None,
                       allowed_verdicts: Iterable[str] | None = None) -> VerdictStore:
    """Wire a VerdictStore beside the other core stores. `allowed_verdicts` is the ratified
    taxonomy once the owner decides it (build plan R3); None keeps the honest accept-any default."""
    from config.loader import get_config

    cfg = config or get_config()
    path = cfg.paths.derived_store.parent / "verdicts.sqlite"
    return VerdictStore(path, allowed_verdicts=frozenset(allowed_verdicts) if allowed_verdicts
                        else None)
