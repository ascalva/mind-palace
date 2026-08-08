"""core/ingest/code_corpus.py — the code embed lane (bp-092 Items 2–3; bp-151 D0).

Pure derivation (L0a byte-cover + bit-identical re-derivability = F-CI2; L0b window reuse; L1
prose), the STRUCTURAL CODE mint (F-CI1: no provenance parameter anywhere), and blob-sha-keyed
incremental sync (the falsifier: an unchanged file must re-embed NOTHING). No Ollama — a
deterministic fake embedder.

bp-151 adds the D0 section: identity (`content_hash`) is the header-free CANONICAL body while the
embed `text` keeps its coordinate header, so a rename or a line shift mints ZERO atoms
(dn-vector-membership-store §8(h)(i), owner-ruled 2026-07-27).
"""

from __future__ import annotations

import inspect
import subprocess
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from core.ingest import code_corpus
from core.ingest.code_corpus import (
    CodeChunk,
    CodeCorpusSync,
    atom_id,
    code_rows,
    derive_code_chunks,
)
from core.kernel.ingest.chunk import chunk_text
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.stores.memberships import EmbedderIdentity, MembershipStore
from core.stores.vectorstore import (
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    LAYER_CODEDOC,
    VectorStore,
    is_code_atom_row,
)
from ops.code_snapshot import parse_source
from tests.fixtures.embedding import DIM, FakeEmbedder

_SRC = (
    '"""Module doc."""\n'                        # 1
    "import json\n"                              # 2
    "\n"                                         # 3
    "# a module-grain comment\n"                 # 4
    "TOP = 1\n"                                  # 5
    "\n"                                         # 6
    "class Thing:\n"                             # 7
    '    """Class doc."""\n'                     # 8
    "    def method(self, x):\n"                 # 9
    '        """Method doc."""\n'                # 10
    "        # inner comment\n"                  # 11
    "        return x + TOP\n"                   # 12
    "\n"                                         # 13
    "def top_level():\n"                         # 14
    "    return Thing()\n"                       # 15
)


# ── L0a: byte-cover (F-CI2) + re-derivability + headers ─────────────────────────────────

def _l0a(src: str) -> list[CodeChunk]:
    return [c for c in derive_code_chunks("m.py", src) if c.layer == LAYER_CODE_AST]


def test_l0a_slices_byte_cover_every_source_line_once():
    lines = _SRC.splitlines()
    bodies: list[str] = []
    for c in _l0a(_SRC):
        # each L0a chunk is "header\nbody"; drop the deterministic header line, keep source lines
        _header, _, body = c.text.partition("\n")
        bodies.extend(body.split("\n"))
    assert sorted(bodies) == sorted(lines)      # every source line appears exactly once (F-CI2)


def test_l0a_is_bit_identically_rederivable():
    assert derive_code_chunks("m.py", _SRC) == derive_code_chunks("m.py", _SRC)


def test_l0a_headers_name_the_symbol():
    by_qual = {c.qualname: c for c in _l0a(_SRC)}
    assert by_qual["Thing.method"].text.startswith("# m.py:Thing.method(self, x)")
    assert by_qual["top_level"].text.startswith("# m.py:top_level()")
    assert by_qual[""].text.startswith("# m.py\n")   # the module shell
    # the shell owns the imports/module preamble; the method owns its body incl. its inner comment
    assert "import json" in by_qual[""].text
    assert "# inner comment" in by_qual["Thing.method"].text
    # fiber coordinates carried on the chunk
    assert (by_qual["Thing.method"].slot_line_start,
            by_qual["Thing.method"].slot_line_end) == (9, 12)


def test_l0a_oversized_slice_hard_splits_via_chunk_text():
    big = "def huge():\n" + "\n".join(f"    x{i} = {i}" for i in range(400))
    chunks = _l0a(big)
    assert len(chunks) > 1                        # a >max_chars symbol splits into several chunks
    assert all(c.qualname == "huge" for c in chunks)


# ── L0b: reuses the ONE window machinery over raw source ────────────────────────────────

def test_l0b_windows_equal_chunk_text_over_raw_source():
    l0b = [c.text for c in derive_code_chunks("m.py", _SRC) if c.layer == LAYER_CODE_TEXT]
    assert l0b == [c.text for c in chunk_text(_SRC)]   # DRY: the note chunker, unmodified


