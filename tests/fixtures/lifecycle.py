"""A whole palace on temporary stores, for the lifecycle's tests (dn-instance-lifecycle §8): notes
in a vault with authored and interpreted relation edges, a superseded note version, open-corpus
items, a repository landed lexically and read by the code sensor, transcripts through the chat
sensor (one grown, one held by the guard), the chat events and causal edges over them, signed
verdicts and their dispositions, and an attestation trail. Every path the configuration names is
under one root; nothing reads or writes a live instance. The embedder is a deterministic fake that
counts its calls.

`dump` reads every store read only: a SQLite file as its tables' rows, a directory as its files'
bytes, so two dumps compare a palace before and after a reset or a destroy.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ingest import ingress
from core.ingest.readers import PalaceView
from core.ingest.table import build_table
from core.ingest.writer import Stores
from core.kernel.config import get_config
from core.kernel.config.loader import InstanceConfig, RepositoryConfig
from core.kernel.stores.rawstore import RawStore
from core.sentence import ast
from core.sentence.plan import compile_sentence
from core.stores.catalog import VaultCatalog
from core.stores.edges import open_edge_store
from core.stores.lexical import LexicalStore, lexical_path
from core.stores.vectorstore import VectorStore, fingerprint_of
from core.stores.versions import open_version_store
from edge.corpus.stream import StreamWriter
from tests.fixtures.embedding import DIM, FakeEmbedder

REPO = "toy"
CORPUS_SOURCE = "alpha"


class CountingEmbedder(FakeEmbedder):
    """The fake embedder, counting the texts it is asked for."""

    def __init__(self) -> None:
        self.calls = 0
        self.texts = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        self.texts += len(texts)
        return super().embed_documents(texts)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@example.org", "-c", "user.name=t", "commit", "-q", "-m",
        message)
    return git(repo, "rev-parse", "HEAD")


def make_repo(at: Path) -> Path:
    """A repository on `main` with code that references a doc, and a doc that names the code."""
    (at / "pkg").mkdir(parents=True)
    (at / "docs").mkdir()
    git(at.parent, "init", "-q", "-b", "main", str(at))
    (at / "pkg" / "embed.py").write_text(
        'def embed_fitting(texts):\n    """Cut a text to fit; see docs/landing.md."""\n'
        "    return texts\n")
    (at / "docs" / "landing.md").write_text(
        "# Landing\n\nThe cut lives in `pkg/embed.py`.\n")
    commit(at, "one")
    (at / "pkg" / "derive.py").write_text(
        "from pkg.embed import embed_fitting\n\n\ndef drain():\n    return embed_fitting([])\n")
    commit(at, "two")
    return at


def instance_config(root: Path, repo: Path | None = None, *, named: str | None = None,
                    lazy: bool = False, embedding: bool = True, model: str | None = None,
                    sources: Path | None = None) -> Any:
    """A palace whose every written path is under `root` (its data under `root/data`), reading
    its vault and transcripts from under `sources` (`root` when not given), its corpus streams
    from `root/sources`, and `repo` as its code. A named instance's destroy refuses a root that
    holds what is not its own state, so a named fixture reads its vault from outside its root.

    A named fixture's configuration is built here, not loaded, so the process's configuration
    (`get_config()`), which the landing log reads its secret through, stays the default
    instance's, and the suite's item keys its catalog. A test of the named instance's own item,
    `<id>.landing-log-key`, loads the instance through an overlay instead."""
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    read = sources if sources is not None else root
    (read / "vault").mkdir(parents=True, exist_ok=True)
    (read / "transcripts").mkdir(exist_ok=True)
    base = get_config()
    paths = replace(base.paths, data_dir=data, raw_store=data / "raw",
                    vector_store=data / "vectors.lance",
                    curated_store=data / "research_curated.lance",
                    vault_catalog=data / "vault_catalog.sqlite",
                    derived_store=data / "derived.sqlite", telemetry_db=data / "telemetry.duckdb",
                    attestation_store=data / "attestations.sqlite")
    code = replace(base.ingestion.code, enabled=repo is not None, embed=False,
                   repositories=(RepositoryConfig(REPO, repo, "main"),) if repo else ())
    corpus = replace(base.ingestion.corpus, enabled=True, root=root / "sources",
                     sources=(CORPUS_SOURCE,))
    ingestion = replace(base.ingestion, code=code, corpus=corpus,
                        vault=replace(base.ingestion.vault, path=read / "vault", enabled=True),
                        transcripts=replace(base.ingestion.transcripts, enabled=True,
                                            transcripts_dir=read / "transcripts"))
    emb = replace(base.embedding, enabled=embedding, lazy=lazy, dim=DIM)
    if model:
        emb = replace(emb, model=model)
    cfg = replace(base, paths=paths, ingestion=ingestion, embedding=emb,
                  interface=replace(base.interface, handoff_dir=data / "handoff"),
                  airlock=replace(base.airlock, handoff_dir=data / "airlock"),
                  selfmod=replace(base.selfmod, ledger_db=data / "selfmod_ledger.sqlite"),
                  effectors=replace(base.effectors, ledger_db=data / "effectors" / "effects.sqlite",
                                    drafts_dir=data / "effectors" / "drafts",
                                    handoff_dir=data / "handoff" / "sensing"))
    if named is not None:
        cfg = replace(cfg, instance=InstanceConfig(named, home=root))
    return cfg


def stores_for(cfg: Any, embedder: Any, *, lexical: LexicalStore | None = None) -> Stores:
    """The writer's stores over `cfg`'s paths, the attestor writing the instance's own ledger."""
    return Stores(raw=RawStore(cfg.paths.raw_store),
                  plane=VectorStore(cfg.paths.vector_store, dim=DIM,
                                    embedder=fingerprint_of(cfg)) if cfg.embedding.enabled
                  else _noplane(),
                  embedder=embedder, catalog=VaultCatalog(cfg.paths.vault_catalog),
                  versions=open_version_store(cfg),
                  attestor=StoreAttestor(AttestationStore(cfg.paths.attestation_store)),
                  edges=open_edge_store(cfg),
                  lexical=lexical if lexical is not None else LexicalStore(lexical_path(cfg)))


