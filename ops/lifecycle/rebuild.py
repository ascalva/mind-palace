"""A lifecycle reset: clear an instance's derived stores and rebuild them from its ledgers
(dn-instance-lifecycle §4).

The class table (`ops/lifecycle/inventory.py`) names the derived stores and their order. A reset
clears each one it finds, each by its own method (the lexical index's `reset`, the plane's
relations with its atoms kept, the authored rows of the relation edges) or by deleting its file,
then runs the rebuild steps in order, each reading only ledgers and the steps before it, and
writes no ledger: the sensors re-project without their attestor, and the reference edges a
re-projection mints again are found held. Every other store is kept as it was.

What it guarantees, and the tests check (§8): every ledger, declaration and kept store is the same
row for row, the catalog's file whole with the landing log in it (every row, every chain's head
hash); each derived store's head after the rebuild equals its head before, wall-clock bookmarks
left out (the causal edges equal a fresh integration over the same inputs); no embedder call while
the atoms are held; a second reset leaves what the first left. The version-keyed stores are rebuilt
for the current versions only (decision D2); a replay of the landing log's rows, which would give
every version landed since its genesis, is a follow-up (§3.6).

No step writes the catalog or appends to its landing log: the two steps that open it
(`OPENS_CATALOG`) read its active rows and nothing else. But its first open through `VaultCatalog`
writes the log's genesis when it holds rows and no log yet, which needs the instance's landing-log
secret. So that case is found read only before anything is cleared, and the reset refuses without
the secret (`missing_inputs`) rather than stopping after the clearing; with the secret, that
genesis is the one write a reset makes to a ledger.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ops.lifecycle.inventory import Kind, Store, derived, marker, read_only, reset_pending

#: Read before the clearing so the dry run and the refusals can say what a reset would do.
SQLITE_SIDECARS = ("-wal", "-shm", "-journal")
_ALL = 1 << 30            # "every session": the projectors' bound, set past any instance


@dataclass
class Context:
    """What the steps share: the configuration, the repository the sensors read, the embedder's
    factory (called only when an atom is missing), and the stores opened once."""

    cfg: Any
    repo: Path
    embedder_factory: Callable[[Any], Any]
    cache: Any = None
    opened: dict[str, Any] = field(default_factory=dict)
    # The plane's current occupancies before the clearing, as (path, digest, title, class): what
    # the plane step rebuilds, and nothing more (§4.2). Read once and kept in the marker, so a
    # reset run again after an interruption rebuilds what the plane held before the first run
    # cleared it. The title and class are the occupancy's own, so a held version that is no longer
    # the catalog's head (an edit a lazy instance has not yet embedded) is rebuilt as it was held.
    plane_held: list[tuple[str, str, str, str]] = field(default_factory=list)

    def raw(self) -> Any:
        if "raw" not in self.opened:
            from core.kernel.stores.rawstore import RawStore

            fallback = self.cache.raw if self.cache is not None else None
            self.opened["raw"] = RawStore(Path(self.cfg.paths.raw_store), fallback=fallback)
        return self.opened["raw"]

    def catalog(self) -> Any:
        if "catalog" not in self.opened:
            from core.stores.catalog import VaultCatalog

            self.opened["catalog"] = VaultCatalog(Path(self.cfg.paths.vault_catalog))
        return self.opened["catalog"]

    def lexical(self) -> Any:
        if "lexical" not in self.opened:
            from core.stores.lexical import LexicalStore

            path = derived_path(self.cfg, "lexical.sqlite")
            self.opened["lexical"] = LexicalStore(path) if path.exists() else None
        return self.opened["lexical"]

    def vectors(self) -> Any:
        if "vectors" not in self.opened:
            from core.stores.vectorstore import open_vector_store

            self.opened["vectors"] = open_vector_store(self.cfg)
        return self.opened["vectors"]

    def close(self) -> None:
        for name in ("lexical",):
            s = self.opened.get(name)
            if s is not None:
                s.close()


class _LazyEmbedder:
    """The embedder, built on its first call: a rebuild whose atoms are all held never builds
    one, so a reset needs no model server when it embeds nothing."""

    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._made: Any = None

    def _it(self) -> Any:
        if self._made is None:
            self._made = self._factory()
        return self._made

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return list(self._it().embed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        return list(self._it().embed_query(text))


def derived_path(cfg: Any, name: str) -> Path:
    for s in derived():
        if s.name == name:
            return s.path(cfg)
    raise KeyError(name)


def applies(cfg: Any, s: Store) -> bool:
    """Whether a derived store is this instance's to rebuild: the plane only where it embeds."""
    if s.clear == "relations":
        return bool(cfg.embedding.enabled)
    return True


