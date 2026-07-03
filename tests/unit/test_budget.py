"""Deterministic context budgeter (BUILD-SPEC §13).

A word-count estimator makes the arithmetic exact. Mandatory frame (Constitution, role,
task) is never trimmed; the trim ladder is retrieval -> history -> tool outputs -> escalate.
"""

import pytest

from scheduler.budget import (
    Budgeter,
    ConstitutionFrameError,
    ContextParts,
    estimate_tokens,
    suggest_num_ctx,
)

WORDS = lambda s: len(s.split())  # noqa: E731 — 1 token per word, exact for tests


def _parts(**kw):
    # Tiny explicit Constitution so the mandatory frame is a known size (no file dependency).
    return ContextParts(constitution="C", role="R", task="T", **kw)


def _assemble(bud, parts):
    # These tests deliberately use a tiny non-canonical Constitution for exact size math, so they
    # pass the loud override that `assemble` now requires for any non-canonical outermost frame.
    return bud.assemble(parts, allow_constitution_override=True)


def test_fits_keeps_everything_and_orders_constitution_first():
    parts = _parts(
        retrieved=("a b c", "d e"),
        history=({"role": "user", "content": "h1 h2"},),
    )
    out = _assemble(Budgeter(window=100, reserve=0, estimator=WORDS), parts)
    assert out.report.fits and not out.report.escalate
    assert out.report.retrieved_kept == 2 and out.report.retrieved_dropped == 0
    assert out.messages[0]["content"] == "C"       # Constitution outermost (Invariant 6)
    assert out.messages[1]["content"] == "R"       # role
    assert out.messages[-1] == {"role": "user", "content": "T"}  # task last


def test_tightens_retrieval_first():
    parts = _parts(
        retrieved=("a b c", "d e"),                          # 7 + 6 tokens
        history=({"role": "user", "content": "h1 h2"},),     # 6 tokens
    )
    # mandatory = 15; total = 34. window 30 -> must shed 4: drop one retrieved (6), keep history.
    out = _assemble(Budgeter(window=30, reserve=0, estimator=WORDS), parts)
    assert out.report.retrieved_dropped == 1 and out.report.retrieved_kept == 1
    assert out.report.history_dropped == 0
    assert out.report.fits


def test_compacts_history_after_retrieval_exhausted():
    parts = _parts(
        retrieved=("a b c", "d e"),
        history=({"role": "user", "content": "h1 h2"},),
    )
    out = _assemble(Budgeter(window=20, reserve=0, estimator=WORDS), parts)
    assert out.report.retrieved_dropped == 2 and out.report.retrieved_kept == 0
    assert out.report.history_dropped == 1 and out.report.history_kept == 0
    assert out.report.fits


def test_escalates_when_mandatory_frame_alone_overflows():
    out = _assemble(Budgeter(window=10, reserve=0, estimator=WORDS), _parts())
    assert out.report.escalate and not out.report.fits
    # Constitution/role/task are never dropped even when escalating.
    assert [m["content"] for m in out.messages] == ["C", "R", "T"]


def test_truncates_tool_output_to_fit_default_estimator():
    # Default estimator is chars/4, consistent with the truncation helper.
    big = "x" * 400                       # ~100 tokens
    parts = ContextParts(constitution="c", role="r", task="t", tool_outputs=(big,))
    out = _assemble(Budgeter(window=40, reserve=0, estimator=estimate_tokens), parts)
    assert out.report.tool_truncated >= 1
    assert out.report.used_tokens <= 40   # fits after truncation


def test_refuses_non_canonical_constitution_frame():
    """G9.3: a substituted outermost frame is refused fail-closed; the loud override permits a
    deliberate test/tool; and the live-shaped path (constitution=None) uses the real fixed point."""
    bud = Budgeter(window=10_000, reserve=0, estimator=WORDS)
    # silent substitution → refused
    with pytest.raises(ConstitutionFrameError):
        bud.assemble(ContextParts(constitution="not the constitution", role="R", task="T"))
    # deliberate, visible override → allowed
    assert bud.assemble(ContextParts(constitution="X", role="R", task="T"),
                        allow_constitution_override=True).messages[0]["content"] == "X"
    # the live path passes constitution=None → the real, canonical Constitution is the frame
    from core.constitution import load_constitution
    out = bud.assemble(ContextParts(role="R", task="T"))
    assert out.messages[0]["content"] == load_constitution()
    # an explicit echo of the canonical text needs no override (it is not a substitution)
    bud.assemble(ContextParts(constitution=load_constitution(), role="R", task="T"))


def test_suggest_num_ctx_rounds_up_with_headroom_and_floor():
    assert suggest_num_ctx(100, floor=2048, step=1024) == 2048     # floor wins
    assert suggest_num_ctx(4000, headroom_frac=0.25, step=1024) == 5120  # 5000 -> next 1024


def test_context_usage_is_recorded(tmp_path):
    from core.stores.telemetry import TelemetryStore

    store = TelemetryStore(tmp_path / "u.duckdb")
    try:
        report = _assemble(Budgeter(window=100, reserve=0, estimator=WORDS), _parts()).report
        store.writer().record_context_usage("librarian", report, job_id="7", tier="routine")
        assert store.reader().context_usage_count("librarian") == 1
    finally:
        store.close()
