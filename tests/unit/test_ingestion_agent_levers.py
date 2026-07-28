"""One lever per ingestion agent, and each lever gates EVERY path its agent uses.

Owner ruling 2026-07-28: *"it should be per agent, the code-sync ingestion agent is its own
ingestion section, the transcript-sync ingestion is its own ingestion section, the author corpus
ingestion (vault) is its own ingestion section"* — and separately, *"chat events is part of
transcript ingestion, integrate is its own type of agent"*.

What that rules out, and why these tests exist:

  1. **One flag spanning several agents.** The first attempt put a single `[chat].enabled` above a
     section that also held `events_max_per_pass` and `integrate_max_per_pass` — knobs it did not
     govern. A lever has to name the agent it stops, and a section has to hold only what its lever
     covers. Hence `[ingestion.vault|transcripts|code]` + a separate `[integrate]`.
  2. **A gate that misses a path.** The first attempt gated the housekeeping pass and the watcher
     but not `_catchup`, which runs on every daemon start — so the "pause" would have lifted itself
     at the next deploy, the exact moment it was meant to hold. Every agent is therefore checked in
     all three: watcher, housekeeping, catch-up.
  3. **A nested overlay silently reverting siblings.** `[ingestion.*]` needs a recursive merge; the
     shallow one replaced whole subsections. See `test_overlay_deep_merges_nested_subsections`.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from core.kernel.config import REPO_ROOT, load_config
from core.kernel.config.loader import _overlay
from ops.lifecycle.launcher import build_components
from scheduler.chat_sync import CHAT_SYNC_KIND
from scheduler.code_sync import CODE_SYNC_KIND
from scheduler.cron import CHAT_EVENTS_KIND, INTEGRATE_KIND
from scheduler.vault_sync import VAULT_SYNC_KIND

# --- the overlay must merge nested tables, not replace them ---------------------------------


def test_overlay_deep_merges_nested_subsections(tmp_path) -> None:
    """The falsifier for the shallow merge that nested sections would otherwise hit.

    An overlay naming ONE key of ONE subsection must leave that subsection's other keys — and its
    sibling subsections — intact. Under the old one-level `update()` this returned
    `{'enabled': False}` and silently dropped `events_max_per_pass`, which no reader would notice
    because they all use `.get(key, default)`."""
    raw: dict[str, Any] = {"ingestion": {
        "transcripts": {"enabled": True, "events_max_per_pass": 50, "watch_debounce_s": 0.5},
        "code": {"enabled": True, "max_chars": 1200}}}
    overlay = tmp_path / "o.toml"
    overlay.write_text("[ingestion.transcripts]\nenabled = false\n", encoding="utf-8")
    _overlay(raw, overlay)

    t = raw["ingestion"]["transcripts"]
    assert t["enabled"] is False           # the key the overlay named changed
    assert t["events_max_per_pass"] == 50  # its siblings SURVIVED (the whole point)
    assert t["watch_debounce_s"] == 0.5
    assert raw["ingestion"]["code"] == {"enabled": True, "max_chars": 1200}   # sibling subsection


def test_overlay_still_merges_flat_sections(tmp_path) -> None:
    """Recursion must not regress the flat case every other section relies on."""
    raw: dict[str, Any] = {"dreaming": {"similarity_threshold": 0.62, "min_cluster_size": 3}}
    overlay = tmp_path / "o.toml"
    overlay.write_text("[dreaming]\nsimilarity_threshold = 0.58\n", encoding="utf-8")
    _overlay(raw, overlay)
    assert raw["dreaming"] == {"similarity_threshold": 0.58, "min_cluster_size": 3}


# --- the shipped defaults ---------------------------------------------------------------------


def test_every_agent_has_its_own_lever_and_ships_on() -> None:
    """Read defaults.toml DIRECTLY so this machine's opt-out overlay cannot mask the default."""
    c = load_config(REPO_ROOT / "config" / "defaults.toml")
    assert c.ingestion.vault.enabled is True
    assert c.ingestion.transcripts.enabled is True
    assert c.ingestion.code.enabled is True
    assert c.integrate.enabled is True          # its own agent type, outside [ingestion]


def test_integrate_is_not_an_ingestion_agent() -> None:
    """`integrate` derives edges from already-ingested material, so it must NOT be reachable as
    `cfg.ingestion.*` — the taxonomy is load-bearing, not decorative."""
    c = load_config(REPO_ROOT / "config" / "defaults.toml")
    assert not hasattr(c.ingestion, "integrate")
    assert c.integrate.max_per_pass == 50        # its knob moved with it, out of the chat section