# ── L1: docstrings + comments as prose, source order ────────────────────────────────────

def test_l1_prose_carries_docstrings_and_comments():
    l1 = " ".join(c.text for c in derive_code_chunks("m.py", _SRC) if c.layer == LAYER_CODEDOC)
    assert "Module doc." in l1 and "Method doc." in l1 and "Class doc." in l1
    assert "a module-grain comment" in l1 and "inner comment" in l1


def test_parse_error_file_still_embeds_as_text_plus_shell():
    chunks = derive_code_chunks("bad.py", "def broken(:\n  pass\n")
    layers = {c.layer for c in chunks}
    assert LAYER_CODE_TEXT in layers                 # L0b windows always land
    assert LAYER_CODE_AST in layers                  # a module-shell L0a covers the whole file


# ── D0 (bp-151): identity is the header-free canonical body, embed text keeps its header ─

_BIG_SRC = "def huge():\n" + "\n".join(f"    x{i} = {i}" for i in range(400)) + "\n"
_FILLER = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor"


def _prose_src(n_comments: int = 30) -> str:
    """A prose-heavy fixture: enough docstrings + comments that L1 spans ≥2 windows at the DEFAULT
    budget, so there is a real window boundary to move. A 0–1-item file is §8(i)'s named degenerate
    input and would pass every claim below vacuously."""
    lines = [f'"""Module doc: {_FILLER}."""', "import json", ""]
    for i in range(n_comments):
        lines.append(f"# comment {i}: {_FILLER}")
        lines.append(f"X{i} = {i}")
    lines += ["", "def worker(a, b):", f'    """Worker doc: {_FILLER}."""', "    return a + b"]
    return "\n".join(lines) + "\n"


def _at(path: str, src: str, layer: str, **kw: int) -> list[CodeChunk]:
    return [c for c in derive_code_chunks(path, src, **kw) if c.layer == layer]


def _atoms(chunks: list[CodeChunk]) -> set[tuple[str, str]]:
    """The ATOM identity D0 pins: (layer, canonical content hash). NB the store row id still carries
    the path (`{path}:{layer}:{hash}`) — the path-free id is D1's change, bp-152, not this one."""
    return {(c.layer, c.content_hash) for c in chunks}


def _raw_atoms(chunks: list[CodeChunk]) -> set[tuple[str, str]]:
    """The PRE-D0 identity — sha256 over the full embed text — kept only as the counterfactual that
    gives the acceptance tests teeth: '0 minted' says nothing unless the old rule DID mint."""
    return {(c.layer, sha256(c.text.encode("utf-8")).hexdigest()) for c in chunks}


def test_l0a_identity_is_the_canonical_body_while_the_embed_text_keeps_its_header():
    """Item 1: the same bytes at two different paths give L0a chunks with EQUAL content_hash and
    UNEQUAL text. Falsified if the hashes differ (the header is still inside identity) or if `text`
    goes header-free (the embed rendering must keep its retrieval context, R7)."""
    here, moved = "pkg/thing.py", "pkg/deeper/renamed_thing.py"
    a = {c.qualname: c for c in _at(here, _SRC, LAYER_CODE_AST)}
    b = {c.qualname: c for c in _at(moved, _SRC, LAYER_CODE_AST)}
    # PRECONDITION: a non-empty, identical symbol set at both paths — an empty derivation satisfies
    # every equality below vacuously.
    assert a and set(a) == set(b)
    assert len(here) != len(moved)                        # a LENGTH-changing move, the hard case
    for q, ca in a.items():
        cb = b[q]
        assert ca.content_hash == cb.content_hash         # identity survives the move (D0)
        assert ca.canonical_body == cb.canonical_body
        assert ca.text != cb.text                         # ...the embed rendering does not
        assert ca.text.startswith(f"# {here}")            # the header rides ON the embed text
        assert cb.text.startswith(f"# {moved}")
        assert here not in ca.canonical_body              # ...and never inside identity


