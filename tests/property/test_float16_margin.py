"""VEC-1's falsifier: float16 storage, its cosine bound and the margin certificate (docs/LAWS.md).

The law (`formal/Palace/Cosine.lean`) is stated over `rn16`, round to nearest, ties to even onto
binary16, and the certificate `core/kernel/margin.py` computes is its `top_unchanged`. Here the law
meets this machine: the store's own write path against an exact transcription of the model, bit
for bit, including the table `formal/PalaceTest/Format.lean` checks the Lean model against; the
coordinate and cosine bounds on adversarial vectors; the certificate on a fixture store, where a
certified top `k` must be the top `k` of the exact cosines, and a margin violated by construction
must both change the top `k` and be refused. LanceDB's distance kernel is held to the hypothesis
`γ` the certificate assumes.
"""

from __future__ import annotations

import math
import re
import struct
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pyarrow as pa

from core.kernel.clearance import CODE_READ
from core.kernel.margin import (
    TAU16,
    U16,
    Margin,
    bound,
    certify,
    kernel_bound,
    query_bound,
    store_bound,
)
from core.stores.vectorstore import VectorStore
from core.typedshims.lancedb import connect

F64 = npt.NDArray[np.float64]
TABLE = Path(__file__).resolve().parents[2] / "formal" / "PalaceTest" / "Format.lean"
DIM = 64


def rnf(x: Fraction, p: int, emin: int) -> Fraction:
    """`Palace.Format.rnf p emin`, transcribed over exact rationals."""
    if x == 0:
        return Fraction(0)
    a = abs(x)
    log = a.numerator.bit_length() - a.denominator.bit_length()
    while Fraction(2) ** log > a:
        log -= 1
    while Fraction(2) ** (log + 1) <= a:
        log += 1
    scale = Fraction(2) ** max(log - (p - 1), emin)
    y = x / scale
    f = math.floor(y)
    r = y - f
    n = f if r < Fraction(1, 2) else f + 1 if r > Fraction(1, 2) else f + (f % 2)
    return n * scale


def rn16(x: float) -> Fraction:
    return rnf(Fraction(x), 11, -24)


def store_path(x: float) -> Fraction:
    """What the store's write path does to a double: float32, then float16 (lancedb 0.33.0)."""
    return rnf(rnf(Fraction(x), 24, -149), 11, -24)


def _samples(rng: np.random.Generator, n: int) -> list[float]:
    """Doubles at binary16's scale: normal, subnormal, exact ties, carries, and near-ties."""
    out: list[float] = []
    for _ in range(n):
        e = int(rng.integers(-14, 15))
        m = int(rng.integers(0, 1024))
        tie = (1024 + m + 0.5) * 2.0 ** (e - 10)
        kind = int(rng.integers(0, 5))
        x = (2.0 ** e * (1 + rng.random()) if kind == 0 else
             2.0 ** -14 * rng.random() if kind == 1 else
             tie if kind == 2 else
             (2047.5 + 0.5 * rng.random()) * 2.0 ** (e - 10) if kind == 3 else
             tie * (1 + float(rng.choice([-1, 1])) * 2.0 ** -int(rng.integers(26, 40))))
        out.append(float(rng.choice([-1.0, 1.0])) * x)
    return out


def _land16(tmp_path: Path, values: list[float]) -> list[float]:
    """The store's write path: a list of Python floats landed in a float16 column, read back."""
    db = connect(str(tmp_path / "w.lance"))
    t = db.create_table("w", schema=pa.schema([("vector", pa.list_(pa.float16(), len(values)))]))
    t.add([{"vector": values}])
    return [float(v) for v in cast(list[float], t.to_arrow().to_pylist()[0]["vector"])]


def test_the_store_rounds_as_the_model_bit_for_bit(tmp_path: Path) -> None:
    values = _samples(np.random.default_rng(20261105), 2000)
    stored = _land16(tmp_path, values)
    assert [Fraction(v) for v in stored] == [store_path(x) for x in values]
    # float32 values, as the embedder returns them, round once: the model's `rn16`
    f32 = [float(np.float32(x)) for x in values]
    assert [Fraction(float(np.float16(np.float32(x)))) for x in f32] == [rn16(x) for x in f32]