def found(cfg: Any) -> list[Store]:
    """The derived stores a reset clears and rebuilds: those present, and those an interrupted
    reset recorded in its marker (whose files it may already have removed), in rebuild order."""
    pending = reset_pending(cfg) or {}
    named = set(pending.get("stores", ()))
    return [s for s in derived()
            if applies(cfg, s) and (s.name in named or s.path(cfg).exists())]


# ── the clearing ───────────────────────────────────────────────────────────────────────────


def _remove_file(path: Path) -> None:
    for p in (path, *(Path(str(path) + x) for x in SQLITE_SIDECARS)):
        if p.is_dir():
            raise RuntimeError(f"{p} is a directory where a derived store's file was expected")
        p.unlink(missing_ok=True)


def under_data(cfg: Any, path: Path) -> bool:
    """Whether `path` lies under the instance's data directory, by real path."""
    data = Path(os.path.realpath(cfg.paths.data_dir))
    return data in Path(os.path.realpath(path)).parents


def _inside_data(cfg: Any, path: Path) -> None:
    """Refuse to clear a store that does not lie under the instance's data directory: the class
    table computes each path from the configuration, and a path mistake must not reach outside.
    The reset finds this before it writes its marker (`missing_inputs`); this is the clearing's own
    guard."""
    if not under_data(cfg, path):
        raise RuntimeError(f"refusing to clear {path}: it does not lie under the data directory "
                           f"{cfg.paths.data_dir}")


def clear(ctx: Context, stores: list[Store]) -> None:
    """Clear each store, idempotently. The chat sensor's retention ledger is seeded from the chat
    log first, for an instance whose chat log predates it, while there is a chat log to read. Every
    path is checked to lie under the data directory before anything is cleared."""
    cfg = ctx.cfg
    for s in stores:
        _inside_data(cfg, s.path(cfg))
    names = {s.name for s in stores}
    if "chatlog.sqlite" in names:
        from core.stores.chat_retention import open_retention_ledger

        ledger = open_retention_ledger(cfg)
        try:
            ledger.seed_from(derived_path(cfg, "chatlog.sqlite"))
        finally:
            ledger.close()
    for s in stores:
        path = s.path(cfg)
        if s.clear == "index":
            lexical = ctx.lexical()
            if lexical is None:
                from core.stores.lexical import LexicalStore

                lexical = ctx.opened["lexical"] = LexicalStore(path)
            lexical.reset()
        elif s.clear == "relations":
            ctx.vectors().plane.reset_relations()
        elif s.clear == "rows":
            from core.kernel.provenance import Provenance
            from core.stores.edges import EdgeStore

            edges = EdgeStore(path)
            try:
                edges.delete_provenance(Provenance.AUTHORED_SOLO.value)
            finally:
                edges.close()
        else:
            _remove_file(path)


# ── the rebuild steps ──────────────────────────────────────────────────────────────────────


def _lexical(ctx: Context) -> str:
    from types import SimpleNamespace

    from core.ingest.derive import derive_lexical

    stores = SimpleNamespace(lexical=ctx.lexical(), catalog=ctx.catalog(), raw=ctx.raw())
    return f"lexical index: {derive_lexical(stores)}"


def _readable(raw: Any, digest: str) -> bool:
    """Whether the raw store can give the bytes of `digest`: it holds them, or its fallback (the
    shared cache) gives them, checked against the digest and copied in."""
    if raw.exists(digest):
        return True
    try:
        raw.get(digest)
    except FileNotFoundError:
        return False
    return True


