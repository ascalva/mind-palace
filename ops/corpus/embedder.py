"""The corpus runner's embedder: the stack's shared embedder, behind the yield policy.

The stack's embedder on its port is shared with the default instance's daemon and with the
bridge's queries, and it shares Metal with the chat model (dn-corpus-instance §5.1). The bulk path
therefore embeds under a policy, measured on 2026-11-07 (`docs/experiments/corpus-measurements-
2026-11-07.md`):

- **streams and batch**: `streams` requests in flight, `batch` texts each (one stream of 64 by
  default; four of 32 measured best when no other caller needs the embedder);
- **pause while the chat model serves**: before each request, the gate reads the chat model's
  process (the one listening on the chat port) and waits while its CPU time is rising, and for a
  quiet interval after, so the bulk path never competes with an answer being generated;
- **stop on Metal or memory**: an embedder error whose text names Metal, memory or a compute
  error stops the run at once (`EmbedderStopped`); the runner records it and exits between
  batches, every stream at its cursor. Other errors (the embedder waking from sleep, a refused
  connection) are retried with backoff for a bounded time, then stop the run the same way.

The gate also times a one-text probe every few minutes, the latency another caller would see,
and keeps counts (texts embedded, seconds embedding, seconds paused) for the run's report.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.typedshims.psutil import process_cpu_seconds

FATAL = ("metal", "out of memory", "oom", "failed to allocate", "compute error",
         "ggml_backend", "insufficient memory")
RETRY_FOR_S = 600.0            # how long a non-fatal embedder error is retried before stopping


class EmbedderStopped(RuntimeError):
    """The embedder failed in a way the policy stops on."""


def _pid_listening(port: int) -> int | None:
    """The pid of the process listening on a loopback TCP port, by `lsof`."""
    try:
        out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                             capture_output=True, text=True, timeout=10).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return None
    return int(out[0]) if out else None


class Gate:
    """Decides when the next embedder request may start, and keeps the run's counts."""

    def __init__(self, *, chat_port: int, embed_port: int, log: Path | None = None,
                 busy_cpu: float = 0.05, quiet_s: float = 20.0, sample_s: float = 1.0,
                 probe_every_s: float = 300.0,
                 probe: Callable[[], float] | None = None) -> None:
        self.chat_port = chat_port
        self.embed_port = embed_port
        self.log = log
        self.busy_cpu = busy_cpu            # CPU seconds per second that count as serving
        self.quiet_s = quiet_s
        self.sample_s = sample_s
        self.probe_every_s = probe_every_s
        self._probe = probe
        self._last_probe = 0.0
        self._pid: int | None = None
        self._cpu: tuple[float, float] | None = None     # (monotonic, cpu seconds)
        self._busy_until = 0.0
        self.paused_s = 0.0
        self.pauses = 0
        self.probes: list[tuple[str, float]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    def _say(self, msg: str) -> None:
        if self.log is not None:
            with self.log.open("a") as fh:
                fh.write(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}\n")

    def _chat_cpu(self) -> float | None:
        """The chat model's CPU seconds since it started, or None when nothing listens."""
        for _ in range(2):
            if self._pid is None:
                self._pid = _pid_listening(self.chat_port)
                if self._pid is None:
                    return None
            cpu = process_cpu_seconds(self._pid)
            if cpu is not None:
                return cpu
            self._pid = None
        return None

    def _watch(self) -> None:
        while not self._stop.wait(self.sample_s):
            now, cpu = time.monotonic(), self._chat_cpu()
            if cpu is None:
                self._cpu = None
                continue
            if self._cpu is not None:
                rate = (cpu - self._cpu[1]) / max(1e-6, now - self._cpu[0])
                if rate >= self.busy_cpu:
                    with self._lock:
                        if self._busy_until < now:
                            self._say(f"chat model serving ({rate:.2f} cpu/s): pausing")
                        self._busy_until = now + self.quiet_s
            self._cpu = (now, cpu)

    def serving(self) -> bool:
        with self._lock:
            return time.monotonic() < self._busy_until

    def wait(self) -> None:
        """Block while the chat model serves (and for the quiet interval after it)."""
        if not self.serving():
            self._maybe_probe()
            return
        t0 = time.monotonic()
        self.pauses += 1
        while self.serving():
            time.sleep(0.5)
        dt = time.monotonic() - t0
        self.paused_s += dt
        self._say(f"resumed after {dt:.0f} s")

    def _maybe_probe(self) -> None:
        if self._probe is None or time.monotonic() - self._last_probe < self.probe_every_s:
            return
        self._last_probe = time.monotonic()
        try:
            ms = self._probe()
        except Exception as e:      # noqa: BLE001 - a probe never stops the run
            self._say(f"probe failed: {e}")
            return
        self.probes.append((datetime.now(UTC).isoformat(timespec="seconds"), round(ms, 1)))

    def summary(self) -> dict[str, Any]:
        return {"pauses": self.pauses, "paused_s": round(self.paused_s, 1),
                "probes_ms": [p[1] for p in self.probes[-20:]],
                "probe_median_ms": (sorted(p[1] for p in self.probes)[len(self.probes) // 2]
                                    if self.probes else None)}

    def close(self) -> None:
        self._stop.set()
        if self.log is not None and self.probes:
            self._say("probes " + json.dumps(self.probes))


class GatedEmbedder:
    """An `Embedder` whose `embed_documents` runs as `streams` requests of `batch` texts, each
    started only when the gate allows, and stops the run on a fatal error. Everything else is the
    inner embedder's (its client, its templates, its dimension)."""

    def __init__(self, inner: Any, gate: Gate, *, streams: int = 1, batch: int = 64) -> None:
        self.inner = inner
        self.gate = gate
        self.streams = max(1, streams)
        self.batch = max(1, batch)
        self.embedded = 0
        self.seconds = 0.0
        self._pool = ThreadPoolExecutor(max_workers=self.streams)
        if gate._probe is None:
            gate._probe = self._probe

    @property
    def dim(self) -> int:
        return int(self.inner.dim)

    @property
    def config(self) -> Any:
        return self.inner.config

    def embed_query(self, text: str) -> list[float]:
        return list(self.inner.embed_query(text))

    def _probe(self) -> float:
        t0 = time.monotonic()
        self.inner.embed_query("probe")
        return (time.monotonic() - t0) * 1000.0

    def _one(self, texts: Sequence[str]) -> list[list[float]]:
        deadline = time.monotonic() + RETRY_FOR_S
        delay = 2.0
        while True:
            self.gate.wait()
            try:
                return [list(v) for v in self.inner.embed_documents(list(texts))]
            except Exception as e:      # noqa: BLE001 - classified: fatal stops, the rest retry
                text = str(e).lower()
                if any(k in text for k in FATAL):
                    raise EmbedderStopped(f"the embedder failed: {e}") from e
                if time.monotonic() > deadline:
                    raise EmbedderStopped(f"the embedder kept failing for "
                                          f"{RETRY_FOR_S:.0f} s: {e}") from e
                time.sleep(delay)
                delay = min(delay * 2, 60.0)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        t0 = time.monotonic()
        parts = [texts[i:i + self.batch] for i in range(0, len(texts), self.batch)]
        out: list[list[float]] = []
        for vecs in self._pool.map(self._one, parts):
            out.extend(vecs)
        self.seconds += time.monotonic() - t0
        self.embedded += len(texts)
        return out
