"""Lane-1 extraction at projection time (bp-013 Item 7, B-c).

Fixture repo with planted references of each VALIDATED type → edges present with correct
typed endpoints and source lines; the below-precision-bar patterns (wikilink 0%,
symbol-mention 20% — bp-011's measured verdicts) mint NOTHING (the Item 7 falsifier);
re-projection is idempotent; the minting is attested WITHIN `project_observations` (no
new attestation kind). Deterministic — no model anywhere in the path.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.sensing import CodeSensingHandoff
from core.stores.code_observations import CodeObservationStore
from core.stores.reference_edges import ReferenceEdgeStore
from ops.code_sensor import VALIDATED_PATTERNS, CodeSensor, extract_references
from ops.code_snapshot import open_snapshot_db


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


PY_BODY = textwrap.dedent('''\
    """Module doc citing `docs/design-notes/planted-note.md` and `config/levers.toml`.

    Prose about [[wikilink]] syntax must mint nothing (bp-011: 0% precision).
    """


    def f(x):
        """Reads `core/thing.py` before returning."""
        return x
''')

MD_BODY = textwrap.dedent("""\
    # Planted note

    The engine is `pkg/mod.py` and the guard argv lives in `core/sandbox/policy.py:42`.
    A dotted `Some.symbol` and `os.fsync` must mint nothing (bp-011: 20% precision).
