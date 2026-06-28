"""Operator front door to the self-modification gate (BUILD-SPEC §14, Phase 10; Invariant 5).

A model may write PROPOSED knob changes; only a human moves one to APPROVED. This CLI is that
human's hands on the gate:

    list                      pending proposals awaiting a decision
    history                   every proposal and its outcome
    show <id>                 full detail of one proposal
    propose <lever> <target>  hand-author a proposal (also the seam a future agent calls)
    deny <id>                 reject a pending proposal (terminal)
    approve <id>              approve → execute → VALIDATE against the frozen golden anchor →
                              keep, or AUTO-ROLLBACK on regression (§15). Validation runs the real
                              anchor; if the embedder is unavailable the approval is REFUSED —
                              never keep an unvalidated change (fail-closed).

`[selfmod] enabled` gates every state-changing command; reads work regardless so the owner can
always inspect history. The live golden validator is built only for `approve`, lazily, so reads
don't pull in the embedder.
"""

from __future__ import annotations

import sys

from ops.ledger import Proposal, ProposalLedger, open_ledger
from ops.levers import LEVERS, ProposedChange
from ops.selfmod import SelfModLoop, Validator, build_loop

_USAGE = (
    "usage: python -m ops.selfmod_cli "
    "<list|history|show ID|propose LEVER TARGET [RATIONALE]|deny ID|approve ID>"
)


def _fmt(p: Proposal) -> str:
    line = f"#{p.id} [{p.status}] {p.lever}: {p.current_value} -> {p.target_value}"
    if p.rationale:
        line += f"  ({p.rationale})"
    if p.status == "rolled_back" and p.rollback_reason:
        line += f"  ROLLED BACK: {p.rollback_reason}"
    return line


def cmd_list(ledger: ProposalLedger) -> str:
    pending = ledger.pending()
    if not pending:
        return "no pending proposals."
    return "\n".join(_fmt(p) for p in pending)


def cmd_history(ledger: ProposalLedger) -> str:
    rows = ledger.all()
    return "\n".join(_fmt(p) for p in rows) if rows else "no proposals yet."


def cmd_show(ledger: ProposalLedger, pid: int) -> str:
    p = ledger.get(pid)
    if p is None:
        return f"no proposal #{pid}"
    lines = [
        _fmt(p),
        f"  proposer={p.proposer or '-'}  approver={p.approver or '-'}",
        f"  proposed_at={p.proposed_at}  executed_at={p.executed_at or '-'}"
        f"  resolved_at={p.resolved_at or '-'}",
    ]
    if p.metrics:
        lines.append(f"  metrics={p.metrics}")
    return "\n".join(lines)


def cmd_propose(loop: SelfModLoop, lever: str, target: float, rationale: str) -> str:
    p = loop.propose(
        ProposedChange(lever=lever, target=target, rationale=rationale), proposer="owner-cli"
    )
    return f"proposed #{p.id}: {_fmt(p)}"


def cmd_deny(loop: SelfModLoop, pid: int) -> str:
    p = loop.deny(pid)
    return f"denied #{p.id}"


def cmd_approve(loop: SelfModLoop, pid: int) -> str:
    """Approve, then mechanically execute + validate. The outcome (kept vs auto-rolled-back) is
    the gate's, not ours — we just report it."""
    loop.approve(pid, approver="owner")
    final = loop.execute_and_validate(pid)
    if final.status == "validated":
        return (
            f"approved + kept #{pid}: {final.lever} = {final.target_value}\n"
            "  (capability anchor held; behavioral conformance is the deferred judge seam — §15)"
        )
    return f"approved but AUTO-ROLLED-BACK #{pid}: {final.rollback_reason}"


def build_live_validator() -> Validator:
    """Validate against the frozen golden anchor with the real embedder: ingest the self-contained
    fixture corpus into a throwaway store and score the blessed queries (mirrors
    tests/e2e/test_golden_live.py). Raises if the embedder isn't available — the caller must NOT
    keep a change it could not validate. Imports core lazily so reads stay light."""
    import tempfile
    from pathlib import Path

    from config.loader import get_config
    from core.ingest.embed import build_embedder
    from core.ingest.index import index_records, semantic_search
    from core.ingest.pipeline import ingest_vault
    from core.stores.rawstore import RawStore
    from core.stores.vectorstore import VectorStore
    from eval.golden import CORPUS_DIR
    from ops.selfmod import build_golden_validator

    cfg = get_config()
    workdir = Path(tempfile.mkdtemp(prefix="selfmod-validate-"))
    raw = RawStore(workdir / "raw")
    store = VectorStore(workdir / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    def retrieve(query, k):
        return semantic_search(query, embedder, store, k=k)

    return build_golden_validator(retrieve)


def main(argv: list[str]) -> int:
    if not argv:
        print(_USAGE, file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    ledger = open_ledger()

    # Read-only commands: never need the loop, the validator, or the enabled flag.
    if cmd == "list":
        print(cmd_list(ledger))
        return 0
    if cmd == "history":
        print(cmd_history(ledger))
        return 0
    if cmd == "show":
        if not rest:
            print(_USAGE, file=sys.stderr)
            return 2
        print(cmd_show(ledger, int(rest[0])))
        return 0

    # State-changing commands go through the loop (which enforces [selfmod] enabled, fail-closed).
    # Only `approve` needs the live validator; the others get a never-called placeholder.
    try:
        if cmd == "approve":
            if not rest:
                print(_USAGE, file=sys.stderr)
                return 2
            loop = build_loop(build_live_validator(), ledger=ledger)
            print(cmd_approve(loop, int(rest[0])))
            return 0

        placeholder: Validator = lambda lever, value: (_ for _ in ()).throw(  # noqa: E731
            AssertionError("validator must not run for this command")
        )
        loop = build_loop(placeholder, ledger=ledger)
        if cmd == "propose":
            if len(rest) < 2:
                print(_USAGE, file=sys.stderr)
                return 2
            lever, target = rest[0], float(rest[1])
            if lever not in LEVERS:
                print(f"unknown lever {lever!r}; registered: {sorted(LEVERS)}", file=sys.stderr)
                return 2
            rationale = " ".join(rest[2:])
            print(cmd_propose(loop, lever, target, rationale))
            return 0
        if cmd == "deny":
            if not rest:
                print(_USAGE, file=sys.stderr)
                return 2
            print(cmd_deny(loop, int(rest[0])))
            return 0
    except Exception as exc:  # surface gate refusals (disabled, bounds, illegal transition) plainly
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(_USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
