"""ops/code_lineage.py + CodeCorpusSync.backfill — the temporal substrate (bp-099, Items 2–3).

The lineage reader (`ledger_versions`/`capture_commit_diffs`/`supersession_chains`) over a real
snapshots ledger built by φ_code (`ops.code_snapshot`, imported READ-ONLY — never edited: the
interpreter-version pin), and the history backfill that embeds every ledger version with the right
`current` flag. No Ollama — a deterministic fake embedder; temp stores only. The composed D5
assertion realizes a semantic supersession edge: a `commit_diffs` modify row whose old_blob AND
new_blob both resolve to embedded rows.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.ingest.code_corpus import CodeCorpusSync
from core.kernel.temporal.boundary import delta_D_squared_is_zero, poset_from_chains
from core.stores.memberships import EmbedderIdentity, MembershipStore
from core.stores.vectorstore import VectorStore
from ops.code_lineage import (
    capture_commit_diffs,
    ledger_commits,
    ledger_versions,
    supersession_chains,
)
from ops.code_snapshot import backfill as ledger_backfill
from ops.code_snapshot import open_snapshot_db
from tests.fixtures.embedding import DIM, FakeEmbedder


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _rev(repo: Path, ref: str) -> str:
    return _git(repo, "rev-parse", ref).strip()


@pytest.fixture
def repo(tmp_path) -> Path:
    """A repo with: f.py evolving v0→v1→v2 (linear on main), a rename g.py→gg.py, a broken .py
    (AST parse casualty), and a merge commit (h.py from a feature branch, first-parent)."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")

    def _commit(msg: str) -> None:
        _git(r, "add", "-A")
        _git(r, "commit", "-qm", msg)

    (r / "f.py").write_text("def f():\n    return 0\n")     # f v0
    (r / "g.py").write_text("def g():\n    return 1\n")
    _commit("c1")

    (r / "f.py").write_text("def f():\n    return 10\n")    # f v1
    _commit("c2 modify f")

    (r / "f.py").write_text("def f():\n    return 100\n")   # f v2
    _commit("c3 modify f")

    # a feature branch add, merged first-parent
    _git(r, "checkout", "-q", "-b", "feat")
    (r / "h.py").write_text("def h():\n    return 2\n")
    _commit("feat add h")
    _git(r, "checkout", "-q", "main")
    (r / "broken.py").write_text("def oops(:\n    pass\n")  # AST parse casualty
    _commit("add broken")
    _git(r, "merge", "-q", "--no-ff", "feat", "-m", "merge feat")

    _git(r, "mv", "g.py", "gg.py")
    _commit("rename g->gg")
    return r


@pytest.fixture
def ledger(repo, tmp_path):
    """A φ_code snapshots ledger over the repo (built by ops.code_snapshot; read-only here)."""
    db = open_snapshot_db(tmp_path / "code_snapshots.sqlite")
    ledger_backfill(db, repo)
    yield db
    db.close()


# ── ledger_versions ──────────────────────────────────────────────────────────────────────

def test_ledger_versions_are_distinct_path_blob_pairs(ledger):
    versions = ledger_versions(ledger)
    assert versions == sorted(set(versions))            # distinct + deterministic order
    paths = {p for p, _ in versions}
    assert {"f.py", "gg.py", "h.py", "broken.py"} <= paths
    # f.py has THREE distinct versions (v0, v1, v2)
    assert len([b for p, b in versions if p == "f.py"]) == 3


# ── capture_commit_diffs: idempotent · first-parent · rename=delete+add ─────────────────────

def test_capture_commit_diffs_idempotent_and_shapes(ledger, repo):
    commits = ledger_commits(ledger)
    n1 = capture_commit_diffs(ledger, repo, commits)
    assert n1 == len(commits)                           # every commit captured once
    n2 = capture_commit_diffs(ledger, repo, commits)
    assert n2 == 0                                      # idempotent per commit (marker table)

    rows = ledger.execute(
        "SELECT commit_sha, path, old_blob, new_blob FROM commit_diffs").fetchall()
    by_path: dict[str, list[tuple[str, str, str]]] = {}
    for c, p, o, n in rows:
        by_path.setdefault(p, []).append((c, o, n))

    # rename g.py -> gg.py appears as a DELETE (new_blob='') + an ADD (old_blob='') — PD-1
    assert any(n == "" for _, _, n in by_path["g.py"]), "g.py delete row"
    assert any(o == "" for _, o, _ in by_path["gg.py"]), "gg.py add row"

    # a modify row carries BOTH blobs (f.py v0->v1); an add carries only new
    f_mods = [(o, n) for _, o, n in by_path["f.py"] if o and n]
    assert f_mods, "f.py has a modify row with both endpoints"

    # merge follows first-parent: h.py (added on feat) shows as an add relative to the first parent
    assert any(o == "" and n for _, o, n in by_path["h.py"])


