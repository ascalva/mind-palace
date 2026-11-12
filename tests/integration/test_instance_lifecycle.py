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
from ops.lifecycle.runs import RunLedger
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
    """The palace's launcher, its embedder factory recording each embedder it builds."""
    made: list[Any] = []

    def factory(_cfg: Any) -> Any:
        e = embedder or CountingEmbedder()
        made.append(e)
        return e

    lau = Launcher(cfg=b.cfg, runs=RunLedger(Path(b.cfg.paths.data_dir) / "runs.sqlite"),
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
    for name in ("derived.sqlite", "queue.sqlite", "run_ledger.sqlite", "claim_ops.sqlite",
                 "staging.sqlite", "verdicts.sqlite", "versions.sqlite", "chat_retention.sqlite",
                 "code_snapshots.sqlite", "reference_edges.sqlite", "attestations.sqlite"):
        assert any(before_kept[name].values()), f"the fixture writes no row in {name}"
    assert lau.reset(confirm=True) == 0
    assert raw_files(b) == before_raw                                   # P2: raw, byte for byte
    assert dump(b.cfg, KEPT) == before_kept                             # P2: every kept store
    assert dump(b.cfg)["attestations.sqlite"] == before_atts            # no ledger written
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
    assert lau.reset(confirm=True) == 0
    once, once_causal, once_kept = heads(b.cfg), causal(b), dump(b.cfg, KEPT)
    assert lau.reset(confirm=True) == 0
    assert heads(b.cfg) == once and causal(b) == once_causal and dump(b.cfg, KEPT) == once_kept
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
    what the plane held, calls no embedder, and the dry run counts the backlog."""
    from core.ingest.derive import drain

    cfg = instance_config(tmp_path / "lazy", None, lazy=True)
    stores = stores_for(cfg, CountingEmbedder())
    for i in range(3):
        (Path(cfg.ingestion.vault.path) / f"n{i}.md").write_text(f"note {i}, embedded later\n")
    assert perform(cfg, stores, "do sync_vault")["effects"] == {"landed": 3}
    assert drain(stores, max_items=1).items == 1            # one held, two waiting
    before = heads(cfg)
    made: list[Any] = []
    lau = Launcher(cfg=cfg, runs=RunLedger(tmp_path / "runs.sqlite"), repo_root=tmp_path,
                   embedder_factory=lambda c: made.append(c) or CountingEmbedder(),
                   cache_root=tmp_path / "cache", installed_plist=tmp_path / "no.plist")
    assert lau.reset(confirm=False) == 0
    out = capsys.readouterr().out
    assert "re-occupies the 1 item(s)" in out and "2 item(s) of the plane's classes hold no " \
        "vector" in out and "the embedder is called for 0 atom(s)" in out
    assert lau.reset(confirm=True) == 0
    assert made == []
    assert heads(cfg)["plane.occupancies"] == before["plane.occupancies"]
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


# ── P9: an interrupted reset finishes ───────────────────────────────────────────────────────


@pytest.mark.parametrize("step", sorted(rebuild.STEPS))
def test_p9_a_reset_interrupted_at_any_step_leaves_the_marker_and_finishes(
        palace: Built, step: str, monkeypatch: pytest.MonkeyPatch) -> None:
    b = palace
    before = heads(b.cfg)
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
    assert heads(b.cfg) == before


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
    assert lau.repo_sync_now() == 0
    healed = LexicalStore(lexical_path(cfg))
    assert not healed.stale and healed.recorded_tokenizer() == Tokenizer().identity
    paths = {p for p, _ in healed.landed_versions()}
    assert f"code/{REPO}/pkg/late.py" in paths and len(paths) == 4


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
    receipt = perform(cfg, stores, "do sync_vault")
    assert receipt["effects"].get("landed") == 1 and "rederive" in receipt["timing"]
    assert not stores.lexical.stale and len(stores.lexical.landed_versions()) == 2


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


def test_p11_the_destroy_dry_run_writes_nothing(named: Built, home: Path) -> None:
    lau, _ = launcher_for(named, cache=home / ".mind-palace" / "cache")
    before = dump(named.cfg)
    assert lau.destroy(confirm=False) == 0
    assert dump(named.cfg) == before and not (home / ".mind-palace" / "cache").exists()


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


def test_p12_destroy_keeps_exactly_the_cache_classes(named: Built, home: Path) -> None:
    from core.stores.cache import Cache, key_of

    b = named
    catalog, occ = _catalog(b), _occupancies(b)
    retained = sqlite3.connect(Path(b.cfg.paths.data_dir) / "chat_retention.sqlite")
    transcripts = {str(r[0]) for r in retained.execute("SELECT digest FROM retained")}
    retained.close()
    stream = b.cfg.ingestion.corpus.root / CORPUS_SOURCE
    cache_root = home / ".mind-palace" / "cache"
    lau, _ = launcher_for(b, cache=cache_root)
    assert lau.destroy(confirm=True) == 0
    assert not b.root.exists()
    cache = Cache(cache_root)
    open_digests = {d for p, d, _ in catalog if p.startswith(("corpus/", "code/"))}
    private = {d for p, d, c in catalog if not p.startswith(("corpus/", "code/"))}
    assert cache.raw_digests() == open_digests
    assert not cache.raw_digests() & (private | transcripts)
    open_paths = {p for p, _, _ in catalog if p.startswith(("corpus/", "code/"))}
    want = {a for p, a in occ if p in open_paths}
    only_private = {a for p, a in occ if p not in open_paths} - want
    key = key_of(b.cfg)[0]
    assert cache.vector_ids(key) == want and want
    assert not cache.vector_ids(key) & only_private
    assert {m["file"] for m in cache.source_manifest(CORPUS_SOURCE)} >= {
        "stream/manifest.json", "meta/items.jsonl"}
    assert not any("cursor" in m["file"] or "state" in m["file"]
                   for m in cache.source_manifest(CORPUS_SOURCE))
    assert not stream.exists()


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
    from core.stores.cache import key_of
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
    b.stores.catalog.tombstone(path)
    result = purge_raw(entry.digest, raw=b.stores.raw, store=b.stores.plane,
                       catalog=b.stores.catalog, confirm=True, cache=cache)
    assert result.cache_raw_removed and result.cache_vectors_removed > 0
    assert not cache.has_raw(entry.digest) and not atoms & cache.vector_ids(key)
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
