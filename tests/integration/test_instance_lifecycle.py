"""The instance's lifecycle (docs/design-notes/dn-instance-lifecycle.md §8): a reset that clears the
derived stores and rebuilds them from raw and the ledgers, a destroy that leaves a shared cache of
open content, the cache's reuse paths, a purge that reaches the cache, a sync that heals a stale
lexical index, and the corpus instance at its own root.

Every test runs on fixture palaces under a temporary directory (`tests/fixtures/lifecycle.py`):
notes, a superseded note version, authored and interpreted relation edges, open-corpus items, a
repository through the repository sync and the code sensor, transcripts through the chat sensor
(one grown, one held by the guard), chat events and causal edges, signed verdicts and an
attestation trail. No test opens a real instance or the real cache.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.kernel.config import loader
from ops.lifecycle import rebuild
from ops.lifecycle.inventory import STORES, Kind, unclassified
from ops.lifecycle.launcher import Launcher
from ops.lifecycle.lock import SupervisorLock
from ops.lifecycle.runs import LazyRunLedger, RunLedger
from tests.fixtures.lifecycle import (
    CORPUS_SOURCE,
    REPO,
    Built,
    CountingEmbedder,
    build_palace,
    commit,
    dump,
    heads,
    instance_config,
    make_repo,
    perform,
    stores_for,
)

KEPT = {Kind.LEDGER, Kind.DECLARATION, Kind.KEPT, Kind.OPERATIONAL}


@pytest.fixture(scope="module")
def repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return make_repo(tmp_path_factory.mktemp("git") / "repo")


@pytest.fixture
def palace(tmp_path: Path, repo: Path) -> Built:
    return build_palace(tmp_path / "p", repo)


def launcher_for(b: Built, *, cache: Path | None = None,
                 embedder: CountingEmbedder | None = None) -> tuple[Launcher, list[Any]]:
    """The palace's launcher, its embedder factory recording each embedder it builds, and its run
    ledger opened at the first write, as `build_launcher` gives it."""
    made: list[Any] = []

    def factory(_cfg: Any) -> Any:
        e = embedder or CountingEmbedder()
        made.append(e)
        return e

    lau = Launcher(cfg=b.cfg, runs=LazyRunLedger(Path(b.cfg.paths.data_dir) / "runs.sqlite"),
                   repo_root=b.repo, embedder_factory=factory,
                   cache_root=cache or b.root.parent / "cache",
                   installed_plist=b.root / "no-agent.plist")
    return lau, made


def raw_files(b: Built) -> dict[str, bytes]:
    raw = Path(b.cfg.paths.raw_store)
    return {str(p.relative_to(raw)): p.read_bytes() for p in sorted(raw.rglob("*"))
            if p.is_file()}


def causal(b: Built) -> list[tuple[Any, ...]]:
    from tests.fixtures.lifecycle import sqlite_rows

    rows = sqlite_rows(Path(b.cfg.paths.data_dir) / "causal_edges.sqlite", wall=False)
    return sorted(r for t in rows.values() for r in t)


# ── the landing log, read back ──────────────────────────────────────────────────────────────


def landing_log(cfg: Any) -> dict[str, list[tuple[Any, ...]]]:
    """The catalog's landing log, read only: every chain's row and every row of the log, in
    order, each column as stored."""
    con = sqlite3.connect(f"file:{cfg.paths.vault_catalog}?mode=ro", uri=True)
    try:
        return {"chains": con.execute("SELECT * FROM landing_chains ORDER BY chain").fetchall(),
                "rows": con.execute("SELECT * FROM landings ORDER BY chain, seq").fetchall()}
    finally:
        con.close()


def chain_heads(cfg: Any) -> dict[int, tuple[int, bytes]]:
    """Each chain's head: its last position and that row's hash."""
    con = sqlite3.connect(f"file:{cfg.paths.vault_catalog}?mode=ro", uri=True)
    try:
        return {int(c): (int(s), bytes(h)) for c, s, h in con.execute(
            "SELECT chain, seq, hash FROM landings AS l WHERE seq = "
            "(SELECT max(seq) FROM landings WHERE chain = l.chain)")}
    finally:
        con.close()


def chains_verify(cfg: Any) -> bool:
    """Whether the log has a chain and every chain verifies (`LandingLog.verify`: the hashes and
    the commitments recomputed), read only. The check needs no secret."""
    from core.stores.landings import LandingLog

    con = sqlite3.connect(f"file:{cfg.paths.vault_catalog}?mode=ro", uri=True)
    try:
        log = LandingLog(con, lambda: b"")
        chains = log.all_chains()
        return bool(chains) and all(log.verify(c).ok for c in chains)
    finally:
        con.close()


def appended(before: dict[str, list[tuple[Any, ...]]],
             after: dict[str, list[tuple[Any, ...]]]) -> list[tuple[Any, ...]]:
    """The log's rows in `after` that `before` did not have, in order, once every chain and every
    row `before` had is found unchanged in `after`."""
    old = {(r[0], r[1]): r for r in before["rows"]}
    new = {(r[0], r[1]): r for r in after["rows"]}
    assert after["chains"] == before["chains"]
    assert all(new.get(k) == r for k, r in old.items())
    return [r for k, r in sorted(new.items()) if k not in old]


def without_log(cfg: Any) -> None:
    """The catalog as one written before the landing log is, as the corpus's still is: its rows
    and no log."""
    con = sqlite3.connect(cfg.paths.vault_catalog)
    try:
        con.executescript("DROP TABLE landings; DROP TABLE landing_chains;")
    finally:
        con.close()


# ── P1: the inventory is total ──────────────────────────────────────────────────────────────


def test_p1_every_store_a_palace_writes_is_in_exactly_one_class(palace: Built) -> None:
    assert unclassified(palace.cfg) == []
    names = [s.name for s in STORES]
    assert len(names) == len(set(names))
    paths = [s.path(palace.cfg) for s in STORES]
    assert len(paths) == len(set(paths)), "two entries name one path"


def test_p1_every_open_helper_path_is_in_the_table(palace: Built) -> None:
    """Each store an `open_*` helper opens lands at a path the table classifies."""
    from core.stores.agent_observations import open_agent_observation_store
    from core.stores.causal_edges import open_causal_edge_store
    from core.stores.chat_events import open_chat_event_store
    from core.stores.chat_retention import open_retention_ledger
    from core.stores.chatlog import open_chatlog_store
    from core.stores.code_observations import open_code_observation_store
    from core.stores.edges import open_edge_store
    from core.stores.lexical import lexical_path
    from core.stores.observation_history import open_observation_history_store
    from core.stores.reference_edges import open_reference_edge_store
    from core.stores.verdicts import open_verdict_store
    from core.stores.versions import open_version_store
    from core.verdict.dispositions import open_disposition_store
    from ops.lifecycle.inventory import classify

    cfg = palace.cfg
    opened: list[Any] = [open_agent_observation_store(cfg), open_causal_edge_store(cfg),
              open_chat_event_store(cfg), open_retention_ledger(cfg), open_chatlog_store(cfg),
              open_code_observation_store(cfg), open_edge_store(cfg),
              open_observation_history_store(cfg), open_reference_edge_store(cfg),
              open_verdict_store(cfg), open_version_store(cfg), open_disposition_store(cfg)]
    for store in opened:
        assert classify(cfg, Path(store.path)) is not None, store.path
    assert classify(cfg, lexical_path(cfg)) is not None


# ── P2 to P5, P8: a confirmed reset ─────────────────────────────────────────────────────────


def test_p2_p3_p5_p8_a_reset_keeps_every_ledger_and_the_rebuild_converges(
        palace: Built) -> None:
    b = palace
    for t in Path(b.cfg.ingestion.transcripts.transcripts_dir).iterdir():
        t.unlink()                      # P5: the transcripts are gone from their directory
    lau, made = launcher_for(b)
    before_kept, before_raw, before = dump(b.cfg, KEPT), raw_files(b), heads(b.cfg)
    before_atts = dump(b.cfg)["attestations.sqlite"]
    before_log, before_heads = landing_log(b.cfg), chain_heads(b.cfg)
    for name in ("derived.sqlite", "queue.sqlite", "run_ledger.sqlite", "claim_ops.sqlite",
                 "staging.sqlite", "verdicts.sqlite", "versions.sqlite", "chat_retention.sqlite",
                 "code_snapshots.sqlite", "reference_edges.sqlite", "attestations.sqlite"):
        assert any(before_kept[name].values()), f"the fixture writes no row in {name}"
    kinds = {r[2] for r in before_log["rows"]}
    assert {"genesis", "store", "horizon"} <= kinds, "the fixture's log has a genesis and landings"
    assert len(before_heads) > 1 and chains_verify(b.cfg)              # a chain for each class
    assert lau.reset(confirm=True) == 0
    assert raw_files(b) == before_raw                                   # P2: raw, byte for byte
    assert dump(b.cfg, KEPT) == before_kept                             # P2: every kept store
    assert dump(b.cfg)["attestations.sqlite"] == before_atts            # no ledger written
    assert landing_log(b.cfg) == before_log                             # P2: every log row, and
    assert chain_heads(b.cfg) == before_heads                           # each chain's head hash:
    assert chains_verify(b.cfg)                                         # the rebuild appends none
    after = heads(b.cfg)
    for name in before:
        assert after[name] == before[name], name                        # P3
    assert after["chatlog.sqlite"]["chat_utterances"]                  # P5: from raw alone
    assert made == []                                                   # P8: no embedder built
    assert not (Path(b.cfg.paths.data_dir) / "reset.pending").exists()


def test_p3_the_interpreted_edges_stay_and_the_authored_are_rebuilt(palace: Built) -> None:
    edges_path = Path(palace.cfg.paths.data_dir) / "edges.sqlite"
    con = sqlite3.connect(edges_path)
    interpreted = con.execute("SELECT * FROM edges WHERE provenance = 'interpreted'").fetchall()
    con.close()
    assert interpreted
    lau, _ = launcher_for(palace)
    assert lau.reset(confirm=True) == 0
    con = sqlite3.connect(edges_path)
    try:
        assert con.execute("SELECT * FROM edges WHERE provenance = 'interpreted'").fetchall() \
            == interpreted                                              # byte for byte, kept
        assert con.execute("SELECT count(*) FROM edges WHERE provenance = 'authored-solo'"
                           ).fetchone()[0] == 1
    finally:
        con.close()


def test_p4_a_reset_twice_is_the_reset_once_and_the_causal_edges_a_fresh_integration(
        palace: Built) -> None:
    b = palace
    lau, _ = launcher_for(b)
    log = landing_log(b.cfg)
    assert lau.reset(confirm=True) == 0
    once, once_causal, once_kept = heads(b.cfg), causal(b), dump(b.cfg, KEPT)
    assert lau.reset(confirm=True) == 0
    assert heads(b.cfg) == once and causal(b) == once_causal and dump(b.cfg, KEPT) == once_kept
    assert landing_log(b.cfg) == log                    # two resets append nothing to the log
    from core.integrator import build_integrator
    build_integrator(b.cfg).integrate(max_sessions=100)                 # a fresh pass adds none
    assert causal(b) == once_causal


def test_p3_the_atom_table_holds_exactly_what_the_rebuilt_rows_name(palace: Built) -> None:
    """The plane's occupancies are forgotten and rebuilt for the heads (§4.2, §4.4), and the atoms
    no rebuilt row holds are dropped last: a superseded version's occupancy and its atom go."""
    from core.stores.plane import OCC
    from core.stores.vectorstore import VectorStore, fingerprint_of
    from tests.fixtures.embedding import DIM

    def atoms() -> set[str]:
        return VectorStore(palace.cfg.paths.vector_store, dim=DIM,
                           embedder=fingerprint_of(palace.cfg)).plane.atoms.ids()

    def rows(current: int) -> list[tuple[str, str]]:
        con = sqlite3.connect(Path(palace.cfg.paths.vector_store) / "plane.sqlite")
        try:
            return [(str(p), str(a)) for t in OCC.values() for p, a in con.execute(
                f"SELECT source_path, atom_id FROM {t} WHERE current = ?", [current])]
        finally:
            con.close()

    superseded = rows(0)
    assert superseded, "the fixture holds a superseded version's occupancy"
    before = atoms()
    lau, _ = launcher_for(palace)
    assert lau.reset(confirm=True) == 0
    assert rows(0) == []                                    # the old relations are forgotten
    after = atoms()
    assert after == {a for _, a in rows(1)}                 # exactly what the rebuilt rows name
    assert before - after                                   # the superseded atom was dropped


