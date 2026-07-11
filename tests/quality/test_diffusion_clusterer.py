"""F9 non-regression for the reasoning-complex diffusion clusterer (H2), through the adapter.

The DONE-WHEN bar: run the diffusion clusterer behind `MindPalaceDreamerAdapter` on the canonical
F9 corpora and show it is at least as good as the lexical single-linkage floor —

  * planted-signal recall (diffusion) ≥ lexical baseline (and clears the absolute F9 bar);
  * no confident theme is invented from pure noise (max confidence ≤ the F9 ceiling).

Same embedder, grounding, and confidence law as the lexical adapter — only the clusterer differs —
so any difference isolates the clusterer. The default suite in `test_dreamer_quality.py` still runs
against the single-linkage adapter (unchanged); this is the added adopted-subset check.
"""

from __future__ import annotations

from collections.abc import Sequence

from tests.fixtures.dreamer_adapter import (
    build_diffusion_dreamer_adapter,
    build_real_dreamer_adapter,
)
from tests.quality.test_dreamer_quality import THRESH, noise_corpus, planted_in_noise_corpus


def _best_recall(dreams: Sequence, signal_ids: set[str]) -> float:
    best = 0.0
    for d in dreams:
        g = set(d.grounding_node_ids)
        if g:
            best = max(best, len(g & signal_ids) / len(signal_ids))
    return best


def test_diffusion_recall_at_least_lexical_baseline():
    notes, signal_ids = planted_in_noise_corpus(planted="photography", seed=2)
    lexical = build_real_dreamer_adapter().run(notes, seed=2)        # single-linkage floor
    diffusion = build_diffusion_dreamer_adapter().run(notes, seed=2)  # adopted diffusion clusterer

    r_lex = _best_recall(lexical, signal_ids)
    r_dif = _best_recall(diffusion, signal_ids)
    assert r_dif >= r_lex - 1e-9, \
        f"diffusion recall {r_dif:.2f} regressed below lexical baseline {r_lex:.2f}"
    assert r_dif >= THRESH["signal_recall"], \
        f"diffusion recall {r_dif:.2f} below the F9 bar {THRESH['signal_recall']}"


def test_diffusion_invents_no_confident_theme_from_noise():
    dreams = build_diffusion_dreamer_adapter().run(noise_corpus(n=40, seed=1), seed=1)
    if not dreams:
        return                                                       # silence on noise is ideal
    assert max(d.confidence for d in dreams) <= THRESH["noise_max_conf"], \
        "diffusion clusterer invented a confident theme from noise"


def test_diffusion_adapter_run_is_deterministic():
    notes, _ = planted_in_noise_corpus(seed=2)
    adapter = build_diffusion_dreamer_adapter()

    def fingerprint():
        return [(d.theme, round(d.confidence, 9), d.grounding_node_ids)
                for d in adapter.run(notes, seed=2)]

    assert fingerprint() == fingerprint()
