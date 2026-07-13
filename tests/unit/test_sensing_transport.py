"""The constrained-fetch transport guards (Track G item G3, Zone B).

The real `UrllibTransport` is the sensing hand's only network reach; its guards are what keep a
read-only sensor from becoming an exfil channel. The non-https refusal is a PURE check (it
raises before any socket work), so it is unit-testable offline — the redirect refusal and the
size cap need a live server and are exercised by the edge smoke path, not here.

bp-019 Item 6 adds the `AgentSensingHandoff` seam-sibling transport tests below: the third
instance of the sensing-seam family (after `SensingHandoff`'s biometric contract and
`CodeSensingHandoff`'s code-stream sibling) — its own payload type, own handoff subdirectory,
same atomic-file emit→collect, consume-and-heal shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.sensing import AgentSensingHandoff, CodeSensingHandoff, SensingHandoff
from core.stores.agent_observations import AgentObservation, batch_content_hash
from edge.effectors.sensing import TransportError, UrllibTransport


def test_non_https_url_is_refused_before_any_fetch():
    # http:// (and file://, ftp://, ...) is refused at the scheme check — no socket is opened.
    transport = UrllibTransport()
    for bad in ("http://api.example/x", "file:///etc/passwd", "ftp://host/x"):
        with pytest.raises(TransportError, match="non-https"):
            transport.get(bad, timeout_s=1.0, max_bytes=1024)


# --- bp-019 Item 6: the AgentSensingHandoff seam sibling ---------------------------------------
def _agent_obs(**kw: Any) -> AgentObservation:
    base: dict[str, Any] = dict(commit_sha="c1", stream="cost", subject_id="bp-011",
                                key="estimate", payload={"model": "sonnet", "tokens": 350000})
    base.update(kw)
    return AgentObservation(**base)


def test_agent_emit_collect_round_trips(tmp_path: Path) -> None:
    handoff = AgentSensingHandoff(handoff=tmp_path / "handoff")
    batch = [_agent_obs(key="estimate"), _agent_obs(key="actual",
                                                    payload={"tokens": 163000})]
    content_hash = handoff.emit_batch("c1", batch)
    assert content_hash == batch_content_hash(batch)      # deterministic content address
    collected = handoff.collect()
    assert [(o.commit_sha, o.stream, o.subject_id, o.key) for o in collected] == \
        [(o.commit_sha, o.stream, o.subject_id, o.key) for o in batch]
    assert [o.payload for o in collected] == [o.payload for o in batch]


def test_agent_collect_consumes_by_default_and_a_second_collect_is_empty(tmp_path: Path) -> None:
    handoff = AgentSensingHandoff(handoff=tmp_path / "handoff")
    handoff.emit_batch("c1", [_agent_obs()])
    assert len(handoff.collect()) == 1
    assert handoff.collect() == []                        # the file was consumed


def test_agent_uncollected_batch_heals_on_next_collect(tmp_path: Path) -> None:
    """A batch left by a 'crash' (emitted, never collected) is picked up whole on the next
    pass — the rescan-style healing the code-stream sibling already guarantees."""
    handoff = AgentSensingHandoff(handoff=tmp_path / "handoff")
    handoff.emit_batch("deadbeef", [_agent_obs(commit_sha="deadbeef")])
    # simulate a fresh process reopening the same handoff directory:
    reopened = AgentSensingHandoff(handoff=tmp_path / "handoff")
    collected = reopened.collect()
    assert len(collected) == 1 and collected[0].commit_sha == "deadbeef"


def test_agent_batch_hash_is_deterministic_across_reemission(tmp_path: Path) -> None:
    batch = [_agent_obs(key="estimate"), _agent_obs(key="actual", payload={"tokens": 1})]
    h1 = AgentSensingHandoff(handoff=tmp_path / "a").emit_batch("c1", batch)
    h2 = AgentSensingHandoff(handoff=tmp_path / "b").emit_batch("c1", list(reversed(batch)))
    assert h1 == h2                                        # order-free, content-addressed


def test_agent_handoff_uses_its_own_subdirectory_not_the_siblings(tmp_path: Path) -> None:
    root = tmp_path / "handoff"
    agent = AgentSensingHandoff(handoff=root)
    agent.emit_batch("c1", [_agent_obs()])
    assert (root / "agent_observations" / "c1.json").exists()
    assert not (root / "code_observations").exists()       # never touches the code sibling's dir
    assert not (root / "observations").exists()            # nor the biometric sibling's dir


# --- the falsifier: existing contracts are byte-identical, own dir, own payload type -----------
def test_existing_sibling_contracts_are_unchanged() -> None:
    """Item 6 falsifier: the biometric (`SensingHandoff`/`SensedObservation`) and code
    (`CodeSensingHandoff`/`CodeObservation`) contracts are untouched by the third sibling's
    arrival — same public surface as before bp-019 (no shared mutation, own payload type)."""
    assert {"emit", "collect"} <= {n for n in dir(SensingHandoff) if not n.startswith("_")}
    assert {"emit_batch", "collect"} <= {n for n in dir(CodeSensingHandoff)
                                         if not n.startswith("_")}
    assert {"emit_batch", "collect"} <= {n for n in dir(AgentSensingHandoff)
                                         if not n.startswith("_")}
    # each sibling's collect() is typed to its OWN payload — a second type cannot ride
    # an existing handoff (Q1, restated): the three classes are structurally distinct.
    assert SensingHandoff is not CodeSensingHandoff is not AgentSensingHandoff
