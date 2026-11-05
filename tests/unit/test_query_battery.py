"""The battery script runs (the review of 2026-11-05, finding 7: it called a method the engine had
renamed, and no test imported it). A stub engine, the sentence universe's fake, drives the whole
battery: every row is instantiated, asked both ways, and rendered; a refusal is a result."""

from __future__ import annotations

from pathlib import Path

from core.query import AMBASSADOR_OVERLAY
from eval import query_battery as qb
from tests.unit.test_sentence_universe import _Engine, _vec, engine  # noqa: F401  (the fixture)


def test_the_battery_runs_and_renders_on_a_stub_engine(engine: _Engine) -> None:  # noqa: F811
    engine._cache["embedder"] = type("E", (), {"embed_query": staticmethod(lambda t: _vec(0))})()
    rows = qb.rows_for(engine, 3)                                     # type: ignore[arg-type]
    assert len(rows) >= 8 and all(r.flat and r.composed and r.wins_when for r in rows)
    results = [(qb._ask(engine, AMBASSADOR_OVERLAY, r.flat, 3),       # type: ignore[arg-type]
                qb._ask(engine, AMBASSADOR_OVERLAY, r.composed, 3))   # type: ignore[arg-type]
               for r in rows]
    text = qb.render(rows, results, k=3, started="2026-11-05T00:00:00", seconds=0.0)
    assert text.startswith("# The query battery") and text.count("\n## ") == len(rows)
    # the composed sentences compile under the grant the battery uses: a refusal here would be a
    # typing regression, not the corpus's answer
    assert not [a.error for _, a in results if a.error.startswith(("ParseError", "SortError"))]


def test_the_battery_reaches_no_private_method_and_writes_no_tracked_doc_by_default() -> None:
    src = Path(qb.__file__).read_text(encoding="utf-8")
    assert "._note_graph" not in src and 'ROOT / "data" / "experiments"' in src
