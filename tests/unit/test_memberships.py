"""core/stores/memberships.py + the D2 lander — the membership store (bp-152).

Every criterion here names the **degenerate input** on which it would pass without testing its
claim, and asserts the precondition that rules it out FIRST (the false-success rule, owner-agreed).
Four separate defects in this wave were "a test that would pass without testing its claim", so the
preconditions are not decoration:

  * §8(a) revert — a do-nothing lander also embeds zero, so the CURRENCY assertions carry the claim,
    and a short-circuiting lander is exhibited beside them to show they have teeth.
  * §8(b) fork — a store that never dedups makes "the other fiber untouched" vacuous, so
    `|V| < Σ chunks` and "the shared atom has 2 current memberships" are asserted first.
  * §8(c) purge — a purge that silently no-ops also "never deletes", so the RECORDED HOLE is what
    is asserted.
  * §8(d) retrieval — an all-current fixture passes any current-filter, so a superseded occupancy
    is asserted to exist first.
  * §8(e) crash — a "crash" injected after all writes makes repair vacuous, so the injection point
    is asserted (|V| grew, |M| did not) and the orphan is asserted OBSERVABLE.
  * §8(f) invariants — each reddens under a seeded violation; a fixture missing any of the four
    shapes (revert, side-branch, shared atom, duplicate L0b pair) makes its invariant vacuous.
  * Item 2's A2 coordinates — a leaf-symbol fixture makes the subset assertion vacuous (span ==
    coverage exactly), so the fixture carries a class with methods AND a module shell.

Deterministic throughout: a fake embedder, a temp lance store, a temp SQLite membership store. No
Ollama, no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from core.ingest.code_corpus import (
    CodeChunk,
    CodeLander,
    atom_id,
    code_memberships,
    code_rows,
    derive_code_chunks,
)
from core.kernel.provenance import Provenance
from core.stores.memberships import (
    EmbedderIdentity,
    Membership,
    MembershipStore,
    current_any_drift,
    purge_atom,
    repair_current_any,
    resolve_occupancies,
)
from core.stores.vectorstore import (
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    VectorStore,
)
from ops.code_snapshot import parse_source
from tests.fixtures.embedding import DIM, FakeEmbedder

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EMB = EmbedderIdentity(model="fake-embedder", dim=DIM)
_EMB_OTHER = EmbedderIdentity(model="a-different-model", dim=DIM)


class _CountingEmbedder(FakeEmbedder):
    """Counts embed calls — the only way to see "reuse" at all: identical text gives an identical
    vector whether it was recomputed or reused, so the vector alone can never show it."""

    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded.extend(texts)
        return super().embed_documents(texts)


@dataclass
class Bench:
    vectors: VectorStore
    memberships: MembershipStore
    embedder: _CountingEmbedder
    lander: CodeLander

    def n_vectors(self) -> int:
        """|V| — atom rows only."""
        return len(self.vectors.atom_rows())


@pytest.fixture
def bench(tmp_path: Path) -> Bench:
    vectors = VectorStore(tmp_path / "v.lance", dim=DIM)
    memberships = MembershipStore(tmp_path / "m.sqlite")
    embedder = _CountingEmbedder()
    return Bench(vectors=vectors, memberships=memberships, embedder=embedder,
                 lander=CodeLander(vectors=vectors, memberships=memberships,
                                   embedder=embedder, embedder_identity=_EMB))


def _chunk(qualname: str, body: str, *, layer: str = LAYER_CODE_AST,
           span: tuple[int, int] = (1, 1)) -> CodeChunk:
    """A hand-built chunk. Used where the ACCEPTANCE needs exact atom arithmetic ("exactly 1 new
    atom"): a real derivation of a real file also recuts its single L0b window on any edit, which
    is correct behavior and useless for counting."""
    return CodeChunk(layer=layer, qualname=qualname, slot_line_start=span[0],
                     slot_line_end=span[1], text=f"# x:{qualname}\n{body}", canonical_body=body)


# ── Item 2 — the fiber round-trip, and the A2 coordinate reading ─────────────────────────

_A2_SRC = (
    '"""Module doc."""\n'          # 1   ← module shell
    "import os\n"                  # 2   ← module shell
    "\n"                           # 3   ← module shell
    "\n"                           # 4   ← module shell
    "class Foo:\n"                 # 5   ← Foo
    '    """Foo doc."""\n'         # 6   ← Foo
    "\n"                           # 7   ← Foo
    "    LIMIT = 3\n"              # 8   ← Foo
    "\n"                           # 9   ← Foo
    "    def bar(self):\n"         # 10  ← Foo.bar
    "        return 1\n"           # 11  ← Foo.bar
    "\n"                           # 12  ← Foo   (blank lines fall to the enclosing owner)
    "    # a stray comment\n"      # 13  ← Foo
    "    def baz(self):\n"         # 14  ← Foo.baz
    "        return 2\n"           # 15  ← Foo.baz
    "\n"                           # 16  ← module shell
    "\n"                           # 17  ← module shell
    "def top():\n"                 # 18  ← top   (a LEAF: span == coverage, the control)
    "    return Foo()\n"           # 19  ← top
)


def test_fiber_round_trips_the_versions_chunks_in_derivation_order(bench: Bench) -> None:
    """Item 2: a fiber written and read back IS the version's chunk list, in `chunk_index` order,
    and Σ fiber sizes = |M| on the fixture."""
    chunks = derive_code_chunks("pkg/a.py", _A2_SRC)
    assert len(chunks) > 3                                  # PRECONDITION: a real derivation
    bench.memberships.write_fiber(code_memberships("pkg/a.py", "blobA", chunks))

    fiber = bench.memberships.fiber("pkg/a.py", "blobA")
    assert [m.chunk_index for m in fiber] == list(range(len(chunks)))
    assert [m.content_id for m in fiber] == [atom_id(c) for c in chunks]
    assert [m.layer for m in fiber] == [c.layer for c in chunks]
    assert sum(bench.memberships.fiber_sizes().values()) == bench.memberships.count()


def test_slot_coordinates_are_the_declared_extent_not_the_atoms_text_coverage(
        bench: Bench) -> None:
    """Item 2 / Amendment A2 / issue #34 — the assertion that makes the RENAME more than cosmetic.

    `slot_line_start`/`slot_line_end` are the SLOT's declared extent, never the atom's text
    coverage. Every leaf-symbol fixture passes either way (there the two coincide exactly), which
    is precisely how this went unnoticed — so the fixture below carries a class WITH METHODS and a
    non-empty MODULE SHELL, and the precondition asserts it does."""
    path = "pkg/a.py"
    src_lines = _A2_SRC.splitlines()
    shape = parse_source(path, "", _A2_SRC)
    by_qual = {s.qualname: s for s in shape.symbols}

    # PRECONDITION (the named degenerate input): a NESTED symbol and a non-empty module shell.
    # A leaf-only fixture makes every "strict subset" below vacuous.
    assert "Foo" in by_qual and "Foo.bar" in by_qual and "Foo.baz" in by_qual
    assert by_qual["Foo"].lineno < by_qual["Foo.bar"].lineno <= by_qual["Foo"].end_lineno

    chunks = derive_code_chunks(path, _A2_SRC)
    bench.memberships.write_fiber(code_memberships(path, "blobA", chunks))
    l0a = {m.slot: m for m in bench.memberships.fiber(path, "blobA")
           if m.layer == LAYER_CODE_AST}
    bodies = {c.qualname: c.canonical_body for c in chunks if c.layer == LAYER_CODE_AST}
    assert set(l0a) >= {"", "Foo", "Foo.bar", "top"}       # PRECONDITION: the shell IS emitted
    assert bodies[""].strip()                              # ...and is NOT empty

    def span_lines(m: Membership) -> list[str]:
        return src_lines[m.slot_line_start - 1:m.slot_line_end]

    # (1) the span is the SYMBOL's declared extent — `owner.lineno, owner.end_lineno`, verbatim
    for q in ("Foo", "Foo.bar", "Foo.baz", "top"):
        assert (l0a[q].slot_line_start, l0a[q].slot_line_end) == (by_qual[q].lineno,
                                                                  by_qual[q].end_lineno)

    # (2) the atom's text coverage is a STRICT SUBSET of that span for the nested case: `Foo`'s
    #     chunk holds the class statement, its docstring, `LIMIT` and the stray comment — but NOT
    #     `bar`, NOT `baz`, which carved their lines out of the parent (innermost-owner partition).
    foo_body = set(bodies["Foo"].splitlines())
    foo_span = set(span_lines(l0a["Foo"]))
    assert foo_body < foo_span                              # ← strict subset, the A2 claim
    assert "    def bar(self):" in foo_span                 # ...in the SPAN
    assert "    def bar(self):" not in foo_body             # ...never in the TEXT
    assert "    LIMIT = 3" in foo_body

    # (3) the module shell is the maximal case: its extent is the ENTIRE FILE by construction,
    #     for four lines of preamble. Rendering the range as "the atom" renders the whole file.
    shell = l0a[""]
    assert (shell.slot_line_start, shell.slot_line_end) == (1, len(src_lines))
    shell_body = set(bodies[""].splitlines())
    assert shell_body < set(src_lines)
    assert len(shell_body) < len(src_lines) / 2             # the divergence is not marginal

    # (4) the CONTROL that makes (2)/(3) meaningful: for a leaf symbol they coincide exactly, so a
    #     leaf-only fixture would have proved nothing at all.
    assert set(bodies["top"].splitlines()) == set(span_lines(l0a["top"]))


def test_a_blob_with_two_identical_windows_stores_two_membership_rows(bench: Bench) -> None:
    """Item 2's falsifier: the atom side dedups, the membership side must NOT.

    `code_rows` collapses duplicates via `by_id.setdefault` — correct for geometry, and WRONG for
    occupancy. Two byte-identical L0b windows in one blob are TWO occupancies with distinct
    `chunk_index` (the F5 multiset pin); inheriting the collapse would make one of them vanish by
    key collision with nothing to see."""
    w = _chunk("", "x = 1\ny = 2\n", layer=LAYER_CODE_TEXT, span=(1, 2))
    chunks = [w, w]
    # PRECONDITION: the two windows really are the same atom — otherwise "two rows" is trivial.
    assert atom_id(chunks[0]) == atom_id(chunks[1])

    bench.vectors.add(code_rows(chunks, [[0.5] * DIM, [0.5] * DIM]))
    bench.memberships.write_fiber(code_memberships("m.py", "blob1", chunks))

    assert len(bench.vectors.atom_rows()) == 1              # the ATOM side dedups (one geometry)
    fiber = bench.memberships.fiber("m.py", "blob1")
    assert len(fiber) == 2                                  # ← the MEMBERSHIP side does not
    assert [m.chunk_index for m in fiber] == [0, 1]
    assert {m.content_id for m in fiber} == {atom_id(w)}
    assert bench.memberships.n_occ(atom_id(w), current_only=False) == 2   # multiset reading
    assert bench.memberships.n_doc(atom_id(w), current_only=False) == 1   # document reading


def test_the_membership_store_is_never_imported_by_the_kernel() -> None:
    """The C5/D3 ring pin, structurally. A `core/kernel/**` import of this module would mechanically
    demote `sourceset` from the inner-ring fixed point; memberships enter the kernel as DATA,
    through the existing `RowSource` protocol. The negative control asserts the scanner works."""
    kernel = sorted((_REPO_ROOT / "core" / "kernel").rglob("*.py"))
    assert len(kernel) > 20                                 # PRECONDITION: the scan sees the tree
    offenders = [p for p in kernel if "core.stores.memberships" in p.read_text(encoding="utf-8")]
    assert offenders == []
    # negative control: the scanner DOES fire where the import exists (the lander is an outer-ring
    # module and imports it) — so the emptiness above is a fact, not a broken check.
    assert "core.stores.memberships" in (
        _REPO_ROOT / "core" / "ingest" / "code_corpus.py").read_text(encoding="utf-8")


# ── Item 4 / §8(a) — the C1 case: land A → B → A ─────────────────────────────────────────

_SRC_A = '"""Doc A."""\n\n\ndef work(x):\n    return x + 1\n'
_SRC_B = '"""Doc A."""\n\n\ndef work(x):\n    return x + 2  # edited\n'


def test_revert_relands_zero_and_currency_converges(bench: Bench) -> None:
    """§8(a), the C1 case — the reason this plan exists.

    Land A → B → A (a real revert: byte-identical bytes return under a new landing). Zero vector
    inserts, zero new membership rows, AND currency converges: A's fiber current, B's not.

    *Degenerate input:* a do-nothing lander ALSO lands zero vectors and zero rows — so the two
    currency assertions are the ones carrying the claim, and the mutation check below exhibits the
    lander that satisfies the counts and fails them."""
    path = "pkg/w.py"
    ch_a = derive_code_chunks(path, _SRC_A)
    ch_b = derive_code_chunks(path, _SRC_B)

    first = bench.lander.land(path, "blobA", ch_a)
    assert first.atoms_embedded > 0                        # PRECONDITION: A's atoms really exist
    v_after_a = bench.n_vectors()

    bench.lander.land(path, "blobB", ch_b)
    assert bench.n_vectors() > v_after_a                   # PRECONDITION: B really differs from A
    v_after_b = bench.n_vectors()
    assert all(m.current for m in bench.memberships.fiber(path, "blobB"))

    embeds_before = len(bench.embedder.embedded)
    third = bench.lander.land(path, "blobA", ch_a)         # ← the revert

    # the reuse half
    assert third.atoms_embedded == 0
    assert third.membership_rows == 0                      # the fiber already stood
    assert len(bench.embedder.embedded) == embeds_before   # nothing re-embedded
    assert bench.n_vectors() == v_after_b                  # |V| did not move (append-only)

    # the CLAIM: currency converged — this is what a short-circuiting lander gets wrong
    assert all(m.current for m in bench.memberships.fiber(path, "blobA"))
    assert not any(m.current for m in bench.memberships.fiber(path, "blobB"))
    assert third.currency.made_current > 0 and third.currency.superseded > 0
    assert current_any_drift(bench.vectors, bench.memberships) == []


def test_a_lander_that_short_circuits_on_an_existing_fiber_leaves_b_current(
        bench: Bench) -> None:
    """The MUTATION CHECK for the test above: the "existing fiber ⇒ no-op" lander — the design's
    own first draft — satisfies every count assertion (zero embeds, zero new rows) and leaves the
    store claiming **B** is HEAD. Without this, "currency converged" could be a claim about a
    property nothing could ever violate."""
    path = "pkg/w.py"
    bench.lander.land(path, "blobA", derive_code_chunks(path, _SRC_A))
    bench.lander.land(path, "blobB", derive_code_chunks(path, _SRC_B))

    # the short-circuit, spelled out: steps 1-3 only, step 4 skipped because step 3 was a no-op
    chunks = derive_code_chunks(path, _SRC_A)
    written = bench.memberships.write_fiber(code_memberships(path, "blobA", chunks))
    assert written == 0                                    # "nothing to do" — the tempting reading

    assert not any(m.current for m in bench.memberships.fiber(path, "blobA"))
    assert all(m.current for m in bench.memberships.fiber(path, "blobB"))   # ← silent corruption

    # ...and the real lander repairs it by convergence, from exactly this state
    bench.lander.land(path, "blobA", chunks)
    assert all(m.current for m in bench.memberships.fiber(path, "blobA"))
    assert not any(m.current for m in bench.memberships.fiber(path, "blobB"))


def test_reuse_is_invalidated_by_a_change_of_embedder(tmp_path: Path) -> None:
    """The embedder pin (owner confirmation 2026-08-01). Atom presence is keyed to
    `(layer, content_hash)` AND the embedder identity, so a model change re-embeds instead of
    serving a vector from another geometry into the same ANN space.

    *Degenerate input:* a suite that only ever exercises one embedder cannot see this bug at all —
    hence a case of its own, with the same-embedder control asserted first so "re-embedded" is
    known to mean "the embedder changed" and not "reuse never worked"."""
    vectors = VectorStore(tmp_path / "v.lance", dim=DIM)
    memberships = MembershipStore(tmp_path / "m.sqlite")
    embedder = _CountingEmbedder()
    chunks = derive_code_chunks("pkg/w.py", _SRC_A)

    same = CodeLander(vectors=vectors, memberships=memberships, embedder=embedder,
                      embedder_identity=_EMB)
    first = same.land("pkg/w.py", "blobA", chunks)
    assert first.atoms_embedded > 0
    # CONTROL: under the SAME embedder, a re-land reuses everything
    assert same.land("pkg/w.py", "blobA", chunks).atoms_embedded == 0

    changed = CodeLander(vectors=vectors, memberships=memberships, embedder=embedder,
                         embedder_identity=_EMB_OTHER)
    after = changed.land("pkg/w.py", "blobA", chunks)
    assert after.atoms_embedded == first.atoms_embedded    # ← every reuse invalidated
    assert after.atoms_reused == 0


# ── Item 5 / §8(b) — fork semantics ──────────────────────────────────────────────────────

def _fork_bench(bench: Bench) -> tuple[CodeChunk, CodeChunk, CodeChunk]:
    """Two files sharing one atom. Hand-built so "exactly 1 new atom" is exact arithmetic."""
    shared = _chunk("shared", "def shared():\n    return 7\n", span=(1, 2))
    only_x = _chunk("only_x", "def only_x():\n    return 1\n", span=(4, 5))
    only_y = _chunk("only_y", "def only_y():\n    return 2\n", span=(4, 5))
    bench.lander.land("x.py", "x1", [shared, only_x])
    bench.lander.land("y.py", "y1", [shared, only_y])
    return shared, only_x, only_y


def test_fork_one_atom_two_memberships_and_an_edit_touches_only_one_lineage(
        bench: Bench) -> None:
    """§8(b). Preconditions FIRST: the shared atom has 2 current memberships and |V| < Σ chunks.

    *Degenerate input:* a store that never dedups makes "the other file's fiber untouched" vacuous
    — it would be untouched because nothing was ever shared. The precondition reddens on it."""
    shared, only_x, only_y = _fork_bench(bench)
    shared_id = atom_id(shared)
    sigma_chunks = bench.memberships.count()               # 2 chunks landed per file, 2 files

    # PRECONDITIONS — without these the whole test is about a store that never shared anything
    assert sigma_chunks == 4
    assert bench.n_vectors() == 3 < sigma_chunks           # ← |V| < Σ chunks: the dedup happened
    assert bench.memberships.n_doc(shared_id) == 2         # the shared atom has 2 current homes
    assert len(bench.memberships.occupancies(shared_id)) == 2

    x_before = bench.memberships.fiber("x.py", "x1")
    embeds_before = len(bench.embedder.embedded)

    # edit ONE file: the same slot, new content
    edited = _chunk("only_y", "def only_y():\n    return 99\n", span=(4, 5))
    report = bench.lander.land("y.py", "y2", [shared, edited])

    assert report.atoms_embedded == 1                      # ← exactly 1 new atom
    assert len(bench.embedder.embedded) == embeds_before + 1
    assert bench.n_vectors() == 4

    # 1 membership swap: y's CURRENT occupancy set differs from before in exactly one atom
    now = {m.content_id for m in bench.memberships.fiber("y.py", "y2")}
    was = {m.content_id for m in bench.memberships.fiber("y.py", "y1")}
    assert now - was == {atom_id(edited)}                  # one in ...
    assert was - now == {atom_id(only_y)}                  # ... one out
    assert shared_id in (now & was)                        # ... the shared node stands

    # the other fiber is BYTE-IDENTICAL — same rows, same currency
    assert bench.memberships.fiber("x.py", "x1") == x_before
    assert all(m.current for m in x_before)
    assert bench.memberships.n_doc(shared_id) == 2         # ...and x.py still holds the shared atom

    # both lineages traverse the shared node; only y's slot minted an edge
    assert bench.memberships.slot_runs("x.py", ["x1"])["shared"] == [shared_id]
    assert bench.memberships.slot_runs("y.py", ["y1", "y2"])["shared"] == [shared_id]
    assert bench.memberships.slot_edges("y.py", ["y1", "y2"])["only_y"] == [
        (atom_id(only_y), atom_id(edited))]
    assert bench.memberships.slot_edges("x.py", ["x1"]) == {"shared": [], "only_x": []}
    assert atom_id(only_x) in bench.memberships.atom_ids_of_path("x.py")


# ── Item 5 / §8(d) — the read path: default is current-view, history is opt-in ────────────

def test_retrieval_resolves_current_occupancies_and_history_is_opt_in(bench: Bench) -> None:
    """§8(d). *Degenerate input:* an all-current fixture passes any current-filter vacuously, so a
    superseded occupancy is asserted to EXIST before anything is read."""
    shared, _only_x, only_y = _fork_bench(bench)
    edited = _chunk("only_y", "def only_y():\n    return 99\n", span=(4, 5))
    bench.lander.land("y.py", "y2", [shared, edited])

    # PRECONDITION: a superseded occupancy exists, and an atom whose EVERY home is superseded
    superseded = [m for m in bench.memberships.occupancies(atom_id(only_y),
                                                           include_superseded=True)
                  if not m.current]
    assert superseded, "fixture holds no superseded occupancy — the filter test would be vacuous"
    assert bench.memberships.n_doc(atom_id(only_y)) == 0
    assert current_any_drift(bench.vectors, bench.memberships) == []

    # the atom whose only home is superseded has current_any=false and drops out of the default
    # search; `include_superseded=True` lifts the prefilter and surfaces it.
    q = bench.embedder.embed_query(only_y.text)
    default_hits = bench.vectors.search(q, k=50, provenances={Provenance.CODE})
    assert atom_id(only_y) not in {str(h["id"]) for h in default_hits}
    with_history = bench.vectors.search(q, k=50, provenances={Provenance.CODE},
                                        include_superseded=True)
    assert atom_id(only_y) in {str(h["id"]) for h in with_history}

    # the JOIN: default consumers see current occupancies only...
    resolved = resolve_occupancies(bench.memberships, default_hits)
    assert resolved and all(o.current for r in resolved for o in r.occupancies)
    # ...and the opt-in surfaces the superseded one
    deep = resolve_occupancies(bench.memberships, with_history, include_superseded=True)
    assert any(not o.current for r in deep for o in r.occupancies)

    # a SHARED atom resolves to all its current homes — one hit, several places (the D3 feature)
    shared_hit = [h for h in with_history if str(h["id"]) == atom_id(shared)]
    assert shared_hit
    (one,) = resolve_occupancies(bench.memberships, shared_hit)
    assert {o.path for o in one.occupancies} == {"x.py", "y.py"}
    assert len(one.occupancies) == 2


# ── Item 6 / §8(c) — append-only, and the one recorded hole ──────────────────────────────

def test_purge_is_the_only_vector_removal_and_it_leaves_a_recorded_hole(bench: Bench) -> None:
    """§8(c). *Degenerate input:* a purge that silently no-ops also satisfies "never deletes" — so
    the assertions are that the hole EXISTS: the row is gone, the memberships are tombstoned (not
    deleted), and every note-lane removal path is shown to act on a note row while leaving |V|
    untouched."""
    shared, _only_x, _only_y = _fork_bench(bench)
    bench.vectors.add([{"id": "n:0", "digest": "noteD", "title": "N",
                        "source_path": "notes/n.md", "chunk_index": 0,
                        "provenance": Provenance.AUTHORED_SOLO.value, "text": "a note",
                        "vector": [0.3] * DIM}])
    v_before = bench.n_vectors()
    m_before = bench.memberships.count()
    assert v_before == 3 and m_before == 4                 # PRECONDITION: something to lose

    # the note-lane removal paths ACT (so this is not "the calls were no-ops")...
    bench.vectors.delete_source("notes/n.md")
    assert len(bench.vectors.all_rows(provenances={Provenance.AUTHORED_SOLO})) == 0
    bench.vectors.delete(digest="noteD")
    bench.vectors.delete_source("x.py")                    # a path an atom row cannot carry
    # ...and reach NO atom row: `source_path`/`digest` are shed, so the predicates cannot match
    assert bench.n_vectors() == v_before
    assert bench.memberships.count() == m_before

    report = purge_atom(bench.vectors, bench.memberships, atom_id(shared))

    assert report.vector_rows_deleted == 1                 # ← the purge OBSERVABLY acted
    assert report.memberships_tombstoned == 2              # ...on both of the shared atom's homes
    assert bench.n_vectors() == v_before - 1               # the ONE admitted |V| decrease
    assert atom_id(shared) not in {str(r["id"]) for r in bench.vectors.atom_rows()}

    # the hole is RECORDED, not silent: the occupancies survive, tombstoned and not current
    holes = bench.memberships.occupancies(atom_id(shared), include_superseded=True)
    assert len(holes) == 2 and all(h.tombstoned and not h.current for h in holes)
    assert bench.memberships.count() == m_before           # nothing was deleted from M
    assert bench.memberships.n_doc(atom_id(shared), current_only=False) == 0


# ── Item 6 / §8(e) — the D8 crash property ───────────────────────────────────────────────

def test_a_crash_between_the_vector_insert_and_the_fiber_write_repairs_on_reland(
        bench: Bench, monkeypatch: pytest.MonkeyPatch) -> None:
    """§8(e). *Degenerate input:* a "crash" injected AFTER all writes makes repair vacuous — so the
    injection point is asserted (|V| grew, |M| did not), and the orphan is asserted OBSERVABLE
    before anything is repaired. "Nothing dangles" is also true of a store that never wrote."""
    path = "pkg/w.py"
    chunks = derive_code_chunks(path, _SRC_A)
    v_before, m_before = bench.n_vectors(), bench.memberships.count()

    def boom(_rows: object) -> int:
        raise RuntimeError("crash: power lost between the vector insert and the fiber write")

    monkeypatch.setattr(bench.memberships, "write_fiber", boom)
    with pytest.raises(RuntimeError):
        bench.lander.land(path, "blobA", chunks)
    monkeypatch.undo()

    # THE INJECTION POINT, asserted: vectors landed, the fiber did not
    assert bench.n_vectors() > v_before
    assert bench.memberships.count() == m_before
    assert bench.memberships.fiber(path, "blobA") == []

    # THE ORPHAN IS OBSERVABLE — dormant geometry with no occupancy, and invisible to the default
    # search because `current_any` is false at insert (D8's write order is what makes this safe)
    orphans = bench.memberships.orphan_atom_ids()
    assert orphans and orphans == {atom_id(c) for c in chunks}
    assert all(not bool(r["current"]) for r in bench.vectors.atom_rows())
    assert current_any_drift(bench.vectors, bench.memberships) == []

    # the idempotent re-land REPAIRS: it adopts the orphans (zero re-embeds) and nothing dangles
    embeds_before = len(bench.embedder.embedded)
    report = bench.lander.land(path, "blobA", chunks)
    assert report.atoms_embedded == 0                      # adopted, not re-embedded
    assert len(bench.embedder.embedded) == embeds_before
    assert bench.memberships.orphan_atom_ids() == set()
    assert len(bench.memberships.fiber(path, "blobA")) == len(chunks)
    assert all(m.current for m in bench.memberships.fiber(path, "blobA"))
    assert current_any_drift(bench.vectors, bench.memberships) == []


def test_repair_current_any_rebuilds_the_cache_from_membership_truth(bench: Bench) -> None:
    """R3: `current_any` is a CACHE over membership truth, with a rebuild path. Seeded drift first,
    so "the repair worked" is not a statement about a store that was never wrong."""
    shared, _x, _y = _fork_bench(bench)
    assert current_any_drift(bench.vectors, bench.memberships) == []   # PRECONDITION: no drift yet

    bench.vectors.set_current_any([atom_id(shared)], False)            # seed the drift by hand
    assert current_any_drift(bench.vectors, bench.memberships) == [atom_id(shared)]

    raised, lowered = repair_current_any(bench.vectors, bench.memberships)
    assert (raised, lowered) == (1, 0)
    assert current_any_drift(bench.vectors, bench.memberships) == []


# ── Item 7 / §8(f) — the §4 invariants on the degenerate fixture ─────────────────────────

@dataclass
class Fixture:
    bench: Bench
    chain: list[str]
    side_branch: str
    shared_id: str
    dup_id: str
    v_trace: list[int]


@pytest.fixture
def degenerate(bench: Bench) -> Fixture:
    """The §8(f) fixture, carrying ALL FOUR shapes — a fixture missing any one makes the matching
    invariant vacuous: a REVERT (so adjacent-collapse is distinguishable from distinct-collapse), a
    MERGE SIDE-BRANCH version (so "chain members ⊊ ledger versions" bites), a SHARED atom (so
    `n_doc` is not always 1), and a DUPLICATE L0b WINDOW PAIR (so the multiset reading bites)."""
    path = "pkg/w.py"
    v_trace: list[int] = []

    shared = _chunk("shared", "def shared():\n    return 7\n", span=(1, 2))
    work_a = _chunk("work", "def work():\n    return 1\n", span=(4, 5))
    work_b = _chunk("work", "def work():\n    return 2\n", span=(4, 5))
    work_s = _chunk("work", "def work():\n    return 3  # side branch\n", span=(4, 5))
    dup = _chunk("", "x = 1\n", layer=LAYER_CODE_TEXT, span=(7, 7))

    for blob, chunks in (("A", [shared, work_a, dup, dup]),
                         ("B", [shared, work_b, dup, dup]),
                         ("S", [shared, work_s, dup, dup]),      # the side branch (off-chain)
                         ("A", [shared, work_a, dup, dup])):     # ← the revert
        bench.lander.land(path, blob, chunks, head_blob_sha=blob)
        v_trace.append(bench.n_vectors())
    # the shared atom also lives in a SECOND path, so n_doc > 1 somewhere
    bench.lander.land("other.py", "o1", [shared])
    v_trace.append(bench.n_vectors())
    # HEAD is A (the revert), reconciled last so the store is in its converged state
    bench.lander.reconcile(path, "A")
    return Fixture(bench=bench, chain=["A", "B", "A"], side_branch="S",
                   shared_id=atom_id(shared), dup_id=atom_id(dup), v_trace=v_trace)


def test_the_fixture_carries_all_four_shapes(degenerate: Fixture) -> None:
    """The precondition for everything below. A fixture missing a shape makes its invariant
    vacuous, so the shapes are asserted once, here, rather than assumed four times."""
    m = degenerate.bench.memberships
    path = "pkg/w.py"
    work = m.slot_runs(path, degenerate.chain)["work"]
    assert len(work) == 3 and work[0] == work[2] != work[1]                  # a REVERT exists
    assert (path, "S") in m.fibers() and "S" not in degenerate.chain         # a side branch exists
    assert m.n_doc(degenerate.shared_id) >= 2                                # a shared atom exists
    assert len([x for x in m.fiber(path, "A")
                if x.content_id == degenerate.dup_id]) == 2                  # a duplicate pair


def test_per_slot_edges_equal_runs_minus_one_and_a_revert_is_not_collapsed(
        degenerate: Fixture) -> None:
    """§4's first invariant, and the C1 formulation that gives it content.

    `|edges| = |runs| - 1` is true of any consecutive-pair construction — what is FALSIFIABLE is
    the collapse rule: A → B → A must give 3 runs and 2 edges (adjacent collapse), not 2 and 1
    (distinct collapse). The seeded violation is distinct-collapse over the same chain."""
    m = degenerate.bench.memberships
    path, chain = "pkg/w.py", degenerate.chain
    runs, edges = m.slot_runs(path, chain), m.slot_edges(path, chain)

    assert set(runs) == {"shared", "work"}                 # L0b is chainless (R4), so `dup` is out
    for slot in runs:
        assert len(edges[slot]) == len(runs[slot]) - 1     # ← the invariant

    # the revert survives: 3 runs, 2 edges, and the second edge RETURNS to the first occupant
    assert len(runs["work"]) == 3 and len(edges["work"]) == 2
    assert edges["work"][0][1] == edges["work"][1][0]
    assert edges["work"][1][1] == runs["work"][0]          # ...back to A's occupant
    # ...and it is a real distinction: distinct-collapse over the SAME chain gives 2 runs / 1 edge
    assert len(dict.fromkeys(runs["work"])) == 2

    # an unchanged slot chains as ONE run and NO edge — the "never mint a spurious edge" half
    assert len(runs["shared"]) == 1 and edges["shared"] == []


def test_a_side_branch_fiber_is_a_member_of_m_but_sits_on_no_chain(degenerate: Fixture) -> None:
    """D4/F3: chains are first-parent, the ledger walks all commits — so a side-branch version is a
    real member of M (it contributes to |M| and to n(v)) and contributes to NO edge count.
    Quantifying the edge invariant over all fibers instead of chain members is the error."""
    m = degenerate.bench.memberships
    path = "pkg/w.py"
    side = m.fiber(path, degenerate.side_branch)
    side_only = {x.content_id for x in side} - {
        x.content_id for b in degenerate.chain for x in m.fiber(path, b)}
    assert side_only, "PRECONDITION: the side branch holds an atom no chain fiber holds"

    assert sum(len(m.fiber(path, b)) for b in {*degenerate.chain, degenerate.side_branch}) \
        <= m.count()
    for cid in side_only:
        assert m.n_occ(cid, current_only=False) > 0        # it IS in M
        assert all(cid not in run
                   for run in m.slot_runs(path, degenerate.chain).values())   # ...on no chain


def test_fiber_sizes_sum_to_the_membership_count(degenerate: Fixture) -> None:
    """§4: Σ fiber sizes = |M| — the fibration is a PARTITION, so no occupancy is outside a fiber
    and none is double-counted. The seeded violation is a `fiber()` that quietly drops superseded
    rows, which is the realistic way this breaks: the fixture holds superseded fibers (asserted),
    so the mutation genuinely bites."""
    m = degenerate.bench.memberships
    assert sum(len(m.fiber(p, b)) for p, b in m.fibers()) == m.count()

    superseded = [(p, b) for p, b in m.fibers() if not any(x.current for x in m.fiber(p, b))]
    assert superseded, "PRECONDITION: without a superseded fiber the mutation below is a no-op"

    class _CurrentOnlyFiber(MembershipStore):
        def fiber(self, path: str, blob_sha: str) -> list[Membership]:
            return [x for x in super().fiber(path, blob_sha) if x.current]

    mutated = _CurrentOnlyFiber(m.path)
    assert sum(len(mutated.fiber(p, b)) for p, b in mutated.fibers()) < mutated.count()
    mutated.close()


def test_current_any_is_equivalent_to_a_positive_current_document_count(
        degenerate: Fixture) -> None:
    """§4/R3: `current_any(v) ⇔ n_doc(v, t) > 0`. The fixture holds BOTH kinds of atom (asserted),
    so the equivalence is not satisfied by a store where every atom is current."""
    b = degenerate.bench
    rows = b.vectors.atom_rows()
    assert any(bool(r["current"]) for r in rows) and any(not bool(r["current"]) for r in rows)

    for r in rows:
        assert bool(r["current"]) == (b.memberships.n_doc(str(r["id"])) > 0)
    assert current_any_drift(b.vectors, b.memberships) == []

    # seeded violation: one flag flipped by hand and the ratchet names exactly that atom
    victim = str(rows[0]["id"])
    b.vectors.set_current_any([victim], not bool(rows[0]["current"]))
    assert current_any_drift(b.vectors, b.memberships) == [victim]


def test_the_vector_plane_never_shrinks_except_across_a_purge(degenerate: Fixture) -> None:
    """§4: append-only ⇒ no test may ever observe |V| decrease, except across a LOGGED purge. The
    trace is recorded while the fixture is built, so this reads real landings (including a revert
    and a side branch) rather than a store nothing ever wrote to."""
    b = degenerate.bench
    trace = degenerate.v_trace
    assert len(trace) >= 4 and trace[0] > 0                # PRECONDITION: real landings happened
    assert trace == sorted(trace)                          # monotone ↑ across every land
    assert trace[-1] > trace[0]                            # ...and it genuinely grew

    before = b.n_vectors()
    b.lander.reconcile("pkg/w.py", "A")                    # currency work never removes geometry
    assert b.n_vectors() == before

    report = purge_atom(b.vectors, b.memberships, degenerate.shared_id)
    assert report.vector_rows_deleted == 1                 # the ONE exception, and it is logged
    assert b.n_vectors() == before - 1
