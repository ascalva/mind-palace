"""Deterministic context budgeter (BUILD-SPEC §13).

A word-count estimator makes the arithmetic exact. Mandatory frame (Constitution, role,
task) is never trimmed; the trim ladder is retrieval -> history -> tool outputs -> escalate.
"""

from scheduler.budget import (
    Budgeter,
    ContextParts,
    estimate_tokens,
    suggest_num_ctx,
)

WORDS = lambda s: len(s.split())  # noqa: E731 — 1 token per word, exact for tests


def _parts(**kw):
    # Tiny explicit Constitution so the mandatory frame is a known size (no file dependency).
    return ContextParts(constitution="C", role="R", task="T", **kw)


def test_fits_keeps_everything_and_orders_constitution_first():
    parts = _parts(
        retrieved=("a b c", "d e"),
        history=({"role": "user", "content": "h1 h2"},),
    )
    out = Budgeter(window=100, reserve=0, estimator=WORDS).assemble(parts)
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
    out = Budgeter(window=30, reserve=0, estimator=WORDS).assemble(parts)
    assert out.report.retrieved_dropped == 1 and out.report.retrieved_kept == 1
    assert out.report.history_dropped == 0
    assert out.report.fits


def test_compacts_history_after_retrieval_exhausted():
    parts = _parts(
        retrieved=("a b c", "d e"),
        history=({"role": "user", "content": "h1 h2"},),
    )
    out = Budgeter(window=20, reserve=0, estimator=WORDS).assemble(parts)
    assert out.report.retrieved_dropped == 2 and out.report.retrieved_kept == 0
    assert out.report.history_dropped == 1 and out.report.history_kept == 0
    assert out.report.fits


def test_escalates_when_mandatory_frame_alone_overflows():
    out = Budgeter(window=10, reserve=0, estimator=WORDS).assemble(_parts())
    assert out.report.escalate and not out.report.fits
    # Constitution/role/task are never dropped even when escalating.
    assert [m["content"] for m in out.messages] == ["C", "R", "T"]


def test_truncates_tool_output_to_fit_default_estimator():
    # Default estimator is chars/4, consistent with the truncation helper.
    big = "x" * 400                       # ~100 tokens
    parts = ContextParts(constitution="c", role="r", task="t", tool_outputs=(big,))
    out = Budgeter(window=40, reserve=0, estimator=estimate_tokens).assemble(parts)
    assert out.report.tool_truncated >= 1
    assert out.report.used_tokens <= 40   # fits after truncation


def test_suggest_num_ctx_rounds_up_with_headroom_and_floor():
    assert suggest_num_ctx(100, floor=2048, step=1024) == 2048     # floor wins
    assert suggest_num_ctx(4000, headroom_frac=0.25, step=1024) == 5120  # 5000 -> next 1024


def test_context_usage_is_recorded(tmp_path):
    from core.stores.telemetry import TelemetryStore

    store = TelemetryStore(tmp_path / "u.duckdb")
    try:
        report = Budgeter(window=100, reserve=0, estimator=WORDS).assemble(_parts()).report
        store.writer().record_context_usage("librarian", report, job_id="7", tier="routine")
        assert store.reader().context_usage_count("librarian") == 1
    finally:
        store.close()
