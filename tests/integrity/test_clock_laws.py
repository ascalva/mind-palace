"""Integrity teeth for the GC-2 clock maps (dn-global-event-clock §2.3 laws C1–C4, §2.8-3) —
non-skippable.

Item 2 (plan §7):
  * commit-as-range — every commit fiber is order-convex (Law C2: "a commit is a RANGE of N"),
    verified over real version structure with a version-respecting commit map; the gap-skipping
    falsifier fails.
  * N_s partition — `n_s(stratum)` restrictions PARTITION Ev by the stratum tag: every event lands
    in exactly one N_s and their union recovers Ev (no event missing from N — the Item 2 falsifier).
  * proper_time — finding-0090: chain_complete=True ONLY on a total chain (a same-doc version
    chain); a cross-doc / cross-stratum pair returns chain_complete=False, never an exact
    cross-chain count.

── VERIFICATION CAVEAT (read before trusting a green run in an isolated worktree) ──
In a delegated worktree `data/` is ABSENT, so `SpineSources.resolve()` yields an EMPTY spine and
every REAL-STORE leg passes TRIVIALLY (this is exactly how bp-051 shipped a latent 1467-event
cycle). The teeth here are the SEEDED in-memory cases (which run everywhere) plus the unit
falsifiers (`tests/unit/test_clock_maps.py`, the primary GC-2 falsifiers). The orchestrator runs
THIS file on main against the live corpus.

The commit clock's tick is sourced EXTERNALLY — no store the spine enumerates carries a commit SHA
(verified on disk: versions/catalog have none), and `core/` never shells to git (§2.10: the spine
is arithmetic over stores, opens no socket). So the commit map is INJECTED. This test verifies the
range LOGIC (C2 convexity) over real event shape with a version-respecting map; a TRUE
git-history-sourced commit map needs an ops-side git helper (finding-0093), flagged for the live
run. The `version_seq`-grouped map used here is a commit-ANALOGUE, not git commits.
"""

from __future__ import annotations

from collections.abc import Hashable
from pathlib import Path

from core.scope import Clock
from core.stores.derived import DerivedStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import Spine, SpineSources

_MEM = Path(":memory:")


# ── helpers ──────────────────────────────────────────────────────────────────────────────────────


def _version_seq_commit_map(spine: Spine) -> dict[str, Hashable]:
    """A commit-ANALOGUE tick for every version event: its `version_seq` (position). Groups the k-th
    version of every doc into "commit k" — a monotone, per-doc-order-respecting map whose fibers are
    the range property's checkable shape (NOT git commits; the git-sourced map is finding-0093)."""
    return {e.event_id: e.position for e in spine.events()
            if e.store == "versions" and e.position is not None}


def _all_fibers_convex(spine: Spine, clock: Clock, ticks: set[Hashable]) -> bool:
    return all(spine.is_fiber_convex(clock, t) for t in ticks)


def _assert_ns_partitions(spine: Spine) -> None:
    """Every event lands in exactly one N_s; the union of the N_s recovers Ev (the Item 2 falsifier:
    any N_s event missing from N, or double-counted, fails here)."""
    all_ids = {e.event_id for e in spine.events()}
    strata = {e.stratum for e in spine.events()}
    union: set[str] = set()
    for s in strata:
        sub = {e.event_id for e in spine.n_s(s).events()}
        assert all(spine._events[e].stratum == s for e in sub)     # restriction keeps only s
        assert union.isdisjoint(sub), f"stratum {s!r} overlaps another N_s"
        union |= sub
    assert union == all_ids, "the N_s restrictions do not cover Ev (an event is missing from N)"


# ── commit-as-range (Law C2) ───────────────────────────────────────────────────────────────────


def test_commit_fibers_are_ranges_seeded() -> None:
    """A version-respecting commit map over a multi-doc corpus: every fiber is order-convex ("a
    commit is a range of N"). Two docs, staggered versions — the realistic shape of a commit
    bundling one new version of each changed doc."""
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docA", "a3")
    vs.record("docB", "b1")
    vs.record("docB", "b2")
    a1, a2, a3 = "versions:docA:1", "versions:docA:2", "versions:docA:3"
    b1, b2 = "versions:docB:1", "versions:docB:2"
    commit_map: dict[str, Hashable] = {a1: 1, a2: 2, b1: 2, a3: 3, b2: 3}   # commit k = kth version
    spine = Spine.derive(SpineSources(versions=vs), coarsening_ticks={Clock.COMMIT: commit_map})
    assert _all_fibers_convex(spine, Clock.COMMIT, {1, 2, 3})
    assert spine.fiber(Clock.COMMIT, 2) == sorted([a2, b1])


