#!/usr/bin/env python
"""The review REPL — model-free owner labeling of dream claims (E6 Item 17, Track L §3).

    uv run scripts/review.py            # review novel claims (pipeline-labeled interleave = A/B)
    uv run scripts/review.py --blind    # hide the pipeline label (unbiased A/B judgment)
    uv run scripts/review.py --all      # include re-emitted (non-novel) claims too

Presents each run-ledger claim (surface text, kind, confidence, novel, pipeline), reads a single
keystroke mapped to the ratified `VERDICT_TAXONOMY`, and for each verdict SIGNS + SUBMITS it through
the BUILT verdict path (`scripts/verdict.py`'s exact pattern: `get_secret` → `sign_verdict(
VerdictPayload(subject_id=claim_id, ...))` → `build_verdict_receiver(cfg)`), with
`subject_id = claim_id` so a re-emitted claim inherits its prior verdict. A `plausible` verdict also
records a theory-probe candidate (`eval/harness/probes.py`).

The REPL is **model-free** (Invariant: the model advises, code acts) — display + keystroke capture +
signing only, no model in the path. The verdict store is append-only (a correction is a new,
higher-seq verdict, never an edit). Fail-closed on a missing owner key (refuse, as
`scripts/verdict.py:43-47`). Verdicts + probes are operational ground truth, ∉ `MIRROR_READABLE`.
Zone A, no network.

A/B is NATIVE: `RunLedger.runs()` maps `run_id → pipeline` ("phase7" | "dream_v2"); interleaving
claims labeled by their run's pipeline IS the A/B — precision splits fall out of a verdict ×
pipeline join (E7). No separate A/B machinery.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.attestation.crypto import Ed25519Signer  # noqa: E402
from core.verdict import SignedVerdict, VerdictPayload, sign_verdict  # noqa: E402

# The keystroke → ratified-taxonomy map (`core/verdict/taxonomy.py`; distinct first letters where
# they collide: noise → 'x' since 'n' is novel_useful, 's' is skip). Any key outside this set +
# {s, q} is rejected with NO store write (the Item-17 acceptance test).
KEY_TO_VERDICT: dict[str, str] = {
    "n": "novel_useful",
    "k": "true_known",
    "p": "plausible",
    "w": "wrong",
    "x": "noise",
}
_PROMPT = ("verdict  [n]ovel_useful [k]nown [p]lausible [w]rong [x]noise   "
           "[s]kip  [q]uit > ")


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


class _Control(Enum):
    """Non-verdict keystroke outcomes — advance without a verdict (`SKIP`) or end the session
    (`QUIT`). Kept distinct from the verdict strings so `run_review` never confuses control with a
    taxonomy category."""

    SKIP = auto()
    QUIT = auto()


@dataclass(frozen=True)
class ReviewItem:
    """One claim queued for review, joined to the pipeline that emitted it (the A/B label)."""

    claim: dict[str, Any]
    pipeline: str


@dataclass
class ReviewDeps:
    """The REPL's injected collaborators — the testability seam that keeps the loop model-free and
    lets tests drive it against in-memory stores + a generated signer WITHOUT touching the real
    signed store.

      * `signer`       — the owner `Ed25519Signer` (real: from the Keychain seed; test: generated).
      * `submit`       — the RECEIVE seam (`build_verdict_receiver(cfg)` in prod): verify + append
                         monotonic-seq + apply. The REPL NEVER writes the store directly.
      * `next_seq`     — the seq the NEXT verdict must use (one past the store's max; prod reads the
                         live store, so appends stay monotonic across the session).
      * `record_probe` — the `plausible`-branch spillover (Item 18); a no-op is legitimate (Item 17
                         alone).
      * `read_key`     — prompt → one keystroke (real: `input`; test: a scripted iterator).
      * `write` / `now`— output sink + clock (injected so tests are deterministic).
    """

    signer: Ed25519Signer
    submit: Callable[[SignedVerdict], object]
    next_seq: Callable[[], int]
    record_probe: Callable[[ReviewItem], None]
    read_key: Callable[[str], str]
    write: Callable[[str], None] = print
    now: Callable[[], str] = _utcnow


@dataclass
class ReviewSummary:
    """Counts per (verdict, pipeline) + skips — the session tally the review closes with. Splitting
    by pipeline IS the A/B legend (precision@review is computed downstream in E7, not here)."""

    counts: Counter[tuple[str, str]] = field(default_factory=Counter)
    skipped: int = 0

    def record(self, verdict: str, pipeline: str) -> None:
        self.counts[(verdict, pipeline)] += 1

    def total_verdicts(self) -> int:
        return sum(self.counts.values())

    def render(self) -> str:
        lines = [f"\n— review session summary — {self.total_verdicts()} verdicts, "
                 f"{self.skipped} skipped —"]
        if not self.counts:
            lines.append("  (no verdicts recorded)")
        for (verdict, pipeline), n in sorted(self.counts.items()):
            lines.append(f"  {verdict:12} × {pipeline:9} : {n}")
        return "\n".join(lines)


def _render_claim(item: ReviewItem, *, blind: bool) -> str:
    c = item.claim
    src = "??" if blind else item.pipeline
    novel = "novel" if c["novel"] else "seen "
    return (f"\n[{src}] {c['kind']}  conf={float(c['confidence']):.2f}  {novel}\n"
            f"  {c['surface_text']}")


def _interleave(items: list[ReviewItem]) -> list[ReviewItem]:
    """Round-robin claims across pipelines (native A/B), each pipeline's group ordered novel-first
    then confidence-descending (Track L §3: "queue ordered novel-first, confidence-descending")."""
    groups: dict[str, list[ReviewItem]] = {}
    for it in items:
        groups.setdefault(it.pipeline, []).append(it)
    for g in groups.values():
        g.sort(key=lambda it: (not bool(it.claim["novel"]), -float(it.claim["confidence"])))
    ordered_groups = [groups[k] for k in sorted(groups)]  # deterministic pipeline order
    out: list[ReviewItem] = []
    idx = 0
    while any(idx < len(g) for g in ordered_groups):
        for g in ordered_groups:
            if idx < len(g):
                out.append(g[idx])
        idx += 1
    return out


def build_queue(ledger: Any, *, novel_only: bool = True) -> list[ReviewItem]:
    """Join `RunLedger.claims()` to `runs()` `run_id → pipeline` and interleave — the review queue.
    `ledger` is duck-typed (`runs()`, `claims(novel_only=...)`) so an in-memory `RunLedger` drives
    it in tests. Defaults to novel claims only (the note's unverdicted-novel queue)."""
    pipelines = {r["run_id"]: r["pipeline"] for r in ledger.runs()}
    items = [ReviewItem(claim=c, pipeline=pipelines.get(c["run_id"], "unknown"))
             for c in ledger.claims(novel_only=novel_only)]
    return _interleave(items)


def _prompt_verdict(deps: ReviewDeps) -> str | _Control:
    """Read keystrokes until a valid outcome: a taxonomy verdict, `SKIP`, or `QUIT`. An unknown key
    re-prompts the SAME claim with NO store write (the Item-17 falsifier guard). Input exhaustion
    (EOF / StopIteration) ends the session (`QUIT`)."""
    while True:
        try:
            key = deps.read_key(_PROMPT).strip().lower()
        except (EOFError, StopIteration):
            return _Control.QUIT
        if key == "q":
            return _Control.QUIT
        if key in ("s", ""):
            return _Control.SKIP
        verdict = KEY_TO_VERDICT.get(key)
        if verdict is None:
            deps.write(f"  ? unknown key {key!r} — no verdict written; "
                       "choose n/k/p/w/x, s=skip, q=quit")
            continue
        return verdict


def run_review(items: list[ReviewItem], deps: ReviewDeps, *, blind: bool = False) -> ReviewSummary:
    """Drive the review loop over `items`. For each valid verdict: sign a `VerdictPayload(
    subject_id=claim_id, ...)` at the next monotonic seq and SUBMIT it through `deps.submit` (the
    built receiver seam) — never writing the store directly. A `plausible` verdict also records a
    probe candidate. Model-free throughout."""
    summary = ReviewSummary()
    for item in items:
        deps.write(_render_claim(item, blind=blind))
        outcome = _prompt_verdict(deps)
        if outcome is _Control.QUIT:
            break
        if outcome is _Control.SKIP:
            summary.skipped += 1
            continue
        verdict = outcome  # a ratified taxonomy category
        payload = VerdictPayload(
            subject_id=str(item.claim["claim_id"]),
            verdict=verdict,
            seq=deps.next_seq(),
            timestamp=deps.now(),
        )
        signed = sign_verdict(payload, deps.signer)
        deps.submit(signed)  # verify + append (monotonic seq) + apply — the BUILT path, reused
        summary.record(verdict, item.pipeline)
        if verdict == "plausible":
            deps.record_probe(item)  # Item 18: the probe-candidate spillover
    deps.write(summary.render())
    return summary


# --- production wiring (the owner's real signed path; NEVER exercised by the builder) ----------

def _real_read_key(prompt: str) -> str:
    return input(prompt)


def _build_production_deps(cfg: Any, seed: str) -> ReviewDeps:
    """Wire the REAL owner path from config: the receiver (`build_verdict_receiver`), the live
    verdict store (for the next monotonic seq), and the probe store. Called only after the owner
    key is confirmed present (fail-closed check lives in `main`)."""
    from core.stores.verdicts import open_verdict_store
    from core.verdict.apply import build_verdict_receiver
    from eval.harness.probes import ProbeCandidate, open_probe_store

    signer = Ed25519Signer.from_seed(seed, "owner")
    receiver = build_verdict_receiver(cfg)     # verify + store + apply, fail-closed on missing pub
    vstore = open_verdict_store(cfg)           # a second read handle for the next seq
    probes = open_probe_store(cfg)

    def _next_seq() -> int:
        latest = vstore.latest_seq()
        return (latest + 1) if latest is not None else 1

    def _record(item: ReviewItem) -> None:
        probes.record(ProbeCandidate.from_claim(item.claim, pipeline=item.pipeline))

    return ReviewDeps(
        signer=signer, submit=receiver, next_seq=_next_seq,
        record_probe=_record, read_key=_real_read_key,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Model-free review REPL for dream claims (E6).")
    parser.add_argument("--blind", action="store_true",
                        help="hide the pipeline label (unbiased A/B judgment)")
    parser.add_argument("--all", action="store_true",
                        help="include re-emitted (non-novel) claims, not just novel ones")
    args = parser.parse_args(argv)

    from config.loader import get_config, get_secret
    from core.stores.runledger import open_run_ledger

    cfg = get_config()
    seed = get_secret(cfg.attestation.owner_key_secret)
    if not seed:  # fail closed — exactly scripts/verdict.py:43-47
        print(f"error: no owner signing key at get_secret({cfg.attestation.owner_key_secret!r}); "
              "place it in Keychain (scripts/gen_attestation_keys.py owner)", file=sys.stderr)
        return 1

    ledger = open_run_ledger(cfg)
    items = build_queue(ledger, novel_only=not args.all)
    if not items:
        print("no claims awaiting review.")
        return 0

    deps = _build_production_deps(cfg, seed)
    run_review(items, deps, blind=args.blind)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
