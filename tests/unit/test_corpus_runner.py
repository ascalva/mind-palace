"""The corpus runner's embedder policy and batch sizing (dn-corpus-instance §5.1): requests of a
batch in streams, a pause while the chat model serves, a stop on a Metal or memory error, a
bounded retry of anything else; and a request sized by the stream's mean item."""

from __future__ import annotations

import importlib.util
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from ops.corpus import embedder as emb


class _Inner:
    def __init__(self, fail: list[Exception] | None = None) -> None:
        self.fail = list(fail or [])
        self.calls: list[int] = []
        self.dim = 3
        self.config = None
        self._lock = threading.Lock()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            self.calls.append(len(texts))
            if self.fail:
                raise self.fail.pop(0)
        return [[float(len(t)), 0.0, 1.0] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class _Gate:
    def __init__(self) -> None:
        self.waits = 0
        self._probe: Any = None

    def wait(self) -> None:
        self.waits += 1


def test_texts_go_out_in_batches_on_streams_and_come_back_in_order():
    inner, gate = _Inner(), _Gate()
    g = emb.GatedEmbedder(inner, gate, streams=4, batch=32)   # type: ignore[arg-type]
    texts = [f"t{i}" * (i % 5 + 1) for i in range(100)]
    out = g.embed_documents(texts)
    assert [v[0] for v in out] == [float(len(t)) for t in texts]
    assert sorted(inner.calls) == [4, 32, 32, 32] and gate.waits == 4
    assert g.embedded == 100


def test_a_metal_or_memory_error_stops_the_run_at_once(monkeypatch):
    monkeypatch.setattr(emb.time, "sleep", lambda s: None)
    g = emb.GatedEmbedder(_Inner([RuntimeError("ggml_metal: out of memory")]), _Gate(),  # type: ignore[arg-type]
                          streams=1, batch=8)
    with pytest.raises(emb.EmbedderStopped, match="out of memory"):
        g.embed_documents(["a", "b"])


def test_another_error_is_retried_then_stops(monkeypatch):
    monkeypatch.setattr(emb.time, "sleep", lambda s: None)
    inner = _Inner([ConnectionError("refused"), ConnectionError("refused")])
    g = emb.GatedEmbedder(inner, _Gate(), streams=1, batch=8)  # type: ignore[arg-type]
    assert len(g.embed_documents(["a"])) == 1 and len(inner.calls) == 3
    clock = iter(range(0, 10**6, 1000))
    monkeypatch.setattr(emb.time, "monotonic", lambda: float(next(clock)))
    inner = _Inner([ConnectionError("refused")] * 50)
    g = emb.GatedEmbedder(inner, _Gate(), streams=1, batch=8)  # type: ignore[arg-type]
    with pytest.raises(emb.EmbedderStopped, match="kept failing"):
        g.embed_documents(["a"])


def test_the_gate_pauses_while_the_chat_model_spends_cpu_and_resumes_after_quiet(monkeypatch):
    cpu = {"s": 0.0}
    monkeypatch.setattr(emb, "_pid_listening", lambda port: 4242)
    monkeypatch.setattr(emb, "process_cpu_seconds", lambda pid: cpu["s"])
    gate = emb.Gate(chat_port=8080, embed_port=8081, busy_cpu=0.05, quiet_s=0.3, sample_s=0.05)
    try:
        time.sleep(0.2)
        assert not gate.serving()
        cpu["s"] += 10.0                                   # the chat model generating
        deadline = time.monotonic() + 2
        while not gate.serving() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert gate.serving()
        t0 = time.monotonic()
        gate.wait()                                        # returns once quiet for quiet_s
        assert time.monotonic() - t0 >= 0.2 and gate.pauses == 1 and gate.paused_s > 0
    finally:
        gate.close()


def _runner() -> Any:
    path = Path(__file__).resolve().parents[2] / "scripts" / "corpus.py"
    spec = importlib.util.spec_from_file_location("corpus_runner", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_request_is_sized_by_the_streams_mean_item(tmp_path: Path):
    from edge.corpus.stream import StreamWriter

    runner = _runner()
    long_, short = tmp_path / "long", tmp_path / "short"
    w = StreamWriter(long_)
    for i in range(4):
        w.append(f"b{i}", "B", "x" * 400_000)               # books: about 520 chunks each
    w.close()
    w = StreamWriter(short)
    for i in range(10):
        w.append(f"a{i}", "A", "y" * 900)                   # abstracts: one chunk each
    w.close()
    assert runner.batch_items(long_, 3000, 2000) == 5
    assert runner.batch_items(short, 3000, 2000) == 2000
    assert runner.batch_items(tmp_path / "empty", 3000, 2000) == 1538


def test_a_text_too_long_for_the_server_is_sent_alone_and_cut_to_what_it_takes(monkeypatch):
    monkeypatch.setattr(emb.time, "sleep", lambda s: None)

    class _Long(_Inner):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            with self._lock:
                self.calls.append(len(texts))
            if any(len(t) > 50 for t in texts):
                raise RuntimeError("/v1/embeddings failed (HTTP 500): input (2951 tokens) is too "
                                   "large to process. increase the physical batch size")
            return [[float(len(t)), 0.0, 1.0] for t in texts]

    inner = _Long()
    g = emb.GatedEmbedder(inner, _Gate(), streams=1, batch=8)  # type: ignore[arg-type]
    texts = ["short", "x" * 300, "also short"]
    out = g.embed_documents(texts)
    assert out[0][0] == 5.0 and out[2][0] == 10.0                    # the others whole
    assert 42 <= out[1][0] <= 50                                     # the long one, cut
    assert g.truncated == [(300, int(out[1][0]))] and g.embedded == 3
