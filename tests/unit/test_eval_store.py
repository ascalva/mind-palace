"""The eval-results store's two load-bearing properties (dn-evaluation-harness §2.2, bp-042).

* **append-only-by-key** — a present `(key, metric_name)` cell is SKIPPED, never overwritten and
  never duplicated (the whole-plan falsifier);
* **resumability** — replaying an interrupted sweep inserts 0 new rows and issues 0 overwrites;
* **honest comparison** — readings differing in exactly one key component are DISTINCT rows, so the
  three confounds (corpus growth / config change / seed) stay separable (§2.1).
"""

from __future__ import annotations

from eval.harness.store import EvalKey, EvalResultsStore, Reading


def _key(seed: int = 0, *, corpus: str = "fixture:c0", cfg: str = "cfg0") -> EvalKey:
    return EvalKey(spec_hash="specA", corpus_ref=corpus, config_fingerprint=cfg, seed=seed)


def test_round_trip_get_returns_equal_reading() -> None:
    store = EvalResultsStore(":memory:")
    r = Reading(_key(), "golden_recall", 0.83, "Inv", interval_lo=0.7, interval_hi=0.9,
                evidence_ref="att:123")
    assert store.put(r) is True
    got = store.get(r.key, "golden_recall")
    assert got == r


def test_put_is_idempotent_by_key_and_never_overwrites() -> None:
    """The append-only falsifier: a second put with the SAME key+metric and a DIFFERENT value must
    be skipped (return False) and leave the first value in place — no overwrite, no duplicate."""
    store = EvalResultsStore(":memory:")
    k = _key()
    assert store.put(Reading(k, "drift_D", 0.10, "Inv")) is True
    assert store.put(Reading(k, "drift_D", 0.99, "Inv")) is False   # differs only in value
    kept = store.get(k, "drift_D")
    assert kept is not None and kept.value == 0.10                  # first write preserved
    assert len(store.query(metric_name="drift_D")) == 1            # exactly one row (no dup)


def test_resumability_replay_inserts_nothing(tmp_path) -> None:
    """An interrupted overnight sweep resumes for free: replaying the same cells inserts 0 rows and
    issues 0 overwrites (every put returns False), across a store REOPEN (persisted to disk)."""
    path = tmp_path / "eval.duckdb"
    cells = [Reading(_key(s), "f9_composite", 0.5 + 0.01 * s, "Inv") for s in range(5)]

    store = EvalResultsStore(path)
    first_pass = [store.put(c) for c in cells]
    assert all(first_pass)                     # all fresh on the first pass
    store.close()

    # "resume" — a new process opens the same file and replays every cell
    resumed = EvalResultsStore(path)
    second_pass = [resumed.put(c) for c in cells]
    assert not any(second_pass)                # every cell already present → all skipped
    assert len(resumed.query(metric_name="f9_composite")) == 5   # still exactly the 5 originals
    resumed.close()


def test_confounds_are_separable_one_key_component_at_a_time() -> None:
    """Readings that differ in exactly one key component are DISTINCT rows — corpus growth, config
    change, and seed never collapse (§2.1's three separable confounds)."""
    store = EvalResultsStore(":memory:")
    base = Reading(_key(), "structural_axes.beta0", 3.0, "Inv")
    assert store.put(base) is True
    # vary corpus_ref only
    r_corpus = Reading(_key(corpus="fixture:c1"), "structural_axes.beta0", 4.0, "Inv")
    assert store.put(r_corpus) is True
    # vary config_fingerprint only
    assert store.put(Reading(_key(cfg="cfg1"), "structural_axes.beta0", 5.0, "Inv")) is True
    # vary seed only
    assert store.put(Reading(_key(seed=1), "structural_axes.beta0", 6.0, "Inv")) is True

    rows = store.query(metric_name="structural_axes.beta0")
    assert len(rows) == 4                                   # four distinct cells, none collapsed
    # the group-by substrate can slice by any one confound:
    assert len(store.query(corpus_ref="fixture:c0")) == 3   # base + cfg-varied + seed-varied
    assert len(store.query(corpus_ref="fixture:c1")) == 1


def test_query_filters_compose_and_empty_store_is_empty() -> None:
    store = EvalResultsStore(":memory:")
    assert store.query() == []
    store.put(Reading(_key(), "golden_recall", 0.8, "Inv"))
    store.put(Reading(_key(seed=1), "drift_D", 0.2, "Inv"))
    assert len(store.query()) == 2
    assert len(store.query(metric_name="golden_recall")) == 1
    assert store.get(_key(seed=9), "golden_recall") is None   # absent cell → None, not error
