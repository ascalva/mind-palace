"""A lifecycle reset: clear an instance's derived stores and rebuild them from its ledgers
(dn-instance-lifecycle §4).

The class table (`ops/lifecycle/inventory.py`) names the derived stores and their order. A reset
clears each one it finds, each by its own method (the lexical index's `reset`, the plane's
relations with its atoms kept, the authored rows of the relation edges) or by deleting its file,
then runs the rebuild steps in order, each reading only ledgers and the steps before it, and
writes no ledger: the sensors re-project without their attestor, and the reference edges a
re-projection mints again are found held. Every other store is kept as it was.

What it guarantees, and the tests check (§8): every ledger, declaration and kept store is the same
row for row; each derived store's head after the rebuild equals its head before, wall-clock
bookmarks left out (the causal edges equal a fresh integration over the same inputs); no embedder
call while the atoms are held; a second reset leaves what the first left. Before the landing log
(pull request #92) the version-keyed stores are rebuilt for the current versions only (decision
D2): no ledger names a superseded version's path outside the version chains.
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

from ops.lifecycle.inventory import Kind, Store, derived, marker, reset_pending

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
    # The plane's current occupancies before the clearing, as (path, digest): what the plane step
    # rebuilds, and nothing more (§4.4). Read once and kept in the marker, so a reset run again
    # after an interruption rebuilds what the plane held before the first run cleared it.
    plane_heads: set[tuple[str, str]] = field(default_factory=set)

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


def _inside_data(cfg: Any, path: Path) -> None:
    """Refuse to clear a store that does not lie under the instance's data directory: the class
    table computes each path from the configuration, and a path mistake must not reach outside."""
    data = Path(os.path.realpath(cfg.paths.data_dir))
    real = Path(os.path.realpath(path))
    if data not in real.parents:
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


def _plane(ctx: Context) -> str:
    """Re-occupy what the plane held before the clearing, and nothing more: an item still waiting
    for its vector (a lazy instance's backlog) is left to the embed job, so the plane comes back to
    its state before and the embedder is called only for a held atom the atom table lacks."""
    from types import SimpleNamespace

    from core.ingest.derive import derive_entries

    cfg = ctx.cfg
    vectors = ctx.vectors()
    view = None
    if ctx.cache is not None:
        from core.stores.cache import key_of

        view = ctx.cache.view(key_of(cfg)[0])
    stores = SimpleNamespace(catalog=ctx.catalog(), raw=ctx.raw(), plane=vectors,
                             lexical=ctx.lexical(),
                             embedder=_LazyEmbedder(lambda: ctx.embedder_factory(cfg)),
                             cache=view)
    entries = [e for e in ctx.catalog().active_entries()
               if (e.source_path, e.digest) in ctx.plane_heads]
    report = derive_entries(stores, entries, batch=cfg.embedding.batch,
                            streams=cfg.embedding.streams)
    dropped = vectors.plane.drop_unheld()
    repaired = vectors.plane.repair()
    return (f"plane: {report}; {dropped} atom(s) no rebuilt row holds dropped; held cache "
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
    ledger = (sqlite3.connect(f"file:{path}?mode=ro", uri=True) if path.exists()
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
        held = before.get("plane_heads")
        if held is None:
            held = sorted(plane_heads(ctx.cfg))
        record["plane_heads"] = held
        ctx.plane_heads = {(str(p), str(d)) for p, d in held}
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


def plane_heads(cfg: Any) -> set[tuple[str, str]]:
    """The (path, digest) of every current occupancy of every plane class, read only."""
    from core.stores.plane import OCC, PLANE_FILE

    db = Path(cfg.paths.vector_store) / PLANE_FILE
    if not db.is_file():
        return set()
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        out: set[tuple[str, str]] = set()
        for occ in OCC.values():
            try:
                out |= {(str(p), str(d)) for p, d in conn.execute(
                    f"SELECT DISTINCT source_path, digest FROM {occ} WHERE current = 1")}
            except sqlite3.Error:
                continue
        return out
    finally:
        conn.close()


def missing_inputs(cfg: Any, repo: Path, stores: list[Store]) -> list[str]:
    """What a rebuild step would need and cannot read, found before anything is cleared, so a
    reset that could not finish refuses with nothing written instead of failing after the
    clearing. Today one input can go missing under a step: a commit the commit ledger holds that
    the repository no longer has (pruned by a rewrite and a garbage collection), which the code
    observations' re-projection reads. A retained transcript whose raw object a purge erased is
    not missing: the chat log's replay skips it and says so (§6.6)."""
    out: list[str] = []
    if any(s.name == "code_observations.sqlite" for s in stores):
        ledger = Path(cfg.paths.data_dir) / "code_snapshots.sqlite"
        if ledger.is_file():
            conn = sqlite3.connect(f"file:{ledger}?mode=ro", uri=True)
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
                           "could not be re-projected")
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
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
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
    return lines


def _plane_lines(cfg: Any, plane_db: Path) -> list[str]:
    """The plane's part of the dry run: what the rebuild re-occupies, the atoms that needs and how
    many of them the atom table lacks (those, and only those, call the embedder), and the items
    with no vector, which the reset leaves to the embed job."""
    heads = plane_heads(cfg)
    atoms = _head_atoms(plane_db)
    lacking = 0
    if atoms:
        from core.stores.vectorstore import open_vector_store

        lacking = len(atoms - open_vector_store(cfg).plane.atoms.present(sorted(atoms)))
    waiting = _without_vector(cfg, heads)
    return [f"      re-occupies the {len(heads)} item(s) the plane holds current, with "
            f"{len(atoms)} distinct atom(s); the atom table lacks {lacking} of them, so the "
            f"embedder is called for {lacking} atom(s)",
            f"      {waiting} item(s) of the plane's classes hold no vector (waiting for the embed "
            "job, or with no text); the reset leaves them so"]


def _without_vector(cfg: Any, heads: set[tuple[str, str]]) -> int:
    """The active catalog items of the plane's classes the plane does not hold current, read
    only."""
    from core.ingest.derive import HOLDS

    path = Path(cfg.paths.vault_catalog)
    if not path.is_file():
        return 0
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT source_path, digest, provenance FROM vault_files "
                            "WHERE active = 1").fetchall()
    finally:
        conn.close()
    return sum(1 for p, d, c in rows if str(c) in HOLDS and (str(p), str(d)) not in heads)


def _head_atoms(plane_db: Path) -> set[str]:
    """The distinct atoms the plane's current occupancies hold, read only."""
    if not plane_db.is_file():
        return set()
    from core.stores.plane import OCC

    conn = sqlite3.connect(f"file:{plane_db}?mode=ro", uri=True)
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
