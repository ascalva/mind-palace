"""The run ledger — content-addressed claims + novel-on-insert (bp-043 Item 5).

The acceptance test (plan §7): round-trip a run + claim; two claims with the same
(kind, support, polarity) but DIFFERENT surface_text share one `claim_id` and the second is
`novel=False`. The falsifier (must FAIL red if tripped): surface/confidence leaking into the
`claim_id`, or `novel` computed per-run instead of across all prior runs.
"""

from __future__ import annotations

from core.stores.runledger import (
    RunLedger,
    claim_id,
    open_run_ledger,
    polarity_and_flag,
    polarity_for,
)


def _ledger() -> RunLedger:
    return RunLedger(":memory:")


def test_start_run_and_claim_roundtrip() -> None:
    led = _ledger()
    run_id = led.start_run(pipeline="phase7", config_fingerprint="cf", corpus_digest="cd",
                           node_count=3, edge_count=2, duration_s=0.1,
                           spectral_stats={"sigma": 0.6})
    assert led.add_claim(run_id, kind="community", confidence=0.0,
                         support=("dA", "dB"), surface_text="two notes group", polarity="+")
    runs = led.runs()
    assert len(runs) == 1 and runs[0]["run_id"] == run_id and runs[0]["pipeline"] == "phase7"
    assert runs[0]["node_count"] == 3 and runs[0]["edge_count"] == 2
    claims = led.claims(run_id=run_id)
    assert len(claims) == 1 and claims[0]["kind"] == "community" and claims[0]["novel"] == 1
    led.close()


def test_claim_id_excludes_surface_and_confidence() -> None:
    """Content-addressing is over (kind, support, polarity) ONLY — surface wording is invisible."""
    a = claim_id("tension", ("dX", "dY", "dZ"), "-")
    b = claim_id("tension", ("dZ", "dY", "dX"), "-")     # order-insensitive
    c = claim_id("tension", ("dX", "dX", "dY", "dZ"), "-")  # duplicate-insensitive
    assert a == b == c
    # a genuinely different claim (different kind / support / polarity) must differ
    assert claim_id("theme", ("dX", "dY", "dZ"), "+") != a


def test_novel_is_false_on_reemit_despite_different_surface() -> None:
    """Same (kind, support, polarity), different surface_text + confidence -> same claim_id; the
    second add is NOT novel. This is the acceptance test AND guards the falsifier."""
    led = _ledger()
    r1 = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                       node_count=3, edge_count=3, duration_s=0.2, spectral_stats={})
    first = led.add_claim(r1, kind="hole", confidence=0.9, support=("dA", "dB", "dC"),
                          surface_text="a conceptual hole (open from 0.8 to 0.4)", polarity="+")
    second = led.add_claim(r1, kind="hole", confidence=0.1, support=("dC", "dB", "dA"),
                           surface_text="THREE notes circle a theme", polarity="+")
    assert first is True
    assert second is False, "re-emitted claim (surface differs only) must be novel=False"
    ids = {c["claim_id"] for c in led.claims()}
    assert len(ids) == 1, "surface/confidence leaked into claim_id"
    led.close()


def test_novel_spans_all_prior_runs_not_just_this_run() -> None:
    """`novel` is a property across ALL runs (the falsifier: per-run novelty). A claim first seen
    in run 1 is NOT novel when re-emitted in run 2."""
    led = _ledger()
    r1 = led.start_run(pipeline="phase7", config_fingerprint="cf", corpus_digest="cd1",
                       node_count=2, edge_count=1, duration_s=0.1, spectral_stats={})
    assert led.add_claim(r1, kind="community", confidence=0.0, support=("dA", "dB"),
                         surface_text="s1", polarity="+") is True
    r2 = led.start_run(pipeline="phase7", config_fingerprint="cf", corpus_digest="cd2",
                       node_count=2, edge_count=1, duration_s=0.1, spectral_stats={})
    assert led.add_claim(r2, kind="community", confidence=0.0, support=("dB", "dA"),
                         surface_text="s2 (reworded)", polarity="+") is False
    assert led.claims(novel_only=True) and len(led.claims(novel_only=True)) == 1
    led.close()


def test_polarity_map() -> None:
    assert polarity_for("tension") == "-"
    for k in ("community", "theme", "hole", "thread"):
        assert polarity_for(k) == "+"
    # unmapped kinds default "+" and are flagged (bridge/centrality/density from collect_claims)
    for k in ("bridge", "centrality", "density"):
        pol, defaulted = polarity_and_flag(k)
        assert pol == "+" and defaulted is True
    assert polarity_and_flag("tension") == ("-", False)


def test_append_only_reemit_is_a_new_row() -> None:
    """Append-only: a re-emit is a NEW row, never an update — two rows, one claim_id."""
    led = _ledger()
    r = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                      node_count=2, edge_count=1, duration_s=0.1, spectral_stats={})
    led.add_claim(r, kind="theme", confidence=0.5, support=("dA", "dB"), surface_text="x",
                  polarity="+")
    led.add_claim(r, kind="theme", confidence=0.5, support=("dA", "dB"), surface_text="y",
                  polarity="+")
    rows = led.claims(run_id=r)
    assert len(rows) == 2
    assert len({row["claim_id"] for row in rows}) == 1
    assert [row["novel"] for row in rows] == [1, 0]
    led.close()


def test_open_run_ledger_uses_configured_path(tmp_path) -> None:
    import dataclasses

    from config.loader import get_config

    cfg = get_config()
    paths = dataclasses.replace(cfg.paths, derived_store=tmp_path / "derived.sqlite")
    cfg = dataclasses.replace(cfg, paths=paths)
    led = open_run_ledger(cfg)
    assert led.path == tmp_path / "run_ledger.sqlite"
    led.close()
