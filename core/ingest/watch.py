"""Local vault watcher — core-side, LOCAL filesystem only, NO network (vault-sync task).

Watches the configured vault path and signals when notes change, so the system keeps the
owner's embeddings current as they write. It does **not** mutate the stores itself and does
**not** import the scheduler: on a change it just calls an injected `on_change` callback. The
scheduler wiring (`scheduler/vault_sync.py`) supplies a callback that enqueues a background
`vault_sync` job, so all store writes stay on the single supervisor writer.

Seal integrity: this module imports no `edge`, no sockets, no http — only the local
filesystem (the import-lint proves it). `watchdog` (FSEvents/inotify) is an OPTIONAL real-time
backend, imported lazily; without it the watcher falls back to **polling** (a timer that
triggers a periodic rescan). Either way `on_change` ultimately runs the idempotent
`VaultSync.rescan`, so missed/duplicate events are harmless.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

OnChange = Callable[[], None]


class ObserverLike(Protocol):
    """The slice of a watchdog Observer this watcher drives (watchdog is an
    OPTIONAL dependency, so its own types never appear in signatures here)."""

    def stop(self) -> None: ...

    def join(self, timeout: float | None = ...) -> None: ...


@dataclass
class VaultWatcher:
    vault: Path
    on_change: OnChange
    debounce_s: float = 1.0       # coalesce a burst of saves into one on_change
    poll_interval_s: float = 5.0  # fallback cadence when watchdog isn't available
    _timer: threading.Timer | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _observer: ObserverLike | None = field(default=None, init=False, repr=False)
    _poll_stop: threading.Event | None = field(default=None, init=False, repr=False)
    backend: str = field(default="", init=False)

    # --- event coalescing -----------------------------------------------------------
    def notify(self) -> None:
        """A change was observed. Arm/re-arm the debounce timer so a save burst fires once."""
        if self.debounce_s <= 0:
            self.on_change()
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_s, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        with self._lock:
            self._timer = None
        self.on_change()

    # --- lifecycle ------------------------------------------------------------------
    def start(self, *, prefer: str = "auto") -> str:
        """Begin watching. `prefer`: 'auto' (watchdog if importable, else poll), 'watchdog',
        or 'poll'. Returns the backend actually started."""
        if prefer in ("auto", "watchdog") and self._start_watchdog():
            self.backend = "watchdog"
        else:
            self._start_poll()
            self.backend = "poll"
        return self.backend

    def _start_watchdog(self) -> bool:
        try:
            from watchdog.events import FileSystemEventHandler  # lazy: optional dependency
            from watchdog.observers import Observer
        except Exception:
            return False

        watcher = self

        class _Handler(FileSystemEventHandler):
            def on_any_event(self, event: object) -> None:
                watcher.notify()

        observer = Observer()
        observer.schedule(_Handler(), str(self.vault), recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer
        return True

    def _start_poll(self) -> None:
        stop = threading.Event()
        self._poll_stop = stop

        def loop() -> None:
            # Poll mode triggers a periodic rescan directly; rescan is idempotent so this is
            # eventual-consistency catch-up without needing per-file events.
            while not stop.wait(self.poll_interval_s):
                self.on_change()

        t = threading.Thread(target=loop, name="vault-watch-poll", daemon=True)
        t.start()
        self._poll_thread = t

    def stop(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None
        if self._poll_stop is not None:
            self._poll_stop.set()
            self._poll_stop = None