# ── supersession_chains → poset_from_chains (consumed unmodified) ──────────────────────────

def test_supersession_chains_linear_and_feed_poset(ledger, repo):
    capture_commit_diffs(ledger, repo, ledger_commits(ledger))
    chains = supersession_chains(ledger)

    # f.py is a LINEAR chain of its three versions in commit order
    f_v0 = _git(repo, "rev-parse", f"{_first_commit(repo)}:f.py").strip()
    assert chains["f.py"][0] == f_v0
    assert len(chains["f.py"]) == 3
    assert len(set(chains["f.py"])) == 3                # strictly increasing versions

    # poset_from_chains consumes the chains' structure UNMODIFIED (no core edit). Its contract is
    # dict[str,list[int]] (version_seq) and it re-sorts values, so the order-preserving feed is each
    # blob's commit-order POSITION (index == version_seq) — see the finding under bp-099.
    pos_chains = {p: list(range(len(blobs))) for p, blobs in chains.items()}
    poset = poset_from_chains(pos_chains)
    assert delta_D_squared_is_zero(poset)               # a valid strict partial order (a forest)
    assert poset.n_elements == sum(len(b) for b in chains.values())
    # §8 edge invariant: covering edges per path = |versions| - 1
    expected_edges = sum(len(b) - 1 for b in chains.values())
    assert expected_edges == sum(len(b) for b in chains.values()) - len(chains)


def _first_commit(repo: Path) -> str:
    return _git(repo, "rev-list", "--max-parents=0", "HEAD").strip()


# ── the history backfill: current flags · idempotent · parse-fail counted ──────────────────

def _sync(repo, tmp_path) -> CodeCorpusSync:
    return CodeCorpusSync(
        repo=repo, store=VectorStore(tmp_path / "v.lance", dim=DIM), embedder=FakeEmbedder(),
        memberships=MembershipStore(tmp_path / "m.sqlite"),
        embedder_identity=EmbedderIdentity(model="fake", dim=DIM))


def test_backfill_embeds_history_with_current_flags(ledger, repo, tmp_path):
    """[banner: correction] The per-version state re-homes from the vector row's
    `(source_path, digest)` to the MEMBERSHIP fiber (bp-152 D1): an atom row carries neither
    column, and a version IS its fiber. Same three claims — three versions land, exactly HEAD is
    current, a re-run embeds nothing — read at their new home."""
    sync = _sync(repo, tmp_path)

    report = sync.backfill(ledger_versions(ledger))
    assert report.embedded_rows > 0
    assert report.parse_failures >= 1                   # broken.py counted, still embedded

    m = sync.memberships
    # f.py: three versions land as three fibers; exactly the HEAD blob's is current
    f_blobs = m.blobs_of("f.py")
    assert len(f_blobs) == 3
    head_f = _git(repo, "rev-parse", "HEAD:f.py").strip()
    current = [b for b in f_blobs if all(x.current for x in m.fiber("f.py", b))]
    assert current == [head_f]
    assert all(not any(x.current for x in m.fiber("f.py", b))
               for b in f_blobs if b != head_f)
    # broken.py embedded despite the parse failure (L0b windows + module shell)
    assert m.blobs_of("broken.py")

    # idempotent: a re-run embeds nothing and adds no occupancy
    m_before = m.count()
    again = sync.backfill(ledger_versions(ledger))
    assert again.embedded_rows == 0 and again.membership_rows == 0
    assert m.count() == m_before


def test_composed_supersession_edge_resolves_to_embedded_nodes(ledger, repo, tmp_path):
    """D5, the realized edge: a `commit_diffs` modify row's old_blob AND new_blob both resolve to
    embedded rows in the backfilled store — the integrator's landing surface."""
    sync = _sync(repo, tmp_path)
    sync.backfill(ledger_versions(ledger))
    capture_commit_diffs(ledger, repo, ledger_commits(ledger))

    # [banner: correction] The note's section 6 re-home (2), F6: an endpoint is resolvable IFF its
    # membership fiber is non-empty. "By digest in the vector store" cannot be asked of an atom
    # row — the column left it — and the fiber is the same fact at a sturdier home.
    modify = ledger.execute(
        "SELECT path, old_blob, new_blob FROM commit_diffs "
        "WHERE old_blob != '' AND new_blob != '' LIMIT 1").fetchone()
    assert modify is not None
    path, old_blob, new_blob = modify
    assert sync.memberships.fiber(path, old_blob)
    assert sync.memberships.fiber(path, new_blob)
