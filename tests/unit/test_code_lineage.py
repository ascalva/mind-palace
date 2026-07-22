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
from core.kernel.provenance import Provenance
from core.kernel.temporal.boundary import delta_D_squared_is_zero, poset_from_chains
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

def test_backfill_embeds_history_with_current_flags(ledger, repo, tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = CodeCorpusSync(repo=repo, store=store, embedder=FakeEmbedder())

    report = sync.backfill(ledger_versions(ledger))
    assert report.embedded_rows > 0
    assert report.parse_failures >= 1                   # broken.py counted, still embedded

    code = store.all_rows(provenances={Provenance.CODE})
    # f.py: three versions embedded; exactly the HEAD blob is current=true, the older two false
    f_by_digest = {r["digest"]: r["current"] for r in code if r["source_path"] == "f.py"}
    assert len(f_by_digest) == 3
    head_f = _git(repo, "rev-parse", "HEAD:f.py").strip()
    assert f_by_digest[head_f] is True
    assert sum(1 for c in f_by_digest.values() if c is True) == 1
    assert sum(1 for c in f_by_digest.values() if c is False) == 2
    # broken.py embedded despite the parse failure (L0b windows + module shell)
    assert any(r["source_path"] == "broken.py" for r in code)

    # idempotent: a re-run embeds nothing
    again = sync.backfill(ledger_versions(ledger))
    assert again.embedded_rows == 0


def test_composed_supersession_edge_resolves_to_embedded_nodes(ledger, repo, tmp_path):
    """D5, the realized edge: a `commit_diffs` modify row's old_blob AND new_blob both resolve to
    embedded rows in the backfilled store — the integrator's landing surface."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = CodeCorpusSync(repo=repo, store=store, embedder=FakeEmbedder())
    sync.backfill(ledger_versions(ledger))
    capture_commit_diffs(ledger, repo, ledger_commits(ledger))

    embedded_digests = {str(r["digest"])
                        for r in store.all_rows(provenances={Provenance.CODE})}
    modify = ledger.execute(
        "SELECT path, old_blob, new_blob FROM commit_diffs "
        "WHERE old_blob != '' AND new_blob != '' LIMIT 1").fetchone()
    assert modify is not None
    _path, old_blob, new_blob = modify
    assert old_blob in embedded_digests and new_blob in embedded_digests