def test_l1_windows_are_cut_over_canonical_prose_so_a_rename_recuts_nothing():
    """Item 2: L1 window boundaries no longer depend on path length. Falsified if the hash SETS
    differ at two paths — that is strip-at-hash-only (the note measured a residual 7 atoms there),
    not the windowing pin."""
    src = _prose_src()
    here, moved = "pkg/thing.py", "pkg/much/deeper/renamed_thing_module.py"
    a, b = _at(here, src, LAYER_CODEDOC), _at(moved, src, LAYER_CODEDOC)
    # PRECONDITION: the prose spans ≥2 windows at both paths — one window has no interior boundary
    # to move and would pass vacuously.
    assert len(a) >= 2 and len(b) >= 2
    assert {c.content_hash for c in a} == {c.content_hash for c in b}
    assert len(a) == len(b)                               # same window count: boundaries held
    for chunks, p in ((a, here), (b, moved)):
        for c in chunks:
            assert c.text.startswith(f"# {p}\n")          # ONE strippable coordinate line
            assert c.text.count(f"# {p}") == 1            # no per-item headers (they live in
            assert f"# {p}:" not in c.text                # memberships now, bp-152)
            assert c.qualname == ""                       # L1 stays slotless (R4) — no re-slot


def test_rename_mints_zero_new_atoms_across_all_three_layers():
    """§8(h), the spine: rename an embedded file (same bytes, new path) → 0 new atoms. The measured
    ladder on the REAL chunkers over `core/ingest/code_corpus.py` at 45c4a15: **38** atoms minted
    under headers-in-hash (the note's probe number), **10** under strip-at-hash-only, **0** here."""
    src = _prose_src()
    here, moved = "core/thing.py", "core/renamed_thing_module.py"
    before, after = derive_code_chunks(here, src), derive_code_chunks(moved, src)
    # PRECONDITION: the atoms pre-exist in ALL THREE layers. §8(h)'s named degenerate input is a
    # never-embedded file — it mints 0 trivially.
    layers = Counter(c.layer for c in before)
    assert layers[LAYER_CODE_AST] and layers[LAYER_CODE_TEXT] and layers[LAYER_CODEDOC]
    assert len(here) != len(moved)                        # the path LENGTH changed (recut pressure)
    assert {c.text for c in after} != {c.text for c in before}   # the rename IS observable
    assert _atoms(after) - _atoms(before) == set()        # ← the claim: nothing minted
    assert _atoms(after) == _atoms(before)
    # ...and it has TEETH: the SAME rename mints under the pre-D0 identity.
    assert len(_raw_atoms(after) - _raw_atoms(before)) > 0


def _n_prose_items(path: str, src: str) -> int:
    """The L1 item count — module docstring + symbol docstrings + inline comments."""
    shape = parse_source(path, "", src)
    return ((1 if shape.docstring else 0)
            + sum(1 for s in shape.symbols if s.docstring) + len(shape.comments))


def test_top_of_file_insert_mints_zero_codedoc_atoms():
    """§8(i) — finding-0167's owed L1 line-header check, discharged. One line inserted at the top of
    the code (after the module docstring, so the docstring stays one) shifts every prose item's
    lineno without changing any prose: under the old interleaved `# {path}:{lineno}` headers that
    alone recut and re-minted every downstream window (the note measured 10)."""
    path = "core/thing.py"
    src = _prose_src()
    head, rest = src.split("\n", 1)                       # line 1 is the module docstring
    shifted = f"{head}\nimport os\n{rest}"                # ← the one-line insert at the top
    before, after = derive_code_chunks(path, src), derive_code_chunks(path, shifted)
    l1_before = [c for c in before if c.layer == LAYER_CODEDOC]
    # PRECONDITION 1 (§8(i)'s named degenerate input): ≥2 prose items — a 0–1-item file passes
    # vacuously. PRECONDITION 2: those items span ≥2 windows, so a recut is possible at all.
    assert _n_prose_items(path, src) >= 2
    assert len(l1_before) >= 2
    # PRECONDITION 3: the edit was REAL and prose-neutral — every prose item's source line moved,
    # the file's other layers noticed, and no prose item was added or removed. Without this, "0 new
    # codedoc atoms" could just mean nothing happened.
    assert (parse_source(path, "", shifted).comments[0].lineno
            == parse_source(path, "", src).comments[0].lineno + 1)
    assert _n_prose_items(path, shifted) == _n_prose_items(path, src)
    assert ({c.content_hash for c in after if c.layer == LAYER_CODE_AST}
            != {c.content_hash for c in before if c.layer == LAYER_CODE_AST})
    doc_before = {c.content_hash for c in l1_before}
    doc_after = {c.content_hash for c in after if c.layer == LAYER_CODEDOC}
    assert doc_after - doc_before == set()                # ← 0 new codedoc atoms
    assert doc_after == doc_before