def _plane(ctx: Context) -> str:
    """Re-occupy what the plane held before the clearing, and nothing more: an item still waiting
    for its vector (a lazy instance's backlog) is left to the embed job, so the plane comes back to
    its state before and the embedder is called only for a held atom the atom table lacks. Each
    held pair is rebuilt from raw at the digest the plane held, with the occupancy's title and
    class, whether or not that digest is still the catalog's head: raw keeps every version, and a
    note edited since it was embedded stays searchable at the version the plane held until the
    embed job takes the new one. The step reads no catalog row, so it does not open the catalog.

    A held pair whose raw object is gone is skipped and counted, as the chat log's replay skips a
    purged transcript: a purge is the raw store's one deletion, and one run between an interrupted
    reset and its rerun erases a version the marker still names (`plane_held`), so the rerun
    finishes with the erasure standing instead of failing at this step every time (§4.3)."""
    from types import SimpleNamespace

    from core.ingest.derive import derive_entries
    from core.stores.catalog import CatalogEntry

    cfg = ctx.cfg
    vectors = ctx.vectors()
    view = None
    if ctx.cache is not None:
        from core.stores.cache import key_of

        view = ctx.cache.view(key_of(cfg)[0])
    raw = ctx.raw()
    stores = SimpleNamespace(raw=raw, plane=vectors, lexical=ctx.lexical(),
                             embedder=_LazyEmbedder(lambda: ctx.embedder_factory(cfg)),
                             cache=view)
    held = sorted(ctx.plane_held)
    kept = [h for h in held if _readable(raw, h[1])]
    entries = [CatalogEntry(source_path=p, digest=d, title=t, active=True, provenance=c)
               for p, d, t, c in kept]
    report = derive_entries(stores, entries, batch=cfg.embedding.batch,
                            streams=cfg.embedding.streams)
    dropped = vectors.plane.drop_unheld()
    repaired = vectors.plane.repair()
    return (f"plane: {report}; {len(held) - len(kept)} held version(s) whose raw object a purge "
            f"erased skipped; {dropped} atom(s) no rebuilt row holds dropped; held cache "
            f"{repaired.held_fixed} fixed")


def _code_observations(ctx: Context) -> str:
    from core.sensing import CodeSensingHandoff
    from core.stores.code_observations import open_code_observation_store
    from core.stores.observation_history import open_observation_history_store
    from core.stores.reference_edges import open_reference_edge_store
    from ops.code_sensor import CodeSensor
    from ops.code_snapshot import open_snapshot_db

    cfg = ctx.cfg
    ledger = Path(cfg.paths.data_dir) / "code_snapshots.sqlite"
    if not ledger.exists():
        return "code observations: no commit ledger, nothing to re-project"
    sensor = CodeSensor(
        repo=ctx.repo, db=open_snapshot_db(ledger), attestor=None,
        observations=open_code_observation_store(cfg),
        obs_handoff=CodeSensingHandoff(handoff=Path(cfg.paths.data_dir) / "code_sensing_handoff"),
        reference_edges=(open_reference_edge_store(cfg)
                         if (Path(cfg.paths.data_dir) / "reference_edges.sqlite").exists()
                         else None),
        history=open_observation_history_store(cfg))
    return f"code observations: re-projected {sensor.backfill_observations()} commit(s)"


def _agent_observations(ctx: Context) -> str:
    from core.sensing import AgentSensingHandoff
    from core.stores.agent_observations import open_agent_observation_store
    from core.stores.observation_history import open_observation_history_store
    from ops.self_sensor import SelfSensor

    cfg = ctx.cfg
    if not (Path(ctx.repo) / ".git").exists():
        return "agent observations: no repository, nothing to re-project"
    sensor = SelfSensor(
        repo=ctx.repo, store=open_agent_observation_store(cfg),
        handoff=AgentSensingHandoff(handoff=Path(cfg.paths.data_dir) / "agent_sensing_handoff"),
        attestor=None, history=open_observation_history_store(cfg))
    return f"agent observations: {sensor.sync()}"


