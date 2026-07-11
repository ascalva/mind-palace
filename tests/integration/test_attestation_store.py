"""Append-only attestation store + chain assembly (attestation-layer.md §4–5).

Proves: content-addressed ids; idempotent append; producer lookup; chain closure with broken-
link detection; and the structural append-only property (no mutation API exists).
"""

from __future__ import annotations

from core.attestation import Attestation, AttestationStore


def _store(tmp_path):
    return AttestationStore(tmp_path / "att.sqlite")


def _att(
    *,
    agent_role: str = "dreamer",
    action: str = "dream_pass",
    input_hashes: list[str] | None = None,
    output_hashes: list[str] | None = None,
    derived_from_ids: list[str] | None = None,
    vault_token_accessor: str = "",
) -> Attestation:
    return Attestation.create(
        timestamp="2026-06-27T00:00:00", agent_role=agent_role, action=action,
        constitution_fingerprint="F",
        input_hashes=input_hashes if input_hashes is not None else ["a"],
        output_hashes=output_hashes if output_hashes is not None else ["o"],
        derived_from_ids=derived_from_ids if derived_from_ids is not None else [],
        vault_token_accessor=vault_token_accessor,
    )


def test_append_and_get_roundtrip(tmp_path):
    s = _store(tmp_path)
    a = _att(vault_token_accessor="acc-1")
    s.append(a)
    assert s.get(a.id) == a            # full-field round-trip (frozen dataclass equality)
    assert s.get("missing") is None


def test_append_is_idempotent_for_same_id(tmp_path):
    s = _store(tmp_path)
    a = _att()
    s.append(a)
    s.append(a)                        # re-emitting the identical record is a no-op
    assert s.count() == 1


def test_id_is_content_addressed_and_order_insensitive(tmp_path):
    assert _att(input_hashes=["x"]).id != _att(input_hashes=["y"]).id
    assert _att(input_hashes=["x"]).id == _att(input_hashes=["x"]).id          # stable
    assert _att(input_hashes=["x", "z"]).id == _att(input_hashes=["z", "x"]).id  # order-free
    # The id covers the chain links too: a different parent set is a different attestation.
    assert _att(derived_from_ids=["p1"]).id != _att(derived_from_ids=["p2"]).id


def test_producers_of_finds_the_output_owner(tmp_path):
    s = _store(tmp_path)
    ingest = _att(agent_role="vault_watcher", action="ingest_note",
                  input_hashes=["d1"], output_hashes=["d1"])
    s.append(ingest)
    assert s.producers_of({"d1"}) == {ingest.id}
    assert s.producers_of({"nope"}) == set()
    assert s.producers_of(set()) == set()


def test_chain_for_assembles_the_closure(tmp_path):
    s = _store(tmp_path)
    ingest = _att(agent_role="vault_watcher", action="ingest_note",
                  input_hashes=["d1"], output_hashes=["d1"], derived_from_ids=[])
    s.append(ingest)
    dream = _att(agent_role="dreamer", input_hashes=["d1"], output_hashes=["dreamX"],
                 derived_from_ids=[ingest.id])
    s.append(dream)

    chain = s.chain_for(dream.id)
    assert chain.is_complete()
    assert {a.id for a in chain.attestations} == {ingest.id, dream.id}
    assert chain.roles() == {"dreamer", "vault_watcher"}
    assert chain.leaves() == (ingest,)                 # the only parentless link
    assert chain.leaf_input_hashes() == {"d1"}


def test_chain_detects_a_broken_link(tmp_path):
    s = _store(tmp_path)
    orphan = _att(agent_role="dreamer", derived_from_ids=["does-not-exist"])
    s.append(orphan)
    assert not s.chain_for(orphan.id).is_complete()    # the referenced parent is absent
    assert not s.chain_for("no-such-root").is_complete()  # missing root


def test_by_role_filters(tmp_path):
    s = _store(tmp_path)
    s.append(_att(agent_role="dreamer", input_hashes=["a"]))
    s.append(_att(agent_role="curator", action="curate_finding", input_hashes=["b"]))
    assert {a.agent_role for a in s.by_role("dreamer")} == {"dreamer"}
    assert len(s.by_role("curator")) == 1


def test_store_has_no_mutation_api():
    # Append-only is structural (attestation-layer.md §4): there is nothing to call to rewrite
    # or erase a record — only `append`.
    assert not hasattr(AttestationStore, "delete")
    assert not hasattr(AttestationStore, "update")
