#!/usr/bin/env python
"""Generate an Ed25519 attestation keypair — OWNER-OPERATED (production key placement).

    ./.venv/bin/python scripts/gen_attestation_keys.py supervisor
    ./.venv/bin/python scripts/gen_attestation_keys.py owner

Prints a fresh base64 PRIVATE SEED to stdout (place it in Keychain — NEVER commit it) and writes
the matching PUBLIC key to ops/attestation/<role>.pub (commit that — it is non-secret). Then set
`[attestation] enabled = true`.

    security add-generic-password -a "$USER" -s attestation-signing-key -w '<seed>'   # supervisor
    security add-generic-password -a "$USER" -s attestation-owner-key   -w '<seed>'   # owner

This script only GENERATES the key — it does not touch Keychain or Vault (that is the owner's
deliberate, logged step). It writes only the public half to disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

ROLES = {"supervisor": "supervisor.pub", "owner": "owner.pub"}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ROLES:
        print(__doc__)
        return 2
    role = argv[0]
    from core.attestation.crypto import generate_seed, private_from_seed, public_b64

    seed = generate_seed()
    pub = public_b64(private_from_seed(seed))
    pub_path = Path(__file__).resolve().parent.parent / "ops" / "attestation" / ROLES[role]
    pub_path.write_text(pub + "\n")

    print(f"# {role} keypair generated")
    print(f"# PUBLIC key written to {pub_path} (commit this)")
    print(f"# PRIVATE seed — place in Keychain as the {role} secret; DO NOT COMMIT:")
    print(seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