def test_control_rounding_once_is_not_the_stores_path(tmp_path: Path) -> None:
    values = _samples(np.random.default_rng(7), 2000)
    stored = _land16(tmp_path, values)
    assert any(Fraction(s) != rn16(x) for s, x in zip(stored, values, strict=True))


def _table() -> list[tuple[float, int]]:
    text = TABLE.read_text(encoding="utf-8")
    body = text[text.index("def table16"):]
    body = body[:body.index("]")]
    pairs = re.findall(r"\(0x([0-9A-F]{16}), 0x([0-9A-F]{4})\)", body)
    return [(struct.unpack("<d", struct.pack("<Q", int(a, 16)))[0], int(h, 16)) for a, h in pairs]


def test_the_lean_attacks_table_is_still_this_machines_float16(tmp_path: Path) -> None:
    table = _table()
    assert len(table) == 234
    stored = _land16(tmp_path, [x for x, _ in table])
    bits = np.asarray(stored, dtype=np.float16).view(np.uint16)
    assert [int(b) for b in bits] == [h for _, h in table]
    assert [Fraction(s) for s in stored] == [store_path(x) for x, _ in table]


def test_the_coordinate_bound_holds_and_needs_its_floor() -> None:
    values = [float(np.float32(x)) for x in _samples(np.random.default_rng(11), 3000)]
    err = [abs(rn16(x) - Fraction(x)) for x in values]
    assert all(e <= Fraction(U16) * max(abs(Fraction(x)), Fraction(TAU16))
               for e, x in zip(err, values, strict=True))
    # the control: the relative bound alone fails below the normal range
    assert any(e > Fraction(U16) * abs(Fraction(x)) for e, x in zip(err, values, strict=True))


def _unit(v: F64) -> F64:
    return np.asarray(v / np.linalg.norm(v), dtype=np.float64)


def _cos(a: F64, b: F64) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def _round16(v: F64) -> F64:
    return np.asarray(v.astype(np.float32).astype(np.float16), dtype=np.float64)


def test_the_storage_bound_holds_and_is_nearly_attained() -> None:
    rng = np.random.default_rng(3)
    d = 768
    beta = store_bound(d)
    worst = 0.0
    for _ in range(200):
        y = _unit(rng.standard_normal(d)).astype(np.float32).astype(np.float64)
        e = _round16(y) - y
        q = e - (e @ y) * y                      # the query that sees the most of the error
        for qq in (q, rng.standard_normal(d), y):
            worst = max(worst, abs(_cos(qq, _round16(y)) - _cos(qq, y)))
    assert worst <= beta
    # vectors whose every coordinate rounds by a full relative 2^-11, half up and half down:
    # the error is orthogonal to the vector, and a query along it sees nearly all of the bound
    signs = np.where(np.arange(d) % 2 == 0, 1.0, 3.0)
    y = (1 + signs * 2.0 ** -11) * 2.0 ** -5
    e = _round16(y) - y
    q = e - (e @ y) / (y @ y) * y
    attained = abs(_cos(q, _round16(y)) - _cos(q, y))
    assert attained <= store_bound(d, nu=float(np.linalg.norm(y)))
    assert attained > 0.9 * U16


def test_the_query_bound_covers_the_querys_rounding() -> None:
    rng = np.random.default_rng(5)
    for _ in range(200):
        q = _unit(rng.standard_normal(DIM))
        x = _unit(rng.standard_normal(DIM))
        q16 = _round16(q)
        assert abs(_cos(q16, x) - _cos(q, x)) <= query_bound(q.tolist())


def _code_row(i: int, v: F64) -> dict[str, Any]:
    return {"id": f"r{i}", "digest": "d", "title": "t", "source_path": "core/x.py",
            "chunk_index": i, "provenance": "code", "text": f"def f{i}(): ...",
            "layer": "code_text", "vector": [float(x) for x in v.astype(np.float32)]}


def _store(tmp_path: Path, vectors: F64) -> VectorStore:
    store = VectorStore(tmp_path / "v.lance", dim=vectors.shape[1])
    store.add([_code_row(i, v) for i, v in enumerate(vectors)])
    return store