def _authored_edges(ctx: Context) -> str:
    from core.relations import rebuild_authored
    from core.stores.edges import EdgeStore

    edges = EdgeStore(derived_path(ctx.cfg, "edges.sqlite"))
    try:
        n = rebuild_authored(ctx.catalog(), ctx.raw(), edges, ctx.cfg)
    finally:
        edges.close()
    return f"authored relation edges: {n}"


def _chatlog(ctx: Context) -> str:
    from core.stores.chat_retention import open_retention_ledger
    from core.stores.chatlog import open_chatlog_store
    from ops.chat_sensor import ChatSecretGuard, ChatSensor

    cfg = ctx.cfg
    if not (Path(cfg.paths.data_dir) / "chat_retention.sqlite").exists():
        return "chat log: no retention ledger, nothing to replay"
    sensor = ChatSensor(transcripts_dir=Path(cfg.paths.data_dir) / "no-transcripts",
                        rawstore=ctx.raw(), store=open_chatlog_store(cfg),
                        guard=ChatSecretGuard(), retention=open_retention_ledger(cfg))
    try:
        return f"chat log: replayed {sensor.rebuild()}"
    finally:
        sensor.store.close()
        if sensor.retention is not None:
            sensor.retention.close()


def _chat_events(ctx: Context) -> str:
    from core.chat_events import ChatEventProjector
    from core.stores.chat_events import open_chat_event_store
    from core.stores.chatlog import open_chatlog_store

    cfg = ctx.cfg
    if not derived_path(cfg, "chatlog.sqlite").exists():
        return "chat events: no chat log, nothing to project"
    projector = ChatEventProjector(chatlog=open_chatlog_store(cfg), rawstore=ctx.raw(),
                                   store=open_chat_event_store(cfg))
    return f"chat events: projected {projector.project(max_sessions=_ALL)} session(s)"


def _causal_edges(ctx: Context) -> str:
    from core.integrator import Integrator
    from core.stores.causal_edges import open_causal_edge_store
    from core.stores.chat_events import open_chat_event_store

    cfg = ctx.cfg
    if not derived_path(cfg, "chat_events.sqlite").exists():
        return "causal edges: no chat events, nothing to integrate"
    path = Path(cfg.paths.data_dir) / "code_snapshots.sqlite"
    # the commit ledger, read only: an instance without one resolves every commit unknown
    ledger = (read_only(path) if path.exists()
              else sqlite3.connect(":memory:"))
    try:
        integrator = Integrator(events=open_chat_event_store(cfg), ledger=ledger,
                                edges=open_causal_edge_store(cfg))
        return f"causal edges: {integrator.integrate(max_sessions=_ALL)}"
    finally:
        ledger.close()


def _dispositions(ctx: Context) -> str:
    from core.stores.verdicts import VerdictStore
    from core.verdict.apply import apply_verdict
    from core.verdict.dispositions import DispositionStore

    cfg = ctx.cfg
    verdicts_path = Path(cfg.paths.derived_store).parent / "verdicts.sqlite"
    if not verdicts_path.exists():
        return "verdict dispositions: no verdicts"
    verdicts = VerdictStore(verdicts_path)
    dispositions = DispositionStore(derived_path(cfg, "verdict_dispositions.sqlite"))
    try:
        records = sorted(verdicts.all(), key=lambda r: r.seq)
        for record in records:
            apply_verdict(record, dispositions)
    finally:
        verdicts.close()
        dispositions.close()
    return f"verdict dispositions: {len(records)} verdict(s) applied"


#: The rebuild steps that open the catalog (`Context.catalog`): the lexical index and the authored
#: relation edges, which read its active rows. The plane step reads none (it rebuilds what the
#: plane held, from raw), so it does not open it. The catalog's first open writes the landing
#: log's genesis when it holds rows and no log yet (`catalog_without_log`). A test checks that
#: these are exactly the steps that open it.
OPENS_CATALOG = frozenset({"lexical.sqlite", "edges.sqlite"})

#: The rebuild step of each derived store, by name. A test replaces one to inject a failure.
STEPS: dict[str, Callable[[Context], str]] = {
    "lexical.sqlite": _lexical,
    "vectors.lance": _plane,
    "code_observations.sqlite": _code_observations,
    "agent_observations.sqlite": _agent_observations,
    "edges.sqlite": _authored_edges,
    "chatlog.sqlite": _chatlog,
    "chat_events.sqlite": _chat_events,
    "causal_edges.sqlite": _causal_edges,
    "verdict_dispositions.sqlite": _dispositions,
}


