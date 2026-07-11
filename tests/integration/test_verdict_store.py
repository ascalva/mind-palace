"""Signed append-only verdict store — build plan Item 4b-store (verdict-authority.md §3–§4).

The store's job is to make the three transport failure modes safe: a FORGED verdict is refused
(only the owner public key is held, so nothing else can inject one); a REPLAY/REORDER is refused
(strict-increasing seq); a genuine DROP is a *detectable gap*, never a silent loss. Append-only is
structural. Deterministic: real SQLite, real Ed25519, temp path, no model, no network.
"""

from __future__ import annotations

import sqlite3

import pytest

from core.attestation import Ed25519Signer, generate_seed
from core.stores.verdicts import (
    VerdictCategoryError,
    VerdictSequenceError,
    VerdictSignatureError,
    VerdictStore,
)
from core.verdict import VerdictPayload, sign_verdict


def _owner() -> Ed25519Signer:
    return Ed25519Signer.from_seed(generate_seed(), "owner")


def _signed(owner, *, seq, subject="insight-1", verdict="promote"):
    return sign_verdict(VerdictPayload(subject_id=subject, verdict=verdict, seq=seq,
                                       timestamp="2026-07-04T00:00:00"), owner)


def test_append_persists_and_reads_back(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "verdicts.sqlite")
    rec = store.append(_signed(owner, seq=1), public_b64=owner.public_b64())
    assert rec.seq == 1 and rec.signer == "owner"
    assert store.latest_seq() == 1 and store.count() == 1
    got = store.get(1)
    assert got is not None and got.verdict == "promote"   # just appended this exact seq
    assert store.verify_all(owner.public_b64())


def test_forged_signature_is_refused_and_stores_nothing(tmp_path):
    owner, attacker = _owner(), _owner()
    store = VerdictStore(tmp_path / "v.sqlite")
    with pytest.raises(VerdictSignatureError):
        store.append(_signed(attacker, seq=1), public_b64=owner.public_b64())
    assert store.count() == 0                       # fail closed — nothing persisted


def test_reused_or_reordered_seq_is_refused(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "v.sqlite")
    store.append(_signed(owner, seq=5), public_b64=owner.public_b64())
    with pytest.raises(VerdictSequenceError):       # reuse of a stored seq
        store.append(_signed(owner, seq=5, subject="other"), public_b64=owner.public_b64())
    with pytest.raises(VerdictSequenceError):       # reorder to a lower seq
        store.append(_signed(owner, seq=3), public_b64=owner.public_b64())
    assert store.count() == 1


def test_a_dropped_verdict_is_a_detectable_gap(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "v.sqlite")
    for s in (1, 2):
        store.append(_signed(owner, seq=s), public_b64=owner.public_b64())
    # seq 3 dropped by the transport; 4 arrives and is accepted (monotone) — the gap stays visible.
    store.append(_signed(owner, seq=4), public_b64=owner.public_b64())
    assert store.gaps() == [3]
    assert [r.seq for r in store.all()] == [1, 2, 4]


def test_store_is_append_only_no_mutation_api(tmp_path):
    store = VerdictStore(tmp_path / "v.sqlite")
    assert not any(hasattr(store, m) for m in ("delete", "update", "remove", "reset"))


def test_ratified_taxonomy_rejects_out_of_set_categories(tmp_path):
    owner = _owner()
    store = VerdictStore(tmp_path / "v.sqlite",
                         allowed_verdicts=frozenset({"novel_useful", "wrong"}))
    store.append(_signed(owner, seq=1, verdict="novel_useful"), public_b64=owner.public_b64())
    with pytest.raises(VerdictCategoryError):
        store.append(_signed(owner, seq=2, verdict="promote"), public_b64=owner.public_b64())
    assert store.count() == 1


def test_verify_all_detects_a_mutated_row(tmp_path):
    owner = _owner()
    db = tmp_path / "v.sqlite"
    store = VerdictStore(db)
    store.append(_signed(owner, seq=1, verdict="promote"), public_b64=owner.public_b64())
    assert store.verify_all(owner.public_b64())
    store.close()

    # Mutate the stored category out-of-band (a tampered store): the signature no longer matches.
    conn = sqlite3.connect(db)
    conn.execute("UPDATE verdicts SET verdict = 'reject' WHERE seq = 1")
    conn.commit()
    conn.close()
    assert not VerdictStore(db).verify_all(owner.public_b64())
