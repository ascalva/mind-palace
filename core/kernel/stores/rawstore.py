"""Content-addressed immutable raw store (BUILD-SPEC §8: "raw is sacred").

Every ingested input is stored verbatim under the SHA-256 of its bytes. The hash is the
identity: identical content stores once (dedup for free), and an object is never
rewritten or summarized away — derived representations (embeddings, summaries, links) are
regenerated from here if a model or strategy changes. This verbatim original is the
source of truth the frozen anchors protect.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawStore:
    root: Path
    # Where a miss is looked up before it raises (dn-instance-lifecycle §6.5): the shared cache's
    # object by digest. What it returns is checked against the digest here as well, and only then
    # copied in, so the address is the whole trust decision. None: a miss raises, as it always did.
    fallback: Callable[[str], bytes | None] | None = None

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        # Shard by the first byte to keep directories small.
        return self.root / digest[:2] / digest

    def add(self, data: bytes) -> tuple[str, bool]:
        """Store bytes; return (digest, is_new). Idempotent: re-adding identical content
        is a no-op and reports is_new=False — that boolean is the dedup signal."""
        digest = hashlib.sha256(data).hexdigest()
        p = self._path(digest)
        if p.exists():
            return digest, False
        p.parent.mkdir(parents=True, exist_ok=True)
        # Write-then-rename: atomic, and never overwrites an existing immutable object.
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)
        return digest, True

    def add_text(self, text: str) -> tuple[str, bool]:
        return self.add(text.encode("utf-8"))

    def get(self, digest: str) -> bytes:
        p = self._path(digest)
        if not p.exists() and self.fallback is not None:
            data = self.fallback(digest)
            if data is not None and hashlib.sha256(data).hexdigest() == digest:
                self.add(data)
                return data
        return p.read_bytes()

    def exists(self, digest: str) -> bool:
        return self._path(digest).exists()

    def delete(self, digest: str) -> bool:
        """Remove a raw blob — the ONE deliberate exception to "raw is sacred".

        Never called by the ingest or watcher path (a vault delete only TOMBSTONES — derived
        rows dropped, raw kept). This is the owner-gated true-deletion primitive used solely by
        the purge action (core/ingest/purge.py). Returns whether a blob was actually removed."""
        p = self._path(digest)
        if p.exists():
            p.unlink()
            return True
        return False
