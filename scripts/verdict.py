#!/usr/bin/env python
"""Owner verdict transport — sign / submit / inspect owner verdicts (verdict-authority.md).

    uv run scripts/verdict.py sign <subject_id> <verdict> [seq]   # -> signed JSON
    uv run scripts/verdict.py submit '<signed-json>'     # verify + store + apply
    uv run scripts/verdict.py list          # stored verdicts + gaps

`sign` uses the owner PRIVATE seed (Keychain: `attestation-owner-key`) to produce a content-bound
Ed25519 signature over the verdict — the artifact a transport carries. `submit` is the RECEIVE seam:
it verifies against the owner PUBLIC key (`ops/attestation/owner.pub`), appends to the append-only
store (monotonic seq), and applies the disposition (a `wrong`/`noise` verdict retracts its subject
from the active projection; weight promotion is parked). The Ambassador is transport only (§4); this
CLI is the owner's direct surface. Zone A, no network.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def _cfg():
    from config.loader import get_config

    return get_config()


def cmd_sign(subject_id: str, verdict: str, seq: int | None) -> int:
    from config.loader import get_secret
    from core.attestation.crypto import Ed25519Signer
    from core.verdict import VerdictPayload, sign_verdict
    from core.verdict.taxonomy import VERDICT_TAXONOMY

    cfg = _cfg()
    if verdict not in VERDICT_TAXONOMY:
        print(f"error: {verdict!r} not in the ratified taxonomy {sorted(VERDICT_TAXONOMY)}",
              file=sys.stderr)
        return 2
    seed = get_secret(cfg.attestation.owner_key_secret)
    if not seed:
        print(f"error: no owner signing key at get_secret({cfg.attestation.owner_key_secret!r}); "
              "place it in Keychain (scripts/gen_attestation_keys.py owner)", file=sys.stderr)
        return 1
    if seq is None:                                    # default: one past the stored maximum
        from core.stores.verdicts import open_verdict_store

        latest = open_verdict_store(cfg).latest_seq()
        seq = (latest + 1) if latest is not None else 1
    ts = datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
    signed = sign_verdict(
        VerdictPayload(subject_id=subject_id, verdict=verdict, seq=seq, timestamp=ts),
        Ed25519Signer.from_seed(seed, "owner"),
    )
    print(json.dumps(signed.to_dict()))
    return 0


def cmd_submit(blob: str) -> int:
    from core.verdict import SignedVerdict
    from core.verdict.apply import build_verdict_receiver, effect_of

    try:
        signed = SignedVerdict.from_dict(json.loads(blob))
    except (ValueError, KeyError) as e:
        print(f"error: malformed signed verdict JSON ({e})", file=sys.stderr)
        return 2
    try:
        rec = build_verdict_receiver(_cfg())(signed)   # verify + store + apply (fail-closed)
    except Exception as e:  # OwnerKeyMissing / signature / seq / taxonomy refusals, shown plainly
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"stored verdict seq={rec.seq} subject={rec.subject_id} verdict={rec.verdict} "
          f"-> effect={effect_of(rec.verdict).value}")
    return 0


def cmd_list() -> int:
    from core.stores.verdicts import open_verdict_store

    store = open_verdict_store(_cfg())
    rows = store.all()
    if not rows:
        print("no verdicts stored.")
        return 0
    for r in rows:
        print(f"#{r.seq} {r.verdict:12} {r.subject_id}  ({r.timestamp})")
    gaps = store.gaps()
    if gaps:
        print(f"WARNING sequence gaps (dropped/censored verdicts): {gaps}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "sign" and len(rest) >= 2:
        return cmd_sign(rest[0], rest[1], int(rest[2]) if len(rest) >= 3 else None)
    if cmd == "submit" and rest:
        return cmd_submit(rest[0])
    if cmd == "list":
        return cmd_list()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