def _noplane() -> Any:
    from core.stores.noplane import NoPlane

    return NoPlane()


def perform(cfg: Any, stores: Stores, text: str, role: str = "cli", *,
            batch: bool = False) -> dict[str, Any]:
    plan = compile_sentence(text, ingress.grant_for(role), role=role)
    assert isinstance(plan.term, ast.Do)
    view = PalaceView(build_table(cfg), role, stores.catalog, refresh=False)
    return ingress.perform(plan.term, cfg, role, stores=stores, view=view, batch=batch)


def fill_stream(cfg: Any, n: int = 3) -> None:
    w = StreamWriter(cfg.ingestion.corpus.root / CORPUS_SOURCE, part_bytes=300)
    for i in range(n):
        w.append(f"a-{i}", f"alpha {i}",
                 f"open item {i}: a paragraph of public text about landing without vectors. "
                 "It shares this sentence with every other item of the stream. " * 2)
    w.close()


def _rec(rtype: str, content: Any, session: str, ts: str) -> dict[str, Any]:
    return {"type": rtype, "sessionId": session, "timestamp": ts, "uuid": "u",
            "parentUuid": None, "message": {"role": rtype, "content": content}}


def transcript(cfg: Any, session: str, turns: list[tuple[str, Any]]) -> Path:
    p = Path(cfg.ingestion.transcripts.transcripts_dir) / f"{session}.jsonl"
    p.write_text("".join(json.dumps(_rec(r, c, session, f"2026-11-0{1 + i % 8}T00:00:00Z")) + "\n"
                         for i, (r, c) in enumerate(turns)), encoding="utf-8")
    return p


@dataclass
class Built:
    cfg: Any
    root: Path
    repo: Path
    embedder: CountingEmbedder
    stores: Stores
    owner: Any = None
    notes: dict[str, Path] = field(default_factory=dict)