def run(ctx: Context, stores: list[Store], say: Callable[[str], None] = print) -> list[str]:
    """The whole reset under the caller's lock: the marker, the clearing, every step in order,
    and the marker's removal last. Interrupted anywhere, the marker stays and names every store,
    so the next run clears and rebuilds them all again."""
    m = marker(ctx.cfg)
    before = reset_pending(ctx.cfg) or {}
    record: dict[str, Any] = {
        "stores": sorted({s.name for s in stores} | set(before.get("stores", ()))),
        "started": datetime.now(UTC).isoformat(timespec="seconds")}
    if any(s.clear == "relations" for s in stores):
        held = before.get("plane_held")
        if held is None:
            held = sorted(plane_held(ctx.cfg))
        record["plane_held"] = held
        ctx.plane_held = [(str(p), str(d), str(t), str(c)) for p, d, t, c in held]
    m.parent.mkdir(parents=True, exist_ok=True)
    tmp = m.with_name(m.name + ".tmp")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(m)
    done: list[str] = []
    try:
        clear(ctx, stores)
        for s in stores:
            line = STEPS[s.name](ctx)
            say(f"  {s.step:>2}. {line}")
            done.append(line)
    finally:
        ctx.close()
    m.unlink()
    return done


# ── reading, for the refusals and the dry run ──────────────────────────────────────────────


def plane_held(cfg: Any) -> set[tuple[str, str, str, str]]:
    """The (path, digest, title, class) of every current occupancy of every plane class, read
    only: what the plane step rebuilds."""
    from core.stores.plane import OCC, PLANE_FILE

    db = Path(cfg.paths.vector_store) / PLANE_FILE
    if not db.is_file():
        return set()
    conn = read_only(db)
    try:
        out: set[tuple[str, str, str, str]] = set()
        for prov, occ in OCC.items():
            try:
                out |= {(str(p), str(d), str(t), prov.value) for p, d, t in conn.execute(
                    f"SELECT source_path, digest, MIN(title) FROM {occ} WHERE current = 1 "
                    "GROUP BY source_path, digest")}
            except sqlite3.Error:
                continue
        return out
    finally:
        conn.close()


def plane_heads(cfg: Any) -> set[tuple[str, str]]:
    """The (path, digest) of every current occupancy of every plane class, read only."""
    return {(p, d) for p, d, _, _ in plane_held(cfg)}


def recorded_geometry(cfg: Any) -> str | None:
    """The geometry the plane recorded at its first landing (its `meta` fingerprint: model,
    document template, dimension), read only; None when there is no plane or no record."""
    from core.stores.plane import PLANE_FILE

    db = Path(cfg.paths.vector_store) / PLANE_FILE
    if not db.is_file():
        return None
    try:
        conn = read_only(db)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'fingerprint'").fetchone()
    except sqlite3.Error:
        row = None
    finally:
        conn.close()
    return None if row is None else str(row[0])


def geometry_mismatch(cfg: Any) -> str | None:
    """Why the configured embedder is not the geometry the plane recorded, or None: the comparison
    `SharedPlane.check_geometry` makes, read only, since opening the plane to ask would create its
    `-wal` and `-shm` and a refusal writes nothing."""
    from core.stores.vectorstore import fingerprint_of

    recorded = recorded_geometry(cfg)
    mine = fingerprint_of(cfg).as_json()
    if recorded is None or recorded == mine:
        return None
    return f"the plane's vectors came from {recorded}; the configured embedder is {mine}"