class _Query:
    """A LanceDB query that records the candidate counts asked of it."""

    def __init__(self, inner: Any, seen: list[int]) -> None:
        self._inner, self._seen = inner, seen

    def metric(self, name: str) -> _Query:
        return _Query(self._inner.metric(name), self._seen)

    def where(self, predicate: str, **kw: Any) -> _Query:
        return _Query(self._inner.where(predicate, **kw), self._seen)

    def select(self, columns: Any) -> _Query:
        return _Query(self._inner.select(columns), self._seen)

    def limit(self, k: int) -> _Query:
        self._seen.append(k)
        return _Query(self._inner.limit(k), self._seen)

    def to_list(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self._inner.to_list())


class _Table:
    def __init__(self, inner: Any, seen: list[int]) -> None:
        self._inner, self._seen = inner, seen

    def search(self, vector: list[float]) -> _Query:
        return _Query(self._inner.search(vector), self._seen)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _record_limits(store: VectorStore) -> list[int]:
    """Every candidate count the store asks LanceDB for, in order."""
    seen: list[int] = []
    inner = type(store)._table

    def recorded(_self: VectorStore = store) -> Any:
        return _Table(inner(_self), seen)

    store._table = recorded       # type: ignore[method-assign]  # test instrument, instance-scoped
    return seen


def test_search_asks_for_k_and_only_the_certified_read_for_more(tmp_path: Path) -> None:
    """The certificate is opt-in: `search` asks each source for its k nearest, as before VEC-1,
    and only `search_ranked` asks for k + 1."""
    rng = np.random.default_rng(23)
    store = _store(tmp_path, np.stack([_unit(rng.standard_normal(DIM)) for _ in range(30)]))
    seen = _record_limits(store)
    q = _unit(rng.standard_normal(DIM)).tolist()
    store.search(q, k=5, clearance=CODE_READ)
    plain, seen[:] = list(seen), []
    store.search_ranked(q, k=5, clearance=CODE_READ)
    assert plain and set(plain) == {5}
    assert len(seen) == len(plain) and set(seen) == {6}


def _ideal(vectors: F64, q: F64, k: int) -> set[str]:
    """The top k of the exact cosines between the query and the float32 vectors."""
    y = vectors.astype(np.float32).astype(np.float64)
    s = y @ q / (np.linalg.norm(y, axis=1) * np.linalg.norm(q))
    return {f"r{i}" for i in np.argsort(-s, kind="stable")[:k]}


def test_a_certified_top_k_is_the_exact_top_k(tmp_path: Path) -> None:
    rng = np.random.default_rng(20261105)
    centre = _unit(rng.standard_normal(DIM))
    vectors = np.stack([_unit(centre + 0.6 * rng.standard_normal(DIM)) for _ in range(400)])
    store = _store(tmp_path, vectors)
    certified = 0
    for _ in range(60):
        q = _unit(centre + 0.5 * rng.standard_normal(DIM))
        ranked = store.search_ranked(q.tolist(), k=10, clearance=CODE_READ)
        assert [r["id"] for r in ranked.rows] == [
            r["id"] for r in store.search(q.tolist(), k=10, clearance=CODE_READ)]
        if ranked.margin.certified:
            certified += 1
            assert {str(r["id"]) for r in ranked.rows} == _ideal(vectors, q, 10)
    assert certified >= 20                       # the certificate is not vacuous here


def _swapped_pair(rng: np.random.Generator) -> tuple[F64, F64, F64]:
    """A query and two vectors whose exact cosines and float16 cosines rank them oppositely."""
    q = _unit(rng.standard_normal(DIM))
    while True:
        a = _unit(rng.standard_normal(DIM)).astype(np.float32).astype(np.float64)
        b = _unit(a + 1e-4 * rng.standard_normal(DIM)).astype(np.float32).astype(np.float64)
        exact = _cos(q, a) - _cos(q, b)
        stored = _cos(_round16(q), _round16(a)) - _cos(_round16(q), _round16(b))
        if exact * stored < 0 and abs(stored) > 1e-6:
            return q, a, b


def test_control_a_violated_margin_changes_the_top_k_and_is_refused(tmp_path: Path) -> None:
    q, a, b = _swapped_pair(np.random.default_rng(13))
    rng = np.random.default_rng(17)
    far = np.stack([_unit(-q + 0.3 * rng.standard_normal(DIM)) for _ in range(20)])
    vectors = np.vstack([a, b, far])
    store = _store(tmp_path, vectors)
    ranked = store.search_ranked(q.tolist(), k=1, clearance=CODE_READ)
    assert {str(r["id"]) for r in ranked.rows} != _ideal(vectors, q, 1)   # float16 changed it
    assert not ranked.margin.certified                                     # and it is refused
    # the mutant that trusts the computed scores, bound 0, would have certified the changed top 1
    assert Margin(k=1, gap=ranked.margin.gap, bound=0.0).certified