def test_gap_skipping_commit_fiber_is_caught_the_falsifier() -> None:
    """The Item 1 falsifier at integrity grain: a commit fiber that SKIPS an event in a chain (a1,a3
    in one commit but a2 in another, with a1 ≺ a2 ≺ a3) is NOT a range — C2 must catch it."""
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docA", "a3")
    spine = Spine.derive(
        SpineSources(versions=vs),
        coarsening_ticks={Clock.COMMIT: {"versions:docA:1": 1, "versions:docA:2": 2,
                                         "versions:docA:3": 1}},
    )
    assert not spine.is_fiber_convex(Clock.COMMIT, 1)     # {a1, a3} skipping a2 — a non-range


def test_commit_fibers_are_ranges_on_the_real_versions_store() -> None:
    """ON THE REAL STORES: a version_seq-grouped commit-analogue over the live versions store has
    order-convex fibers. In a worktree (no data/) this resolves to an empty spine and is trivial;
    on main it exercises the real corpus. See the module VERIFICATION CAVEAT."""
    real = Spine.derive(SpineSources.resolve())
    commit_map = _version_seq_commit_map(real)
    spine = Spine.derive(SpineSources.resolve(), coarsening_ticks={Clock.COMMIT: commit_map})
    ticks = set(commit_map.values())
    assert _all_fibers_convex(spine, Clock.COMMIT, ticks)


# ── N_s partition ──────────────────────────────────────────────────────────────────────────────


def test_ns_restrictions_partition_events_seeded() -> None:
    vs = VersionStore(_MEM)                               # mirror
    vs.record("doc", "DIG")
    led = RunLedger(_MEM)                                 # ops
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    ds = DerivedStore(_MEM)                               # interpreted
    ds.add(kind="dream", summary="s", subjects=("t",), derived_from=("DIG",))
    spine = Spine.derive(SpineSources(versions=vs, ledger=led, derived=ds))
    _assert_ns_partitions(spine)
    assert {e.stratum for e in spine.events()} >= {"mirror", "ops", "interpreted"}


def test_ns_restrictions_partition_events_on_the_real_stores() -> None:
    """ON THE REAL STORES: the N_s partition holds over whatever the live corpus records (trivial in
    a worktree; real on main)."""
    _assert_ns_partitions(Spine.derive(SpineSources.resolve()))


# ── proper_time discipline (finding-0090) ───────────────────────────────────────────────────────


def test_proper_time_exact_on_a_chain_never_across_chains_seeded() -> None:
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docA", "a3")
    vs.record("docB", "b1")
    spine = Spine.derive(SpineSources(versions=vs))
    # a total chain (one doc): proper time == event count, chain_complete=True
    assert spine.proper_time("versions:docA:1", "versions:docA:3") == (3, True)
    # across docs (same stratum, different chains): NEVER an exact proper time (finding-0090)
    _len, complete = spine.proper_time("versions:docA:2", "versions:docB:1")
    assert complete is False


def test_proper_time_discipline_holds_on_the_real_version_chains() -> None:
    """ON THE REAL STORES: for any doc with ≥2 versions, proper_time along its own chain is
    chain_complete=True; a pair drawn from two different docs is never chain_complete. Guarded on
    real data being present (trivial no-op in a worktree)."""
    spine = Spine.derive(SpineSources.resolve())
    by_doc: dict[str, list[int]] = {}
    for e in spine.events():
        if e.store == "versions" and e.position is not None:
            by_doc.setdefault(e.event_id.rsplit(":", 1)[0], []).append(e.position)
    multi = [chain for chain, seqs in by_doc.items() if len(seqs) >= 2]
    for chain in multi:                                  # same-doc chain ⇒ exact
        seqs = sorted(by_doc[chain])
        lo, hi = f"{chain}:{seqs[0]}", f"{chain}:{seqs[-1]}"
        length, complete = spine.proper_time(lo, hi)
        assert complete is True
        assert length == len(seqs)                       # count == chain length on a total chain
    if len(multi) >= 2:                                  # two distinct docs ⇒ never exact
        (c1, c2) = multi[0], multi[1]
        _length, complete = spine.proper_time(f"{c1}:{by_doc[c1][0]}", f"{c2}:{by_doc[c2][0]}")
        assert complete is False
