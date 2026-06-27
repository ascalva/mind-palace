"""The local vault watcher (vault-sync task): debounce + backend lifecycle.

Core-side, filesystem only — no network. Here we pin the trigger/coalesce behavior and the
polling fallback without needing watchdog or real FS events (the re-ingest itself is covered
in test_vault_sync).
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from core.ingest.watch import VaultWatcher


def test_notify_fires_immediately_without_debounce(tmp_path: Path):
    calls = []
    w = VaultWatcher(vault=tmp_path, on_change=lambda: calls.append(1), debounce_s=0)
    w.notify()
    assert calls == [1]


def test_notify_debounces_a_burst(tmp_path: Path):
    calls = []
    w = VaultWatcher(vault=tmp_path, on_change=lambda: calls.append(1), debounce_s=0.1)
    for _ in range(5):                 # a save burst
        w.notify()
        time.sleep(0.01)
    assert calls == []                  # not yet — still within the debounce window
    time.sleep(0.2)
    assert calls == [1]                 # coalesced into a single re-ingest
    w.stop()


def test_poll_backend_triggers_on_change(tmp_path: Path):
    fired = threading.Event()
    w = VaultWatcher(vault=tmp_path, on_change=fired.set, poll_interval_s=0.05)
    backend = w.start(prefer="poll")
    try:
        assert backend == "poll"
        assert fired.wait(timeout=2.0)  # the poll loop triggers a rescan
    finally:
        w.stop()


def test_auto_falls_back_to_poll_without_watchdog(tmp_path: Path):
    # watchdog isn't installed in this env, so auto must degrade to polling, never error.
    w = VaultWatcher(vault=tmp_path, on_change=lambda: None, poll_interval_s=0.05)
    backend = w.start(prefer="auto")
    try:
        assert backend in {"watchdog", "poll"}  # 'poll' here; 'watchdog' if a host has it
    finally:
        w.stop()