def build_palace(root: Path, repo: Path, *, named: str | None = None) -> Built:
    """Exercise every lane the lifecycle tests read, under `root`."""
    from core.attestation import Ed25519Signer, generate_seed
    from core.chat_events import build_chat_event_projector
    from core.integrator import build_integrator
    from core.kernel.complex_types import EdgeSign
    from core.relations import RelationDetector
    from core.sensing import AgentSensingHandoff, CodeSensingHandoff
    from core.stores.agent_observations import open_agent_observation_store
    from core.stores.code_observations import open_code_observation_store
    from core.stores.observation_history import open_observation_history_store
    from core.stores.reference_edges import open_reference_edge_store
    from core.stores.verdicts import VerdictStore
    from core.verdict import VerdictPayload, sign_verdict
    from core.verdict.apply import apply_verdict, receive_verdict
    from core.verdict.dispositions import DispositionStore
    from ops.chat_sensor import build_chat_sensor
    from ops.code_sensor import CodeSensor
    from ops.code_snapshot import open_snapshot_db
    from ops.self_sensor import SelfSensor

    cfg = instance_config(root, repo, named=named,
                          sources=root.parent / f"{named}-read" if named else None)
    emb = CountingEmbedder()
    stores = stores_for(cfg, emb)
    b = Built(cfg, root, repo, emb, stores)
    vault = Path(cfg.ingestion.vault.path)
    # notes: one supports another; one changes, so a superseded version exists
    b.notes = {
        "alpha": vault / "alpha.md", "beta": vault / "beta.md", "gamma": vault / "gamma.md"}
    b.notes["alpha"].write_text("supports:: [[beta]]\n\nAlpha: landing needs no vector.\n")
    b.notes["beta"].write_text("Beta: an item is complete without its vector.\n")
    b.notes["gamma"].write_text("Gamma, first draft.\n")
    assert perform(cfg, stores, "do sync_vault")["effects"].get("landed") == 3
    b.notes["gamma"].write_text("Gamma, second draft, which supersedes the first.\n")
    perform(cfg, stores, "do sync_vault")
    assert stores.edges is not None
    detector = RelationDetector(config=cfg, edges=stores.edges, catalog=stores.catalog,
                                vectors=stores.plane, chat=None)
    detector.run()
    cat = {e.title: e.digest for e in stores.catalog.active_entries()}
    stores.edges.add(cat["beta"], cat["gamma"], sign=EdgeSign.SUPPORT, rel_type="supports",
                     w=0.8, provenance="interpreted")
    # open corpus items, observed, with plane rows
    fill_stream(cfg)
    perform(cfg, stores, f'do sync_corpus(name: "{CORPUS_SOURCE}", batch: 10)', role="corpus",
            batch=True)
    # the repository, lexically, and its commits through the code sensor
    perform(cfg, stores, f'do sync_repository(name: "{REPO}")')
    data = Path(cfg.paths.data_dir)
    sensor = CodeSensor(
        repo=repo, db=open_snapshot_db(data / "code_snapshots.sqlite"), attestor=stores.attestor,
        observations=open_code_observation_store(cfg),
        obs_handoff=CodeSensingHandoff(handoff=data / "code_sensing_handoff"),
        reference_edges=open_reference_edge_store(cfg),
        history=open_observation_history_store(cfg))
    sensor.sync()
    sensor.backfill_observations()
    SelfSensor(repo=repo, store=open_agent_observation_store(cfg),
               handoff=AgentSensingHandoff(handoff=data / "agent_sensing_handoff"),
               attestor=None, history=open_observation_history_store(cfg)).sync()
    # transcripts: one plain, one grown, one held at its state before a secret
    chat = build_chat_sensor(cfg)
    transcript(cfg, "s-plain", [("user", "how does a reset work?"),
                                ("assistant", [{"type": "text", "text": "it rebuilds."}])])
    transcript(cfg, "s-grown", [("user", "first question")])
    transcript(cfg, "s-held", [("user", "a clean opening")])
    head = git(repo, "rev-parse", "HEAD")
    transcript(cfg, "s-commit", [
        ("user", "commit it"),
        ("assistant", [{"type": "tool_use", "id": "t1", "name": "Bash",
                        "input": {"command": "git commit -m two"}}]),
        ("user", [{"type": "tool_result", "tool_use_id": "t1",
                   "content": f"[main {head[:7]}] two"}]),
        ("assistant", "committed")])
    chat.sync()
    transcript(cfg, "s-grown", [("user", "first question"),
                                ("assistant", "a later answer, after it grew")])
    transcript(cfg, "s-held", [("user", "a clean opening"),
                               ("assistant", "api_key = " + "A1b2C3d4" * 5)])
    chat.sync()
    build_chat_event_projector(cfg).project(max_sessions=100)
    build_integrator(cfg).integrate(max_sessions=100)
    # verdicts, signed by an owner key, and their dispositions
    owner = Ed25519Signer.from_seed(generate_seed(), "owner")
    b.owner = owner
    verdicts = VerdictStore(data / "verdicts.sqlite")
    dispositions = DispositionStore(data / "verdict_dispositions.sqlite")
    for seq, (subject, verdict) in enumerate([("claim-1", "novel_useful"), ("claim-2", "wrong"),
                                              ("claim-1", "noise")], start=1):
        rec = receive_verdict(sign_verdict(VerdictPayload(
            subject_id=subject, verdict=verdict, seq=seq, timestamp="2026-11-01T00:00:00"),
            owner), verdicts, owner_pub_b64=owner.public_b64())
        apply_verdict(rec, dispositions)
    verdicts.close()
    dispositions.close()
    write_kept_stores(cfg)
    return b


