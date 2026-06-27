"""Supervisor integration (BUILD-SPEC §13; roadmap §7), all deterministic (warm=False, no
Ollama): tier grouping minimizes swaps; the foreground check gates heavy tiers; the RAM
ceiling defers rather than crashes; a handler failure is isolated; checkpointed jobs yield
and resume at job boundaries."""

import dataclasses

import pytest
from fixtures.secrets import fake_vault

from config.loader import load_config
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry
from scheduler.presence import Presence
from scheduler.queue import DEFERRED, DONE, FAILED, QUEUED, JobQueue
from scheduler.supervisor import Supervisor


def _loader(cfg=None):
    cfg = cfg or load_config()
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


def _present(active: bool) -> Presence:
    # idle 0s => owner present; idle huge => idle. Threshold is 300s.
    return Presence(idle_probe=lambda: 0.0 if active else 10_000.0)


def _supervisor(tmp_path, handlers, *, active=False, loader=None, secrets=None):
    return Supervisor(
        queue=JobQueue(tmp_path / "q.db"),
        loader=loader or _loader(),
        handlers=handlers,
        presence=_present(active),
        warm=False,
        secrets=secrets,
    )


def test_runs_jobs_in_order_and_records_results(tmp_path):
    order = []
    sup = _supervisor(tmp_path, {"x": lambda j: order.append(j.id) or "done"})
    sup.loader.ensure_pinned(warm=False)
    a = sup.queue.enqueue("x", "routine", 16384)
    b = sup.queue.enqueue("x", "routine", 16384)
    assert sup.run() == 2
    assert order == [a.id, b.id]
    assert sup.queue.get(a.id).state == DONE and sup.queue.get(a.id).result == "done"


def test_groups_same_tier_to_minimize_swaps(tmp_path):
    sup = _supervisor(tmp_path, {"k": lambda j: None}, active=False)
    sup.loader.ensure_pinned(warm=False)
    sup.queue.enqueue("k", "routine", 16384)
    sup.queue.enqueue("k", "synthesis", 32768)
    sup.queue.enqueue("k", "routine", 16384)
    sup.run()
    # The two routine jobs run back-to-back; only one swap (to synthesis) is incurred.
    assert sup.swaps == 1


def test_foreground_gates_heavy_tiers(tmp_path):
    ran = []
    sup = _supervisor(tmp_path, {"k": lambda j: ran.append(j.tier)}, active=True)
    sup.loader.ensure_pinned(warm=False)
    sup.queue.enqueue("k", "routine", 16384)
    syn = sup.queue.enqueue("k", "synthesis", 32768)
    assert sup.run() == 1
    assert ran == ["routine"]                          # synthesis gated while present
    assert sup.queue.get(syn.id).state == QUEUED       # left for a trough


def test_ceiling_breach_defers_job(tmp_path):
    cfg = dataclasses.replace(
        load_config(), resources=dataclasses.replace(load_config().resources, usable_ram_gb=5.0)
    )
    ld = _loader(cfg)
    ld.ensure_pinned(warm=False)                       # 2.7 GB of a 5 GB budget
    sup = Supervisor(queue=JobQueue(tmp_path / "q.db"), loader=ld,
                     handlers={"k": lambda j: None}, presence=_present(False), warm=False)
    j = sup.queue.enqueue("k", "synthesis", 32768)     # 2.7 + 17 > 5 -> refused
    sup.run()
    assert sup.queue.get(j.id).state == DEFERRED
    assert "ceiling" in sup.queue.get(j.id).error


def test_handler_exception_fails_job_not_loop(tmp_path):
    ran = []

    def boom(_j):
        raise ValueError("kaboom")

    sup = _supervisor(tmp_path, {"boom": boom, "ok": lambda j: ran.append(j.id)})
    sup.loader.ensure_pinned(warm=False)
    bad = sup.queue.enqueue("boom", "routine", 16384)
    good = sup.queue.enqueue("ok", "routine", 16384)
    assert sup.run() == 2                               # the loop survived the failure
    assert sup.queue.get(bad.id).state == FAILED
    assert sup.queue.get(good.id).state == DONE and ran == [good.id]


def test_checkpointed_job_yields_and_resumes(tmp_path):
    calls = []
    handlers = {}
    sup = _supervisor(tmp_path, handlers, active=False)

    def stepper(j):
        calls.append(j.checkpoint)
        if j.checkpoint is None:
            sup.queue.checkpoint(j.id, "step-2")        # yield at the boundary
            return None
        return "finished"

    handlers["dream"] = stepper
    sup.loader.ensure_pinned(warm=False)
    j = sup.queue.enqueue("dream", "synthesis", 32768)
    sup.run()
    assert calls == [None, "step-2"]
    assert sup.queue.get(j.id).state == DONE and sup.queue.get(j.id).result == "finished"


def test_mint_token_returns_a_token_scoped_to_the_role(tmp_path):
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    sup = _supervisor(tmp_path, {}, secrets=vault)
    minted = sup.mint_token("dreamer", ttl="5m")
    assert vault.minted == [("dreamer", "5m")]
    assert vault.read_secret("oura-daily-aggregates", minted.token) == "42 steps"
    # The accessor is the audit handle, minted alongside, and resolves back to the role.
    assert vault.role_for_accessor(minted.accessor) == "dreamer"


def test_mint_token_without_a_wired_backend_raises(tmp_path):
    sup = _supervisor(tmp_path, {})
    with pytest.raises(RuntimeError):
        sup.mint_token("dreamer")
