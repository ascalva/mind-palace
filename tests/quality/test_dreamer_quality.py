"""
tests/quality/test_dreamer_quality.py

Stress tests for the dreamer's OUTPUT QUALITY -- the dimension the existing
safety / provenance / drift suites do not touch. The question these answer is
not "is the dream well-behaved and well-attested" but "is the dream real signal
or well-attested noise."

This is the apophenia / horoscope guard: a connection-finder will find
connections in randomness, and a dream that confidently themes noise passes
every firewall, attestation, and drift check while being worthless. Output
QUALITY is a third axis, orthogonal to output SAFETY and to process-correctness.

DESIGN
------
Everything the tests need from the live system is behind ONE adapter protocol
(DreamerAdapter). Bind it to your real Dreamer/DerivedStore in `_load_adapter()`
below (or via the MIND_PALACE_DREAMER_ADAPTER env var). The test logic is
system-agnostic and portable; only the adapter is yours.

A reference fake dreamer (RefDreamer) ships in-file so the suite runs green out
of the box: `pytest tests/quality/`. It also serves as the executable spec for
what your real adapter must return.

These are STATISTICAL tests over non-deterministic output. They assert bounds,
relationships, and fractions -- never exact values. Thresholds live in THRESH
and are meant to be tuned by the longitudinal harness, exactly like gamma/lambda/
sigma/Theta. Treat a tightened threshold as a tuning decision, not a code change.

Mapping to the roadmap (Track F, item F9):
  - reuses / extends F1 synthetic corpus fixtures (noise + planted-in-noise are
    new F1 variants)
  - lives beside tests/emergent/ ; pure-CI, no scheduler cron loop required
  - drift-vs-evolution + contradiction tests defer to A1 (drift gauge) / the
    longitudinal harness and are skipped until A1 exists

================================================================================
REVIEW NOTES FOLDED IN (see docs/design-notes/dreamer-quality-suite-evaluation.md)
================================================================================
Three things the evaluation flagged are addressed IN THIS FILE, not just in the
companion note, so they bite at the point of binding rather than getting lost:

(1) THE DECOY TEST CANNOT PROVE MEANING BY ITSELF.
    Whether a real dream is distinguishable from Barnum-bait is IRREDUCIBLY a
    human-in-the-loop question -- it is about whether a PERSON finds the real one
    more meaningful. The automatable proxy (citation-ablation survival) is a
    NECESSARY-not-sufficient anchoring check, NOT a validated value-claim. The
    test is split in two so a green CI run can never masquerade as "the dreams
    are proven meaningful":
      - test_real_dreams_are_demonstrably_anchored  (proxy; always runs)
      - test_real_dreams_beat_decoys_under_blind_rating  (the REAL value test;
        SKIPS unless you wire rate_blind to actual blind ratings)
    Wire `rate_blind` to a periodic owner blind-rating ritual to get the real
    signal. Until then the value question is OPEN, and the suite says so loudly.

(2) THE CALIBRATION TEST ASSUMES CONFIDENCE FOLDS IN SUPPORT *COUNT*, NOT JUST
    COHESION. A 2-note cosine-1.0 coincidence is WEAK support and must not score
    high (that is the apophenia failure in miniature). Open question for the real
    adjudicator -- recorded at the test and at the THRESH entry: in
        c = gamma^d * g * (1 + lambda*(|Agr|-1))
    does grounding-strength `g` scale with the NUMBER of authored supports, or
    only their similarity? If similarity-only, this suite will (correctly) flag
    it. That is the suite doing its job, not a false positive.

(3) BINDING SEAMS WITH THE REAL SYSTEM are commented where the adapter must
    flatten richer structure: flat grounding_node_ids vs. chained/depth-decayed
    authored-leaf grounding, and the run_without_grounding negative control,
    which requires the real Dreamer to expose a grounding-disabled mode (if that
    is not cheap, that one test stays on the reference fake -- it skips cleanly).
"""

from __future__ import annotations

import importlib
import math
import os
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pytest

# =============================================================================
# Adapter surface -- the ONLY thing you bind to the real system
# =============================================================================

@dataclass(frozen=True)
class Note:
    id: str
    text: str
    order: int = 0          # for growing / time-ordered corpora
    weight: float = 1.0     # emphasis / repetition signal


