"""The id-mint migration end-to-end (bp-034; oq-0019 B; §11 ruling 2026-07-14).

The migration's ONE job: mint a durable `id::` into each no-id note and re-key its version history,
so no lineage forks at the identity switch — now or on any future rename (the A6 payoff,
temporal-retrieval-algebra.md §2.4). These tests are the acceptance surface for Items 13 (dry-run
preview, mutates nothing), 15 (byte-preserving minter), and 16 (offline orchestration + no-fork /
post-rename-stability / idempotency / fail-closed verification), plus the §6 crash-convergence and
§4b restore-rehearsal the journal determination added. Deterministic — a fake embedder, real stores;
no network, no model, daemon down.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.ingest.logseq import parse_note
from core.ingest.mint_ids import (
    MintRefusedError,
    has_stable_id,
    mint,
    preview,
    restore_from_backup,
    run,
)
from core.ingest.sync import VaultSync
from core.stores.authored_supersession import owner_declaration
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore
from ops.lifecycle.runs import RunLedger
from tests.fixtures.embedding import DIM, FakeEmbedder


def _sync(tmp_path: Path) -> VaultSync:
    vault = tmp_path / "vault"
    vault.mkdir()
    return VaultSync(
        vault=vault,
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        catalog=VaultCatalog(tmp_path / "catalog.sqlite"),
        embedder=FakeEmbedder(),  # type: ignore[arg-type]  # test fixture duck-types Embedder
        version_store=VersionStore(tmp_path / "versions.sqlite"),
    )


def _write(sync: VaultSync, name: str, content: str) -> Path:
    p = sync.vault / name
    p.write_text(content, encoding="utf-8")
    return p


def _vs(sync: VaultSync) -> VersionStore:
    assert sync.version_store is not None   # _sync always wires one; narrows the Optional for mypy
    return sync.version_store


# ── Item 13 — dry-run preview (mutates NOTHING) ────────────────────────────────────────────────

def test_preview_lists_only_no_id_notes_and_mutates_nothing(tmp_path: Path):
    sync = _sync(tmp_path)
    _write(sync, "has_logseq.md", "id:: abc-123\ncontent")
    _write(sync, "has_yaml.md", "---\nid: dn-x\ntitle: t\n---\ncontent")
    none1 = _write(sync, "bare1.md", "just content")
    none2 = _write(sync, "bare2.md", "more content")
    sync.rescan()                                            # build catalog + version rows

    counts_before = (sync.catalog._conn.execute("SELECT count(*) FROM vault_files").fetchone()[0],
                     _vs(sync).count())
    mtimes_before = {p.name: p.stat().st_mtime_ns for p in sync.vault.glob("*.md")}

    plan = preview(sync)

    assert set(plan.mint_set) == {str(none1), str(none2)}    # exactly the no-stable-id notes
    counts_after = (sync.catalog._conn.execute("SELECT count(*) FROM vault_files").fetchone()[0],
                    _vs(sync).count())
    assert counts_after == counts_before                     # no store row added/removed
    mtimes_after = {p.name: p.stat().st_mtime_ns for p in sync.vault.glob("*.md")}
    assert mtimes_after == mtimes_before                     # no file written (pure read)


# ── Item 15 — byte-preserving minter ───────────────────────────────────────────────────────────

def test_mint_adds_exactly_one_id_line_and_is_idempotent(tmp_path: Path):
    sync = _sync(tmp_path)
    bare = _write(sync, "bare.md", "first line\nsecond line\n")
    already = _write(sync, "already.md", "id:: keep-me\nbody\n")
    original_bare = bare.read_bytes()

    minted = mint(sync, [str(bare), str(already)])

    assert set(minted) == {str(bare)}                        # the id-bearing note was skipped
    new_bytes = bare.read_bytes()
    # byte-diff is EXACTLY the one prepended id:: line; the original bytes follow verbatim.
    added = new_bytes[: len(new_bytes) - len(original_bare)]
    assert new_bytes[len(added):] == original_bare
    assert added == f"id:: {minted[str(bare)]}\n".encode()
    # the minted id parses back as the note's durable identity.
    assert parse_note(bare, sync.vault).properties["id"] == minted[str(bare)]
    assert already.read_bytes() == b"id:: keep-me\nbody\n"   # untouched

    assert mint(sync, [str(bare)]) == {}                     # re-mint: now has an id → skipped


def test_mint_refuses_yaml_front_matter(tmp_path: Path):
    # §10: a note that opens with a `---` block is the ambiguous case — refuse, never guess.
    sync = _sync(tmp_path)
    _write(sync, "fm.md", "---\ntitle: t\n---\nbody\n")      # front-matter WITHOUT an id
    with pytest.raises(MintRefusedError):
        mint(sync, [str(sync.vault / "fm.md")])


# ── Item 16 — orchestration + end-to-end verification ──────────────────────────────────────────

def test_run_migrates_without_forking_lineage(tmp_path: Path):
    # (a) the whole point: every note's history is ONE chain under its minted id, no orphan.
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "alpha one")
    sync.rescan()                                            # v1
    a.write_text("alpha two", encoding="utf-8")
    sync.rescan()                                            # v2
    old_id = sync.catalog.doc_id_for(str(a))
    assert old_id == str(a)                                  # filed under its path (no id yet)
    pre = [(v.version_seq, v.digest) for v in _vs(sync).history(old_id)]
    assert [s for s, _ in pre] == [1, 2]

    report = run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak")

    assert report.verified is True
    new_id = sync.catalog.doc_id_for(str(a))
    assert new_id != str(a) and new_id == minted_id(sync, a)   # now a durable id::
    assert _vs(sync).history(str(a)) == []          # NO orphaned source_path chain
    post = [(v.version_seq, v.digest) for v in _vs(sync).history(new_id)]
    assert [s for s, _ in post] == [1, 2, 3]                 # carried v1,v2 + "id added"
    assert [d for _, d in post][:2] == [d for _, d in pre]   # carried content preserved exactly


def test_run_then_rename_preserves_lineage(tmp_path: Path):
    # (b) a rename AFTER migration keeps one chain — the id::, not the path, is the identity.
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "gardening notes")
    sync.rescan()
    run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak")
    the_id = sync.catalog.doc_id_for(str(a))

    b = sync.vault / "renamed.md"
    a.rename(b)
    sync.rescan()                                            # re-appears at the new path

    assert sync.catalog.doc_id_for(str(b)) == the_id         # id carried across the rename
    assert _vs(sync).history(str(b)) == []          # never a path-keyed chain
    assert len(_vs(sync).history(the_id)) >= 1      # the one continuous chain


def test_second_run_is_a_noop(tmp_path: Path):
    # (c) idempotent: a fully-migrated corpus re-runs to a no-op (nothing minted, nothing re-keyed).
    sync = _sync(tmp_path)
    _write(sync, "a.md", "one")
    _write(sync, "b.md", "two")
    sync.rescan()
    run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak")

    second = run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak2")
    assert second.minted == {}
    assert second.rekeyed == 0
    assert second.verified is True


def test_run_refuses_without_confirm(tmp_path: Path):
    # (d) fail-closed: no confirm → refuse, nothing written.
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "content")
    sync.rescan()
    before = a.read_bytes()
    with pytest.raises(MintRefusedError):
        run(sync, declaration=owner_declaration(), confirm=False, backup_dir=tmp_path / "bak")
    assert a.read_bytes() == before                          # untouched


def test_run_refuses_while_daemon_up(tmp_path: Path):
    # (d) fail-closed: a live daemon (an active run whose pid is alive) → refuse (finding-0066).
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "content")
    sync.rescan()
    led = RunLedger(tmp_path / "runs.sqlite")
    led.open_run(commit_sha="deadbeef", dirty=False, pid=os.getpid())  # alive → daemon "up"
    before = a.read_bytes()
    with pytest.raises(MintRefusedError):
        run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak",
            run_ledger=led)
    assert a.read_bytes() == before


def test_run_allowed_when_last_run_stopped(tmp_path: Path):
    # the daemon-down path: the newest run is marked stopped → not live → the migration proceeds.
    sync = _sync(tmp_path)
    _write(sync, "a.md", "content")
    sync.rescan()
    led = RunLedger(tmp_path / "runs.sqlite")
    rec = led.open_run(commit_sha="deadbeef", dirty=False, pid=os.getpid())
    led.mark_stopped(rec.id, clean=True)                     # daemon down
    report = run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak",
                 run_ledger=led)
    assert report.verified is True


# ── §6 crash-convergence (the fresh-uuid orphan the journal determination surfaced) ─────────────

def test_partial_run_converges_no_orphan_no_fork(tmp_path: Path):
    # Simulate a crash AFTER the mint but BEFORE the re-key: the note carries id::X, but its chain
    # is still under source_path. A re-run must move the chain to X (CHECK ORDER (iv)) — not orphan
    # it under source_path nor mint a second id — converging on one chain, no fork.
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "content")
    sync.rescan()                                            # v1 under source_path
    minted = mint(sync, [str(a)])                            # mint only — the crash window
    the_id = minted[str(a)]
    assert sync.catalog.doc_id_for(str(a)) == str(a)         # chain NOT yet re-keyed
    assert has_stable_id(parse_note(a, sync.vault))          # but the note now carries id::X

    report = run(sync, declaration=owner_declaration(), confirm=True, backup_dir=tmp_path / "bak")

    assert report.minted == {}                               # not re-minted (idempotent)
    assert report.verified is True
    assert sync.catalog.doc_id_for(str(a)) == the_id         # chain re-keyed onto the existing id
    assert _vs(sync).history(str(a)) == []          # no orphan under source_path
    assert len(_vs(sync).history(the_id)) >= 1      # one convergent chain


# ── §4b restore-rehearsal (reversibility is exercised, not merely asserted) ─────────────────────

def test_restore_from_backup_reproduces_pre_state(tmp_path: Path):
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "reversible content")
    sync.rescan()
    pre_bytes = a.read_bytes()
    pre_hist = [(v.version_seq, v.digest) for v in
                _vs(sync).history(sync.catalog.doc_id_for(str(a)))]

    backup_dir = tmp_path / "bak"
    run(sync, declaration=owner_declaration(), confirm=True, backup_dir=backup_dir)
    assert a.read_bytes() != pre_bytes                       # migration did write the id:: line

    # Close the stores (SQLite holds the files), restore, re-open, assert byte-identical pre-state.
    sync.catalog.close()
    _vs(sync).close()
    restore_from_backup(backup_dir, sync)
    sync.catalog = VaultCatalog(tmp_path / "catalog.sqlite")
    sync.version_store = VersionStore(tmp_path / "versions.sqlite")

    assert a.read_bytes() == pre_bytes                       # vault byte-identical to pre-migration
    restored = [(v.version_seq, v.digest) for v in
                _vs(sync).history(sync.catalog.doc_id_for(str(a)))]
    assert restored == pre_hist                              # version history reproduced exactly


def minted_id(sync: VaultSync, path: Path) -> str:
    """The `id::` a migrated note now carries — read back from the file (the durable identity)."""
    val = parse_note(path, sync.vault).properties.get("id")
    assert val is not None
    return val
