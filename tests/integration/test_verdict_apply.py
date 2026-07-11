"""Verdict receive + verify seam — build plan Item 4b wiring (verdict-authority.md §4).

The transport (Ambassador or otherwise) carries a SignedVerdict to `receive_verdict`, which
verifies it against the owner PUBLIC key and appends it. The ratified L2 taxonomy is enforced;
forged/mis-categorized verdicts never persist. The owner key is loaded from the same committed
`[attestation] owner_pub` file the attestation verifier uses (no parallel key path). Deterministic.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from config.loader import Config
from core.attestation import Ed25519Signer, generate_seed
from core.stores.verdicts import VerdictCategoryError, VerdictSignatureError, VerdictStore
from core.verdict import VERDICT_TAXONOMY, VerdictPayload, sign_verdict
from core.verdict.apply import OwnerKeyMissing, load_owner_pub_b64, receive_verdict


def _owner() -> Ed25519Signer:
    return Ed25519Signer.from_seed(generate_seed(), "owner")


def _signed(owner, *, seq=1, subject="claim-1", verdict="novel_useful"):
    return sign_verdict(VerdictPayload(subject_id=subject, verdict=verdict, seq=seq,
                                       timestamp="2026-07-04T00:00:00"), owner)


def test_receive_verifies_and_persists(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "v.sqlite", allowed_verdicts=VERDICT_TAXONOMY)
    rec = receive_verdict(_signed(owner), store, owner_pub_b64=owner.public_b64())
    assert rec.verdict == "novel_useful" and store.count() == 1
    assert store.verify_all(owner.public_b64())


def test_receive_enforces_the_ratified_taxonomy(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "v.sqlite", allowed_verdicts=VERDICT_TAXONOMY)
    with pytest.raises(VerdictCategoryError):                 # "promote" is not an L2 label
        receive_verdict(_signed(owner, verdict="promote"), store, owner_pub_b64=owner.public_b64())
    assert store.count() == 0


def test_receive_refuses_a_forged_verdict(tmp_path):
    owner, attacker = _owner(), _owner()
    store = VerdictStore(tmp_path / "v.sqlite", allowed_verdicts=VERDICT_TAXONOMY)
    with pytest.raises(VerdictSignatureError):
        receive_verdict(_signed(attacker), store, owner_pub_b64=owner.public_b64())
    assert store.count() == 0


def test_load_owner_pub_reads_the_committed_key(tmp_path):
    owner = _owner()
    key_file = tmp_path / "owner.pub"
    key_file.write_text(owner.public_b64() + "\n", encoding="utf-8")   # trailing ws tolerated
    # load_owner_pub_b64 reads only cfg.attestation.owner_pub -- a minimal SimpleNamespace mirror
    # is the deliberate fixture; the cast says "this is intentionally partial," not a real Config.
    cfg = cast(Config, SimpleNamespace(attestation=SimpleNamespace(owner_pub=key_file)))
    assert load_owner_pub_b64(cfg) == owner.public_b64()


def test_load_owner_pub_fails_closed_when_absent(tmp_path):
    missing_ns = SimpleNamespace(attestation=SimpleNamespace(owner_pub=tmp_path / "nope.pub"))
    cfg = cast(Config, missing_ns)
    with pytest.raises(OwnerKeyMissing):
        load_owner_pub_b64(cfg)


def test_taxonomy_is_the_five_l2_verdicts():
    assert VERDICT_TAXONOMY == frozenset(
        {"novel_useful", "true_known", "plausible", "wrong", "noise"}
    )
