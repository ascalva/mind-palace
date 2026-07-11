"""F9 — end-to-end proof that the quality binding reaches the REAL Dreamer AND DerivedStore.

The signal-vs-noise suite (`test_dreamer_quality.py`) exercises the fast clustering/grounding/
confidence path. This module closes the other half of "bind the DreamerAdapter to the real
Dreamer/**DerivedStore**": it runs the FULL live `Dreamer.dream()` through the adapter against a
REAL on-disk `DerivedStore` and asserts the live persistence contract holds —

  * dreams are stored INTERPRETED-only (the §8 firewall — `DerivedStore` has no provenance
    parameter, structural);
  * each dream's `derived_from` is exactly the authored leaf digests it clustered (G2 — the
    grounding chain bottoms out in authored ground);
  * the Constitution pre-return grounding self-check PASSES on the grounded synthesis;
  * the persisted grounding agrees with what the suite's fast `run()` reports as
    `grounding_node_ids` (the two paths cannot disagree about what a dream cites).

Pure-CI: deterministic embedder + a grounded synthesizer stand in for Ollama (the quality
layer does not grade prose); everything else is the live machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.provenance import Provenance
from core.stores.derived import DREAM, DerivedStore
from tests.fixtures.dreamer_adapter import MindPalaceDreamerAdapter, build_real_dreamer_adapter


@dataclass(frozen=True)
class _Note:
    """Minimal authored note — the adapter is duck-typed on `.id` / `.text` (the suite's
    `Note` carries extra fields the binding does not read)."""

    id: str
    text: str


# Two clean themes the deterministic clustering must recover (shared signature token + vocab),
# plus an isolated note that must NOT form a cluster (< min_cluster_size).
_PHOTO = [_Note(f"p{i}:photography", f"photography leica aperture grain film exposure note {i}")
          for i in range(4)]
_SYNTH = [_Note(f"s{i}:synthesis", f"synthesis eurorack oscillator envelope filter patch note {i}")
          for i in range(4)]
_LONE = [_Note("x0:lone", "vermouth bitters stir dilution garnish")]
_CORPUS = _PHOTO + _SYNTH + _LONE
_AUTHORED_IDS = {n.id for n in _CORPUS}


def test_persist_dreams_writes_interpreted_dreams_grounded_in_authored_leaves(tmp_path):
    """The full live dream() pass, through the adapter, into a real DerivedStore."""
    derived = DerivedStore(tmp_path / "derived.sqlite")
    adapter = build_real_dreamer_adapter()

    themes = adapter.persist_dreams(_CORPUS, derived)

    # The two planted themes are recovered; the lone note is dropped (< min_cluster_size).
    assert len(themes) == 2, [t.titles for t in themes]

    stored = derived.all(kind=DREAM)
    assert len(stored) == 2
    for art in stored:
        # INTERPRETED-only — the structural §8 firewall (no other provenance is writable).
        assert art.provenance is Provenance.INTERPRETED
        # Grounding bottoms out in AUTHORED leaves (G2): every ref is a real authored note id.
        assert art.derived_from, "a dream with no recorded grounding is not grounded"
        assert set(art.derived_from) <= _AUTHORED_IDS
        # derived_from never leaks the lone (unclustered) note.
        assert "x0:lone" not in art.derived_from

    # The Constitution pre-return grounding check PASSED on every grounded synthesis.
    assert all(t.check.passed for t in themes), [t.check.notes for t in themes]

    # The clusters are the planted themes, not a merged blob.
    grounded_sets = {frozenset(art.derived_from) for art in stored}
    assert frozenset(n.id for n in _PHOTO) in grounded_sets
    assert frozenset(n.id for n in _SYNTH) in grounded_sets


def test_fast_run_and_persisted_grounding_agree(tmp_path):
    """The suite's fast `run()` and the full persisted pass must cite the SAME authored leaves —
    the quality suite cannot be testing different grounding than the system actually records."""
    derived = DerivedStore(tmp_path / "derived.sqlite")
    adapter = build_real_dreamer_adapter()

    run_grounding = {frozenset(d.grounding_node_ids) for d in adapter.run(_CORPUS)}
    adapter.persist_dreams(_CORPUS, derived)
    persisted_grounding = {frozenset(a.derived_from) for a in derived.all(kind=DREAM)}

    assert run_grounding == persisted_grounding


def test_idempotent_repersist_is_regenerable(tmp_path):
    """Re-running the pass over the same corpus is idempotent (content-addressed artifact ids,
    INSERT OR REPLACE) — the derived layer is regenerable, never accumulating duplicates (§8)."""
    derived = DerivedStore(tmp_path / "derived.sqlite")
    adapter = build_real_dreamer_adapter()

    adapter.persist_dreams(_CORPUS, derived)
    first = derived.count(kind=DREAM)
    adapter.persist_dreams(_CORPUS, derived)
    assert derived.count(kind=DREAM) == first


def test_run_is_deterministic():
    """The clustering/grounding/confidence path has no RNG — identical input ⇒ identical dreams
    (theme, confidence, grounding). Determinism is what lets the statistical suite reuse seeds."""
    adapter = MindPalaceDreamerAdapter()
    a = adapter.run(_CORPUS, seed=0)
    b = adapter.run(_CORPUS, seed=0)
    assert [(d.theme, round(d.confidence, 9), d.grounding_node_ids) for d in a] == \
           [(d.theme, round(d.confidence, 9), d.grounding_node_ids) for d in b]