def test_the_kernel_stays_within_its_hypothesis(tmp_path: Path) -> None:
    rng = np.random.default_rng(19)
    vectors = np.stack([_unit(rng.standard_normal(DIM)) for _ in range(300)])
    store = _store(tmp_path, vectors)
    x16 = _round16(vectors)
    worst = 0.0
    for _ in range(30):
        q = _unit(rng.standard_normal(DIM))
        q16 = _round16(q)
        for r in store.search(q.tolist(), k=50, clearance=CODE_READ):
            i = int(str(r["id"])[1:])
            worst = max(worst, abs(float(r["_distance"]) - (1.0 - _cos(q16, x16[i]))))
    assert worst <= kernel_bound(DIM)


def test_the_bound_carries_the_querys_double_rounding(tmp_path: Path) -> None:
    """VEC-1's query term. LanceDB scores the float16 rounding of a query reached through float32,
    so `betaQuery` is taken against that rounding. A coordinate just above a float16 tie,
    `1 + 2⁻¹¹ + 2⁻³⁰`, tells it from rounding once: float32 drops the `2⁻³⁰` and the tie goes to
    the even `1`, where rounding once goes up to `1 + 2⁻¹⁰`. LanceDB's own distance is the witness.
    Fails if the bound drops the query term, or takes it against rounding once."""
    q = [1 + 2.0 ** -11 + 2.0 ** -30, 0.3, -0.7, 0.1234567, 2.0 ** -20, -1e-6, 0.5,
         (1024 + 7 + 0.5) * 2.0 ** -12 * (1 + 2.0 ** -31)]
    d = len(q)
    qa = np.asarray(q, dtype=np.float64)
    twice = np.asarray([float(store_path(x)) for x in q], dtype=np.float64)
    once = np.asarray([float(rn16(x)) for x in q], dtype=np.float64)

    def beta(qq: F64) -> float:
        return 2 * float(np.linalg.norm(qq - qa)) / float(np.linalg.norm(qa) + np.linalg.norm(qq))

    db = connect(str(tmp_path / "q.lance"))
    t = db.create_table("q", schema=pa.schema([("i", pa.int32()),
                                               ("vector", pa.list_(pa.float16(), d))]))
    t.add([{"i": i, "vector": [1.0 if j == i else 0.0 for j in range(d)]} for i in range(d)])
    hits = t.search(q).metric("cosine").limit(d).to_list()
    got = {int(cast(int, h["i"])): float(cast(float, h["_distance"])) for h in hits}
    assert abs(got[0] - (1 - twice[0] / np.linalg.norm(twice))) <= kernel_bound(d)
    assert abs(got[0] - (1 - once[0] / np.linalg.norm(once))) > 1e-4      # not rounding once
    assert query_bound(q) > 0
    assert math.isclose(query_bound(q), beta(twice), rel_tol=1e-12)
    assert not math.isclose(beta(twice), beta(once), rel_tol=1e-9)
    assert math.isclose(bound(q), 2 * (store_bound(d) + beta(twice) + kernel_bound(d))
                        * (1 + 2.0 ** -20), rel_tol=1e-12)


def test_the_gap_skips_rows_of_one_atom_and_is_infinite_with_nothing_outside() -> None:
    q = [1.0] + [0.0] * 7
    m = certify([0.1, 0.2, 0.2, 0.5], ["a", "b", "b", "c"], 2, q)
    assert math.isclose(m.gap, 0.3) and m.certified
    assert certify([0.1, 0.2, 0.2], ["a", "b", "b"], 2, q).gap == math.inf
    # the control: keyed by row, the two rows of `b` tie at the cut and nothing is certified
    assert not certify([0.1, 0.2, 0.2, 0.5], ["a", "b", "b2", "c"], 2, q).certified
    assert math.isclose(bound(q), 2 * (store_bound(8) + kernel_bound(8)) * (1 + 2.0 ** -20))