def catalog_without_log(cfg: Any) -> int:
    """The catalog's rows when it holds rows and no landing log yet, else 0, read only. That is
    the catalog whose first open through `VaultCatalog`, the rebuild's own included, writes the
    log's genesis (`VaultCatalog._migrate`), which needs the instance's landing-log secret. A
    file that is not a SQLite database, or holds no catalog table, is 0: no step would open it as
    a catalog."""
    path = Path(cfg.paths.vault_catalog)
    if not path.is_file():
        return 0
    try:
        conn = read_only(path)
    except sqlite3.Error:
        return 0
    try:
        tables = {str(r[0]) for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "vault_files" not in tables:
            return 0
        if "landing_chains" in tables and conn.execute(
                "SELECT 1 FROM landing_chains LIMIT 1").fetchone() is not None:
            return 0
        return int(conn.execute("SELECT count(*) FROM vault_files").fetchone()[0])
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def landing_log_secret() -> str | None:
    """Why the landing log's secret cannot be read, or None when it can: the item the catalog's
    own open reads (`core.stores.landings.landing_log_key`, under the process's configuration),
    absent, or not 32 bytes of hex."""
    from core.kernel.config import get_config
    from core.stores.landings import LANDING_LOG_KEY, LandingLogKeyMissing, landing_log_key

    try:
        landing_log_key()
    except LandingLogKeyMissing:
        name = get_config().instance.secret(LANDING_LOG_KEY)
        return (f"get_secret({name!r}) is not in the environment, or is not 32 random bytes as "
                "64 hex digits")
    return None


def missing_inputs(cfg: Any, repo: Path, stores: list[Store]) -> list[str]:
    """What would stop a rebuild the same way on every run, found before anything is written, the
    marker included, so a reset that could not finish refuses with nothing written instead of
    failing after the clearing and leaving the marker to block every writer. A derived store that
    does not lie under the data directory (a store beside `derived_store` configured elsewhere),
    which the clearing refuses to touch. A commit the commit ledger holds that the repository no
    longer has (pruned by a rewrite and a garbage collection), which the code observations'
    re-projection reads. And the landing log's secret, when the catalog holds rows and no log yet:
    the first step that opens the catalog writes the log's genesis there, and without the secret
    that open refuses, after it has created the log's two empty tables, so the case is found here,
    read only, before any open. A raw object a purge erased is not missing: the chat log's replay
    and the plane step skip it and say so (§4.3, §6.6)."""
    out = [f"the derived store {s.path(cfg)} does not lie under the data directory "
           f"{cfg.paths.data_dir}, and a reset clears nothing outside it. Configure it under the "
           "data directory first" for s in stores if not under_data(cfg, s.path(cfg))]
    if any(s.name in OPENS_CATALOG for s in stores):
        rows = catalog_without_log(cfg)
        why = landing_log_secret() if rows else None
        if why is not None:
            out.append(f"the catalog holds {rows:,} row(s) and no landing log yet, so the "
                       "rebuild's first open of it writes the log's genesis, which needs the "
                       f"instance's landing-log secret, and {why}. Place it (runbook §0) and run "
                       "the reset with it in the environment")
    if any(s.name == "code_observations.sqlite" for s in stores):
        ledger = Path(cfg.paths.data_dir) / "code_snapshots.sqlite"
        if ledger.is_file():
            conn = read_only(ledger)
            try:
                shas = [str(r[0]) for r in conn.execute("SELECT commit_sha FROM snapshots")]
            except sqlite3.Error:
                shas = []
            finally:
                conn.close()
            gone = _absent_commits(repo, shas)
            if gone:
                out.append(f"{len(gone)} commit(s) the commit ledger holds are not in the "
                           f"repository {repo} ({', '.join(g[:10] for g in gone[:3])}"
                           f"{', ...' if len(gone) > 3 else ''}), so their code observations "
                           "could not be re-projected. Bring the commits back first")
    return out


def _absent_commits(repo: Path, shas: list[str]) -> list[str]:
    """The commits of `shas` the repository at `repo` does not hold, by one `cat-file` pass."""
    if not shas:
        return []
    if not (Path(repo) / ".git").exists():
        return sorted(shas)
    proc = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch-check"],
                          input="".join(f"{s}^{{commit}}\n" for s in shas), text=True,
                          capture_output=True, check=True)
    return sorted(s for s, line in zip(shas, proc.stdout.splitlines(), strict=True)
                  if line.endswith(" missing"))


