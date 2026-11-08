"""A palace on temporary stores for the ingress's tests: its configuration (the vault, the data
directory and the handoff directory under one root, never the live ones), the stores the writer
lands into, and what a landing leaves, for comparing two palaces."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ingest import ingress
from core.ingest.embed import Embedder
from core.ingest.readers import PalaceView
from core.ingest.table import build_table
from core.ingest.writer import Stores
from core.kernel.config import get_config
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.sentence import ast
from core.sentence.plan import compile_sentence
from core.stores.catalog import VaultCatalog
from core.stores.edges import EdgeStore
from core.stores.lexical import LexicalStore
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore
from tests.fixtures.clearances import grant
from tests.fixtures.embedding import DIM, FakeEmbedder

EVERY = grant(*Provenance)


def palace_config(root: Path, *, lazy: bool = False) -> Any:
    """The configuration of a palace under `root`: its vault and data directory are `root`'s
    (made here), its handoff directory `data/handoff` (made by whoever writes it first); `lazy`
    is `[embedding] lazy`, two-phase ingestion (dn-two-phase-ingestion)."""
    vault, data = root / "vault", root / "data"
    vault.mkdir(parents=True, exist_ok=True)
    data.mkdir(exist_ok=True)
    base = get_config()
    return replace(base,
                   ingestion=replace(base.ingestion,
                                     vault=replace(base.ingestion.vault, path=vault)),
                   paths=replace(base.paths, data_dir=data),
                   interface=replace(base.interface, handoff_dir=data / "handoff"),
                   embedding=replace(base.embedding, lazy=lazy))


@dataclass
class Palace:
    cfg: Any
    stores: Stores
    att: AttestationStore
    vault: Path
    data: Path
    jobs: list[tuple[str, dict[str, Any]]]
    root: Path

    def run(self, text: str, role: str = "cli", *, budget: int | None = None) -> dict[str, Any]:
        """A request performed as the handler performs it, its structured sources read as they
        are (no edge reader refreshes them)."""
        plan = compile_sentence(text, ingress.grant_for(role), role=role)
        assert isinstance(plan.term, ast.Do)
        view = PalaceView(build_table(self.cfg), role, self.stores.catalog, refresh=False)
        return ingress.perform(plan.term, self.cfg, role, stores=self.stores, view=view,
                            budget=budget)

    def outcomes(self, text: str, role: str = "cli") -> list[dict[str, Any]]:
        return self.run(text, role)["changed"]


def palace_at(tmp_path: Path, name: str = "p", *, lazy: bool = False,
              lexical: bool | None = None) -> Palace:
    """A palace on temporary stores. `lazy` lands items without their vectors (the embed drain
    derives them); `lexical` opens the lexical index (by default exactly when `lazy`)."""
    root = tmp_path / name
    cfg = palace_config(root, lazy=lazy)
    att = AttestationStore(root / "att.sqlite")
    jobs: list[tuple[str, dict[str, Any]]] = []

    def enqueue(kind: str, payload: dict[str, Any], *, role: str,
                request: str | None = None) -> int:
        jobs.append((kind, payload))
        return len(jobs)

    stores = Stores(raw=RawStore(root / "raw"), plane=VectorStore(root / "vectors", dim=DIM),
                    embedder=cast(Embedder, FakeEmbedder()),
                    catalog=VaultCatalog(root / "catalog.sqlite"),
                    versions=VersionStore(root / "versions.sqlite"),
                    attestor=StoreAttestor(att), edges=EdgeStore(root / "edges.sqlite"),
                    enqueue=enqueue,
                    lexical=(LexicalStore(root / "lexical.sqlite")
                             if (lazy if lexical is None else lexical) else None))
    return Palace(cfg, stores, att, root / "vault", root / "data", jobs, root)


def state_of(p: Palace) -> dict[str, Any]:
    """What a landing leaves, its paths relative to the palace's root, without times or agents."""
    def rel(path: str) -> str:
        return path.replace(str(p.root), "<root>")
    cat = sorted((rel(e.source_path), e.digest, e.title, str(e.provenance), e.active,
                  rel(p.stores.catalog.doc_id_for(e.source_path)))
                 for e in p.stores.catalog.active_entries())
    rows = sorted((rel(str(r["source_path"])), str(r["digest"]), str(r["provenance"]),
                   str(r["text"])) for r in p.stores.plane.all_rows(clearance=EVERY))
    assert p.stores.versions is not None
    versions = sorted((rel(d), tuple(v.digest for v in p.stores.versions.history(d)))
                      for d in {p.stores.catalog.doc_id_for(e.source_path)
                                for e in p.stores.catalog.active_entries()})
    atts = sorted((a.action, tuple(a.output_hashes)) for a in p.att.all())
    return {"catalog": cat, "rows": rows, "versions": versions, "attestations": atts}


def write_file(vault: Path, name: str, text: str) -> Path:
    path = vault / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