def write_kept_stores(cfg: Any) -> None:
    """One row or more in each kept store a reset must leave as it was (§3.5, §3.7): an
    interpreted artifact (decision D4), a queued job carrying a request (D7), a dream run and its
    claim, a claim operation and a staged hypothesis."""
    from core.kernel.provenance import Provenance
    from core.kernel.recursion_ops import OpKind
    from core.kernel.scope import Stratum
    from core.stores.claim_ops import open_claim_op_store
    from core.stores.derived import DerivedStore
    from core.stores.runledger import open_run_ledger
    from core.stores.staging import StagedItem, open_staging_store
    from scheduler.queue import JobQueue

    derived = DerivedStore(Path(cfg.paths.derived_store))
    derived.add(kind="synthesis", summary="a model's sentence over two notes", subjects=("x",))
    derived.close()
    queue = JobQueue(Path(cfg.paths.data_dir) / "queue.sqlite")
    queue.enqueue("ingress", "small", 1024, payload={"text": "a request only the queue holds"})
    queue.close()
    runs = open_run_ledger(cfg)
    run = runs.start_run(pipeline="toy", config_fingerprint="f", corpus_digest="c", node_count=3,
                         edge_count=2, duration_s=0.1, spectral_stats={})
    runs.add_claim(run, kind="bridge", confidence=0.5, support=("a", "b"),
                   surface_text="a claim a model wrote", polarity="support")
    runs.close()
    ops = open_claim_op_store(cfg)
    ops.record(OpKind.RECORD_WARRANT, "claim-1", text="a warrant")
    ops.close()
    staging = open_staging_store(cfg)
    staging.stage("toy", [StagedItem(Stratum.OBSERVED, Provenance.OBSERVED, "d" * 64, "p")])
    staging.close()


# ── reading a palace back ───────────────────────────────────────────────────────────────────

#: Columns that hold a wall-clock bookmark: a rebuild writes its own time there (Law C4).
WALL = frozenset({"landed_at", "observed_at", "created_at", "at", "updated_at", "recorded_at",
                  "projected_at", "integrated_at", "extracted_at", "minted_at"})