def test_every_chunk_pairs_a_headered_embed_text_with_a_header_free_canonical_body():
    """The structural ratchet on D0's two renderings: for the HEADERED layers (L0a, L1) `text` is
    exactly one coordinate line + `canonical_body`; for the headerless layer (L0b) they are the
    same string. A construction site that ever passed the wrong canonical body — silent identity
    corruption, the exact failure class D0 exists to remove — reddens HERE, at every site."""
    path = "pkg/mod.py"
    prose = _prose_src()
    # PRECONDITION: the fixtures together reach all four construction sites — L0a whole, L0a
    # oversized (the re-headered window branch), L0b window, L1 window.
    assert {c.layer for c in derive_code_chunks(path, _SRC)} == {LAYER_CODE_AST, LAYER_CODE_TEXT,
                                                                 LAYER_CODEDOC}
    assert len(_at(path, _BIG_SRC, LAYER_CODE_AST)) > 1
    assert len(_at(path, prose, LAYER_CODEDOC)) >= 2
    for src in (_SRC, _BIG_SRC, prose):
        for c in derive_code_chunks(path, src):
            if c.layer == LAYER_CODE_TEXT:
                assert c.canonical_body == c.text         # headerless by construction
            else:
                header, sep, rest = c.text.partition("\n")
                assert sep == "\n" and rest == c.canonical_body
                assert header.startswith(f"# {path}")
                assert path not in c.canonical_body       # the mutable coordinate stays out


def test_l0a_oversize_cut_is_canonical_body_scoped():
    """bp-151's deliberate tripwire, formerly `test_l0a_oversize_threshold_is_the_one_rename_
    residue`: it pinned issue #31, the single case where §8(h) did NOT hold as built — the
    oversize cut was decided over the HEADER-BEARING length (`len(header + body) <= max_chars`),
    so a slice sitting at the budget flipped whole↔windowed when the path lengthened, minting one
    spurious atom. Its docstring named its own re-entry verbatim: "if #31 is ruled that way, this
    expectation becomes 0 and this test reddens — that redness is the tripwire." Amendment A1.2
    (dn-vector-membership-store) ruled it that way 2026-08-06; bp-155 landed the one-token fix
    (`len(body) <= max_chars`) and this test reddened exactly as designed. Converted here to
    assert the residue is GONE, guarding that the cut stays canonical-body-scoped going forward."""
    here, moved = "a/m.py", "a/much_longer_module_name.py"
    body = "def f():\n    y = 1\n\n    return y"
    budget = len(f"# {here}:f()") + 1 + len(body)         # exactly at the budget at the short path
    # PRECONDITION: the rename still straddles the threshold under the OLD (header-bearing) rule —
    # that IS the mechanism under test. Without this, "0 minted" could mean the fixture never
    # crossed the budget at either path, and the test would prove nothing.
    assert len(f"# {here}:f()") + 1 + len(body) <= budget < len(f"# {moved}:f()") + 1 + len(body)
    a = _at(here, body + "\n", LAYER_CODE_AST, max_chars=budget)
    b = _at(moved, body + "\n", LAYER_CODE_AST, max_chars=budget)
    assert len(a) == 1                                    # whole at the short path
    assert len(b) == 1                                    # ...and now still whole at the long one
    assert len({c.content_hash for c in b} - {c.content_hash for c in a}) == 0   # issue #31, closed


# ── the STRUCTURAL CODE mint (F-CI1: no provenance parameter anywhere) ──────────────────

def test_code_rows_hardcode_code_provenance():
    chunks = derive_code_chunks("m.py", _SRC)
    rows = code_rows(chunks, [[0.0] * DIM for _ in chunks])
    assert {r["provenance"] for r in rows} == {Provenance.CODE.value}
    assert Provenance.CODE not in MIRROR_READABLE    # ∉ the mirror set
    # ids are (layer, content)-scoped so identical text in two layers stays distinct
    assert len({r["id"] for r in rows}) == len(rows)


# ── D1 (bp-152) Item 1: the atom row — path-free identity, occupancy shed, provenance KEPT ──