""")


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    (r / "docs" / "design-notes").mkdir(parents=True)
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "mod.py").write_text(PY_BODY)
    (r / "docs" / "design-notes" / "planted-note.md").write_text(MD_BODY)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "feat: plant references")
    return r


def _sensor(repo: Path, tmp_path) -> tuple[CodeSensor, AttestationStore, ReferenceEdgeStore]:
    att_store = AttestationStore(tmp_path / "attestations.sqlite")
    refs = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    return CodeSensor(
        repo=repo,
        db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
        attestor=StoreAttestor(att_store),
        observations=CodeObservationStore(tmp_path / "code_observations.sqlite"),
        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
        reference_edges=refs,
    ), att_store, refs


# --- the docstring pass (pure function) ------------------------------------------------------
def test_extract_references_validated_patterns_only():
    refs = extract_references(PY_BODY, source_line=1)
    assert {(r["type"], r["target"]) for r in refs} == {
        ("note-citation", "docs/design-notes/planted-note.md"),
        ("path-mention", "docs/design-notes/planted-note.md"),   # backticked .md is BOTH,
        ("path-mention", "config/levers.toml"),                  # bp-011's probe verbatim
        ("path-mention", "core/thing.py"),
    }
    assert all(r["source_line"] == 1 for r in refs)
    assert not any(r["type"] in ("wikilink", "symbol-mention") for r in refs)


def test_extract_references_dedupes_exact_repeats_deterministically():
    doc = "Twice `config/levers.toml` and again `config/levers.toml`."
    assert extract_references(doc, source_line=3) == (
        {"type": "path-mention", "target": "config/levers.toml", "source_line": 3},
    )


# --- edges present, correct typed endpoints + lines (Item 7 acceptance) -----------------------
def test_projection_mints_edges_with_correct_endpoints_and_lines(repo, tmp_path):
    sensor, _, refs = _sensor(repo, tmp_path)
    report = sensor.sync()
    sha = _git(repo, "rev-list", "main").strip()

    got = {(e.direction, e.ref_type, e.code_path, e.qualname, e.corpus_ref, e.source_line)
           for e in refs.all()}
    assert got == {
        # code→corpus: module docstring (owner line 1) + function docstring (def f, line 7)
        ("code_to_corpus", "note-citation", "mod.py", "",
         "docs/design-notes/planted-note.md", 1),
        ("code_to_corpus", "path-mention", "mod.py", "",
         "docs/design-notes/planted-note.md", 1),
        ("code_to_corpus", "path-mention", "mod.py", "", "config/levers.toml", 1),
        ("code_to_corpus", "path-mention", "mod.py", "f", "core/thing.py", 7),
        # corpus→code: md line 3; the `:42` suffix is STRIPPED from the typed code endpoint
        ("corpus_to_code", "path-mention", "pkg/mod.py", "",
         "docs/design-notes/planted-note.md", 3),
        ("corpus_to_code", "path-mention", "core/sandbox/policy.py", "",
         "docs/design-notes/planted-note.md", 3),
    }
    assert report.reference_edges == len(got) == refs.count()
    assert all(e.commit_sha == sha and e.corpus_kind == "path" for e in refs.all())

    # ... and references_out on the landed observation rows carries the code→corpus half.
    obs = sensor.observations
    assert obs is not None
    by_key = {(r["path"], r["qualname"]): r["references_out"] for r in obs.rows_for(sha)}
    assert {(r["type"], r["target"]) for r in by_key[("mod.py", "")]} == {
        ("note-citation", "docs/design-notes/planted-note.md"),
        ("path-mention", "docs/design-notes/planted-note.md"),
        ("path-mention", "config/levers.toml"),
    }
    assert by_key[("mod.py", "f")] == [
        {"type": "path-mention", "target": "core/thing.py", "source_line": 7}]


# --- the Item 7 falsifier: nothing minted from a below-bar pattern ----------------------------
def test_no_edge_is_minted_from_a_pattern_below_the_precision_bar(repo, tmp_path):
    sensor, _, refs = _sensor(repo, tmp_path)
    sensor.sync()
    # The fixture PLANTS a [[wikilink]] and dotted symbol-mentions (`Some.symbol`,
    # `os.fsync`) — bp-011 measured them at 0% / 20% precision. None may become an edge.
    assert all((e.direction, e.ref_type) in VALIDATED_PATTERNS for e in refs.all())
    assert refs.all(ref_type="symbol-mention") == [] and refs.all(ref_type="design-ref") == []
    assert not any("Some.symbol" in (e.corpus_ref, e.code_path) or
                   "wikilink" in (e.corpus_ref, e.code_path) for e in refs.all())
    assert VALIDATED_PATTERNS == {("code_to_corpus", "note-citation"),
                                  ("code_to_corpus", "path-mention"),
                                  ("corpus_to_code", "path-mention")}


# --- idempotency ------------------------------------------------------------------------------
def test_re_projection_mints_nothing_new(repo, tmp_path):
    sensor, att_store, refs = _sensor(repo, tmp_path)
    sensor.sync()
    before, atts = refs.count(), att_store.count()
    report2 = sensor.sync()
    assert refs.count() == before and report2.reference_edges == 0
    assert att_store.count() == atts


def test_backfill_observations_mints_edges_for_unprojected_history(repo, tmp_path):
    ledger_only = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
                             attestor=None)
    ledger_only.sync()                                    # pre-B-b/B-c history: no edges

    sensor, _, refs = _sensor(repo, tmp_path)
    assert sensor.sync().reference_edges == 0             # nothing NEW → nothing minted
    assert refs.count() == 0
    assert sensor.backfill_observations() == 1            # the owner-nod path
    assert refs.count() == 6
    assert sensor.backfill_observations() == 0            # idempotent
    assert refs.count() == 6


# --- attested within project_observations: no new attestation kind ---------------------------
def test_minting_introduces_no_new_attestation_kind(repo, tmp_path):
    sensor, att_store, refs = _sensor(repo, tmp_path)
    sensor.sync()
    assert refs.count() > 0                               # edges really minted this sync
    assert {a.action for a in att_store.all()} == {"ingest_commit", "project_observations"}


# --- graceful degrade: no reference store wired = B-b behavior --------------------------------
def test_sensor_without_the_reference_store_degrades_to_b_b(repo, tmp_path):
    att_store = AttestationStore(tmp_path / "attestations.sqlite")
    sensor = CodeSensor(
        repo=repo, db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
        attestor=StoreAttestor(att_store),
        observations=CodeObservationStore(tmp_path / "code_observations.sqlite"),
        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
    )
    report = sensor.sync()
    assert report.projected == 1 and report.reference_edges == 0
    obs = sensor.observations
    assert obs is not None and obs.count() > 0            # observations still land,
    sha = _git(repo, "rev-list", "main").strip()          # references_out still populated
    assert any(r["references_out"] for r in obs.rows_for(sha))