# --- temp-config fixture ----------------------------------------------------------------------


def _cfg(root: Path, *, vault=True, transcripts=True, code=True, integrate=True):
    """A fully temp-pathed Config with each agent's lever set independently."""
    root.mkdir(parents=True, exist_ok=True)
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=root, raw_store=root / "raw", vector_store=root / "v.lance",
        vault_catalog=root / "cat.sqlite", derived_store=root / "d.sqlite",
        attestation_store=root / "att.sqlite", telemetry_db=root / "t.duckdb")
    ingestion = dataclasses.replace(
        base.ingestion,
        vault=dataclasses.replace(base.ingestion.vault, path=root / "vault", enabled=vault),
        transcripts=dataclasses.replace(base.ingestion.transcripts, enabled=transcripts),
        code=dataclasses.replace(base.ingestion.code, enabled=code))
    return dataclasses.replace(
        base, paths=paths, ingestion=ingestion,
        integrate=dataclasses.replace(base.integrate, enabled=integrate))


def _kinds(comps, which: str) -> list[str]:
    (comps.enqueue_housekeeping if which == "housekeeping" else comps.enqueue_catchup)()
    return [j.kind for j in comps.queue.list()]


# --- all three paths, per agent -----------------------------------------------------------------


def test_transcript_agent_gates_both_its_kinds_in_housekeeping(tmp_path) -> None:
    """chat_sync AND chat_events are ONE agent, so one lever stops both (owner ruling)."""
    on = build_components(_cfg(tmp_path / "on"))
    try:
        k = _kinds(on, "housekeeping")
        assert CHAT_SYNC_KIND in k and CHAT_EVENTS_KIND in k
    finally:
        on.queue.close()
    off = build_components(_cfg(tmp_path / "off", transcripts=False))
    try:
        k = _kinds(off, "housekeeping")
        assert CHAT_SYNC_KIND not in k and CHAT_EVENTS_KIND not in k
    finally:
        off.queue.close()


def test_catchup_is_gated_for_every_agent(tmp_path) -> None:
    """THE regression this suite exists for. `_catchup` runs on every daemon start, so an agent
    gated only in housekeeping unpauses itself at the next deploy — the precise moment a pause is
    supposed to hold."""
    on = build_components(_cfg(tmp_path / "on"))
    try:
        k = _kinds(on, "catchup")
        assert VAULT_SYNC_KIND in k and CHAT_SYNC_KIND in k
    finally:
        on.queue.close()
    off = build_components(_cfg(tmp_path / "off", vault=False, transcripts=False, code=False))
    try:
        k = _kinds(off, "catchup")
        assert VAULT_SYNC_KIND not in k and CHAT_SYNC_KIND not in k
    finally:
        off.queue.close()


def test_watchers_are_gated_per_agent(tmp_path) -> None:
    """The real-time path. Each watcher answers to its OWN agent's lever, so disabling one must
    drop exactly one — not both, and not neither."""
    both = build_components(_cfg(tmp_path / "both"))
    no_chat = build_components(_cfg(tmp_path / "nochat", transcripts=False))
    no_vault = build_components(_cfg(tmp_path / "novault", vault=False))
    neither = build_components(_cfg(tmp_path / "neither", vault=False, transcripts=False))
    try:
        assert len(both.watchers) == 2
        assert len(no_chat.watchers) == 1
        assert len(no_vault.watchers) == 1
        assert len(neither.watchers) == 0
    finally:
        for c in (both, no_chat, no_vault, neither):
            c.queue.close()


def test_integrate_has_its_own_independent_lever(tmp_path) -> None:
    """Its own agent type: pausing all ingestion must NOT stop it, and stopping it must not
    disturb ingestion."""
    no_ingest = build_components(_cfg(tmp_path / "ni", vault=False, transcripts=False, code=False))
    try:
        assert INTEGRATE_KIND in _kinds(no_ingest, "housekeeping")
    finally:
        no_ingest.queue.close()
    no_integ = build_components(_cfg(tmp_path / "no_i", integrate=False))
    try:
        k = _kinds(no_integ, "housekeeping")
        assert INTEGRATE_KIND not in k
        assert CHAT_SYNC_KIND in k and CODE_SYNC_KIND in k
    finally:
        no_integ.queue.close()
