"""Every store an instance writes, in exactly one class (dn-instance-lifecycle §3).

One table, the same for every instance, says what each store under an instance's data directory
is and so what a reset does to it:

* **ledger**: a source of truth: the raw objects, the catalog with its landing log, the version
  chains, the attestations, the chat sensor's retention ledger, the commit ledger, the observation
  history, the reference edges, the query log, the run and self-modification ledgers, the effects.
  Kept. The landing log (`LANDING_LOG`, dn-temporal-snapshot §3.2) is two tables in the catalog's
  own file, so the catalog's entry is kept whole, the log with it.
* **declaration**: what the owner declared and no code computes: the authored supersessions and
  the signed verdicts. Kept.
* **derived**: a function of the ledgers, computed again without a model: cleared by a reset and
  rebuilt, in the order of `step`, each step reading only ledgers and the steps before it.
* **kept**: model output, and what else no rebuild computes again exactly: the interpreted
  artifacts, the dream claims, the claim operations, the staged hypotheses, the structural
  snapshots, the curated store, the measurements, and the code lane's membership store, which
  holds the code atoms' embedder ledger beside their occupancy. Kept.
* **operational**: the queue, the locks, the spools and their marks, the logs, the backups and
  the HashiCorp Vault storage. Kept: not content.

`reset_targets` and `_RESET_GUARD` were two lists that disagreed with the chat sensor's design;
this table replaces both. A store opened under the data directory that the table does not name
fails the inventory's test (falsifier LCF-1).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

#: The landing log's tables, a ledger inside the catalog's file (`core/stores/landings.py`): the
#: append-only, hash-chained history of which digest each path held when, whose fold is the
#: catalog's rows. They share the catalog's entry below, so a reset keeps them as it keeps the file.
LANDING_LOG = ("landing_chains", "landings")

#: Written before a reset clears anything, removed when its last rebuild step has run. While it is
#: there the daemon's start and every command that lands or writes a derived store refuse (each
#: reads it when it starts, through `refusal`), so nothing starts to land into a half-rebuilt
#: instance; it names the derived stores the reset found, so a reset run again after an
#: interruption rebuilds every one of them, a store whose file it had already removed included.
RESET_MARKER = "reset.pending"


class Kind(StrEnum):
    LEDGER = "ledger"
    DECLARATION = "declaration"
    DERIVED = "derived"
    KEPT = "kept"
    OPERATIONAL = "operational"


@dataclass(frozen=True)
class Store:
    """One entry of the data directory: its name there, its class, where it is under a given
    configuration, and for a derived store its rebuild step and how a reset clears it."""

    name: str
    kind: Kind
    where: Callable[[Any], Path]
    step: int = 0                 # the rebuild's order, for a derived store
    clear: str = "file"           # "file", "relations" (the plane), "index" (lexical), "rows"
    note: str = ""

    def path(self, cfg: Any) -> Path:
        return Path(self.where(cfg))


def _data(name: str) -> Callable[[Any], Path]:
    return lambda cfg: Path(cfg.paths.data_dir) / name


def _paths(attr: str) -> Callable[[Any], Path]:
    return lambda cfg: Path(getattr(cfg.paths, attr))


def _sibling(name: str) -> Callable[[Any], Path]:
    """A store opened beside the interpreted artifacts (`derived_store.parent / name`)."""
    return lambda cfg: Path(cfg.paths.derived_store).parent / name


L, D, X, K, OP = Kind.LEDGER, Kind.DECLARATION, Kind.DERIVED, Kind.KEPT, Kind.OPERATIONAL

STORES: tuple[Store, ...] = (
    # ── ledgers ──────────────────────────────────────────────────────────────────────────────
    Store("raw", L, _paths("raw_store"), note="the verbatim bytes; a purge is its one deletion"),
    Store("vault_catalog.sqlite", L, _paths("vault_catalog"),
          note="path to digest, title, class, identity, and the landing log, its past"),
    Store("versions.sqlite", L, _data("versions.sqlite"), note="mirror_authored's chains"),
    Store("attestations.sqlite", L, _paths("attestation_store"), note="append-only"),
    Store("chat_retention.sqlite", L, _data("chat_retention.sqlite"),
          note="which raw objects are transcripts, in retention order"),
    Store("code_snapshots.sqlite", L, _data("code_snapshots.sqlite"), note="the commit ledger"),
    Store("observation_history.sqlite", L, _data("observation_history.sqlite"),
          note="superseded generations, whose interpreters no longer exist"),
    Store("reference_edges.sqlite", L, _data("reference_edges.sqlite"),
          note="append-only, no extractor version on its rows (decision D3)"),
    Store("query_log.jsonl", L, _data("query_log.jsonl"), note="what was asked"),
    Store("runs.sqlite", L, _data("runs.sqlite"), note="the system's runs"),
    Store("selfmod_ledger.sqlite", L, lambda cfg: Path(cfg.selfmod.ledger_db)),
    Store("effectors", L, lambda cfg: Path(cfg.effectors.ledger_db).parent,
          note="the effects ledger and the drafts it stages"),
    # ── the owner's declarations ─────────────────────────────────────────────────────────────
    Store("authored_supersessions.sqlite", D, _sibling("authored_supersessions.sqlite")),
    Store("verdicts.sqlite", D, _sibling("verdicts.sqlite"), note="owner-signed, verified"),
    # ── derived: cleared and rebuilt, in this order ──────────────────────────────────────────
    Store("lexical.sqlite", X, _data("lexical.sqlite"), step=1, clear="index",
          note="catalog, raw"),
    Store("vectors.lance", X, _paths("vector_store"), step=2, clear="relations",
          note="the plane's occupancies and supersession log; the atoms are kept as a memo"),
    Store("code_observations.sqlite", X, _data("code_observations.sqlite"), step=3,
          note="commit ledger, by re-projection without the attestor"),
    Store("agent_observations.sqlite", X, _data("agent_observations.sqlite"), step=4,
          note="git's first-parent history of the build plans, without the attestor"),
    Store("edges.sqlite", X, _sibling("edges.sqlite"), step=6, clear="rows",
          note="the authored rows only; the interpreted rows are model output and stay"),
    Store("chatlog.sqlite", X, _data("chatlog.sqlite"), step=7, note="retention ledger, raw"),
    Store("chat_events.sqlite", X, _data("chat_events.sqlite"), step=8, note="chat log, raw"),
    Store("causal_edges.sqlite", X, _data("causal_edges.sqlite"), step=9,
          note="chat events, commit ledger (decision D6: a fresh integration)"),
    Store("verdict_dispositions.sqlite", X, _sibling("verdict_dispositions.sqlite"), step=10,
          note="verdicts, applied in sequence order"),
    # ── kept: model output and what no rebuild computes again exactly ────────────────────────
    Store("derived.sqlite", K, _paths("derived_store"), note="interpreted artifacts (D4)"),
    Store("memberships.sqlite", K, _sibling("memberships.sqlite"),
          note="the code atoms' embedder ledger with their occupancy; rebuilt by code-rebuild"),
    Store("run_ledger.sqlite", K, _sibling("run_ledger.sqlite")),
    Store("dream_runs.sqlite", K, _sibling("dream_runs.sqlite")),
    Store("claim_ops.sqlite", K, _sibling("claim_ops.sqlite")),
    Store("staging.sqlite", K, _sibling("staging.sqlite")),
    Store("structural.duckdb", K, _sibling("structural.duckdb")),
    Store("research_curated.lance", K, _paths("curated_store"), note="decision D5"),
    Store("eval_results.duckdb", K, _sibling("eval_results.duckdb")),
    Store("probes.sqlite", K, _sibling("probes.sqlite")),
    Store("lexical", K, _data("lexical"), note="the corpus's measurement outputs"),
    Store("edges", K, _data("edges"), note="the corpus's measurement outputs"),
    Store("codes", K, _data("codes"), note="the corpus's measurement outputs"),
    # ── operational: kept, not content ───────────────────────────────────────────────────────
    Store("queue.sqlite", OP, _data("queue.sqlite"), note="decision D7: kept"),
    Store("tasks.sqlite", OP, _data("tasks.sqlite")),
    Store("telemetry.duckdb", OP, _paths("telemetry_db")),
    Store("supervisor.lock", OP, _data("supervisor.lock")),
    Store(RESET_MARKER, OP, _data(RESET_MARKER)),
    Store("handoff", OP, lambda cfg: Path(cfg.interface.handoff_dir)),
    Store("airlock", OP, lambda cfg: Path(cfg.airlock.handoff_dir)),
    Store("code", OP, _data("code"), note="the repository sources' marks"),
    Store("code_sensing_handoff", OP, _data("code_sensing_handoff")),
    Store("agent_sensing_handoff", OP, _data("agent_sensing_handoff")),
    Store("corpus", OP, lambda cfg: Path(cfg.ingestion.corpus.root),
          note="the corpus sources' streams and cursors"),
    Store("logs", OP, _data("logs")),
    Store("backup-staging", OP, _data("backup-staging")),
    Store("mint_ids_backup", OP, _data("mint_ids_backup")),
    Store("reembed_bodyonly_backup", OP, _data("reembed_bodyonly_backup")),
    Store("vault", OP, _data("vault"), note="the HashiCorp Vault storage"),
)


def derived() -> list[Store]:
    """The derived stores, in rebuild order."""
    return sorted((s for s in STORES if s.kind is Kind.DERIVED), key=lambda s: s.step)


def classify(cfg: Any, path: Path) -> Store | None:
    """The table's entry for `path`: the store it is, or lies inside, or is a SQLite sidecar of
    (`-wal`, `-shm`, `-journal`); None when the table names nothing there."""
    p = Path(path)
    for suffix in ("-wal", "-shm", "-journal"):
        if p.name.endswith(suffix):
            p = p.with_name(p.name[: -len(suffix)])
    found: Store | None = None
    for s in STORES:
        where = s.path(cfg)
        if p == where or where in p.parents:
            # the innermost entry wins (`effectors` holds its ledger and its drafts)
            if found is None or len(where.parts) > len(found.path(cfg).parts):
                found = s
    return found


def unclassified(cfg: Any) -> list[Path]:
    """Every entry directly under the data directory the table does not name (LCF-1)."""
    data = Path(cfg.paths.data_dir)
    if not data.is_dir():
        return []
    return sorted(p for p in data.iterdir() if classify(cfg, p) is None)


def read_only(path: Path) -> sqlite3.Connection:
    """A read of a SQLite store that creates and touches no file when the store is at rest. A
    database at rest has every committed page in its main file: it has no `-wal` file, or an empty
    one a reader left behind (a `mode=ro` reader cannot remove the files it made), and no
    `-journal`. It is read `immutable=1`, since a `mode=ro` connection to a WAL database creates its
    `-wal` and `-shm` files, and rewrites a `-shm` already there. A database whose `-wal` holds
    frames, or that has a `-journal`, may hold committed pages outside its main file, which
    `immutable=1` would not see, so it is read `mode=ro`, beside the files already there, and that
    read updates its `-shm`."""
    wal, journal = Path(f"{path}-wal"), Path(f"{path}-journal")
    pending = journal.exists() or (wal.exists() and wal.stat().st_size > 0)
    query = "mode=ro" if pending else "immutable=1"
    return sqlite3.connect(f"file:{path}?{query}", uri=True)


def marker(cfg: Any) -> Path:
    return Path(cfg.paths.data_dir) / RESET_MARKER


def reset_pending(cfg: Any) -> dict[str, Any] | None:
    """The interrupted reset's record, or None when no reset is pending."""
    m = marker(cfg)
    if not m.exists():
        return None
    try:
        return dict(json.loads(m.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        return {"stores": [s.name for s in derived()]}


def refusal(cfg: Any, what: str) -> str | None:
    """The line a writer prints when it refuses because a reset is pending, else None."""
    if reset_pending(cfg) is None:
        return None
    return (f"refusing {what} — a reset of this instance is pending ({marker(cfg)}): its derived "
            "stores are being rebuilt. Run `palace reset --confirm` again to finish it.")
