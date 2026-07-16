"""Integration tests — the review REPL over a real run ledger + verdict store (E6 Item 17).

Drives `run_review` against an in-memory `RunLedger` (seeded phase7 + dream_v2 claims), a real (tmp)
`VerdictStore`, a GENERATED test `Ed25519Signer`, and scripted keystrokes — the builder NEVER
touches the owner's real signed store. Pins the Item-17 acceptance + falsifiers: each verdict lands
signed + seq-monotonic with `subject_id = claim_id` (so re-emission inherits); an out-of-taxonomy
keystroke is rejected with NO store write; the summary splits by pipeline; the REPL is model-free.
"""

from __future__ import annotations

from pathlib import Path

from core.attestation import Ed25519Signer, generate_seed
from core.stores.runledger import RunLedger, claim_id
from core.stores.verdicts import VerdictStore
from core.verdict.taxonomy import VERDICT_TAXONOMY
from scripts.review import (
    KEY_TO_VERDICT,
    ReviewDeps,
    ReviewItem,
    build_queue,
    run_review,
)


def _seed_ledger():
    """A shared-snapshot ledger: phase7 emits A (tension) + B (theme); dream_v2 emits C (community)
    + a RE-EMIT of A (same kind/support/polarity → same claim_id, novel=0)."""
    ledger = RunLedger(":memory:")
    p7 = ledger.start_run(pipeline="phase7", config_fingerprint="f1", corpus_digest="snap",
                          node_count=3, edge_count=2, duration_s=0.1, spectral_stats={})
    d2 = ledger.start_run(pipeline="dream_v2", config_fingerprint="f2", corpus_digest="snap",
                          node_count=3, edge_count=2, duration_s=0.1, spectral_stats={})
    ledger.add_claim(p7, kind="tension", confidence=0.9, support=("a", "b"),
                     surface_text="A: tension between a and b", polarity="-")
    ledger.add_claim(p7, kind="theme", confidence=0.7, support=("c",),
                     surface_text="B: theme c", polarity="+")
    ledger.add_claim(d2, kind="community", confidence=0.8, support=("d", "e"),
                     surface_text="C: cluster d,e", polarity="+")
    ledger.add_claim(d2, kind="tension", confidence=0.4, support=("a", "b"),
                     surface_text="A: tension between a and b", polarity="-")  # re-emit of A
    return ledger


def _sink(tmp_path):
    store = VerdictStore(tmp_path / "verdicts.sqlite", allowed_verdicts=VERDICT_TAXONOMY)
    signer = Ed25519Signer.from_seed(generate_seed(), "owner")
    pub = signer.public_b64()

    def submit(signed):
        return store.append(signed, public_b64=pub)

    def next_seq():
        latest = store.latest_seq()
        return (latest + 1) if latest is not None else 1

    return store, signer, submit, pub, next_seq


def _reader(keys):
    it = iter(keys)

    def read_key(_prompt):
        return next(it)   # exhaustion → StopIteration → the loop quits

    return read_key


def _deps(tmp_path, keys, *, probes=None, out=None):
    store, signer, submit, pub, next_seq = _sink(tmp_path)

    def record_probe(item):
        if probes is not None:
            probes.append(item)

    write = (lambda m: out.append(m)) if out is not None else (lambda _m: None)
    deps = ReviewDeps(signer=signer, submit=submit, next_seq=next_seq,
                      record_probe=record_probe, read_key=_reader(keys),
                      write=write, now=lambda: "2026-07-16T00:00:00")
    return store, pub, deps


# --- acceptance --------------------------------------------------------------------------------