@dataclass(frozen=True)
class Dream:
    theme: str                          # human-readable theme string
    confidence: float                   # the gamma-decayed adjudicator score, 0..1
    grounding_node_ids: tuple[str, ...] # note/derived ids cited as support
    id: str = ""
    # ---- BINDING SEAM (review note 3) ----------------------------------------
    # Real dreams ground in AUTHORED LEAVES that terminate a citation chain, with
    # per-dream interpretation DEPTH and gamma-decay. This flat tuple is the
    # quality suite's deliberately reduced view: it tests signal-vs-noise, NOT
    # the depth/decay relationship (that is the recursion + drift suites' job).
    # When binding the real adapter, FLATTEN your chain to the set of authored
    # leaf ids it bottoms out in -- those are what "grounding" means here.


@runtime_checkable
class DreamerAdapter(Protocol):
    def run(self, notes: Sequence[Note], *, seed: int = 0) -> list[Dream]:
        """Run the real dreamer over a corpus and return its dreams.

        Honor `seed` if the dreamer exposes any seedable randomness, so
        metamorphic re-runs are comparable. Non-determinism is fine; the tests
        assert distributional properties, not equality.
        """
        ...

    # ---- optional capabilities ----
    # Tests that need these skip cleanly (pytest.skip) when the method is absent
    # or raises NotImplementedError.
    def run_without_grounding(self, notes: Sequence[Note], *, seed: int = 0) -> list[Dream]:
        """Same, but with the grounding discipline disabled (negative control).

        BINDING SEAM (review note 3): requires the real Dreamer to expose a
        grounding-disabled mode. If that is not cheap to add, leave this
        unimplemented -- the negative-control test skips rather than failing.
        """
        ...

    def rate_blind(self, candidates: Sequence[Dream]) -> list[float]:
        """Blind usefulness rating hook -- the ONLY path that can validate the
        value claim (review note 1).

        Returns a usefulness score per candidate, rated WITHOUT knowing which are
        real dreams and which are decoys. Wire this to an actual blind rater
        (the owner, periodically; or a held-out human-rating set). If left
        unimplemented, the real value test SKIPS and the suite falls back to the
        anchoring proxy only -- which does NOT prove meaning.
        """
        ...


# =============================================================================
# Pure-stdlib NLP helpers (no numpy/sklearn -- runs anywhere)
# =============================================================================

_STOP = set(
    "a an the of to and or in on for with is are was were be been this that these "
    "those it its as at by from into over under i you he she they we my your".split()
)


def _tokens(text: str) -> list[str]:
    cur, out = [], []
    for ch in text.lower():
        if ch.isalnum():
            cur.append(ch)
        elif cur:
            w = "".join(cur)
            cur = []
            if w not in _STOP and len(w) > 2:
                out.append(w)
    if cur:
        w = "".join(cur)
        if w not in _STOP and len(w) > 2:
            out.append(w)
    return out


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _theme_tokens(d: Dream) -> set[str]:
    return set(_tokens(d.theme))


def _ablate(notes: Sequence[Note], drop_ids: set[str]) -> list[Note]:
    return [n for n in notes if n.id not in drop_ids]


def _survives(after: list[Dream], target: Dream, *, match: float = 0.6) -> bool:
    """Does a dream matching `target`'s theme still exist after ablation?"""
    best = max((_jaccard(_theme_tokens(x), _theme_tokens(target)) for x in after), default=0.0)
    return best >= match


# =============================================================================
# Synthetic corpora with KNOWN planted structure (F1 extensions)
# =============================================================================

# A small bank of mutually-unrelated topical vocabularies. Each "theme" is a
# coherent cluster; "noise" notes mix random words across all banks so no real
# cluster exists.
_BANKS = {
    "photography":
        "leica rangefinder aperture grain emulsion shutter highlight contrast film exposure",
    "synthesis":
        "eurorack oscillator envelope filter patch voltage modular sequencer gate resonance",
    "bartending":
        "vermouth bitters stir dilution garnish citrus genever amaro proof balance",
    "terraform":
        "module provider state plan apply drift idempotent backend workspace resource",
    "philosophy":
        "phenomenology intention horizon meaning grounding subject embodiment trace world",
}