def test_the_same_body_at_two_paths_is_one_atom_row_keyed_layer_and_hash():
    """Item 1's acceptance. The same chunk body appearing in two different FILES yields ONE row,
    whose id is `f"{layer}:{content_hash}"`. That single character-level change — dropping the path
    from the id — IS the atom model: it promotes `code_rows`' old per-path dedup to corpus-wide
    dedup (PD-1, owner-ruled in).

    *Falsifier:* two rows appear, i.e. the id still carries the path."""
    body = "def shared_helper(x):\n    return x * 2\n"
    a = [c for c in derive_code_chunks("pkg/one.py", body) if c.layer == LAYER_CODE_AST]
    b = [c for c in derive_code_chunks("pkg/much_deeper/two.py", body)
         if c.layer == LAYER_CODE_AST]
    # PRECONDITION: the two derivations really are at DIFFERENT paths of different length, and
    # each emits the same non-empty symbol set — otherwise "one row" is trivially true.
    assert a and {c.qualname for c in a} == {c.qualname for c in b}
    assert len("pkg/one.py") != len("pkg/much_deeper/two.py")

    rows_a = code_rows(a, [[0.1] * DIM for _ in a])
    rows_b = code_rows(b, [[0.1] * DIM for _ in b])
    assert {r["id"] for r in rows_a} == {r["id"] for r in rows_b}      # ← ONE atom, not two
    for r, c in zip(rows_a, a, strict=True):
        assert r["id"] == f"{c.layer}:{c.content_hash}" == atom_id(c)
        assert "pkg/one.py" not in str(r["id"])                       # the path is GONE from the id


def test_every_atom_row_keeps_its_provenance_and_sheds_its_occupancy():
    """Item 1's other half, and its falsifier is the worse outcome: `provenance` absent or empty on
    an atom row would not weaken the mirror firewall, it would REMOVE it — the firewall is a row
    prefilter (`provenance IN (...)`, `prefilter=True`) and holds only if the column is there to
    filter. So this asserts presence AND equality to CODE on every row, and asserts the occupancy
    columns really did go (otherwise "shed" would be a docstring claim)."""
    chunks = derive_code_chunks("m.py", _SRC)
    rows = code_rows(chunks, [[0.2] * DIM for _ in chunks])
    assert rows                                                        # PRECONDITION: rows exist
    for r in rows:
        assert r["provenance"] == Provenance.CODE.value                # present AND correct
        assert (r["source_path"], r["digest"], r["title"]) == ("", "", "")
        assert (r["chunk_index"], r["qualname"]) == (0, "")
        assert (r["line_start"], r["line_end"]) == (0, 0)
        assert is_code_atom_row(r)
    # one-layer-one-provenance: an atom never spans strata (the PD-2 fence, as a test invariant)
    by_layer: dict[str, set[str]] = {}
    for r in rows:
        by_layer.setdefault(str(r["layer"]), set()).add(str(r["provenance"]))
    assert set(by_layer) == {LAYER_CODE_AST, LAYER_CODE_TEXT, LAYER_CODEDOC}
    assert all(v == {Provenance.CODE.value} for v in by_layer.values())
    # ...and identity keeps the layer inside it, so the same text in two layers stays two atoms
    assert len({r["id"] for r in rows}) == len(rows)


def test_no_public_api_accepts_a_provenance_parameter():
    """F-CI1, structural: a code-lane API with a provenance argument is a laundering surface."""
    for name, obj in vars(code_corpus).items():
        if name.startswith("_") or not callable(obj):
            continue
        try:
            params = inspect.signature(obj).parameters
        except (ValueError, TypeError):
            continue
        assert "provenance" not in params and "provenances" not in params, name


# ── incremental sync: the seed + the "unchanged file = zero embeds" falsifier ───────────