def row_count(path: Path) -> int | None:
    """The rows of every table of a SQLite file, read only; None for anything else."""
    if not path.is_file():
        return None
    try:
        conn = read_only(path)
    except sqlite3.Error:
        return None
    try:
        tables = [str(r[0]) for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        return sum(int(conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0])
                   for t in tables)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def describe(cfg: Any, stores: list[Store]) -> list[str]:
    """The dry run's lines: what is cleared, by class what is kept."""
    from ops.lifecycle.inventory import STORES

    lines = ["clears and rebuilds (derived):"]
    for s in stores:
        path = s.path(cfg)
        target = path / "plane.sqlite" if s.clear == "relations" else path
        n = row_count(target)
        how = {"index": "reset, then the lexical backfill",
               "relations": "occupancies and supersession log; atoms kept",
               "rows": "the authored rows only"}.get(s.clear, "file")
        lines.append(f"  {s.step:>2}. {s.name}  ({'?' if n is None else n} row(s); {how}) "
                     f"<- {s.note}")
        if s.clear == "relations":
            lines.extend(_plane_lines(cfg, target))
    for kind in (Kind.LEDGER, Kind.DECLARATION, Kind.KEPT, Kind.OPERATIONAL):
        present = [s.name for s in STORES if s.kind is kind and s.path(cfg).exists()]
        lines.append(f"keeps ({kind.value}): {', '.join(present) or '(none present)'}")
    rows = catalog_without_log(cfg) if any(s.name in OPENS_CATALOG for s in stores) else 0
    if rows:
        lines.append(f"the catalog holds {rows:,} row(s) and no landing log yet: the rebuild's "
                     "first open of it writes the log's genesis, as any first open does, and "
                     "leaves its rows as they are")
    return lines


def _plane_lines(cfg: Any, plane_db: Path) -> list[str]:
    """The plane's part of the dry run: what the rebuild re-occupies (every pair the plane holds
    current, as `_plane` rebuilds them), how many of those are no longer the catalog's head, the
    atoms that needs and how many of them the atom table lacks (those, and only those, call the
    embedder), and the items whose current version holds no vector, which the reset leaves to the
    embed job."""
    heads = plane_heads(cfg)
    atoms = _head_atoms(plane_db)
    lacking = 0
    if atoms:
        from core.stores.vectorstore import open_vector_store

        lacking = len(atoms - open_vector_store(cfg).plane.atoms.present(sorted(atoms)))
    waiting, older = _without_vector(cfg, heads)
    return [f"      re-occupies the {len(heads)} item(s) the plane holds current ({older} of them "
            f"at a version older than the catalog's), with {len(atoms)} distinct atom(s); the "
            f"atom table lacks {lacking} of them, so the embedder is called for {lacking} atom(s)",
            f"      {waiting} item(s) of the plane's classes hold no vector for their current "
            "version (waiting for the embed job, or with no text); the reset leaves them so"]


def _without_vector(cfg: Any, heads: set[tuple[str, str]]) -> tuple[int, int]:
    """Read only: the active catalog items of the plane's classes whose current version the plane
    does not hold current, and how many of those the plane holds at an older version."""
    from core.ingest.derive import HOLDS

    path = Path(cfg.paths.vault_catalog)
    if not path.is_file():
        return 0, 0
    conn = read_only(path)
    try:
        rows = conn.execute("SELECT source_path, digest, provenance FROM vault_files "
                            "WHERE active = 1").fetchall()
    finally:
        conn.close()
    paths = {p for p, _ in heads}
    waiting = [str(p) for p, d, c in rows
               if str(c) in HOLDS and (str(p), str(d)) not in heads]
    return len(waiting), sum(1 for p in waiting if p in paths)


def _head_atoms(plane_db: Path) -> set[str]:
    """The distinct atoms the plane's current occupancies hold, read only."""
    if not plane_db.is_file():
        return set()
    from core.stores.plane import OCC

    conn = read_only(plane_db)
    try:
        held: set[str] = set()
        for occ in OCC.values():
            try:
                held |= {str(r[0]) for r in conn.execute(
                    f"SELECT DISTINCT atom_id FROM {occ} WHERE current = 1")}
            except sqlite3.Error:
                continue
        return held
    finally:
        conn.close()
