#!/usr/bin/env python
"""Verify attestation signatures + chain integrity — the owner's standalone audit tool.

    uv run scripts/verify_attestation.py <attestation_id>   # verify one + its chain
    uv run scripts/verify_attestation.py --all              # verify every record
    uv run scripts/verify_attestation.py --list             # list records

Checks each attestation's Ed25519 signature against the committed public keys
(ops/attestation/*.pub), enforces the gate-action owner-key policy, and reports chain
completeness back to authored leaves. Read-only; no network, no model (BUILD-SPEC §3).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1)
    from config.loader import get_config
    from core.attestation import build_verifier, open_attestation_store

    cfg = get_config()
    store = open_attestation_store(cfg)
    verify = build_verifier(cfg)

    args = list(argv)
    if "--list" in args:
        for a in store.all():
            tag = f"signed:{a.signer}" if a.signer else "UNSIGNED"
            print(f"{a.id}  {a.agent_role}/{a.action}  {tag}")
        return 0

    if "--all" in args:
        records = store.all()
        if not records:
            print("no attestations")
            return 0
        bad = 0
        for a in records:
            if not a.signer:
                print(f"--   {a.id}  {a.agent_role}/{a.action}  UNSIGNED")
                continue
            ok = verify(a)
            bad += not ok
            print(f"{'OK ' if ok else 'BAD'}  {a.id}  {a.agent_role}/{a.action}  signer={a.signer}")
        suffix = f", {bad} FAILED" if bad else ""
        print(f"\n{len(records) - bad}/{len(records)} verified{suffix}")
        return 1 if bad else 0

    ids = [a for a in args if not a.startswith("-")]
    if not ids:
        print(__doc__)
        return 2

    rc = 0
    for att_id in ids:
        att = store.get(att_id)
        if att is None:
            print(f"BAD  {att_id}  (not found)")
            rc = 1
            continue
        chain = store.chain_for(att_id)
        sig_ok = verify(att) if att.signer else False
        chain_ok = chain.is_complete() and chain.verify_signatures(verify)
        ok = sig_ok and chain_ok
        rc = rc or (0 if ok else 1)
        print(f"{'OK ' if ok else 'BAD'}  {att_id}  ({att.agent_role}/{att.action})")
        sig_state = "valid" if sig_ok else ("unsigned" if not att.signer else "INVALID")
        print(f"     signature: {sig_state} (signer={att.signer or '-'})")
        print(f"     chain: {'complete' if chain.is_complete() else 'BROKEN'}, "
              f"{len(chain.attestations)} link(s), roles={sorted(chain.roles())}")
        print(f"     leaf inputs (authored): {sorted(chain.leaf_input_hashes())}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