class _CountingEmbedder(FakeEmbedder):
    def __init__(self) -> None:
        self.embedded_texts = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts += len(texts)
        return super().embed_documents(texts)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _sync(repo: Path, tmp_path: Path, embedder) -> CodeCorpusSync:
    """A wired sync driver. `memberships` and `embedder_identity` are REQUIRED fields (bp-152):
    the lander cannot record occupancy without the first, and cannot decide reuse honestly without
    the second — a reuse across two embedders mixes geometries in one ANN space."""
    return CodeCorpusSync(
        repo=repo,
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        embedder=embedder,
        memberships=MembershipStore(tmp_path / "m.sqlite"),
        embedder_identity=EmbedderIdentity(model="fake", dim=DIM),
    )


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "a.py").write_text("def a():\n    return 1\n")
    (r / "b.py").write_text("def b():\n    return 2\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "one")
    return r


def test_seed_then_unchanged_resync_embeds_nothing(repo, tmp_path):
    emb = _CountingEmbedder()
    sync = _sync(repo, tmp_path, emb)
    store = sync.store

    seeded = sync.seed()
    assert seeded.changed_files == 2 and seeded.embedded_rows > 0
    after_seed = emb.embedded_texts
    code_count = len(store.all_rows(provenances={Provenance.CODE}))
    assert code_count == store.count()               # only code rows in this store
    fibers = set(sync.memberships.fibers())
    assert {p for p, _ in fibers} == {"a.py", "b.py"}   # the D-fiber state is the fiber set now

    # a second sync with NO change: zero new embeds, store unchanged (the incremental claim)
    again = sync.sync()
    assert again.changed_files == 0 and again.embedded_rows == 0
    assert emb.embedded_texts == after_seed
    assert len(store.all_rows(provenances={Provenance.CODE})) == code_count
    assert set(sync.memberships.fibers()) == fibers


def test_changed_blob_reembeds_only_that_file(repo, tmp_path):
    emb = _CountingEmbedder()
    sync = _sync(repo, tmp_path, emb)
    sync.seed()
    baseline = emb.embedded_texts

    (repo / "a.py").write_text("def a():\n    return 1 + 1  # changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")

    report = sync.sync()
    assert report.changed_files == 1 and report.unchanged_files == 1
    assert emb.embedded_texts > baseline             # a.py re-embedded
    # [banner: correction] the changed text is found through the MEMBERSHIP fiber now — the atom
    # row carries no `source_path` to filter on (D1). Same claim, resolved through the join (D3).
    head = _git(repo, "rev-parse", "HEAD:a.py").strip()
    by_id = {str(r["id"]): r for r in sync.store.all_rows(provenances={Provenance.CODE})}
    a_texts = [str(by_id[m.content_id]["text"]) for m in sync.memberships.fiber("a.py", head)]
    assert any("changed" in t for t in a_texts)


def test_vanished_file_is_retained_but_marked_superseded(repo, tmp_path):
    """Keep-and-link (dn-temporal-code-corpus D2, bp-099 — reverses the old delete): a vanished
    file's rows are RETAINED (never deleted) but flipped current=false, so the current-view no
    longer surfaces them while history is preserved."""
    sync = _sync(repo, tmp_path, FakeEmbedder())
    sync.seed()
    b_head = _git(repo, "rev-parse", "HEAD:b.py").strip()
    v_before = len(sync.store.atom_rows())
    assert sync.memberships.fiber("b.py", b_head)     # PRECONDITION: b.py really landed
    (repo / "b.py").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "drop b")
    report = sync.sync()
    assert report.deleted_files == 1
    assert report.superseded_rows > 0                # b.py's OCCUPANCIES flipped, not deleted
    # b.py is RETAINED (the falsifier: a superseded occupancy must never be deleted), and the
    # ATOMS are untouched — append-only means a vanished file removes no geometry at all.
    b_fiber = sync.memberships.fiber("b.py", b_head)
    assert b_fiber and not any(m.current for m in b_fiber)
    assert not any(m.tombstoned for m in b_fiber)     # superseded is not purged
    a_head = _git(repo, "rev-parse", "HEAD:a.py").strip()
    assert all(m.current for m in sync.memberships.fiber("a.py", a_head))
    assert len(sync.store.atom_rows()) == v_before    # |V| never decreases (§4)