def sqlite_rows(path: Path, *, wall: bool = True) -> dict[str, list[tuple[Any, ...]]]:
    """Every table's rows, sorted, read only, creating no file (`read_only`); `wall=False` leaves
    the wall-clock columns out."""
    from ops.lifecycle.inventory import read_only

    conn = read_only(path)
    try:
        out: dict[str, list[tuple[Any, ...]]] = {}
        for (table,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                                     "AND name NOT LIKE 'sqlite_%'"):
            cols = [str(r[1]) for r in conn.execute(f'PRAGMA table_info("{table}")')]
            keep = [c for c in cols if wall or c not in WALL]
            sel = ", ".join(f'"{c}"' for c in keep)
            out[str(table)] = sorted(conn.execute(f'SELECT {sel} FROM "{table}"').fetchall(),
                                     key=repr)
        return out
    finally:
        conn.close()


def dump_path(path: Path, *, wall: bool = True) -> Any:
    """A store's content: a SQLite file's rows, another file's bytes, a directory's files."""
    if path.is_dir():
        return {str(p.relative_to(path)): dump_path(p, wall=wall)
                for p in sorted(path.rglob("*")) if p.is_file()
                and not p.name.endswith(("-wal", "-shm", ".lock"))}
    if not path.exists():
        return None
    head = path.read_bytes()[:16]
    if head.startswith(b"SQLite format 3"):
        return sqlite_rows(path, wall=wall)
    return path.read_bytes()


def dump(cfg: Any, kinds: set[Any] | None = None) -> dict[str, Any]:
    """Every store of the class table under `cfg`, of `kinds` (all when None), in full."""
    from ops.lifecycle.inventory import STORES

    return {s.name: dump_path(s.path(cfg)) for s in STORES
            if (kinds is None or s.kind in kinds) and s.name not in {"vectors.lance",
                                                                     "supervisor.lock"}}


def heads(cfg: Any) -> dict[str, Any]:
    """Each derived store's head, the wall-clock bookmarks left out (§4.4)."""
    from core.kernel.clearance import MAINTENANCE_READ
    from core.stores.plane import OCC

    data = Path(cfg.paths.data_dir)
    out: dict[str, Any] = {}
    for name in ("chatlog.sqlite", "chat_events.sqlite", "verdict_dispositions.sqlite",
                 "code_observations.sqlite", "agent_observations.sqlite"):
        p = data / name
        out[name] = sqlite_rows(p, wall=False) if p.exists() else None
    edges = sqlite_rows(data / "edges.sqlite", wall=False)["edges"]
    out["edges"] = edges
    lex = sqlite3.connect(f"file:{data / 'lexical.sqlite'}?mode=ro", uri=True)
    try:
        out["lexical.units"] = sorted(lex.execute(
            "SELECT source_path, digest, chunk_index, provenance, title, length FROM units "
            "WHERE current = 1").fetchall())
        out["lexical.postings"] = sorted(lex.execute(
            "SELECT u.source_path, u.digest, u.chunk_index, p.term, p.tf FROM postings p "
            "JOIN units u ON u.unit_id = p.unit_id WHERE u.current = 1").fetchall())
        out["lexical.versions"] = sorted(lex.execute(
            "SELECT v.source_path, v.digest, v.units FROM versions v WHERE EXISTS (SELECT 1 "
            "FROM units u WHERE u.source_path = v.source_path AND u.digest = v.digest "
            "AND u.current = 1) OR v.units = 0").fetchall())
    finally:
        lex.close()
    if cfg.embedding.enabled:
        plane_db = Path(cfg.paths.vector_store) / "plane.sqlite"
        conn = sqlite3.connect(f"file:{plane_db}?mode=ro", uri=True)
        try:
            occ = {p.value: sorted(conn.execute(
                f"SELECT source_path, digest, chunk_index, atom_id, row_id, title FROM {t} "
                "WHERE current = 1").fetchall()) for p, t in OCC.items()}
        finally:
            conn.close()
        out["plane.occupancies"] = occ
        store = VectorStore(cfg.paths.vector_store, dim=DIM, embedder=fingerprint_of(cfg))
        atoms = sorted({a for rows in occ.values() for _, _, _, a, _, _ in rows})
        out["plane.vectors"] = {a: list(v) for a, (_t, v)
                                in sorted(store.plane.atoms.payload(atoms).items())}
        out["plane.count"] = store.reader(MAINTENANCE_READ).count()
    return out