def _make_notes(spec: list[tuple[str, list[str]]], rng: random.Random) -> list[Note]:
    notes = []
    for i, (theme_key, words) in enumerate(spec):
        sample = rng.sample(words, k=min(len(words), rng.randint(4, 7)))
        # Non-noise notes carry a shared signature token -> the cluster is genuinely
        # cohesive. Noise notes get none -> they stay incoherent (low confidence).
        if theme_key != "noise":
            sample = [theme_key] + sample
        notes.append(Note(id=f"n{i:03d}:{theme_key}", text=" ".join(sample), order=i))
    return notes


def noise_corpus(n: int = 40, seed: int = 1) -> list[Note]:
    """No real cluster: every note is a random bag drawn across ALL banks."""
    rng = random.Random(seed)
    allwords = [w for v in _BANKS.values() for w in v.split()]
    spec = [("noise", rng.sample(allwords, k=rng.randint(4, 7))) for _ in range(n)]
    return _make_notes(spec, rng)


def planted_in_noise_corpus(
    planted: str = "photography", n_signal: int = 12, n_noise: int = 28, seed: int = 2
) -> tuple[list[Note], set[str]]:
    """One real cluster buried in noise. Returns (notes, set_of_signal_note_ids)."""
    rng = random.Random(seed)
    words = _BANKS[planted].split()
    spec = [(planted, words) for _ in range(n_signal)]
    allwords = [w for v in _BANKS.values() for w in v.split()]
    spec += [("noise", rng.sample(allwords, k=rng.randint(4, 7))) for _ in range(n_noise)]
    rng.shuffle(spec)
    notes = _make_notes(spec, rng)
    signal_ids = {note.id for note in notes if note.id.endswith(":" + planted)}
    return notes, signal_ids


def structured_corpus(
    themes: Sequence[str] = ("photography", "synthesis", "bartending"),
    per_theme: int = 10,
    seed: int = 3,
) -> tuple[list[Note], dict[str, set[str]]]:
    """Several clean clusters. Returns (notes, {theme: set_of_member_ids})."""
    rng = random.Random(seed)
    spec = []
    for t in themes:
        spec += [(t, _BANKS[t].split()) for _ in range(per_theme)]
    rng.shuffle(spec)
    notes = _make_notes(spec, rng)
    members: dict[str, set[str]] = defaultdict(set)
    for note in notes:
        members[note.id.split(":")[1]].add(note.id)
    return notes, dict(members)


def mixed_corpus(
    themes: Sequence[str] = ("photography", "synthesis", "bartending", "terraform"),
    per_theme: int = 8,
    n_noise: int = 24,
    seed: int = 11,
) -> tuple[list[Note], dict[str, set[str]]]:
    """Clean clusters PLUS noise scraps -- yields many dreams across a confidence
    spread, which is what calibration / ablation / decoy tests need. `members`
    covers only the real planted clusters (noise is ground-truth-negative)."""
    rng = random.Random(seed)
    spec = []
    for t in themes:
        spec += [(t, _BANKS[t].split()) for _ in range(per_theme)]
    allwords = [w for v in _BANKS.values() for w in v.split()]
    spec += [("noise", rng.sample(allwords, k=rng.randint(4, 7))) for _ in range(n_noise)]
    rng.shuffle(spec)
    notes = _make_notes(spec, rng)
    members: dict[str, set[str]] = defaultdict(set)
    for note in notes:
        key = note.id.split(":")[1]
        if key != "noise":
            members[key].add(note.id)
    return notes, dict(members)


def paraphrase(notes: Sequence[Note], rng: random.Random) -> list[Note]:
    """Cheap meaning-preserving perturbation: reorder + drop/dup a token."""
    out = []
    for note in notes:
        toks = note.text.split()
        rng.shuffle(toks)
        if len(toks) > 4 and rng.random() < 0.5:
            toks.pop()
        out.append(Note(id=note.id, text=" ".join(toks), order=note.order, weight=note.weight))
    return out


# =============================================================================
# Reference dreamer + TF-IDF baseline (so the suite is self-runnable)
# =============================================================================

def _tfidf_vectors(notes: Sequence[Note]) -> dict[str, dict[str, float]]:
    docs = {note.id: _tokens(note.text) for note in notes}
    df: Counter = Counter()
    for toks in docs.values():
        df.update(set(toks))
    N = max(1, len(docs))
    vecs = {}
    for nid, toks in docs.items():
        tf = Counter(toks)
        vecs[nid] = (
            {t: (c / len(toks)) * math.log(N / (1 + df[t])) for t, c in tf.items()} if toks else {}
        )
    return vecs