def test_changed_blob_keeps_and_links_old_version(repo, tmp_path):
    """D2: on a changed blob the OLD version survives current=false (same ids, vectors intact) and
    the NEW version lands current=true. The falsifier: any superseded row deleted."""
    sync = _sync(repo, tmp_path, FakeEmbedder())
    sync.seed()
    old_blob = _git(repo, "rev-parse", "HEAD:a.py").strip()
    old_fiber = sync.memberships.fiber("a.py", old_blob)
    before = {(str(r["id"]), tuple(r["vector"])) for r in sync.store.atom_rows()}
    assert old_fiber and before                            # PRECONDITION: v1 really landed

    (repo / "a.py").write_text("def a():\n    return 1 + 1  # changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")
    report = sync.sync()
    assert report.superseded_rows > 0
    new_blob = _git(repo, "rev-parse", "HEAD:a.py").strip()
    assert new_blob != old_blob

    # BOTH versions retained as fibers — the old one superseded, never deleted
    now_old = sync.memberships.fiber("a.py", old_blob)
    now_new = sync.memberships.fiber("a.py", new_blob)
    assert now_old == [replace(m, current=False) for m in old_fiber]   # same rows, flag flipped
    assert now_new and all(m.current for m in now_new)
    by_id = {str(r["id"]): r for r in sync.store.atom_rows()}
    assert any("changed" in str(by_id[m.content_id]["text"]) for m in now_new)
    assert not any("changed" in str(by_id[m.content_id]["text"]) for m in now_old)
    # every atom that existed before survives with its vector intact (append-only, section 4)
    assert before <= {(str(r["id"]), tuple(r["vector"])) for r in sync.store.atom_rows()}


def test_default_search_is_current_view_history_is_opt_in(repo, tmp_path):
    """D3: a superseded version never surfaces on the default search; include_superseded=True
    returns it. A deterministic fake embedder + a real temp lance store (no Ollama)."""
    emb = FakeEmbedder()
    sync = _sync(repo, tmp_path, emb)
    store = sync.store
    sync.seed()
    (repo / "a.py").write_text("def a():\n    return 42  # newtoken\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")
    sync.sync()

    # PRECONDITION (the named degenerate input): an atom whose every occupancy is superseded must
    # EXIST, or the current-filter below passes vacuously.
    assert any(not bool(r["current"]) for r in store.atom_rows())
    q = emb.embed_documents(["def a"])[0]
    current_only = store.search(q, k=50, provenances={Provenance.CODE})
    assert current_only and all(r["current"] is True for r in current_only)
    with_history = store.search(q, k=50, provenances={Provenance.CODE},
                                include_superseded=True)
    assert any(r["current"] is False for r in with_history)


def test_current_column_additive_migration_preserves_rows(tmp_path):
    """The `current` migration mirrors the `layer` migration precedent: a store written under the
    old (pre-`current`) schema is migrated in place on the next add — every row preserved
    bit-identically, stamped current=true (correct while the store is HEAD-only), vectors/ids
    untouched. The legacy table is built with raw lancedb (no `current` column)."""
    import lancedb  # type: ignore[import-untyped]  # typedshim-exempt: builds a pre-bp-099 legacy table the shim cannot model (the migration under test)  # noqa: E501

    from core.stores.vectorstore import TABLE
    path = tmp_path / "v.lance"
    chunks = derive_code_chunks("m.py", _SRC)
    # a LEGACY (pre-D1) code row still carries its occupancy columns — that IS the shape being
    # migrated, and restoring it here is what lets the migration assertion mean anything.
    landed = [{**r, "id": f"m.py:{r['id']}", "source_path": "m.py", "digest": "blob0",
               "title": "m.py"}
              for r in code_rows(chunks, [[0.1] * DIM for _ in chunks])]
    legacy = [{k: v for k, v in r.items() if k != "current"} for r in landed]   # strip current

    raw = lancedb.connect(str(path))
    raw.create_table(TABLE, data=legacy)                       # a pre-bp-099 (no-current) table

    store = VectorStore(path, dim=DIM)                         # opens the legacy table
    n_chunks = derive_code_chunks("n.py", _SRC)
    store.add(code_rows(n_chunks, [[0.2] * DIM for _ in n_chunks]))
    rows = store.all_rows(provenances={Provenance.CODE})
    assert all("current" in r for r in rows)
    m_rows = [r for r in rows if r["source_path"] == "m.py"]
    assert m_rows and all(r["current"] is True for r in m_rows)   # migrated rows stamped true
    # vectors/ids preserved bit-identically for the migrated rows (the falsifier: migration
    # must not touch vectors/ids)
    by_id = {r["id"]: r for r in m_rows}
    for r in legacy:
        assert r["id"] in by_id
        assert list(by_id[r["id"]]["vector"]) == pytest.approx(list(r["vector"]))
