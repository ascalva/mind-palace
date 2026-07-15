"""Unit tests for `ReferenceView` (bp-035 Items 1 & 2, dn-core-query-protocol §2.3).

Item 1 — the commit-anchored read window: `references_to`/`references_from` filter to the
anchor commit (the stale-union bug is the falsifier), and no mutator is reachable through the
view (the scope-leak falsifier). Plus the `open_reference_view` factory's anchor resolution.

Item 2 — `connected_set`: the bounded, cycle-safe BFS over fibers F, with `depth` honored and
`ref` self-excluded (the §11 pinned default).
"""

from __future__ import annotations

from types import SimpleNamespace

from core.reference_view import ReferenceView, open_reference_view
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore


def _c2c(source: str, target: str, *, commit: str, ref_type: str = "design-ref",
         line: int = 1) -> ReferenceEdge:
    """A doc→doc (corpus_to_corpus) edge at a given commit."""
    return ReferenceEdge.mint(
        source_kind="corpus", source_ref=source, source_detail="",
        target_kind="corpus", target_ref=target, target_detail="",
        ref_type=ref_type, commit_sha=commit, source_line=line,
    )


# ── Item 1 — the commit-anchored read window ─────────────────────────────────────────────────
def test_references_to_returns_only_anchor_commit_edges(tmp_path):
    """The stale-union falsifier: over a store seeded at two commits, the view anchored at C1
    returns exactly the C1 edges whose target == the ref — never the C2 rows."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/x.md", "docs/a.md", commit="C1", line=1),   # cites a, at C1
        _c2c("docs/y.md", "docs/a.md", commit="C1", line=2),   # cites a, at C1
        _c2c("docs/z.md", "docs/a.md", commit="C2", line=3),   # cites a, but at C2 — excluded
    ])
    view = ReferenceView.over(store, commit="C1")
    citing_a = view.references_to("docs/a.md")
    assert {e.source_ref for e in citing_a} == {"docs/x.md", "docs/y.md"}
    assert all(e.commit_sha == "C1" for e in citing_a)          # never the C2 row


def test_references_from_is_the_dual_on_source_ref(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="C1", line=1),
        _c2c("docs/a.md", "docs/c.md", commit="C1", line=2),
        _c2c("docs/a.md", "docs/d.md", commit="C2", line=3),   # C2 — excluded at anchor C1
    ])
    view = ReferenceView.over(store, commit="C1")
    from_a = view.references_from("docs/a.md")
    assert {e.target_ref for e in from_a} == {"docs/b.md", "docs/c.md"}
    assert all(e.commit_sha == "C1" for e in from_a)


def test_anchor_commit_is_recorded_on_the_view(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    view = ReferenceView.over(store, commit="deadbeef")
    assert view.commit == "deadbeef"


def test_unknown_ref_returns_empty(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_c2c("docs/a.md", "docs/b.md", commit="C1")])
    view = ReferenceView.over(store, commit="C1")
    assert view.references_to("docs/nope.md") == []
    assert view.references_from("docs/nope.md") == []


def test_view_exposes_no_mutator(tmp_path):
    """The scope-leak falsifier: no write method (`add_batch`) nor the raw connection (`_conn`)
    is reachable as an attribute of the view — it is reads and only reads (§2.1 scope)."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    view = ReferenceView.over(store, commit="C1")
    assert not hasattr(view, "add_batch")
    assert not hasattr(view, "_conn")
    assert not hasattr(view, "close")
    # the public surface is exactly the three reads + the anchor:
    public = {name for name in dir(view) if not name.startswith("_")}
    assert public == {"references_to", "references_from", "connected_set", "commit", "over"}


