"""Exhaustive FSM check of the two-slot loader (Invariant 8; formal-properties §FSM).

The loader is a tiny state machine: the state is the *resident set*, transitions are
`ensure(model)`. Its state space is small enough to ENUMERATE — so instead of spot-checking a
few sequences (test_models.py), this walks every reachable state via BFS and asserts the
ceiling invariant `|R| ≤ 2 ∧ Σ resident_gb ≤ budget` (and the two-slot structural rules) holds
in ALL of them, and that a load is refused EXACTLY when it would breach. Enumeration is the
proof that no sequence of loads can sneak the loader into an over-ceiling state.

Run with warm=False so no Ollama call is made (the ceiling is checked before any load).
"""

from __future__ import annotations

import dataclasses

from config.loader import Config, load_config
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import MemoryCeilingError, Registry


def _loader(cfg: Config) -> TwoSlotLoader:
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


def _drive(cfg: Config, sequence: list[str]) -> TwoSlotLoader:
    """A fresh loader driven through `sequence` (refusals are absorbed; the FSM is
    memoryless in its resident set, so replaying a reaching sequence rebuilds the state)."""
    ld = _loader(cfg)
    for name in sequence:
        try:
            ld.ensure(name, warm=False)
        except MemoryCeilingError:
            pass
    return ld


def _gb(cfg: Config, names: frozenset[str]) -> float:
    by_name = {m.name: m for m in cfg.models}
    return sum(by_name[n].resident_gb for n in names)


def _reachable(cfg: Config) -> dict[frozenset[str], list[str]]:
    """BFS over ensure() transitions; returns every reachable resident set + a reaching seq."""
    names = [m.name for m in cfg.models]
    seen: dict[frozenset[str], list[str]] = {frozenset(): []}
    frontier: list[frozenset[str]] = [frozenset()]
    while frontier:
        state = frontier.pop()
        seq = seen[state]
        for name in names:
            ld = _drive(cfg, seq)
            try:
                ld.ensure(name, warm=False)
            except MemoryCeilingError:
                continue                      # refusal — no new state
            nxt = frozenset(ld.resident_models())
            if nxt not in seen:
                seen[nxt] = seq + [name]
                frontier.append(nxt)
    return seen


def _assert_state_invariants(cfg: Config, state: frozenset[str]) -> None:
    pinned = cfg.pinned_model.name
    budget = cfg.resources.usable_ram_gb
    max_n = cfg.resources.max_resident_models
    assert len(state) <= max_n, f"{set(state)} exceeds {max_n} resident models (I8)"
    assert _gb(cfg, state) <= budget, f"{set(state)} = {_gb(cfg, state)}GB > {budget}GB (I8)"
    # Two-slot structural rules: at most one non-pinned worker; stretch never coexists w/ pinned.
    assert len(state - {pinned}) <= 1, f"{set(state)} holds >1 worker (slot 2 is single)"
    for m in cfg.models:
        if m.name in state and m.evicts_pinned:
            assert pinned not in state, "a pinned-evicting model coexisted with the pinned model"


def _check_all_transitions(cfg: Config, states: dict[frozenset[str], list[str]]) -> None:
    """From every reachable state, ensure(candidate) is refused IFF it would breach — and a
    refusal leaves the state untouched (refuse, never half-apply)."""
    max_n = cfg.resources.max_resident_models
    budget = cfg.resources.usable_ram_gb
    for _state, seq in states.items():
        for m in cfg.models:
            ld = _drive(cfg, seq)
            before = set(ld.resident_models())
            prospective = ld._prospective(m)           # the loader's own two-slot accounting
            would_breach = len(prospective) > max_n or _gb(cfg, frozenset(prospective)) > budget
            try:
                ld.ensure(m.name, warm=False)
                refused = False
            except MemoryCeilingError:
                refused = True
            assert refused == would_breach, (
                f"from {before} loading {m.name}: refused={refused} but breach={would_breach}"
            )
            if refused:
                assert set(ld.resident_models()) == before, "a refused load mutated state"


def test_fsm_default_budget_every_reachable_state_is_within_ceiling():
    cfg = load_config()
    states = _reachable(cfg)
    for state in states:
        _assert_state_invariants(cfg, state)
    _check_all_transitions(cfg, states)
    # Sanity: the space really is small (fully enumerated), and the rich states are present.
    assert frozenset({cfg.pinned_model.name, cfg.model_for_tier("synthesis").name}) in states
    assert frozenset({cfg.model_for_tier("stretch").name}) in states     # stretch runs solo


def test_fsm_tight_budget_exercises_refusal_transitions():
    # Shrink the budget so most 2-model loads breach — proving the refusal path is exhaustive
    # and that NO reachable state ever exceeds the (now tiny) ceiling.
    cfg = load_config()
    cfg = dataclasses.replace(cfg, resources=dataclasses.replace(cfg.resources, usable_ram_gb=5.0))
    states = _reachable(cfg)
    for state in states:
        _assert_state_invariants(cfg, state)
    _check_all_transitions(cfg, states)
    # Under a 5GB budget only the pinned (2.7) fits with anything; no worker can join it.
    assert all(_gb(cfg, s) <= 5.0 for s in states)
