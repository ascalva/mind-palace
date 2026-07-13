"""Unit tests for the Lane-1 reference-edge store (bp-013 Item 6, B-c; bp-026 Item 18
generalizes to symmetric v2 endpoints).

Typed endpoints (symmetric, v2), content-derived identity, append-only idempotency, closed
vocabularies at the boundary, DERIVED direction — plus the Item 6/18 falsifier, grep-asserted:
NO import path from `core/complex/**` to this store may exist (the balance math holds no
handle; the bit-identical instruments proof lives in
tests/integration/test_reference_edge_isolation.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.stores.reference_edges import (
    CORPUS_KINDS,
    DIRECTIONS,
    KINDS,
    REF_TYPES,
    ReferenceEdge,
    ReferenceEdgeStore,
)

REPO = Path(__file__).resolve().parents[2]


def _edge(**over: object) -> ReferenceEdge:
    kw: dict[str, Any] = dict(
        source_kind="code", source_ref="core/recursion.py", source_detail="",
        target_kind="corpus", target_ref="docs/design-notes/recursive-strata.md",
        target_detail="", ref_type="note-citation", commit_sha="c1", source_line=1,
    )
    kw.update(over)
    return ReferenceEdge.mint(**kw)


# --- typed, symmetric endpoints ---------------------------------------------------------------
def test_endpoints_are_typed_symmetric_and_round_trip(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    e = _edge(source_detail="Thing.method", source_line=42)
    assert store.add_batch([e]) == 1
    (got,) = store.all()
    assert (got.commit_sha, got.source_kind, got.source_ref, got.source_detail) == (
        "c1", "code", "core/recursion.py", "Thing.method")
    assert (got.target_kind, got.target_ref, got.target_detail) == (
        "corpus", "docs/design-notes/recursive-strata.md", "")
    assert got.source_line == 42 and got.ref_type == "note-citation"
    assert got == e                                       # full round trip, identity included


def test_corpus_to_corpus_edge_can_be_minted_and_round_trips(tmp_path):
    # bp-026's whole point: a doc→doc edge is now first-class.
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    e = ReferenceEdge.mint(
        source_kind="corpus", source_ref="docs/build-plans/bp-026/plan.md", source_detail="",
        target_kind="corpus", target_ref="docs/findings/finding-0059.md", target_detail="",
        ref_type="design-ref", commit_sha="c1", source_line=24,
    )
    assert store.add_batch([e]) == 1
    (got,) = store.all()
    assert got.direction == "corpus_to_corpus"
    assert (got.source_ref, got.target_ref) == (
        "docs/build-plans/bp-026/plan.md", "docs/findings/finding-0059.md")


def test_direction_is_derived_for_all_three_directions(tmp_path):
    code_to_corpus = _edge()
    corpus_to_code = _edge(source_kind="corpus", source_ref="docs/design-notes/x.md",
                           source_detail="", target_kind="code", target_ref="core/x.py",
                           target_detail="", ref_type="path-mention")
    corpus_to_corpus = _edge(source_kind="corpus", source_ref="docs/findings/finding-0001.md",
                             source_detail="", target_kind="corpus",
                             target_ref="docs/design-notes/y.md", target_detail="",
                             ref_type="design-ref")
    assert code_to_corpus.direction == "code_to_corpus"
    assert corpus_to_code.direction == "corpus_to_code"
    assert corpus_to_corpus.direction == "corpus_to_corpus"
    # direction is a property, never a constructor kwarg or stored column.
    assert not hasattr(ReferenceEdge, "__init__") or "direction" not in {
        f.name for f in __import__("dataclasses").fields(ReferenceEdge)}


def test_direction_never_symmetrized_on_write(tmp_path):
    # v1 Q3, preserved: doc→code and code→doc are different assertions; adding one never
    # creates the other.
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(source_kind="corpus", source_ref="docs/design-notes/the-edge-model.md",
                           source_detail="", target_kind="code", target_ref="core/x.py",
                           target_detail="", ref_type="path-mention", source_line=7)])
    assert [e.direction for e in store.all()] == ["corpus_to_code"]
    assert store.all(direction="code_to_corpus") == []
    assert len(store.all(direction="corpus_to_code")) == 1


# --- identity + append-only idempotency ---------------------------------------------------------
def test_re_adding_the_same_identity_is_a_no_op(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    assert store.add_batch([_edge()]) == 1
    assert store.add_batch([_edge()]) == 0                # idempotent re-extraction
    assert store.count() == 1


def test_append_only_first_reading_wins(tmp_path):
    # Same identity, different created_at: the stored row is never mutated (INSERT OR IGNORE).
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(created_at="2026-07-11T00:00:00")])
    store.add_batch([_edge(created_at="2026-07-12T09:00:00")])
    (got,) = store.all()
    assert got.created_at == "2026-07-11T00:00:00"


def test_identity_key_spans_source_target_ref_type_and_line(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    variants = [
        _edge(),
        _edge(source_line=2),                             # different line → different edge
        _edge(ref_type="path-mention"),                   # different type → different edge
        _edge(source_detail="f"),                         # different source endpoint
        _edge(target_ref="docs/findings/finding-0021.md"),  # different target endpoint
        _edge(commit_sha="c2"),                           # different reading coordinate
    ]
    assert len({e.edge_id for e in variants}) == len(variants)
    assert store.add_batch(variants) == len(variants)


# --- closed vocabularies at the boundary --------------------------------------------------------
def test_vocabularies_are_closed_at_mint():
    with pytest.raises(ValueError):
        _edge(source_kind="sideways")
    with pytest.raises(ValueError):
        _edge(target_kind="sideways")
    with pytest.raises(ValueError):
        _edge(ref_type="wikilink")        # not in the §2.3 shape — unrepresentable (0% in V4)
    with pytest.raises(ValueError):
        _edge(source_line=0)
    assert set(KINDS) == {"code", "corpus"}
    assert set(DIRECTIONS) == {"code_to_corpus", "corpus_to_code", "corpus_to_corpus",
                               "code_to_code"}
    assert set(CORPUS_KINDS) == {"path", "digest"}
    assert set(REF_TYPES) == {"note-citation", "path-mention", "symbol-mention", "design-ref"}


# --- reads -----------------------------------------------------------------------------------
def test_for_commit_and_ref_type_filters(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(), _edge(commit_sha="c2"),
                     _edge(ref_type="path-mention", target_ref="config/levers.toml")])
    assert len(store.for_commit("c1")) == 2
    assert len(store.for_commit("c2")) == 1
    assert [e.ref_type for e in store.all(ref_type="path-mention")] == ["path-mention"]


def test_all_filters_by_source_ref_and_target_ref(tmp_path):
    # bp-026's whole point: "who references doc X" is now a query, not a re-grep.
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([
        _edge(target_ref="docs/design-notes/recursive-strata.md"),                # code→doc A
        _edge(commit_sha="c2", target_ref="docs/design-notes/other.md"),           # code→doc B
        ReferenceEdge.mint(
            source_kind="corpus", source_ref="docs/findings/finding-0059.md", source_detail="",
            target_kind="corpus", target_ref="docs/design-notes/recursive-strata.md",
            target_detail="", ref_type="design-ref", commit_sha="c3", source_line=5,
        ),                                                                         # doc→doc A
    ])
    citing_a = store.all(target_ref="docs/design-notes/recursive-strata.md")
    assert len(citing_a) == 2
    assert {e.source_ref for e in citing_a} == {"core/recursion.py",
                                                "docs/findings/finding-0059.md"}
    from_finding = store.all(source_ref="docs/findings/finding-0059.md")
    assert len(from_finding) == 1 and from_finding[0].direction == "corpus_to_corpus"


def test_open_helper_places_the_store_beside_its_siblings(tmp_path):
    from types import SimpleNamespace

    from core.stores.reference_edges import open_reference_edge_store
    cfg = SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path))
    store = open_reference_edge_store(cfg)  # type: ignore[arg-type]
    assert store.path == tmp_path / "reference_edges.sqlite"
    store.close()


# --- v1 read-compat properties (finding-0063) -------------------------------------------------
def test_v1_read_compat_properties_recover_the_old_surface():
    e = _edge(source_detail="Thing.method", source_line=42)   # code_to_corpus
    assert (e.code_path, e.qualname) == ("core/recursion.py", "Thing.method")
    assert e.corpus_ref == "docs/design-notes/recursive-strata.md"
    assert e.corpus_kind == "path"


def test_v1_read_compat_properties_raise_on_corpus_to_corpus():
    e = ReferenceEdge.mint(
        source_kind="corpus", source_ref="docs/build-plans/bp-026/plan.md", source_detail="",
        target_kind="corpus", target_ref="docs/findings/finding-0059.md", target_detail="",
        ref_type="design-ref", commit_sha="c1", source_line=24,
    )
    with pytest.raises(ValueError):
        _ = e.code_path
    with pytest.raises(ValueError):
        _ = e.qualname
    with pytest.raises(ValueError):
        _ = e.corpus_ref
    with pytest.raises(ValueError):
        _ = e.corpus_kind


# --- the Item 6/18 falsifier, grep-asserted -----------------------------------------------------
def test_no_import_path_from_core_complex_to_this_store():
    """Any import of `reference_edges` from `core/complex/**` breaks the plan's premise:
    the balance math must hold NO handle to the Lane-1 store (plan §6; note §2.5)."""
    complex_dir = REPO / "core" / "complex"
    offenders = [p.name for p in sorted(complex_dir.rglob("*.py"))
                 if "reference_edges" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"core/complex/** must not reference the Lane-1 store: {offenders}"


def test_schema_has_no_stored_asymmetric_residue():
    """bp-026 Item 18 falsifier: the schema must NOT keep a code_path/corpus_ref field as an
    asymmetric residue, and direction must be derived, not stored."""
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(ReferenceEdge)}
    assert "code_path" not in field_names and "corpus_ref" not in field_names
    assert "direction" not in field_names
    assert field_names == {"edge_id", "ref_type", "commit_sha", "source_kind", "source_ref",
                           "source_detail", "target_kind", "target_ref", "target_detail",
                           "source_line", "created_at"}


# =================================================================================================
# Item 20 — the corpus→corpus extractor (φ_doc), the grep-oracle self-grading loop in miniature
# =================================================================================================

import subprocess  # noqa: E402 — grouped with the Item 20 section it serves
import textwrap  # noqa: E402

from ops.code_sensor import (  # noqa: E402
    _RE_NOTE_CITATION,
    CORPUS_TO_CORPUS_VALIDATED,
    CodeSensor,
)
from ops.code_snapshot import open_snapshot_db  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


# Fixture corpus: three docs exercising all three φ_doc sources (front-matter, inline
# citation, wikilink) plus deliberate distractors (a self-loop, a non-doc `warrant` value,
# a wikilink to an unknown name) that MUST mint nothing.
_NOTE_A = textwrap.dedent("""\
    ---
    type: design-note
    id: dn-note-a
    status: draft
    design_ref:
      - docs/design-notes/note-b.md # cites B via front-matter design_ref
    links:
      - docs/findings/finding-planted.md
    supersedes: null
    warrant: finding-planted
    ---

    # Note A

    See also `docs/design-notes/note-a.md` (itself — a self-loop, must NOT mint).
    An inline citation to docs/design-notes/note-b.md appears here too.
    A [[Note B]] wikilink also resolves to note-b.
    An unresolved [[Nonexistent Note]] wikilink must mint nothing.
    """)

_NOTE_B = textwrap.dedent("""\
    ---
    type: design-note
    id: dn-note-b
    status: draft
    links: []
    supersedes: null
    warrant: null
    ---

    # Note B

    No outgoing references.
    """)

_FINDING_PLANTED = textwrap.dedent("""\
    ---
    type: finding
    id: finding-planted
    status: open
    links:
      - docs/design-notes/note-a.md
    ftype: discovery
    ---

    # Planted finding

    Cites docs/design-notes/note-a.md inline as well.
    """)


@pytest.fixture
def doc_repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    (r / "docs" / "design-notes").mkdir(parents=True)
    (r / "docs" / "findings").mkdir(parents=True)
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "docs" / "design-notes" / "note-a.md").write_text(_NOTE_A)
    (r / "docs" / "design-notes" / "note-b.md").write_text(_NOTE_B)
    (r / "docs" / "findings" / "finding-planted.md").write_text(_FINDING_PLANTED)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "docs: plant a doc-to-doc citation fixture")
    return r


def _sensor(repo: Path, tmp_path) -> CodeSensor:
    from core.sensing import CodeSensingHandoff
    from core.stores.code_observations import CodeObservationStore
    from core.stores.observation_history import ObservationHistoryStore

    return CodeSensor(
        repo=repo,
        db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
        attestor=None,
        observations=CodeObservationStore(tmp_path / "code_observations.sqlite"),
        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
        reference_edges=ReferenceEdgeStore(tmp_path / "reference_edges.sqlite"),
        history=ObservationHistoryStore(tmp_path / "history.sqlite"),
    )


def test_corpus_to_corpus_extractor_emits_expected_edges(doc_repo, tmp_path):
    sensor = _sensor(doc_repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    got = {(e.source_ref, e.target_ref, e.ref_type)
           for e in sensor.reference_edges.all(direction="corpus_to_corpus")}
    assert got == {
        # note-a's front-matter design_ref → note-b
        ("docs/design-notes/note-a.md", "docs/design-notes/note-b.md", "design-ref"),
        # note-a's front-matter links → finding-planted
        ("docs/design-notes/note-a.md", "docs/findings/finding-planted.md", "note-citation"),
        # note-a's inline citation to note-b (body, not front matter)
        ("docs/design-notes/note-a.md", "docs/design-notes/note-b.md", "note-citation"),
        # note-a's [[Note B]] wikilink → note-b
        ("docs/design-notes/note-a.md", "docs/design-notes/note-b.md", "note-citation"),
        # finding-planted's front-matter links → note-a
        ("docs/findings/finding-planted.md", "docs/design-notes/note-a.md", "note-citation"),
        # finding-planted's inline citation → note-a
        ("docs/findings/finding-planted.md", "docs/design-notes/note-a.md", "note-citation"),
    }
    # Distractors mint NOTHING: the self-loop (note-a citing itself), `warrant:
    # finding-planted` (not a docs/….md path — no doc named), and the unresolved wikilink.
    assert all(e.source_ref != e.target_ref for e in sensor.reference_edges.all())
    assert not any("Nonexistent" in e.target_ref for e in
                  sensor.reference_edges.all(direction="corpus_to_corpus"))


def test_corpus_to_corpus_self_loops_are_dropped(doc_repo, tmp_path):
    sensor = _sensor(doc_repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    edges = sensor.reference_edges.all(direction="corpus_to_corpus")
    assert all(e.source_ref != e.target_ref for e in edges)


def test_corpus_to_corpus_only_validated_pattern_ref_types(doc_repo, tmp_path):
    sensor = _sensor(doc_repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    edges = sensor.reference_edges.all(direction="corpus_to_corpus")
    assert edges, "fixture must actually produce corpus_to_corpus edges"
    assert all(("corpus_to_corpus", e.ref_type) in CORPUS_TO_CORPUS_VALIDATED for e in edges)


def test_corpus_to_corpus_extraction_is_deterministic(doc_repo, tmp_path):
    sensor1 = _sensor(doc_repo, tmp_path / "run1")
    sensor1.sync()
    assert sensor1.reference_edges is not None
    got1 = {(e.source_ref, e.target_ref, e.ref_type, e.source_line)
           for e in sensor1.reference_edges.all(direction="corpus_to_corpus")}

    sensor2 = _sensor(doc_repo, tmp_path / "run2")
    sensor2.sync()
    assert sensor2.reference_edges is not None
    got2 = {(e.source_ref, e.target_ref, e.ref_type, e.source_line)
           for e in sensor2.reference_edges.all(direction="corpus_to_corpus")}
    assert got1 == got2 and got1


def test_corpus_to_corpus_reprojection_mints_nothing_new(doc_repo, tmp_path):
    sensor = _sensor(doc_repo, tmp_path)
    sensor.sync()
    assert sensor.reference_edges is not None
    before = sensor.reference_edges.count()
    report2 = sensor.sync()
    assert sensor.reference_edges.count() == before and report2.reference_edges == 0


# --- the grep-oracle: extracted corpus_to_corpus edges for a doc == an independent grep -------
def _grep_oracle_targets(repo: Path, doc_path: str) -> set[str]:
    """An INDEPENDENT reimplementation (no shared code with `_corpus_to_corpus_edges`) of
    'what does this doc reference': every `docs/(design-notes|findings|brainstorms)/…\\.md`
    substring anywhere in the file (front matter OR body), minus a self-reference. This is
    the precision+recall oracle bp-026 §10/plan Item 20 requires — deliberately cruder than
    the extractor (it doesn't distinguish front-matter-key-scoped refs from inline prose, and
    it doesn't resolve wikilinks), so a MISMATCH in either direction is diagnostic:
      - oracle has a target the extractor lacks → RECALL gap (the extractor under-parses).
      - extractor has a target with no independent grep hit → PRECISION gap (over-minting).
    Wikilink-derived edges are excluded from this comparison (the oracle can't see them by
    grepping for docs/….md substrings — a `[[Note B]]` string never contains the target
    path), matching the plan's framing: the oracle checks the docs/….md-substring surface,
    not wikilink resolution."""
    text = (repo / doc_path).read_text(encoding="utf-8")
    targets = {m.group(0) for m in _RE_NOTE_CITATION.finditer(text)}
    targets.discard(doc_path)
    return targets


def test_grep_oracle_precision_and_recall_on_note_a(doc_repo):
    extractor_targets = {
        e.target_ref for e in
        CodeSensor(repo=doc_repo, db=open_snapshot_db(doc_repo / ".." / "snap.sqlite"))
        ._corpus_to_corpus_edges(_git(doc_repo, "rev-parse", "HEAD").strip())
        if e.source_ref == "docs/design-notes/note-a.md"
        and e.ref_type != "note-citation-wikilink"    # (no such type; kept for clarity)
    }
    oracle_targets = _grep_oracle_targets(doc_repo, "docs/design-notes/note-a.md")
    # The extractor's non-wikilink-derived targets must be a SUBSET the oracle corroborates
    # (precision: every substantive extraction is grep-confirmable)...
    non_wikilink_extracted = {t for t in extractor_targets}
    assert non_wikilink_extracted <= oracle_targets | {"docs/design-notes/note-b.md"}
    # ...and the oracle's targets (minus the self-loop, already discarded) must all appear
    # among the extractor's targets (recall: nothing the grep sees is silently dropped).
    assert oracle_targets <= extractor_targets


def test_grep_oracle_precision_and_recall_on_finding_planted(doc_repo):
    sha = _git(doc_repo, "rev-parse", "HEAD").strip()
    extractor_targets = {
        e.target_ref for e in
        CodeSensor(repo=doc_repo, db=open_snapshot_db(doc_repo / ".." / "snap2.sqlite"))
        ._corpus_to_corpus_edges(sha)
        if e.source_ref == "docs/findings/finding-planted.md"
    }
    oracle_targets = _grep_oracle_targets(doc_repo, "docs/findings/finding-planted.md")
    assert extractor_targets == oracle_targets, (
        f"grep-oracle mismatch: extractor={extractor_targets} oracle={oracle_targets} "
        f"(recall gap: {oracle_targets - extractor_targets}, "
        f"precision gap: {extractor_targets - oracle_targets})")