def test_code_and_corpus_endpoints_both_read_back(tmp_path):
    """The view is endpoint-kind-agnostic: a doc citing a `.py` path (corpus_to_code) reads back
    through `references_from` just like a doc→doc edge."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref="docs/a.md", source_detail="",
                           target_kind="code", target_ref="core/x.py", target_detail="",
                           ref_type="path-mention", commit_sha="C1", source_line=5),
        _c2c("docs/a.md", "docs/b.md", commit="C1"),
    ])
    view = ReferenceView.over(store, commit="C1")
    assert {e.target_ref for e in view.references_from("docs/a.md")} == {"core/x.py", "docs/b.md"}


# ── the factory's anchor resolution (§3 Q1) ──────────────────────────────────────────────────
def test_factory_anchors_at_the_active_run_commit(tmp_path):
    """`open_reference_view` with no explicit commit resolves the anchor to the active run's
    `commit_sha` (`RunLedger.last()`) — the §3 Q1 default."""
    from ops.lifecycle.runs import open_run_ledger

    cfg = SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path))
    ledger = open_run_ledger(cfg)  # type: ignore[arg-type]
    ledger.open_run(commit_sha="run_commit_sha", dirty=False, pid=1234)
    ledger.close()
    store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="run_commit_sha"),
        _c2c("docs/a.md", "docs/old.md", commit="a_stale_commit"),
    ])
    store.close()

    view = open_reference_view(cfg)  # type: ignore[arg-type]
    assert view.commit == "run_commit_sha"
    assert {e.target_ref for e in view.references_from("docs/a.md")} == {"docs/b.md"}


def test_factory_falls_back_to_git_head_when_no_run(tmp_path):
    """With no run recorded, the anchor falls back to git HEAD (`git_state(REPO_ROOT)`)."""
    from config.loader import REPO_ROOT
    from ops.lifecycle.runs import git_state

    cfg = SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path))
    view = open_reference_view(cfg)  # type: ignore[arg-type]
    head, _dirty = git_state(REPO_ROOT)
    assert view.commit == head


def test_factory_honors_an_explicit_commit(tmp_path):
    cfg = SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path))
    view = open_reference_view(cfg, commit="explicit_sha")  # type: ignore[arg-type]
    assert view.commit == "explicit_sha"


# ── Item 2 — connected_set (bounded BFS over fibers F) ───────────────────────────────────────
def _chain_store(tmp_path) -> ReferenceEdgeStore:
    """a → b → c (a cites b, b cites c), all at commit C1."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="C1", line=1),
        _c2c("docs/b.md", "docs/c.md", commit="C1", line=2),
    ])
    return store


def test_connected_set_depth_1_excludes_self(tmp_path):
    """The §11 pinned default: `connected_set` returns reached OTHERS, not `ref` itself."""
    view = ReferenceView.over(_chain_store(tmp_path), commit="C1")
    assert view.connected_set("docs/a.md", depth=1) == {"docs/b.md"}


def test_connected_set_depth_2_reaches_two_hops(tmp_path):
    view = ReferenceView.over(_chain_store(tmp_path), commit="C1")
    assert view.connected_set("docs/a.md", depth=2) == {"docs/b.md", "docs/c.md"}


def test_connected_set_traverses_both_directions(tmp_path):
    """BFS is over `references_to ∪ references_from`: from b, one hop reaches BOTH a (cites b)
    and c (b cites)."""
    view = ReferenceView.over(_chain_store(tmp_path), commit="C1")
    assert view.connected_set("docs/b.md", depth=1) == {"docs/a.md", "docs/c.md"}


def test_connected_set_terminates_on_a_cycle(tmp_path):
    """The falsifier: a cyclic citation graph must not loop forever."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="C1", line=1),
        _c2c("docs/b.md", "docs/a.md", commit="C1", line=2),   # a ↔ b cycle
    ])
    view = ReferenceView.over(store, commit="C1")
    assert view.connected_set("docs/a.md", depth=10) == {"docs/b.md"}  # terminates, self-excluded


def test_connected_set_depth_bounds_the_traversal(tmp_path):
    """The falsifier: `depth` is honored — a longer chain is not fully reached at low depth."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="C1", line=1),
        _c2c("docs/b.md", "docs/c.md", commit="C1", line=2),
        _c2c("docs/c.md", "docs/d.md", commit="C1", line=3),
    ])
    view = ReferenceView.over(store, commit="C1")
    assert view.connected_set("docs/a.md", depth=1) == {"docs/b.md"}
    assert view.connected_set("docs/a.md", depth=2) == {"docs/b.md", "docs/c.md"}
    assert view.connected_set("docs/a.md", depth=3) == {"docs/b.md", "docs/c.md", "docs/d.md"}


def test_connected_set_depth_zero_reaches_nothing(tmp_path):
    view = ReferenceView.over(_chain_store(tmp_path), commit="C1")
    assert view.connected_set("docs/a.md", depth=0) == set()


def test_connected_set_unknown_ref_is_empty(tmp_path):
    view = ReferenceView.over(_chain_store(tmp_path), commit="C1")
    assert view.connected_set("docs/nope.md", depth=3) == set()


def test_connected_set_respects_the_anchor_commit(tmp_path):
    """A neighbour reachable only via a DIFFERENT-commit edge is not traversed."""
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _c2c("docs/a.md", "docs/b.md", commit="C1", line=1),
        _c2c("docs/b.md", "docs/c.md", commit="C2", line=2),   # only at C2
    ])
    view = ReferenceView.over(store, commit="C1")
    assert view.connected_set("docs/a.md", depth=5) == {"docs/b.md"}  # c unreachable at C1