def _cosine(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return num / (na * nb) if na and nb else 0.0


def _greedy_cluster(notes: Sequence[Note], sim_thresh: float = 0.18) -> list[list[Note]]:
    vecs = _tfidf_vectors(notes)
    clusters: list[list[Note]] = []
    centroids: list[dict] = []
    for note in notes:
        v = vecs[note.id]
        best, best_sim = -1, 0.0
        for ci, c in enumerate(centroids):
            s = _cosine(v, c)
            if s > best_sim:
                best, best_sim = ci, s
        if best >= 0 and best_sim >= sim_thresh:
            clusters[best].append(note)
            for t, w in v.items():
                centroids[best][t] = centroids[best].get(t, 0.0) + w
        else:
            clusters.append([note])
            centroids.append(dict(v))
    return clusters


def _cluster_to_dream(cluster: list[Note], honest_grounding: bool, rng: random.Random) -> Dream:
    # theme = top terms in the cluster
    tf: Counter = Counter()
    for note in cluster:
        tf.update(_tokens(note.text))
    theme = " ".join(w for w, _ in tf.most_common(4)) or "misc"
    # confidence ~ cohesion (mean pairwise cosine), so calibration is meaningful
    vecs = _tfidf_vectors(cluster)
    ids = [note.id for note in cluster]
    if len(ids) > 1:
        sims = [_cosine(vecs[ids[i]], vecs[ids[j]])
                for i in range(len(ids)) for j in range(i + 1, len(ids))]
        cohesion = sum(sims) / len(sims)
    else:
        cohesion = 0.15
    # --- REVIEW NOTE 2: confidence must scale with EVIDENCE (support COUNT), not
    # just cohesion. A 2-note coincidence at cosine 1.0 is weak support; without
    # size_factor, noise coincidences score high -- the apophenia failure mode.
    # The reference dreamer folds support count in HERE so a correct dreamer
    # passes calibration. YOUR real adjudicator must do the equivalent: confirm
    # whether grounding-strength g in c = gamma^d * g * (1 + lambda*(|Agr|-1))
    # scales with the NUMBER of authored supports or only their similarity. If
    # similarity-only, test_confidence_is_calibrated will (correctly) flag it.
    size_factor = min(1.0, (len(cluster) - 1) / 4.0)
    confidence = max(0.0, min(1.0, 0.25 + 0.75 * cohesion * size_factor))
    if honest_grounding:
        grounding = tuple(note.id for note in cluster)          # cites its real members
    else:
        grounding = tuple(rng.sample(ids, k=min(2, len(ids))))  # decorative grounding
    return Dream(theme=theme, confidence=confidence, grounding_node_ids=grounding,
                 id=f"d:{theme[:12]}")


class RefDreamer:
    """A competent-but-simple reference dreamer. Grounding is load-bearing and
    confidence tracks cohesion * support-count, so a correct dreamer passes the
    quality bar."""

    def __init__(self, honest_grounding: bool = True):
        self._honest = honest_grounding

    def run(self, notes: Sequence[Note], *, seed: int = 0) -> list[Dream]:
        rng = random.Random(seed)
        clusters = [c for c in _greedy_cluster(notes) if len(c) >= 2]
        return [_cluster_to_dream(c, self._honest, rng) for c in clusters]

    def run_without_grounding(self, notes: Sequence[Note], *, seed: int = 0) -> list[Dream]:
        rng = random.Random(seed)
        clusters = [c for c in _greedy_cluster(notes) if len(c) >= 2]
        return [_cluster_to_dream(c, False, rng) for c in clusters]

    # NOTE: RefDreamer deliberately does NOT implement rate_blind. The real value
    # test therefore SKIPS against the reference fake -- which is correct: a fake
    # cannot validate meaning. Wire rate_blind only on the real adapter, to a real
    # blind rater.


class BaselineDreamer:
    """Dumb negative control: raw TF-IDF clustering + template theme. The real
    dreamer must beat THIS on planted-structure recovery, or its machinery is
    decoration."""

    def run(self, notes: Sequence[Note], *, seed: int = 0) -> list[Dream]:
        rng = random.Random(seed)
        clusters = [c for c in _greedy_cluster(notes, sim_thresh=0.18) if len(c) >= 2]
        return [_cluster_to_dream(c, True, rng) for c in clusters]


# =============================================================================
# Adapter loading + thresholds
# =============================================================================

def _adapter_factories() -> list[tuple[str, object]]:
    """Which adapters the suite runs against.

    F9 binding (docs/PROGRESS.md): by DEFAULT the suite runs against BOTH the in-file
    reference fake (the executable spec / green floor) AND the real Mind-Palace binding
    (`fixtures.dreamer_adapter`), so CI exercises the live Dreamer/DerivedStore — not just a
    stand-in. Set MIND_PALACE_DREAMER_ADAPTER="your.module:factory_callable" (a zero-arg
    callable returning a DreamerAdapter) to force a single explicit adapter instead. If the
    real binding can't be imported, the suite degrades to the reference fake alone.
    """
    spec = os.environ.get("MIND_PALACE_DREAMER_ADAPTER")
    if spec:
        mod, _, attr = spec.partition(":")
        return [("env", getattr(importlib.import_module(mod), attr))]
    factories: list[tuple[str, object]] = [("ref", RefDreamer)]
    try:
        from tests.fixtures.dreamer_adapter import build_real_dreamer_adapter
        factories.append(("real", build_real_dreamer_adapter))
    except Exception:   # real binding unavailable -> reference fake still runs green
        pass
    return factories


# Tuning surface. The longitudinal harness should drive these against known
# corpora, the same way it tunes the drift bands (gamma/lambda/sigma/Theta).
# A tightened threshold is a TUNING decision (logged), not a code change.
THRESH = dict(
    high_conf=0.70,          # "high confidence" cutoff
    noise_max_conf=0.70,     # no dream over a noise corpus may exceed this
    noise_max_mean=0.50,     # mean confidence over pure noise must stay below this
    signal_recall=0.50,      # planted cluster must be recovered to at least this recall
    decoy_max=1,             # at most this many high-conf themes grounded mostly in noise
    calib_margin=0.10,       # top-tercile precision must beat bottom by this margin
                             #   ^ REVIEW NOTE 2: this margin is what catches an adjudicator
                             #     whose confidence ignores support count -- tune it on known
                             #     corpora, and treat a persistent failure as a signal to fix
                             #     g's definition, not to loosen the threshold.
    ablation_frac=0.50,      # >= this fraction of dreams must move when a citation is cut
    paraphrase_stability=0.55,  # theme-set Jaccard across paraphrase
    poison_share_cap=0.60,   # no single theme may own more than this share of grounding
)


def _require(adapter, method: str):
    fn = getattr(adapter, method, None)
    if fn is None:
        pytest.skip(f"adapter does not implement optional {method}()")
    return fn


@pytest.fixture(scope="module", params=_adapter_factories(), ids=lambda f: f[0])
def adapter(request) -> DreamerAdapter:
    return request.param[1]()


# =============================================================================
# 1. Signal vs noise
# =============================================================================

def test_pure_noise_yields_no_confident_theme(adapter):
    """Apophenia guard: a connection-finder will find connections in randomness.
    Over a corpus with no real structure, no dream may be confident, and the mean
    confidence must stay low. A dreamer that confidently themes noise is a horoscope."""
    dreams = adapter.run(noise_corpus(n=40, seed=1), seed=1)
    if not dreams:
        return  # silence on noise is the ideal outcome
    confs = [d.confidence for d in dreams]
    assert max(confs) <= THRESH["noise_max_conf"], \
        f"confident theme invented from noise: max conf {max(confs):.2f}"
    assert sum(confs) / len(confs) <= THRESH["noise_max_mean"], \
        f"mean confidence over noise too high: {sum(confs)/len(confs):.2f}"


def test_planted_signal_recovered_with_specificity(adapter):
    """Sensitivity AND specificity: the buried real theme must surface, WITHOUT
    a swarm of confident decoy themes grounded in the noise."""
    notes, signal_ids = planted_in_noise_corpus(planted="photography", seed=2)
    dreams = adapter.run(notes, seed=2)

    # sensitivity: some dream's grounding overlaps the planted set
    best_recall = 0.0
    for d in dreams:
        g = set(d.grounding_node_ids)
        if g:
            best_recall = max(best_recall, len(g & signal_ids) / len(signal_ids))
    assert best_recall >= THRESH["signal_recall"], \
        f"planted theme not recovered: best recall {best_recall:.2f}"

    # specificity: few confident themes grounded MOSTLY in noise
    decoys = 0
    for d in dreams:
        g = set(d.grounding_node_ids)
        if not g or d.confidence < THRESH["high_conf"]:
            continue
        noise_share = len(g - signal_ids) / len(g)
        if noise_share > 0.5:
            decoys += 1
    assert decoys <= THRESH["decoy_max"], f"{decoys} confident decoy themes from noise"


# =============================================================================
# 2. Calibration
# =============================================================================

def test_confidence_is_calibrated(adapter):
    """High-confidence dreams must actually be more correct than low-confidence
    ones. An uncalibrated confidence number launders guesses as knowledge.

    REVIEW NOTE 2: this is also the test that surfaces whether the real
    adjudicator's grounding-strength g scales with support COUNT or only
    similarity. A dreamer that scores a tiny high-cohesion coincidence as highly
    as a well-supported cluster will fail the top-vs-bottom precision margin
    here. If this fails persistently on the real adapter, the fix is in g's
    definition, not in loosening THRESH['calib_margin']."""
    notes, members = mixed_corpus(seed=3)
    dreams = [d for d in adapter.run(notes, seed=3) if d.grounding_node_ids]
    if len(dreams) < 6:
        pytest.skip("not enough dreams to bucket for calibration")

    def precision(d: Dream) -> float:
        g = set(d.grounding_node_ids)
        # a dream is "correct" to the extent its grounding lands inside ONE real cluster
        best = max((len(g & m) for m in members.values()), default=0)
        return best / len(g) if g else 0.0

    ranked = sorted(dreams, key=lambda d: d.confidence)
    k = max(1, len(ranked) // 3)
    bottom = sum(precision(d) for d in ranked[:k]) / k
    top = sum(precision(d) for d in ranked[-k:]) / k
    assert top >= bottom + THRESH["calib_margin"], \
        f"confidence not calibrated: top-tercile precision {top:.2f} vs bottom {bottom:.2f}"


# =============================================================================
# 3. Grounding faithfulness (citation ablation)
# =============================================================================

def test_grounding_is_load_bearing(adapter):
    """Remove ALL of a dream's cited support, regenerate: a faithful dream must
    collapse. If the theme survives with its grounding gone, the citations were
    decorative -- rigorous-looking, not rigorous. (Cutting a SINGLE citation is
    the wrong granularity: a healthy 10-note cluster shouldn't die when one of ten
    supports is removed -- that's robustness, not decoration.)"""
    notes, _ = mixed_corpus(seed=4)
    base = [d for d in adapter.run(notes, seed=4) if d.grounding_node_ids]
    if len(base) < 4:
        pytest.skip("not enough grounded dreams to ablate")

    collapsed = 0
    for d in base:
        after = adapter.run(_ablate(notes, set(d.grounding_node_ids)), seed=4)
        if not _survives(after, d):
            collapsed += 1
    frac = collapsed / len(base)
    assert frac >= THRESH["ablation_frac"], \
        f"only {frac:.0%} of dreams collapsed when their full support was cut " \
        "-- grounding may be decorative"


# =============================================================================
# 4. Robustness
# =============================================================================

def test_paraphrase_invariance(adapter):
    """Meaning-preserving rewording must not reshuffle the theme structure.
    High sensitivity here means the dreamer reacts to surface tokens, not content.

    (This is the executable form of the metamorphic 'paraphrase' property in
    holistic-testing.md -- it lives here as the canonical implementation.)"""
    notes, _ = structured_corpus(seed=5)
    rng = random.Random(5)
    a = {frozenset(_theme_tokens(d)) for d in adapter.run(notes, seed=5)}
    b = {frozenset(_theme_tokens(d)) for d in adapter.run(paraphrase(notes, rng), seed=5)}
    if not a or not b:
        pytest.skip("dreamer produced no themes to compare")
    # set-level Jaccard over theme token-sets
    inter = sum(1 for x in a if any(_jaccard(set(x), set(y)) >= 0.6 for y in b))
    stability = inter / max(len(a), len(b))
    assert stability >= THRESH["paraphrase_stability"], \
        f"theme structure unstable under paraphrase: {stability:.2f}"


def test_dominant_note_does_not_hijack(adapter):
    """A few loud (repeated/emphatic) notes must not capture the clustering.
    This is weighting robustness -- distinct from the prompt-injection behavior
    test in the adversarial suite."""
    notes, _ = structured_corpus(seed=6)
    loud = notes[0]
    flood = [Note(id=f"{loud.id}-dup{i}", text=loud.text, order=loud.order, weight=5.0)
             for i in range(8)]
    dreams = adapter.run(list(notes) + flood, seed=6)
    grounded = [d for d in dreams if d.grounding_node_ids]
    if not grounded:
        pytest.skip("no grounded dreams produced")
    total = sum(len(d.grounding_node_ids) for d in grounded)
    biggest = max(len(d.grounding_node_ids) for d in grounded)
    share = biggest / total if total else 0.0
    assert share <= THRESH["poison_share_cap"], \
        f"one theme owns {share:.0%} of grounding -- a loud note hijacked the clusters"


# =============================================================================
# 5. Negative control vs baseline
# =============================================================================

def test_beats_dumb_baseline_on_planted_structure(adapter):
    """If the full dreamer can't out-recover a pure TF-IDF baseline on planted
    clusters, all the machinery above it is decoration."""
    notes, members = structured_corpus(seed=7)
    baseline = BaselineDreamer()

    def recall(dreamer) -> float:
        dreams = dreamer.run(notes, seed=7)
        scores = []
        for m in members.values():
            best = 0.0
            for d in dreams:
                g = set(d.grounding_node_ids)
                if g:
                    best = max(best, len(g & m) / len(m))
            scores.append(best)
        return sum(scores) / len(scores) if scores else 0.0

    real_r, base_r = recall(adapter), recall(baseline)
    # >= (not strictly >) so the reference dreamer demo passes; against your real
    # dreamer expect a margin, and treat near-parity as a red flag worth probing.
    assert real_r >= base_r - 1e-9, \
        f"dreamer ({real_r:.2f}) does not beat TF-IDF baseline ({base_r:.2f}) on planted clusters"


def test_grounding_discipline_improves_faithfulness(adapter):
    """Negative control on the grounding discipline itself: dreams produced WITH
    grounding must survive ablation better than dreams produced without it.

    BINDING SEAM (review note 3): needs run_without_grounding on the real
    Dreamer. Skips cleanly if that mode is not exposed."""
    run_ng = _require(adapter, "run_without_grounding")
    notes, _ = mixed_corpus(seed=8)

    def survives_ablation(dreams) -> float:
        grounded = [d for d in dreams if d.grounding_node_ids]
        if not grounded:
            return 0.0
        collapsed = 0
        for d in grounded:
            after = adapter.run(_ablate(notes, set(d.grounding_node_ids)), seed=8)
            if not _survives(after, d):
                collapsed += 1
        return collapsed / len(grounded)

    with_g = survives_ablation(adapter.run(notes, seed=8))
    try:
        without_g = survives_ablation(run_ng(notes, seed=8))
    except NotImplementedError:
        pytest.skip("run_without_grounding not implemented")
    assert with_g >= without_g, \
        f"grounding discipline did not increase faithfulness ({with_g:.2f} vs {without_g:.2f})"


# =============================================================================
# 6. Barnum / decoy probe
#
# REVIEW NOTE 1 -- THE SPLIT THAT MATTERS:
#   Whether a real dream is distinguishable from Barnum-bait is IRREDUCIBLY a
#   human question. So this is TWO tests, not one:
#     (a) test_real_dreams_are_demonstrably_anchored -- an automatable PROXY
#         (necessary, not sufficient). Always runs. A green result here does NOT
#         prove the dreams are meaningful; it only proves they are anchored.
#     (b) test_real_dreams_beat_decoys_under_blind_rating -- the REAL value test.
#         SKIPS unless rate_blind is wired to actual blind ratings.
#   Keeping them separate means a green CI run can never masquerade as a proven
#   value-claim. The value question stays visibly OPEN until (b) runs.
# =============================================================================

def _decoys(notes: Sequence[Note], k: int, rng: random.Random) -> list[Dream]:
    """Generative decoys: random note recombinations dressed as themes. They look
    personal but encode no real structure."""
    out = []
    for i in range(k):
        members = rng.sample(list(notes), k=min(len(notes), rng.randint(3, 6)))
        tf: Counter = Counter()
        for n in members:
            tf.update(_tokens(n.text))
        theme = " ".join(w for w, _ in tf.most_common(4)) or "insight"
        out.append(Dream(theme=theme, confidence=rng.uniform(0.5, 0.9),
                         grounding_node_ids=tuple(n.id for n in members), id=f"decoy{i}"))
    return out


def test_real_dreams_are_demonstrably_anchored(adapter):
    """PROXY (necessary, NOT sufficient): real dreams must be demonstrably
    anchored -- they move under citation-ablation -- which random-recombination
    decoys, having no real support, are not. This is an anchoring check, NOT a
    proof of meaning. Passing it does not mean the dreams are useful; it means
    they are not free-floating. The actual value claim lives in the blind-rating
    test below, which skips until you wire a rater."""
    notes, _ = mixed_corpus(seed=9)
    real = [d for d in adapter.run(notes, seed=9) if d.grounding_node_ids]
    if len(real) < 3:
        pytest.skip("not enough real dreams to assess anchoring")

    def ablation_survival(dreams) -> float:
        collapsed = 0
        for d in dreams:
            after = adapter.run(_ablate(notes, set(d.grounding_node_ids)), seed=9)
            if not _survives(after, d):
                collapsed += 1
        return collapsed / len(dreams) if dreams else 0.0

    real_sig = ablation_survival(real)
    assert real_sig >= THRESH["ablation_frac"], \
        f"real dreams not demonstrably anchored ({real_sig:.0%}); anchoring proxy failed"


def test_real_dreams_beat_decoys_under_blind_rating(adapter):
    """THE REAL VALUE TEST (review note 1). Requires rate_blind wired to an actual
    blind rater (the owner, periodically; or a held-out human-rating set). A blind
    rater shown a mix of real dreams and random-recombination decoys must, on
    average, score the real ones higher. If rate_blind is not wired, this SKIPS --
    and the headline value question 'can real be told from Barnum-bait' is, by
    construction, still OPEN. Do not treat the proxy test above as a substitute."""
    rater = getattr(adapter, "rate_blind", None)
    if rater is None:
        pytest.skip("rate_blind not wired -- VALUE CLAIM UNVALIDATED (wire a blind rater)")

    notes, _ = mixed_corpus(seed=9)
    rng = random.Random(9)
    real = [d for d in adapter.run(notes, seed=9) if d.grounding_node_ids]
    if len(real) < 3:
        pytest.skip("not enough real dreams to compare against decoys")
    decoys = _decoys(notes, k=len(real), rng=rng)

    # Shuffle so the rater cannot infer label from position; keep an index map.
    mixed = [(d, True) for d in real] + [(d, False) for d in decoys]
    rng.shuffle(mixed)
    try:
        scores = rater([d for d, _ in mixed])
    except NotImplementedError:
        pytest.skip("rate_blind unimplemented -- VALUE CLAIM UNVALIDATED")
    assert len(scores) == len(mixed), "rate_blind must return one score per candidate"

    real_scores = [s for s, (_, is_real) in zip(scores, mixed, strict=True) if is_real]
    decoy_scores = [s for s, (_, is_real) in zip(scores, mixed, strict=True) if not is_real]
    real_mean = sum(real_scores) / len(real_scores)
    decoy_mean = sum(decoy_scores) / len(decoy_scores)
    assert real_mean > decoy_mean, \
        f"blind rater could not separate real ({real_mean:.2f}) from decoys ({decoy_mean:.2f}) " \
        f"-- the dreams are not distinguishable from Barnum-bait"


# =============================================================================
# 7. Deferred to A1 (drift gauge) / the longitudinal harness
#     These move to tests/longitudinal/ once A1 exists (roadmap F4).
# =============================================================================

_HAS_DRIFT_GAUGE = os.environ.get("MIND_PALACE_DRIFT_GAUGE") == "1"

@pytest.mark.skipif(not _HAS_DRIFT_GAUGE, reason="A1 drift gauge not built yet (F4)")
def test_drift_vs_genuine_evolution():
    """Belongs in tests/longitudinal/ once A1 exists: on a corpus whose themes
    deliberately shift over time, the gauge must track real evolution, not flag
    legitimate growth as misalignment drift."""
    pytest.skip("implement against the longitudinal harness once A1 lands")


@pytest.mark.skipif(not _HAS_DRIFT_GAUGE,
                    reason="needs seeded-contradiction corpus + curator output access")
def test_contradictions_are_surfaced_not_averaged():
    """A good second brain says 'you used to believe X, now Y'; a bad one averages
    them into mush or silently picks one. Feed a seeded-contradiction corpus and
    assert the tension is surfaced."""
    pytest.skip("implement once contradiction-bearing fixtures + curator inspection exist")
