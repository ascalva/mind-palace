"""The Vault↔attestation join records the token's ACCESSOR, never the token (Step 5).

Part of the non-skippable integrity gate. The join (attestation-layer.md §2, vault-runtime-auth.md
§6) ties each attested action to the Vault authorization it ran under — but the credential must
never enter the audit trail (Invariant 10). What lands in `vault_token_accessor` is Vault's
non-secret accessor: enough to cross-reference the Vault audit log (and, in dev, resolve back to
the role it was minted for), powerless to read any secret. The accessor is inside
`signing_payload()`, so the authorization claim is part of the signed, tamper-evident surface.
"""

from __future__ import annotations

import json
from dataclasses import replace

from fixtures.attestation import attestor_with_store, dev_signer, dev_verifier
from fixtures.secrets import fake_vault

from core.attestation import Attestation


def test_emit_records_the_accessor_and_never_the_token(tmp_path):
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    minted = vault.mint_token("dreamer", "10m")
    store, attestor = attestor_with_store(tmp_path)

    att = attestor.emit(agent_role="dreamer", action="dream_pass",
                        input_hashes=["d1"], output_hashes=["x"],
                        vault_token_accessor=minted.accessor)

    stored = store.get(att.id)
    assert stored.vault_token_accessor == minted.accessor
    # The firewall: the accessor is present, the credential is NOWHERE in the serialized record.
    blob = json.dumps(stored.to_dict())
    assert minted.accessor in blob
    assert minted.token not in blob


def test_accessor_resolves_to_the_attested_role(tmp_path):
    # The verifiable join: given a stored attestation, its accessor resolves (via the dev-mode
    # lookup-accessor analogue) to exactly the role the action claims — proof the action ran under
    # an authorization minted for that role, cross-checkable without ever touching the token.
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    minted = vault.mint_token("dreamer", "10m")
    _, attestor = attestor_with_store(tmp_path)

    att = attestor.emit(agent_role="dreamer", action="dream_pass",
                        input_hashes=["d1"], vault_token_accessor=minted.accessor)

    assert vault.role_for_accessor(att.vault_token_accessor) == att.agent_role
    assert vault.role_for_accessor("accessor-forged-deadbeef") is None


def test_accessor_is_part_of_the_signed_surface(tmp_path):
    # The accessor is in signing_payload(), so a signed attestation's authorization claim is
    # tamper-evident: swapping the accessor invalidates the signature (mirrors the field-tamper
    # test in test_attestation_signatures.py — the authorization is as protected as the hashes).
    _, attestor = attestor_with_store(tmp_path, signer=dev_signer("supervisor"))
    att = attestor.emit(agent_role="dreamer", action="dream_pass",
                        input_hashes=["d1"], vault_token_accessor="accessor-real")
    verify = dev_verifier()

    assert verify(att)
    assert not verify(replace(att, vault_token_accessor="accessor-swapped"))


def test_accessor_is_in_the_content_address():
    # Two actions identical except for the authorization they ran under are DISTINCT attestations
    # (the accessor is in the id surface) — an action authorized as one role can't be conflated
    # with the same action under another authorization.
    base = dict(timestamp="2026-06-27T00:00:00", agent_role="dreamer", action="dream_pass",
                constitution_fingerprint="F", input_hashes=["d1"])
    a = Attestation.create(**base, vault_token_accessor="accessor-a")
    b = Attestation.create(**base, vault_token_accessor="accessor-b")
    assert a.id != b.id
