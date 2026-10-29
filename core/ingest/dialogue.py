"""Capture owner↔Ambassador dialogue into the corpus as `authored-dialogue` (Track B).

Chatting with the Ambassador is itself a form of feeding the system — "your words to it are
more yours than its words to you" (nervous-system-and-ambassador.md §4). So the owner's
messages are captured as a distinct provenance, `AUTHORED_DIALOGUE`, which IS mirror-readable
(it is the owner's own writing) — closing the capture loop.

It rides the SAME deterministic path as vault ingest — `ingest_note` (now provenance-parametric)
→ `index_records` → `VaultCatalog.record` — never a bespoke writer (the §1 split is exactly what
makes this one-line provenance swap possible). Raw is sacred: the message bytes are stored
content-addressed; identical text dedups. The attestor (optional) stamps a `capture` action so
the dialogue leaf is part of the same attestation chain as authored notes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_records
from core.kernel.config import Config
from core.kernel.ingest.logseq import ParsedNote
from core.kernel.ingest.pipeline import ingest_note
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import VectorStore


def _compact_ts() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass
class DialogueCapture:
    raw: RawStore
    store: VectorStore
    embedder: Embedder
    catalog: VaultCatalog
    attestor: Attestor | None = None

    def capture(self, text: str, *, conversation: str = "default") -> str:
        """Store one owner message as `authored-dialogue`; return its content digest.

        Idempotent on content: identical text is one raw object + one set of vectors (delete-
        then-index, the store's own re-index idiom); each call still records a distinct catalog
        entry keyed by timestamp so the conversation's turns are individually tracked."""
        data = text.encode("utf-8")
        short = hashlib.sha256(data).hexdigest()[:8]
        ts = _compact_ts()
        source_path = f"dialogue/{conversation}/{ts}-{short}"
        title = f"dialogue/{conversation}/{ts}"
        parsed = ParsedNote(
            source_path=source_path, title=title, text=text,
            tags=frozenset({"dialogue", conversation}), links=frozenset(),
            properties={}, raw_bytes=data,
        )
        record = ingest_note(parsed, self.raw, provenance=Provenance.AUTHORED_DIALOGUE)
        self.store.delete(digest=record.digest)          # idempotent re-index
        index_records([record], self.embedder, self.store)
        self.catalog.record(source_path, record.digest, title,
                            provenance=Provenance.AUTHORED_DIALOGUE)
        if self.attestor is not None:
            self.attestor.emit(agent_role="ambassador", action="capture",
                               input_hashes=[record.digest], output_hashes=[record.digest])
        return record.digest


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
        title = f"dialogue/{conversation}/{at or _compact_ts()} ({role})"
        parsed = ParsedNote(
            source_path=source_path, title=title, text=text,
            tags=frozenset({"dialogue", role}), links=frozenset(), properties={}, raw_bytes=data,
        )
        record = ingest_note(parsed, self.raw, provenance=provenance)
        self.store.delete(digest=record.digest)
        index_records([record], self.embedder, self.store)
        self.catalog.record(source_path, record.digest, title, provenance=provenance)
        if self.attestor is not None:
            self.attestor.emit(agent_role="ambassador", action="capture",
                               input_hashes=[record.digest], output_hashes=[record.digest])
        return record.digest, True


def build_dialogue_capture(config: Config | None = None) -> DialogueCapture:
    """Wire a DialogueCapture against the configured stores + embedder."""
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config

    cfg = config or get_config()
    return DialogueCapture(
        raw=RawStore(cfg.paths.raw_store),
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        embedder=build_embedder(cfg),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        attestor=build_attestor(cfg),
    )
