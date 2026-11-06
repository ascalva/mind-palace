"""The first form's turn lander (dn-ingress D7): one turn of an external chat captured under
its role, the owner's `authored-dialogue` and the model's `observed`.

No production path calls it now. The dialogue sync is the library script `sync_dialogue`, and the
Ambassador's inbox lands through `capture_inbox` (dn-ingress-language §E13), which replaced this
module's `capture`, the inbox's first-form lander. `capture_turn` stays as what the second form
is measured against: the differential oracle for `sync_dialogue` (DS-5), ING-7's falsifier for a
turn (`tests/integration/test_landing_order.py`), and the way the plane's tests land turns. It
rides the same path as vault ingest (`ingest_note` → `index_records` → `VaultCatalog.record`),
with the key last.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_records
from core.ingest.landing import attest_once
from core.kernel.ingest.logseq import ParsedNote
from core.kernel.ingest.pipeline import ingest_note
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import VectorStore


def _compact_ts() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


_DIALOGUE_CLASSES = frozenset({Provenance.AUTHORED_DIALOGUE.value, Provenance.OBSERVED.value})

@dataclass
class DialogueCapture:
    raw: RawStore
    store: VectorStore
    embedder: Embedder
    catalog: VaultCatalog
    attestor: Attestor | None = None

    def capture_turn(self, text: str, *, conversation: str, turn_id: str, role: str,
                     at: str | None = None) -> tuple[str, bool]:
        """Store one turn of an external chat (e.g. Open WebUI) idempotently; return
        `(digest, created)`. The path is deterministic — `dialogue/<conversation>/<turn_id>` — so a
        re-sync of the same turn is a no-op. Provenance is fixed by ROLE, never by the text: the
        owner's turns are `authored-dialogue` (mirror-readable, their own words); the model's are
        `observed` (recallable as context, never in the mirror or the baselines)."""
        source_path = f"dialogue/{conversation}/{turn_id}"
        data = text.encode("utf-8")
        prev = self.catalog.get(source_path)
        if prev is not None and prev.active and prev.digest == hashlib.sha256(data).hexdigest():
            return prev.digest, False
        provenance = Provenance.AUTHORED_DIALOGUE if role == "user" else Provenance.OBSERVED
        # a turn's class is fixed with its identity: an observed turn never supersedes the
        # owner's words on the same path, nor the reverse (dn-ingress D8, §9); a label outside
        # the two dialogue classes (a relabel's) is the catalog's to keep, not a refusal
        held = prev.provenance if prev is not None else ""
        if held in _DIALOGUE_CLASSES and held != str(provenance):
            raise PermissionError(f"{source_path} is {held}; a {provenance} turn never "
                                  "supersedes it")
        title = f"dialogue/{conversation}/{at or _compact_ts()} ({role})"
        parsed = ParsedNote(
            source_path=source_path, title=title, text=text,
            tags=frozenset({"dialogue", role}), links=frozenset(), properties={}, raw_bytes=data,
        )
        record = ingest_note(parsed, self.raw, provenance=provenance)
        index_records([record], self.embedder, self.store)   # idempotent: the plane reconciles
        # the landing order (dn-ingress D1, ING-7): attest, then the catalog's digest last, the
        # idempotence key the check above reads
        attest_once(self.attestor, agent_role="ambassador", action="capture", digest=record.digest)
        self.catalog.record(source_path, record.digest, title, provenance=provenance)   # the key
        return record.digest, True