def test_each_verdict_lands_signed_monotonic_and_keyed_to_claim_id(tmp_path):
    ledger = _seed_ledger()
    queue = build_queue(ledger, novel_only=True)      # novel: A(p7), B(p7), C(d2); re-emit excluded
    # interleave = round-robin across pipelines (alphabetical: dream_v2 before phase7),
    # novel-first/conf-desc within each group → [C(d2), A(p7), B(p7)]
    assert [it.claim["surface_text"][0] for it in queue] == ["C", "A", "B"]

    probes: list[ReviewItem] = []
    store, pub, deps = _deps(tmp_path, ["n", "p", "w"], probes=probes)
    summary = run_review(queue, deps)

    records = store.all()
    assert [r.seq for r in records] == [1, 2, 3]                 # strictly monotonic
    assert store.verify_all(pub)                                 # every row is a valid owner sig
    # subject_id is the CONTENT-ADDRESSED claim_id, never the run_id or surface text (the falsifier)
    a_id = claim_id("tension", ("a", "b"), "-")
    c_id = claim_id("community", ("d", "e"), "+")
    b_id = claim_id("theme", ("c",), "+")
    assert records[0].subject_id == c_id and records[0].verdict == "novel_useful"
    assert records[1].subject_id == a_id and records[1].verdict == "plausible"
    assert records[2].subject_id == b_id and records[2].verdict == "wrong"
    for r in records:
        assert r.subject_id not in ("run-abc", "A: tension between a and b")
    # summary splits by pipeline (the native A/B legend)
    assert summary.counts[("novel_useful", "dream_v2")] == 1
    assert summary.counts[("plausible", "phase7")] == 1
    assert summary.counts[("wrong", "phase7")] == 1
    assert len(probes) == 1 and probes[0].claim["claim_id"] == a_id   # plausible → probe spillover
    ledger.close()


def test_reemitted_claim_verdict_reuses_same_subject_id(tmp_path):
    ledger = _seed_ledger()
    queue = build_queue(ledger, novel_only=False)     # includes A (p7 novel) + A' (d2 re-emit)
    a_id = claim_id("tension", ("a", "b"), "-")
    a_items = [it for it in queue if it.claim["claim_id"] == a_id]
    assert len(a_items) == 2                            # the same claim, emitted by both pipelines

    store, _pub, deps = _deps(tmp_path, ["n", "k"])
    run_review(a_items, deps)
    records = store.all()
    assert len(records) == 2
    assert {r.subject_id for r in records} == {a_id}   # both verdicts share ONE subject (inherit)
    assert [r.seq for r in records] == [1, 2]          # append-only: a correction is a higher seq
    ledger.close()


def test_out_of_taxonomy_keystroke_is_rejected_with_no_store_write(tmp_path):
    ledger = _seed_ledger()
    queue = build_queue(ledger, novel_only=True)[:1]   # a single claim
    out: list[str] = []
    # 'z' is not a verdict/skip/quit key → re-prompt SAME claim, no write; then 'n' commits.
    store, _pub, deps = _deps(tmp_path, ["z", "n"], out=out)
    run_review(queue, deps)
    assert store.count() == 1                           # exactly one write — 'z' wrote nothing
    assert store.all()[0].verdict == "novel_useful"
    assert any("unknown key" in m for m in out)         # the rejection was surfaced, not silent
    ledger.close()


def test_skip_advances_and_quit_ends_without_writing(tmp_path):
    ledger = _seed_ledger()
    queue = build_queue(ledger, novel_only=True)        # [A, C, B]
    store, _pub, deps = _deps(tmp_path, ["s", "q"])      # skip A, quit before C
    summary = run_review(queue, deps)
    assert store.count() == 0                            # neither skip nor quit writes a verdict
    assert summary.skipped == 1
    ledger.close()


def test_input_exhaustion_ends_the_session_cleanly(tmp_path):
    ledger = _seed_ledger()
    queue = build_queue(ledger, novel_only=True)
    store, _pub, deps = _deps(tmp_path, ["n"])           # one key, three claims → EOF after first
    summary = run_review(queue, deps)
    assert store.count() == 1                            # the one verdict landed; then clean stop
    assert summary.total_verdicts() == 1
    ledger.close()


def test_keymap_covers_exactly_the_ratified_taxonomy(tmp_path):
    # Falsifier guard: the keystroke map maps onto EXACTLY the ratified verdict taxonomy — no
    # invented category, none missing.
    assert set(KEY_TO_VERDICT.values()) == set(VERDICT_TAXONOMY)


def test_repl_is_model_free(tmp_path):
    # Invariant (the model advises, code acts): the REPL source imports/invokes no model.
    src = Path("scripts/review.py").read_text()
    for forbidden in ("core.reasoning", "core.dreaming", "llm", "load_model", "generate("):
        assert forbidden not in src, f"review.py must be model-free — found {forbidden!r}"