def test_p3_a_lazy_backlog_is_left_to_the_embed_job(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """On a lazy instance, items landed without their vector stay so: the reset re-occupies only
    what the plane held, calls no embedder, and the dry run counts the backlog. A held note edited
    since it was embedded comes back at the version the plane held, not dropped."""
    from core.ingest.derive import drain

    cfg = instance_config(tmp_path / "lazy", None, lazy=True)
    stores = stores_for(cfg, CountingEmbedder())
    for i in range(3):
        (Path(cfg.ingestion.vault.path) / f"n{i}.md").write_text(f"note {i}, embedded later\n")
    assert perform(cfg, stores, "do sync_vault")["effects"] == {"landed": 3}
    assert drain(stores, max_items=1).items == 1            # one held, two waiting
    before = heads(cfg)
    made: list[Any] = []

    def factory(c: Any) -> CountingEmbedder:
        made.append(c)
        return CountingEmbedder()

    lau = Launcher(cfg=cfg, runs=RunLedger(tmp_path / "runs.sqlite"), repo_root=tmp_path,
                   embedder_factory=factory,
                   cache_root=tmp_path / "cache", installed_plist=tmp_path / "no.plist")
    assert lau.reset(confirm=False) == 0
    out = capsys.readouterr().out
    assert "re-occupies the 1 item(s)" in out and "2 item(s) of the plane's classes hold no " \
        "vector" in out and "the embedder is called for 0 atom(s)" in out
    assert lau.reset(confirm=True) == 0
    assert made == []
    assert heads(cfg)["plane.occupancies"] == before["plane.occupancies"]
    assert sum(len(v) for v in before["plane.occupancies"].values()) == 1

    # The held note is edited and landed again, not yet embedded: the plane holds its old version,
    # which is no longer the catalog's head. The reset rebuilds that version from raw, so the note
    # stays searchable as it was and its new version stays with the embed job.
    held_path = next(r[0] for rows in before["plane.occupancies"].values() for r in rows)
    (Path(cfg.ingestion.vault.path) / held_path).write_text("note edited, embedded later\n")
    assert perform(cfg, stores, "do sync_vault")["effects"] == {"landed": 1, "unchanged": 2}
    head = stores.catalog.get(held_path)
    assert head is not None and all(r[1] != head.digest
                                    for rows in before["plane.occupancies"].values()
                                    for r in rows)
    before = heads(cfg)
    assert lau.reset(confirm=False) == 0
    out = capsys.readouterr().out
    assert "re-occupies the 1 item(s) the plane holds current (1 of them at a version older " \
        "than the catalog's)" in out and "3 item(s) of the plane's classes hold no vector " \
        "for their current version" in out and "the embedder is called for 0 atom(s)" in out
    assert lau.reset(confirm=True) == 0
    out = capsys.readouterr().out
    assert "plane: 1 item(s)" in out and "0 atom(s) no rebuilt row holds dropped" in out
    assert made == []
    assert heads(cfg)["plane.occupancies"] == before["plane.occupancies"]
    assert heads(cfg)["plane.vectors"] == before["plane.vectors"]
    assert sum(len(v) for v in before["plane.occupancies"].values()) == 1


def test_p3_a_purged_transcript_is_skipped_and_the_reset_finishes(
        palace: Built, capsys: pytest.CaptureFixture[str]) -> None:
    """A purge is how raw content is erased, and a transcript has no catalog row, so a retained
    transcript can lose its raw object. The replay skips it and says so; the reset finishes, and
    the chat log comes back without that session."""
    from core.ingest.purge import purge_raw

    b = palace
    con = sqlite3.connect(Path(b.cfg.paths.data_dir) / "chat_retention.sqlite")
    held = [str(d) for d, f in con.execute("SELECT digest, file FROM retained ORDER BY seq")
            if f == "s-held"]
    con.close()
    assert len(held) == 2
    for digest in held:
        purge_raw(digest, raw=b.stores.raw, store=b.stores.plane, catalog=b.stores.catalog,
                  confirm=True)
    lau, _ = launcher_for(b)
    assert lau.reset(confirm=True) == 0
    assert "purged=2" in capsys.readouterr().out
    assert not (Path(b.cfg.paths.data_dir) / "reset.pending").exists()
    con = sqlite3.connect(Path(b.cfg.paths.data_dir) / "chatlog.sqlite")
    sessions = {str(r[0]) for r in con.execute("SELECT DISTINCT session_id FROM chat_utterances")}
    con.close()
    assert "s-plain" in sessions and "s-held" not in sessions
    assert lau.reset(confirm=True) == 0                     # and again, as a reset is


def test_p7_a_missing_commit_refuses_before_anything_is_cleared(tmp_path: Path) -> None:
    """A commit the commit ledger holds that the repository has since pruned: the re-projection
    could not read it, so the reset refuses with nothing written, rather than failing after the
    clearing and leaving the marker behind."""
    from tests.fixtures.lifecycle import git

    repo = make_repo(tmp_path / "git" / "repo")
    b = build_palace(tmp_path / "p", repo)
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    git(repo, "reflog", "expire", "--expire=now", "--all")
    git(repo, "gc", "-q", "--prune=now")
    lau, _ = launcher_for(b)
    _unchanged(b, lambda: lau.reset(confirm=True))
    assert not (Path(b.cfg.paths.data_dir) / "reset.pending").exists()


# ── P6: the dry run ─────────────────────────────────────────────────────────────────────────


def test_p6_the_dry_run_writes_nothing_and_names_every_store_it_would_clear(
        palace: Built, capsys: pytest.CaptureFixture[str]) -> None:
    lau, _ = launcher_for(palace)
    before, before_heads = dump(palace.cfg), heads(palace.cfg)
    assert lau.reset(confirm=False) == 0
    out = capsys.readouterr().out
    assert dump(palace.cfg) == before and heads(palace.cfg) == before_heads
    for s in rebuild.found(palace.cfg):
        assert s.name in out
    assert "DRY RUN" in out


def test_p6_the_dry_run_at_rest_creates_and_touches_no_file(palace: Built) -> None:
    """On an instance at rest, every store closed: the dry run reads each SQLite file, the plane's
    included, without creating or touching a file, asks the plane's geometry read only, and reads
    the run ledger read only, so nothing under the root changes, not even a modification time."""
    from tests.fixtures.lifecycle import close_stores

    lau, _ = launcher_for(palace)
    close_stores(palace)
    before = _files(palace.root)
    assert not [f for f in before if f.endswith(("-wal", "-shm"))], "the fixture is not at rest"
    assert lau.reset(confirm=False) == 0
    assert _files(palace.root) == before


# ── P7: the refusals ────────────────────────────────────────────────────────────────────────


def _unchanged(b: Built, act: Any) -> None:
    before, before_heads = dump(b.cfg), heads(b.cfg)
    assert act() == 1
    assert dump(b.cfg) == before and heads(b.cfg) == before_heads


def test_p7_a_live_run_refuses(palace: Built) -> None:
    lau, _ = launcher_for(palace)
    lau.runs.open_run(commit_sha="x", dirty=False, pid=os.getpid())
    _unchanged(palace, lambda: lau.reset(confirm=True))


def test_p7_the_lock_held_refuses(palace: Built) -> None:
    lau, _ = launcher_for(palace)
    lock = SupervisorLock(Path(palace.cfg.paths.data_dir) / "supervisor.lock")
    lock.acquire()
    try:
        _unchanged(palace, lambda: lau.reset(confirm=True))
    finally:
        lock.release()


def test_p7_a_changed_embedder_geometry_refuses(palace: Built) -> None:
    lau, _ = launcher_for(palace)
    lau.cfg = replace(palace.cfg, embedding=replace(palace.cfg.embedding, model="another-model"))
    _unchanged(palace, lambda: lau.reset(confirm=True))


def test_p7_a_derived_store_outside_the_data_directory_refuses_before_the_marker(
        palace: Built, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`derived_store` configured outside the data directory puts the dispositions beside it, where
    the clearing refuses to reach. The reset finds that before it writes anything, the marker
    included, so no writer is left refusing behind a marker every rerun would leave again."""
    import shutil

    lau, _ = launcher_for(palace)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    data = Path(palace.cfg.paths.data_dir)
    for name in ("derived.sqlite", "verdicts.sqlite", "verdict_dispositions.sqlite"):
        shutil.copy2(data / name, elsewhere / name)
    lau.cfg = replace(palace.cfg, paths=replace(palace.cfg.paths,
                                                derived_store=elsewhere / "derived.sqlite"))
    before = _files(elsewhere)
    for confirm in (True, True, False):
        _unchanged(palace, lambda c=confirm: lau.reset(confirm=c))
        assert not (data / "reset.pending").exists()
    assert "does not lie under the data directory" in capsys.readouterr().out
    assert _files(elsewhere) == before


# ── P17: the landing log through a reset and a destroy ──────────────────────────────────────


def test_p17_the_steps_that_open_the_catalog_are_the_ones_the_refusal_reads(
        palace: Built, monkeypatch: pytest.MonkeyPatch) -> None:
    """The refusal without the landing log's secret is read for the steps of `OPENS_CATALOG`
    alone, so those must be every step that opens the catalog: each step is run with the step's
    name recorded at each open, through the context or through `VaultCatalog` itself, and the
    clearing opens it never."""
    from core.stores.catalog import VaultCatalog

    current = ["the clearing"]
    opened: set[str] = set()
    real_context, real_init = rebuild.Context.catalog, VaultCatalog.__post_init__

    def context_catalog(self: Any) -> Any:
        opened.add(current[0])
        return real_context(self)

    def init(self: Any) -> None:
        opened.add(current[0])
        real_init(self)

    monkeypatch.setattr(rebuild.Context, "catalog", context_catalog)
    monkeypatch.setattr(VaultCatalog, "__post_init__", init)
    for name, step in list(rebuild.STEPS.items()):
        def named(ctx: Any, _name: str = name, _step: Any = step) -> str:
            current[0] = _name
            return str(_step(ctx))
        monkeypatch.setitem(rebuild.STEPS, name, named)
    assert {s.name for s in rebuild.found(palace.cfg)} == set(rebuild.STEPS)   # every step runs
    lau, _ = launcher_for(palace)
    assert lau.reset(confirm=True) == 0
    assert opened == rebuild.OPENS_CATALOG


def test_p17_a_reset_that_would_write_the_genesis_refuses_without_the_secret(
        palace: Built, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """A catalog with rows and no landing log, as one written before the log is: the rebuild's
    first open of it writes the log's genesis, which needs the secret. Without it the reset
    refuses, its dry run too, before anything is written, the log's empty tables included; with it
    the genesis is written at that open, the catalog's rows stay as they were and the log
    verifies."""
    from core.stores.landings import LANDING_LOG_KEY
    from tests.conftest import LANDING_LOG_TEST_KEY
    from tests.fixtures.lifecycle import sqlite_rows

    b = palace
    rows = sqlite_rows(Path(b.cfg.paths.vault_catalog))["vault_files"]
    without_log(b.cfg)
    assert rebuild.catalog_without_log(b.cfg) == len(rows) > 0
    before = heads(b.cfg)
    monkeypatch.delenv(LANDING_LOG_KEY)
    lau, _ = launcher_for(b)
    _unchanged(b, lambda: lau.reset(confirm=False))
    _unchanged(b, lambda: lau.reset(confirm=True))
    out = capsys.readouterr().out
    assert "no landing log yet" in out and f"get_secret({LANDING_LOG_KEY!r})" in out
    assert not (Path(b.cfg.paths.data_dir) / "reset.pending").exists()
    tables = sqlite_rows(Path(b.cfg.paths.vault_catalog))
    assert set(tables) == {"vault_files"} and tables["vault_files"] == rows
    monkeypatch.setenv(LANDING_LOG_KEY, LANDING_LOG_TEST_KEY)
    before_dry = dump(b.cfg)
    assert lau.reset(confirm=False) == 0
    assert "writes the log's genesis" in capsys.readouterr().out
    # with the secret at hand the dry run still writes nothing: no genesis, no log table
    assert dump(b.cfg) == before_dry
    assert set(sqlite_rows(Path(b.cfg.paths.vault_catalog))) == {"vault_files"}
    assert lau.reset(confirm=True) == 0
    assert sqlite_rows(Path(b.cfg.paths.vault_catalog))["vault_files"] == rows
    assert chains_verify(b.cfg) and heads(b.cfg) == before
    log = landing_log(b.cfg)["rows"]
    # the genesis: a `store` of every catalog row, and nothing a rebuild step appended
    assert sorted(r[4] for r in log if r[2] == "store") == sorted(r[0] for r in rows)
    assert {r[2] for r in log} <= {"genesis", "store", "retire", "move", "horizon"}


def _lexical_overlay(tmp_path: Path, name: str, root: Path, repo: Path) -> Path:
    """A named instance declared as `config/instances/code.toml` declares the code instance, under
    another id and root, reading the fixture's repository: no embedder, the repository landed
    lexically."""
    import json
    import tomllib

    declared = tomllib.loads(
        (Path(loader.REPO_ROOT) / "config" / "instances" / "code.toml").read_text())
    lines = ["[instance]", f'id = "{name}"', f'root = "{root}"', ""]
    for section, values in declared.items():
        if section == "instance":
            continue
        for title, table in ([(f"{section}.{k}", v) for k, v in values.items()]
                             if section == "ingestion" else [(section, values)]):
            lines.append(f"[{title}]")
            lines += [f"{k} = {json.dumps(v)}" for k, v in table.items() if k != "repositories"]
            lines.append("")
    lines += ["[[ingestion.code.repositories]]", f'name = "{REPO}"', f'path = "{repo}"',
              'ref = "main"', ""]
    overlay = tmp_path / f"{name}.toml"
    overlay.write_text("\n".join(lines))
    return overlay


def _log_values(cfg: Any) -> list[bytes]:
    """What of the landing log no cache may hold: each chain's secret half and key check, each
    row's key of its path, commitment and hash, and the suite's secret, as hex and as bytes."""
    from tests.conftest import LANDING_LOG_TEST_KEY

    con = sqlite3.connect(f"file:{cfg.paths.vault_catalog}?mode=ro", uri=True)
    try:
        out = [bytes(v) for row in con.execute("SELECT secret, key_check FROM landing_chains")
               for v in row]
        out += [bytes(v) for row in con.execute(
            "SELECT path_key, commitment, hash FROM landings") for v in row if v is not None]
    finally:
        con.close()
    return [*out, LANDING_LOG_TEST_KEY.encode(), bytes.fromhex(LANDING_LOG_TEST_KEY)]


def _cache_holds_nothing_of(cache_root: Path, values: list[bytes]) -> None:
    """No file of the cache holds one of `values`, and no SQLite file of it holds a table of the
    catalog's file: the map or the landing log."""
    files = [p for p in cache_root.rglob("*") if p.is_file()]
    assert files
    for p in files:
        data = p.read_bytes()
        assert not any(v in data for v in values), p
        if data.startswith(b"SQLite format 3"):
            con = sqlite3.connect(f"file:{p}?immutable=1", uri=True)
            try:
                tables = {str(r[0]) for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'")}
            finally:
                con.close()
            assert not tables & {"vault_files", "landing_chains", "landings"}, p


def test_p17_a_named_instance_resets_with_its_own_item_and_destroys_with_none(
        tmp_path: Path, repo: Path, home: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Under a named instance, loaded as a process loads it (`MIND_PALACE_OVERLAY`), the landing
    log's secret is the instance's own item, `<id>.landing-log-key`. A reset of a catalog with a
    log needs no secret; one whose first open writes the genesis needs that item, and the default
    instance's does not serve. A destroy needs none, leaves nothing of the log in the cache, and
    names the item among those it leaves for the owner."""
    from core.stores.landings import LANDING_LOG_KEY
    from tests.conftest import LANDING_LOG_TEST_KEY

    root = home / ".mind-palace" / "instances" / "t"
    monkeypatch.setenv(loader.OVERLAY_ENV, str(_lexical_overlay(tmp_path, "t", root, repo)))
    loader.get_config.cache_clear()
    cfg = loader.get_config()
    item = cfg.instance.secret(LANDING_LOG_KEY)
    assert cfg.instance.named and cfg.instance.root == root and item == "t.landing-log-key"
    monkeypatch.setenv(item, LANDING_LOG_TEST_KEY)
    cache_root = home / ".mind-palace" / "cache"
    Path(cfg.paths.data_dir).mkdir(parents=True)
    lau = Launcher(cfg=cfg, runs=RunLedger(Path(cfg.paths.data_dir) / "runs.sqlite"),
                   repo_root=repo, cache_root=cache_root,
                   launchd_label=cfg.instance.label("palace"),
                   installed_plist=tmp_path / "no-agent.plist")
    assert lau.repo_sync_now() == 0
    log = landing_log(cfg)
    assert log["rows"] and chains_verify(cfg)
    # a catalog with its log: no step appends to it, so the reset needs no secret at all
    monkeypatch.delenv(item)
    monkeypatch.delenv(LANDING_LOG_KEY)
    assert lau.reset(confirm=True) == 0
    assert landing_log(cfg) == log
    # a catalog without a log: the reset's first open writes the genesis, keyed by the item
    without_log(cfg)
    monkeypatch.setenv(LANDING_LOG_KEY, LANDING_LOG_TEST_KEY)        # the default's, not t's
    before = dump(cfg)
    assert lau.reset(confirm=True) == 1
    assert repr(item) in capsys.readouterr().out
    assert dump(cfg) == before
    monkeypatch.setenv(item, LANDING_LOG_TEST_KEY)
    assert lau.reset(confirm=True) == 0
    assert chains_verify(cfg)
    values = _log_values(cfg)
    # a destroy reads the catalog read only and removes it whole: no secret, the dry run included
    monkeypatch.delenv(item)
    monkeypatch.delenv(LANDING_LOG_KEY)
    capsys.readouterr()
    assert lau.destroy(confirm=False) == 0
    assert item in capsys.readouterr().out                 # left for the owner, and named
    assert lau.destroy(confirm=True) == 0
    assert not root.exists()
    _cache_holds_nothing_of(cache_root, values)


# ── P9: an interrupted reset finishes ───────────────────────────────────────────────────────


@pytest.mark.parametrize("step", sorted(rebuild.STEPS))
def test_p9_a_reset_interrupted_at_any_step_leaves_the_marker_and_finishes(
        palace: Built, step: str, monkeypatch: pytest.MonkeyPatch) -> None:
    b = palace
    before, log = heads(b.cfg), landing_log(b.cfg)
    lau, _ = launcher_for(b)

    def boom(_ctx: Any) -> str:
        raise RuntimeError(f"injected at {step}")

    monkeypatch.setitem(rebuild.STEPS, step, boom)
    if step not in {s.name for s in rebuild.found(b.cfg)}:
        pytest.skip(f"the fixture has no {step}")
    with pytest.raises(RuntimeError, match="injected"):
        lau.reset(confirm=True)
    assert (Path(b.cfg.paths.data_dir) / "reset.pending").exists()
    assert lau.start(max_ticks=1) == 1                                  # the daemon refuses
    assert lau.repo_sync_now() == 1                                     # and a writer refuses
    monkeypatch.undo()
    assert lau.reset(confirm=True) == 0
    assert not (Path(b.cfg.paths.data_dir) / "reset.pending").exists()
    assert heads(b.cfg) == before and landing_log(b.cfg) == log


def _interrupt_at_the_plane(lau: Launcher, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_ctx: Any) -> str:
        raise RuntimeError("injected at the plane step")

    monkeypatch.setitem(rebuild.STEPS, "vectors.lance", boom)
    with pytest.raises(RuntimeError, match="injected"):
        lau.reset(confirm=True)
    monkeypatch.undo()


def test_p9_a_purge_while_a_reset_is_pending_leaves_it_to_finish(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """The marker names the versions the plane held. A purge between the interrupted run and the
    rerun (the core's `purge_raw`; `scripts/purge_raw.py` itself refuses while the marker stands)
    erases one of them: the rerun skips it and says so, as the chat log's replay skips a purged
    transcript, and finishes, the erasure standing."""
    from core.ingest.derive import drain
    from core.ingest.purge import purge_raw

    cfg = instance_config(tmp_path / "lazy", None, lazy=True)
    stores = stores_for(cfg, CountingEmbedder())
    for i in range(3):
        (Path(cfg.ingestion.vault.path) / f"n{i}.md").write_text(f"note {i}, embedded later\n")
    perform(cfg, stores, "do sync_vault")
    drain(stores, max_items=1)
    held_path, old = next((r[0], r[1]) for rows in heads(cfg)["plane.occupancies"].values()
                          for r in rows)
    (Path(cfg.ingestion.vault.path) / held_path).write_text("note edited, embedded later\n")
    perform(cfg, stores, "do sync_vault")                   # the plane holds the old version
    lau = Launcher(cfg=cfg, runs=LazyRunLedger(tmp_path / "runs.sqlite"), repo_root=tmp_path,
                   embedder_factory=lambda _c: CountingEmbedder(),
                   cache_root=tmp_path / "cache", installed_plist=tmp_path / "no.plist")
    _interrupt_at_the_plane(lau, monkeypatch)
    purge_raw(old, raw=stores.raw, store=stores.plane, catalog=stores.catalog, confirm=True)
    assert not stores.raw.exists(old)
    capsys.readouterr()
    assert lau.reset(confirm=True) == 0
    assert "1 held version(s) whose raw object a purge erased skipped" in capsys.readouterr().out
    assert not (Path(cfg.paths.data_dir) / "reset.pending").exists()
    assert not any(heads(cfg)["plane.occupancies"].values())       # the erasure stands


def test_p9_a_changed_embedder_while_a_reset_is_pending_names_the_way_out(
        palace: Built, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """`reembed` refuses while a reset is pending and names the reset; the reset refuses a changed
    embedder. So the reset's refusal names the one way out: finish the reset under the embedder the
    plane was built with, then change the embedder."""
    lau, _ = launcher_for(palace)
    _interrupt_at_the_plane(lau, monkeypatch)
    capsys.readouterr()
    lau.cfg = replace(palace.cfg, embedding=replace(palace.cfg.embedding, model="another-model"))
    assert lau.reset(confirm=True) == 1
    out = capsys.readouterr().out
    assert "a reset of this instance is pending" in out and "restore that embedder" in out
    assert lau.reembed_now(confirm=True) == 1
    assert "`palace reset --confirm` again" in capsys.readouterr().out
    lau.cfg = palace.cfg                                    # restored: the reset finishes
    assert lau.reset(confirm=True) == 0
    assert not (Path(palace.cfg.paths.data_dir) / "reset.pending").exists()


# ── the scripts that write refuse while a reset is pending ──────────────────────────────────

#: Each script that lands into an instance or writes a store the reset rebuilds, with the
#: arguments of its writing run.
WRITER_SCRIPTS = (("purge_raw", ["0" * 64, "--confirm"]), ("ingest_self_knowledge", None),
                  ("mint_ids", ["--confirm"]), ("migrate_chunk_keys", ["--apply"]),
                  ("migrate_provenance_split", ["--apply"]), ("reembed_bodyonly", ["--confirm"]),
                  ("watch", None), ("corpus", ["embed"]))


@pytest.mark.parametrize(("script", "argv"), WRITER_SCRIPTS, ids=[s for s, _ in WRITER_SCRIPTS])
def test_p9_every_writing_script_refuses_while_a_reset_is_pending(
        script: str, argv: list[str] | None, tmp_path: Path, repo: Path, home: Path,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """LCF-5: the marker refuses every writer, the scripts as the launcher's verbs, and each
    refuses before it opens anything, so the instance holds nothing but the marker after it."""
    import argparse
    import importlib

    root = home / ".mind-palace" / "instances" / "t"
    monkeypatch.setenv(loader.OVERLAY_ENV, str(_lexical_overlay(tmp_path, "t", root, repo)))
    loader.get_config.cache_clear()
    cfg = loader.get_config()
    Path(cfg.paths.data_dir).mkdir(parents=True)
    (Path(cfg.paths.data_dir) / "reset.pending").write_text('{"stores": []}')
    module = importlib.import_module(f"scripts.{script}")
    monkeypatch.setattr(module, "seal", lambda: None, raising=False)    # process-wide otherwise
    if script == "corpus":
        monkeypatch.setattr(module, "corpus_config", lambda: cfg)
        with pytest.raises(SystemExit) as refused:
            module.cmd_embed(argparse.Namespace())
        out = str(refused.value.code)
    else:
        assert (module.main() if argv is None else module.main(argv)) == 1
        out = capsys.readouterr().out
    assert "a reset of this instance is pending" in out
    assert sorted(str(p.relative_to(root)) for p in root.rglob("*")) == \
        ["data", "data/reset.pending"]


# ── the chat sensor's retention ledger ──────────────────────────────────────────────────────


def test_the_retention_ledger_seeds_from_a_chat_log_that_predates_it(palace: Built) -> None:
    """An instance whose chat log was written before the ledger existed: the ledger is seeded
    from the chat log, and its replay gives back the same chat log."""
    data = Path(palace.cfg.paths.data_dir)
    before = heads(palace.cfg)["chatlog.sqlite"]
    (data / "chat_retention.sqlite").unlink()
    lau, _ = launcher_for(palace)
    assert lau.reset(confirm=True) == 0
    assert heads(palace.cfg)["chatlog.sqlite"] == before


# ── P10: a sync heals a stale lexical index ─────────────────────────────────────────────────


def test_p10_repo_sync_lands_where_a_stale_index_refused(tmp_path: Path) -> None:
    """The 2026-11-11 state: the code instance's index made by the legacy tokenizer, so every
    repository sync stopped at `LexicalStore.land_many` (`TokenizerMismatch`). The sync now
    re-derives the index in the writer before it lands."""
    from core.ingest import ingress
    from core.ingest.lexical import LEGACY, Tokenizer, TokenizerMismatch
    from core.stores.lexical import LexicalStore, lexical_path

    repo = make_repo(tmp_path / "repo")
    cfg = instance_config(tmp_path / "lite", repo, embedding=False)
    stores = ingress.build_stores(cfg)
    stores.lexical = LexicalStore(lexical_path(cfg), tokenizer=LEGACY)
    assert ingress.run_library(cfg, "sync_repository", {"name": REPO}, stores=stores,
                               refresh=False)["effects"] == {"landed": 3}
    (repo / "pkg" / "late.py").write_text("def late():\n    return 'landed after the change'\n")
    commit(repo, "three")
    current = LexicalStore(lexical_path(cfg), tokenizer=Tokenizer())
    assert current.stale
    with pytest.raises(TokenizerMismatch):          # the stuck state, reproduced
        current.land(source_path="x", digest="d", provenance="code", title="x", chunks=())
    lau = Launcher(cfg=cfg, runs=RunLedger(tmp_path / "runs.sqlite"), repo_root=repo)
    log = landing_log(cfg)
    assert lau.repo_sync_now() == 0
    healed = LexicalStore(lexical_path(cfg))
    assert not healed.stale and healed.recorded_tokenizer() == Tokenizer().identity
    paths = {p for p, _ in healed.landed_versions()}
    assert f"code/{REPO}/pkg/late.py" in paths and len(paths) == 4
    # the heal re-derived every item's units and appended nothing: the one new row of the log is
    # the new file's landing
    assert [(r[2], r[4]) for r in appended(log, landing_log(cfg))] == \
        [("store", f"code/{REPO}/pkg/late.py")]


def test_p10_the_writer_heals_a_stale_index_for_a_vault_plan(tmp_path: Path) -> None:
    from core.ingest.lexical import LEGACY, Tokenizer
    from core.stores.lexical import LexicalStore, lexical_path

    cfg = instance_config(tmp_path / "v", None, lazy=True)
    emb = CountingEmbedder()
    stores = stores_for(cfg, emb, lexical=LexicalStore(lexical_path(cfg), tokenizer=LEGACY))
    (Path(cfg.ingestion.vault.path) / "one.md").write_text("one note\n")
    assert perform(cfg, stores, "do sync_vault")["effects"] == {"landed": 1}
    (Path(cfg.ingestion.vault.path) / "two.md").write_text("a second note\n")
    stores.lexical = LexicalStore(lexical_path(cfg), tokenizer=Tokenizer())
    assert stores.lexical.stale
    log = landing_log(cfg)
    receipt = perform(cfg, stores, "do sync_vault")
    assert receipt["effects"].get("landed") == 1 and "rederive" in receipt["timing"]
    assert not stores.lexical.stale and len(stores.lexical.landed_versions()) == 2
    new = appended(log, landing_log(cfg))                   # the landing's row, none of the heal's
    assert len(new) == 1 and new[0][2] == "store" and str(new[0][4]).endswith("two.md")


# ── P11, P12: destroy ───────────────────────────────────────────────────────────────────────


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    return h


@pytest.fixture
def named(tmp_path: Path, repo: Path, home: Path) -> Built:
    return build_palace(home / ".mind-palace" / "instances" / "t", repo, named="t")


def test_p11_destroy_refuses_the_default_instance(palace: Built) -> None:
    lau, _ = launcher_for(palace)
    _unchanged(palace, lambda: lau.destroy(confirm=True))


def test_p11_destroy_refuses_a_live_run_and_the_lock_held(named: Built, home: Path) -> None:
    lau, _ = launcher_for(named, cache=home / ".mind-palace" / "cache")
    lock = SupervisorLock(Path(named.cfg.paths.data_dir) / "supervisor.lock")
    lock.acquire()
    try:
        _unchanged(named, lambda: lau.destroy(confirm=True))
    finally:
        lock.release()
    lau.runs.open_run(commit_sha="x", dirty=False, pid=os.getpid())
    _unchanged(named, lambda: lau.destroy(confirm=True))
    assert not (home / ".mind-palace" / "cache").exists()


def test_p11_destroy_refuses_a_root_that_holds_the_cache_or_links_out(
        named: Built, home: Path, tmp_path: Path) -> None:
    lau, _ = launcher_for(named, cache=named.root / "cache")
    _unchanged(named, lambda: lau.destroy(confirm=True))                # the root holds it
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("not the instance's")
    (named.root / "link").symlink_to(outside)
    lau, _ = launcher_for(named, cache=home / ".mind-palace" / "cache")
    _unchanged(named, lambda: lau.destroy(confirm=True))                # a link out of the root
    assert (outside / "keep.txt").exists()


def test_p11_destroy_refuses_a_root_in_a_working_tree_or_the_home_root(
        tmp_path: Path, repo: Path, home: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / ".git").mkdir()
    b = build_palace(tree / "inst", repo, named="w")
    lau, _ = launcher_for(b, cache=home / ".mind-palace" / "cache")
    _unchanged(b, lambda: lau.destroy(confirm=True))
    from core.stores.cache import Cache
    from ops.lifecycle import destroy as d

    at_home = replace(b.cfg, instance=loader.InstanceConfig("h", home=home / ".mind-palace"))
    assert any("home root" in w for w in d.refusals(
        at_home, Cache(tmp_path / "elsewhere"), installed=False, home=home / ".mind-palace"))


def test_p11_destroy_refuses_an_installed_agent(named: Built, home: Path) -> None:
    lau, _ = launcher_for(named, cache=home / ".mind-palace" / "cache")
    lau.installed_plist.write_text("<plist/>")
    _unchanged(named, lambda: lau.destroy(confirm=True))


def _files(root: Path) -> dict[str, tuple[int, int, bool]]:
    """Every entry under `root`, directories included: its size, its mtime and whether it is a
    directory, so a dry run that creates, removes or touches anything is seen."""
    out: dict[str, tuple[int, int, bool]] = {}
    for p in [root, *sorted(root.rglob("*"))]:
        st = p.lstat()
        out[str(p.relative_to(root))] = (st.st_size if p.is_file() else 0, st.st_mtime_ns,
                                          p.is_dir())
    return out


def test_p11_the_destroy_dry_run_writes_nothing(
        named: Built, home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """On an instance at rest: its stores closed, so no SQLite file has a `-wal` or `-shm` beside
    it, and a reader that opened one `mode=ro` would create them; the run ledger is read only. The
    dry run names the sources it leaves and those it removes with the root."""
    from tests.fixtures.lifecycle import close_stores

    lau, _ = launcher_for(named, cache=home / ".mind-palace" / "cache")
    before = dump(named.cfg)
    close_stores(named)
    before_files = _files(home)
    assert [f for f in before_files if f.endswith(("-wal", "-shm"))] == []
    assert lau.destroy(confirm=False) == 0
    # the tree first: a read of a WAL database (the dump's own) creates its -wal and -shm
    assert _files(home) == before_files                 # no file added, removed or touched
    assert dump(named.cfg) == before and not (home / ".mind-palace" / "cache").exists()
    assert not (Path(named.cfg.paths.data_dir) / "supervisor.lock").exists()
    out = capsys.readouterr().out
    left = [line for line in out.splitlines() if line.strip().startswith("left:")]
    assert len(left) == 1
    for kept in (named.cfg.ingestion.vault.path, named.cfg.ingestion.transcripts.transcripts_dir,
                 named.repo):
        assert str(kept) in left[0]
    assert str(named.cfg.ingestion.corpus.root) not in left[0]       # inside the root: removed
    assert f"sources inside the root, removed with it: {named.cfg.ingestion.corpus.root}" in out


def _palace(env: dict[str, str], *argv: str) -> Any:
    """`scripts/palace.py` in a process of its own, as a shell runs it."""
    import subprocess
    import sys

    return subprocess.run([sys.executable, str(Path(loader.REPO_ROOT) / "scripts" / "palace.py"),
                           *argv], capture_output=True, text=True, timeout=300, env=env)


def test_p11_the_commands_dry_runs_create_and_touch_no_file(
        tmp_path: Path, repo: Path, home: Path) -> None:
    """`palace destroy`, `palace reset` and `palace cache fill`, each run as a shell runs it under
    a named instance's overlay, on an instance at rest whose catalog has an empty `-wal` beside
    it, as a `mode=ro` reader leaves it with a `-shm` (the corpus's catalog has both): no file
    under the home is created, removed or touched, the launcher's run ledger included. On a root
    that does not exist, none of the three creates it."""
    from tests.conftest import LANDING_LOG_TEST_KEY

    root = home / ".mind-palace" / "instances" / "t"
    env = {**os.environ, "HOME": str(home),
           loader.OVERLAY_ENV: str(_lexical_overlay(tmp_path, "t", root, repo))}
    landed = _palace({**env, "t.landing-log-key": LANDING_LOG_TEST_KEY}, "repo-sync")
    assert landed.returncode == 0, landed.stdout + landed.stderr
    for db in root.rglob("*.sqlite"):           # at rest: each database checkpointed and closed
        con = sqlite3.connect(db)
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.close()
    catalog = root / "data" / "vault_catalog.sqlite"
    con = sqlite3.connect(f"file:{catalog}?mode=ro", uri=True)   # it leaves an empty -wal, a -shm
    con.execute("SELECT count(*) FROM vault_files").fetchone()
    con.close()
    wal = Path(f"{catalog}-wal")
    if not wal.exists():                # a platform whose reader leaves none: one left by hand
        wal.write_bytes(b"")
    assert wal.stat().st_size == 0
    before = _files(home)
    for argv in (["destroy"], ["reset"], ["cache", "fill"]):
        done = _palace(env, *argv)
        assert done.returncode == 0 and "DRY RUN" in done.stdout, (argv, done.stdout, done.stderr)
        assert _files(home) == before, argv
    absent = home / ".mind-palace" / "instances" / "u"
    env[loader.OVERLAY_ENV] = str(_lexical_overlay(tmp_path, "u", absent, repo))
    for argv in (["destroy"], ["reset"], ["cache", "fill"]):
        done = _palace(env, *argv)
        assert done.returncode == 0 and "DRY RUN" in done.stdout, (argv, done.stdout, done.stderr)
        assert not absent.exists(), argv
        assert argv != ["destroy"] or "it does not exist" in done.stdout


def test_p11_destroy_refuses_a_root_that_holds_a_checkout_or_foreign_files(
        tmp_path: Path, repo: Path, home: Path) -> None:
    """A root may hold only the instance's own state: a git repository below it, or a file no
    namespace of the instance names, refuses, and nothing under the root is removed."""
    from tests.fixtures.lifecycle import git

    b = build_palace(home / "work", repo, named="w")
    lau, _ = launcher_for(b, cache=home / ".mind-palace" / "cache")
    (b.root / "notes-of-mine.txt").write_text("not the instance's")
    _unchanged(b, lambda: lau.destroy(confirm=True))
    (b.root / "notes-of-mine.txt").unlink()
    project = b.root / "data" / "logs" / "someproject"
    project.mkdir(parents=True)
    git(project, "init", "-q")
    _unchanged(b, lambda: lau.destroy(confirm=True))
    assert (project / ".git").exists()
    import shutil

    shutil.rmtree(project)
    assert lau.destroy(confirm=False) == 0              # its own state alone: a dry run proceeds


def test_p11_destroy_refuses_a_root_around_another_instance(
        tmp_path: Path, repo: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A root that holds other instances' roots, whether they are declared on the host or are
    only directories it does not own, refuses."""
    from core.stores.cache import Cache
    from ops.lifecycle import destroy as d

    b = build_palace(home / ".mind-palace" / "instances" / "t", repo, named="t")
    around = instance_config(home / ".mind-palace" / "instances", None, named="u",
                             sources=tmp_path / "u-read")
    why = d.refusals(around, Cache(home / ".mind-palace" / "cache"), installed=False)
    assert any("not the instance's own state" in w and "t/" in w for w in why), why
    monkeypatch.setattr(d, "other_roots", lambda cfg: [
        ("'corpus'", home / ".mind-palace" / "instances" / "corpus", True)])
    why = d.refusals(around, Cache(home / ".mind-palace" / "cache"), installed=False)
    assert any("'corpus'" in w for w in why), why
    assert d.refusals(b.cfg, Cache(home / ".mind-palace" / "cache"), installed=False) == []


def test_p11_destroy_and_fill_refuse_a_changed_embedder_geometry(
        named: Built, home: Path) -> None:
    """After a change of model in the overlay and before a re-embed, the plane holds the old
    model's vectors: filing them under the new model's key would mix two geometries."""
    from core.stores.cache import Cache
    from core.stores.plane import GeometryMismatch
    from ops.lifecycle import destroy as d

    cache_root = home / ".mind-palace" / "cache"
    lau, _ = launcher_for(named, cache=cache_root)
    lau.cfg = replace(named.cfg, embedding=replace(named.cfg.embedding, model="another-model"))
    _unchanged(named, lambda: lau.destroy(confirm=True))
    _unchanged(named, lambda: lau.destroy(confirm=False))
    _unchanged(named, lambda: lau.cache_fill(confirm=True))
    with pytest.raises(GeometryMismatch):
        d.plan_fill(lau.cfg, Cache(cache_root))
    assert not cache_root.exists()


def _catalog(b: Built) -> list[tuple[str, str, str]]:
    con = sqlite3.connect(f"file:{b.cfg.paths.vault_catalog}?mode=ro", uri=True)
    try:
        return [(str(p), str(d), str(c)) for p, d, c in con.execute(
            "SELECT source_path, digest, provenance FROM vault_files")]
    finally:
        con.close()


def _occupancies(b: Built) -> list[tuple[str, str]]:
    from core.stores.plane import OCC

    con = sqlite3.connect(f"file:{Path(b.cfg.paths.vector_store) / 'plane.sqlite'}?mode=ro",
                          uri=True)
    try:
        return [(str(p), str(a)) for t in OCC.values()
                for p, a in con.execute(f"SELECT source_path, atom_id FROM {t}")]
    finally:
        con.close()


def _land_by_hand(b: Built, rows: list[tuple[str, Any, bytes]]) -> dict[str, str]:
    """Raw objects and catalog rows the fixture's lanes do not write: {path: digest}."""
    out: dict[str, str] = {}
    for path, provenance, text in rows:
        digest, _ = b.stores.raw.add(text)
        b.stores.catalog.record(path, digest, path, provenance=provenance)
        out[path] = digest
    return out


def test_p12_destroy_keeps_exactly_the_cache_classes(named: Built, home: Path) -> None:
    """The expectations are written from the fixture's own lanes, by path and class, not by the
    selection the code makes: the corpus stream's items, the repository's files and one curated
    item enter; the notes, a dialogue turn, a model's reply in the dialogue, an inbox item and the
    transcripts do not."""
    from core.kernel.provenance import Provenance
    from core.stores.cache import Cache, key_of
    from ops.lifecycle import destroy as d

    b = named
    private_rows = _land_by_hand(b, [
        ("dialogue/openwebui/c1/m1", Provenance.AUTHORED_DIALOGUE, b"a dialogue turn, private"),
        ("dialogue/openwebui/c1/m2", Provenance.OBSERVED, b"the model's reply, private"),
        ("dialogue/inbox/c/1/owner", Provenance.AUTHORED_DIALOGUE, b"an inbox item, private")])
    curated = _land_by_hand(b, [("curated/ref-1", Provenance.CURATED, b"a curated reference")])
    catalog, occ = _catalog(b), _occupancies(b)
    notes = {d_ for p, d_, c in catalog if c == Provenance.AUTHORED_SOLO.value}
    corpus = {d_ for p, d_, c in catalog if p.startswith(f"corpus/{CORPUS_SOURCE}/")
              and c == Provenance.OBSERVED.value}
    code = {d_ for p, d_, c in catalog if p.startswith(f"code/{REPO}/")}
    assert notes and corpus and code
    retained = sqlite3.connect(Path(b.cfg.paths.data_dir) / "chat_retention.sqlite")
    transcripts = {str(r[0]) for r in retained.execute("SELECT digest FROM retained")}
    retained.close()
    stream = b.cfg.ingestion.corpus.root / CORPUS_SOURCE
    downloaded = set(d._source_files(stream))
    assert any(f.startswith("stream/") and f != "stream/manifest.json" for f in downloaded)
    cache_root = home / ".mind-palace" / "cache"
    log_values = _log_values(b.cfg)
    lau, _ = launcher_for(b, cache=cache_root)
    assert lau.destroy(confirm=True) == 0
    assert not b.root.exists()                  # the catalog's file with it, the landing log in it
    _cache_holds_nothing_of(cache_root, log_values)
    cache = Cache(cache_root)
    assert cache.raw_digests() == corpus | code | set(curated.values())
    assert not cache.raw_digests() & (notes | set(private_rows.values()) | transcripts)
    open_paths = {p for p, _, _ in catalog
                  if p.startswith((f"corpus/{CORPUS_SOURCE}/", f"code/{REPO}/"))}
    want = {a for p, a in occ if p in open_paths}
    only_private = {a for p, a in occ if p not in open_paths} - want
    key = key_of(b.cfg)[0]
    assert cache.vector_ids(key) == want and want
    assert not cache.vector_ids(key) & only_private
    assert {m["file"] for m in cache.source_manifest(CORPUS_SOURCE)} == downloaded
    assert not any("cursor" in m["file"] or "state" in m["file"]
                   for m in cache.source_manifest(CORPUS_SOURCE))
    assert not stream.exists()


def test_p12_a_source_file_that_is_a_link_enters_no_cache(
        named: Built, home: Path, tmp_path: Path) -> None:
    """The fill takes a source's stream files by name, so a name that is a link would carry other
    bytes in: a symbolic link to the catalog's file inside the root, a hard link to it, or a link
    to a note outside the root. A destroy and a fill refuse each, writing nothing, and the cache
    itself refuses to store one."""
    import json
    import os

    from core.stores.cache import Cache

    b = named
    base = Path(b.cfg.ingestion.corpus.root) / CORPUS_SOURCE
    manifest = json.loads((base / "stream" / "manifest.json").read_text())
    part = base / "stream" / str(manifest["parts"][0]["file"])
    original = part.read_bytes()
    catalog = Path(b.cfg.paths.vault_catalog)
    note = Path(b.cfg.ingestion.vault.path) / "alpha.md"
    cache_root = home / ".mind-palace" / "cache"
    lau, _ = launcher_for(b, cache=cache_root)
    for make in (lambda: part.symlink_to(catalog), lambda: os.link(catalog, part),
                 lambda: part.symlink_to(note)):
        part.unlink()
        make()
        _unchanged(b, lambda: lau.destroy(confirm=True))
        _unchanged(b, lambda: lau.destroy(confirm=False))
        _unchanged(b, lambda: lau.cache_fill(confirm=True))
        assert not cache_root.exists() and b.root.exists()
        with pytest.raises(ValueError, match="not a plain file"):
            Cache(tmp_path / "direct").put_source_files(CORPUS_SOURCE, base,
                                                        [str(part.relative_to(base))])
        assert not (tmp_path / "direct").exists()
    part.unlink()
    part.write_bytes(original)
    assert lau.destroy(confirm=False) == 0                  # a plain stream again: it proceeds


def test_a_fill_streams_its_vectors_in_batches(
        palace: Built, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The plan counts the atoms and holds no vector; the fill reads them a batch at a time."""
    from core.stores.cache import Cache, key_of
    from ops.lifecycle import destroy as d

    monkeypatch.setattr(d, "FILL_BATCH", 2)
    cache = Cache(tmp_path / "cache")
    plan = d.plan_fill(palace.cfg, cache)
    assert len(plan.atoms) > 2 and not hasattr(plan, "vectors")
    report = d.fill(palace.cfg, cache, plan)
    assert report.vectors == len(plan.atoms)
    assert cache.vector_ids(key_of(palace.cfg)[0]) == set(plan.atoms)


def test_the_cache_records_its_uses_to_the_day(tmp_path: Path) -> None:
    import hashlib

    from core.stores.cache import Cache

    cache = Cache(tmp_path / "cache")
    data = b"an open object"
    cache.put_raw(hashlib.sha256(data).hexdigest(), data)
    cache.forget("0" * 64, [])
    for name, table in (("uses.sqlite", "SELECT last FROM uses"),
                        ("purged.sqlite", "SELECT at FROM purged")):
        con = sqlite3.connect(tmp_path / "cache" / name)
        times = [float(r[0]) for r in con.execute(table)]
        con.close()
        assert times and all(t % 86400 == 0 for t in times), name


# ── P13, P14: reuse ─────────────────────────────────────────────────────────────────────────


def _filled_cache(b: Built, root: Path) -> Any:
    from core.stores.cache import Cache
    from ops.lifecycle import destroy as d

    cache = Cache(root)
    d.fill(b.cfg, cache, d.plan_fill(b.cfg, cache))
    return cache


def test_p13_a_cached_vector_is_reused_without_the_embedder(
        palace: Built, tmp_path: Path) -> None:
    from core.ingest.derive import drain
    from core.stores.cache import key_of, with_cache
    from tests.fixtures.lifecycle import fill_stream

    cache = _filled_cache(palace, tmp_path / "cache")
    key = key_of(palace.cfg)[0]
    for model, calls in ((None, 0), ("another-model", None)):
        cfg = instance_config(tmp_path / f"new-{model}", None, lazy=True, model=model)
        emb = CountingEmbedder()
        stores = with_cache(stores_for(cfg, emb), cfg, cache)
        fill_stream(cfg)
        perform(cfg, stores, f'do sync_corpus(name: "{CORPUS_SOURCE}", batch: 10)',
                role="corpus", batch=True)
        report = drain(stores)
        if calls == 0:
            assert emb.calls == 0 and report.cached > 0 and report.embedded == 0
            atoms = sorted(cache.vector_ids(key))
            mine = stores.plane.plane.atoms.payload(atoms)
            assert {a: list(v) for a, (_t, v) in mine.items()} == cache.vectors(key, atoms)
        else:
            assert emb.calls > 0 and report.cached == 0


def test_p13_a_cached_vector_of_another_width_is_not_landed(tmp_path: Path) -> None:
    """A cache entry under the instance's key whose width is not the plane's is never landed
    (§10 item 7): the drain embeds the atom instead."""
    from core.ingest.derive import drain
    from core.kernel.ingest.pipeline import derive_chunks
    from core.stores.cache import Cache, key_of, with_cache
    from core.stores.plane import atom_id
    from tests.fixtures.embedding import DIM
    from tests.fixtures.lifecycle import fill_stream

    cfg = instance_config(tmp_path / "w", None, lazy=True)
    cache = Cache(tmp_path / "cache")
    emb = CountingEmbedder()
    stores = with_cache(stores_for(cfg, emb), cfg, cache)
    fill_stream(cfg)
    perform(cfg, stores, f'do sync_corpus(name: "{CORPUS_SOURCE}", batch: 10)', role="corpus",
            batch=True)
    atoms = {atom_id(c.text) for e in stores.catalog.active_entries()
             for c in derive_chunks(stores.raw.get(e.digest))}
    key, fields = key_of(cfg)
    assert cache.put_vectors(key, fields, {a: [0.5] * (DIM + 1) for a in atoms}) == len(atoms)
    report = drain(stores)
    assert report.cached == 0 and emb.calls > 0
    held = stores.plane.plane.atoms.payload(sorted(atoms))
    assert held and all(len(v) == DIM for _t, v in held.values())


def test_p13_the_vector_key_names_the_backend() -> None:
    """Two instances that differ only in the backend serving the embedder share no vectors."""
    from core.kernel.config import get_config
    from core.stores.cache import key_of

    base = get_config()
    other = replace(base, runtime=replace(base.runtime, embedding_backend=(
        "ollama" if base.runtime.embedding_backend != "ollama" else "llamacpp")))
    assert key_of(base)[0] != key_of(other)[0]
    assert key_of(base)[1]["backend"] != key_of(other)[1]["backend"]


def test_p14_a_raw_object_is_taken_by_digest_and_checked(tmp_path: Path) -> None:
    import hashlib

    from core.kernel.stores.rawstore import RawStore
    from core.stores.cache import Cache

    cache = Cache(tmp_path / "cache")
    data = b"open bytes, addressed by their hash"
    digest = hashlib.sha256(data).hexdigest()
    assert cache.put_raw(digest, data)
    raw = RawStore(tmp_path / "raw", fallback=cache.raw)
    assert raw.get(digest) == data and raw.exists(digest)               # copied in on a miss
    other = b"another object"
    d2 = hashlib.sha256(other).hexdigest()
    assert cache.put_raw(d2, other)
    (tmp_path / "cache" / "raw" / d2[:2] / d2).write_bytes(b"tampered")
    with pytest.raises(FileNotFoundError):
        RawStore(tmp_path / "raw2", fallback=cache.raw).get(d2)
    assert not cache.has_raw(d2)                                        # refused and removed


# ── P15: a purge reaches the cache ──────────────────────────────────────────────────────────


def test_p15_a_purge_reaches_the_cache_and_no_fill_puts_it_back(
        palace: Built, tmp_path: Path, repo: Path) -> None:
    from core.ingest.purge import purge_raw
    from core.kernel.ingest.pipeline import derive_chunks
    from core.stores.cache import key_of, vector_key
    from core.stores.plane import atom_id
    from ops.lifecycle import destroy as d

    b = palace
    cache = _filled_cache(b, tmp_path / "cache")
    path = f"corpus/{CORPUS_SOURCE}/a-0"
    entry = b.stores.catalog.get(path)
    assert entry is not None and cache.has_raw(entry.digest)
    atoms = {atom_id(c.text) for c in derive_chunks(b.stores.raw.get(entry.digest))}
    key = key_of(b.cfg)[0]
    assert atoms & cache.vector_ids(key)
    # the same atoms under a second embedder's key: a purge reaches every key
    other_key, other_fields = vector_key("another-model", "t", 3, "another-backend")
    assert cache.put_vectors(other_key, other_fields, {a: [0.1, 0.2, 0.3] for a in atoms})
    b.stores.catalog.tombstone(path)
    result = purge_raw(entry.digest, raw=b.stores.raw, store=b.stores.plane,
                       catalog=b.stores.catalog, confirm=True, cache=cache)
    assert result.cache_raw_removed and result.cache_vectors_removed > len(atoms)
    assert not cache.has_raw(entry.digest) and not atoms & cache.vector_ids(key)
    assert not atoms & cache.vector_ids(other_key)
    assert entry.digest in cache.purged()
    other = build_palace(tmp_path / "other", repo)          # an instance still holding it
    assert other.stores.catalog.get(path) is not None
    d.fill(other.cfg, cache, d.plan_fill(other.cfg, cache))
    assert not cache.has_raw(entry.digest)
    assert not atoms & cache.vector_ids(key) - _shared_atoms(other, path)


def _shared_atoms(b: Built, purged_path: str) -> set[str]:
    """Atoms of the purged item another open item of `b` also holds: those may stay."""
    occ = _occupancies(b)
    return {a for p, a in occ if p != purged_path and p.startswith("corpus/")}


def test_a_cached_source_is_taken_only_inside_its_directories(tmp_path: Path) -> None:
    """Every instance of the user can write the cache, so a manifest row that names a path out of
    the source's directory, or an absolute one, is refused: nothing is read or written for it."""
    import json

    from core.stores.cache import Cache

    cache = Cache(tmp_path / "cache")
    base = tmp_path / "src"
    (base / "stream").mkdir(parents=True)
    (base / "stream" / "manifest.json").write_text("{}")
    assert cache.put_source_files("alpha", base, ["stream/manifest.json"]) == 1
    with pytest.raises(ValueError):
        cache.put_source_files("alpha", base, ["../outside"])
    secret = tmp_path / "secret.txt"
    secret.write_text("outside the cache")
    manifest = tmp_path / "cache" / "sources" / "alpha" / "MANIFEST"
    rows = json.loads(manifest.read_text())
    import hashlib

    sha = hashlib.sha256(secret.read_bytes()).hexdigest()
    rows += [{"file": "../../../secret.txt", "size": secret.stat().st_size, "sha256": sha},
             {"file": str(secret), "size": secret.stat().st_size, "sha256": sha}]
    manifest.write_text(json.dumps(rows))
    dest = tmp_path / "dest" / "alpha"
    assert cache.take_source("alpha", dest) == 1
    assert sorted(str(p.relative_to(tmp_path / "dest")) for p in (tmp_path / "dest").rglob("*")
                  if p.is_file()) == ["alpha/stream/manifest.json"]
    assert secret.read_text() == "outside the cache"


def test_the_cache_prunes_what_was_not_taken_for_the_retention(tmp_path: Path) -> None:
    import hashlib
    import time

    from core.stores.cache import RETENTION_DAYS, Cache

    cache = Cache(tmp_path / "cache")
    data = b"old"
    digest = hashlib.sha256(data).hexdigest()
    cache.put_raw(digest, data)
    later = time.time() + (RETENTION_DAYS + 1) * 86400
    assert cache.stale(now=later)["raw"] == [digest]
    assert cache.stale()["raw"] == []
    assert cache.prune(now=later) == 1 and not cache.has_raw(digest)


# ── P16: the corpus at its own root ─────────────────────────────────────────────────────────


def test_p16_the_corpus_overlay_resolves_to_its_own_root(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")
    monkeypatch.setenv(loader.OVERLAY_ENV,
                       str(loader.REPO_ROOT / "config" / "instances" / "corpus.toml"))
    cfg = loader.load_config()
    root = home / ".mind-palace" / "instances" / "corpus"
    assert cfg.instance.id == "corpus" and cfg.instance.root == root
    assert cfg.paths.data_dir == root / "data"
    assert cfg.ingestion.corpus.root == root / "sources"
    for p in loader.namespaces_of(cfg).paths:
        assert str(p).startswith(str(root)), p
