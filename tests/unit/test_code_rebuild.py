"""ops/code_rebuild.py — the D7 rebuild (bp-153): baseline, step-0 capture, the resumable walk,
compaction, and the owner-visible verb.

Every criterion here names the **degenerate input** on which it would pass without testing its
claim, and asserts that precondition FIRST. The two that matter most, because both have a
false-success shape the design explicitly warns about:

  * **The dedup factor.** `|atoms| <= Sigma chunks` holds vacuously at zero savings (D7/§8 g), so
    the fixture is asserted to contain atoms SHARED across versions and ACROSS FILES before any
    ratio is read — and the measured factor, not the inequality, is what is asserted.
  * **Compaction.** "row count and search results unchanged" is exactly what a compaction that
    silently did nothing produces, so the version count is asserted to have DROPPED in the same
    breath — and the fixture is asserted to hold several dataset versions before that can mean
    anything.

No Ollama: a deterministic counting fake embedder, temp stores, and a real git repo + real φ_code
ledger built per-test. Nothing here touches the live corpus.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from core.ingest.code_corpus import CodeCorpusSync, atom_id, derive_code_chunks
from core.stores.memberships import EmbedderIdentity, MembershipStore, frequency_gauges
from core.stores.vectorstore import LAYER_CODE_AST, LAYER_CODE_TEXT, VectorStore
from ops.code_lineage import ledger_versions, supersession_chains
from ops.code_rebuild import (
    PHASE_CAPTURE,
    PHASE_COMPACT,
    PHASE_LAND,
    PHASE_SEED,
    canonical_body_of_stored,
    capture_slice,
    carry_forward_candidates,
    measure_baseline,
    pending_commits,
    rebuild_slice,
    rebuild_step,
    retire_legacy_rows,
    seed_carry_forward,
)
from ops.code_snapshot import backfill as ledger_backfill
from ops.code_snapshot import open_snapshot_db
from tests.fixtures.embedding import DIM, FakeEmbedder

_EMB = EmbedderIdentity(model="fake-embedder", dim=DIM)

# A helper written IDENTICALLY into two files. This is the cross-file sharing PD-1 rules in, and it
# is what stops the dedup assertions below from being about one file's history alone.
_SHARED_HELPER = (
    "def helper(value):\n"
    '    """Double it."""\n'
    "    return value * 2\n"
)


class _CountingEmbedder(FakeEmbedder):
    """Counts embed calls. Reuse is INVISIBLE in the vectors — identical text gives an identical
    vector whether it was recomputed or carried forward — so the call count is the only place the
    carry-forward's "zero embeds" claim can actually be read."""

    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded.extend(texts)
        return super().embed_documents(texts)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo carrying every shape the rebuild's claims need:

    * `a.py` evolves v0 -> v1 -> **back to v0** (a real REVERT: the [A, B, A] chain shape);
    * `b.py` holds a byte-identical copy of `a.py`'s helper (CROSS-FILE sharing, PD-1) and is
      itself edited on main, so it has two versions;
    * `c.py` is created AND THEN EDITED on a side branch before the merge — so its intermediate
      blob is a ledger version that appears at NO commit on HEAD's first-parent line (D4/F3);
    * every version re-lands the unchanged helper, so atoms are shared ACROSS versions too.
    """
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")

    def commit(msg: str) -> None:
        _git(r, "add", "-A")
        _git(r, "commit", "-qm", msg)

    v0 = _SHARED_HELPER + "\ndef work():\n    return 1\n"
    v1 = _SHARED_HELPER + "\ndef work():\n    return 2\n"
    (r / "a.py").write_text(v0)
    (r / "b.py").write_text(_SHARED_HELPER + "\ndef other():\n    return 9\n")
    commit("c1")

    (r / "a.py").write_text(v1)                       # a.py -> B
    commit("c2 edit work")

    (r / "a.py").write_text(v0)                       # a.py -> back to A: THE REVERT
    commit("c3 revert work")

    _git(r, "checkout", "-q", "-b", "feat")
    # TWO commits on the branch: the intermediate c.py blob never appears on HEAD's first-parent
    # line, which is the side-branch shape D4/F3 is about.
    (r / "c.py").write_text(_SHARED_HELPER + "\ndef side():\n    return 3\n")
    commit("feat add c")
    (r / "c.py").write_text(_SHARED_HELPER + "\ndef side():\n    return 4\n")
    commit("feat edit c")
    _git(r, "checkout", "-q", "main")
    (r / "b.py").write_text(_SHARED_HELPER + "\ndef other():\n    return 10\n")
    commit("c4 edit b")
    _git(r, "merge", "-q", "--no-ff", "feat", "-m", "merge feat")
    return r


@pytest.fixture
def ledger(repo: Path, tmp_path: Path) -> Iterator[sqlite3.Connection]:
    db = open_snapshot_db(tmp_path / "code_snapshots.sqlite")
    ledger_backfill(db, repo)
    yield db
    db.close()


@dataclass
class Bench:
    sync: CodeCorpusSync
    embedder: _CountingEmbedder

    @property
    def vectors(self) -> VectorStore:
        return self.sync.store

    @property
    def memberships(self) -> MembershipStore:
        return self.sync.memberships


def _bench(repo: Path, root: Path, name: str = "b") -> Bench:
    embedder = _CountingEmbedder()
    return Bench(
        sync=CodeCorpusSync(
            repo=repo, store=VectorStore(root / f"{name}.lance", dim=DIM), embedder=embedder,
            memberships=MembershipStore(root / f"{name}.sqlite"), embedder_identity=_EMB),
        embedder=embedder)


@pytest.fixture
def bench(repo: Path, tmp_path: Path) -> Bench:
    return _bench(repo, tmp_path)


# ── Item 1 — the read-only baseline ──────────────────────────────────────────────────────


def test_the_fixture_shares_atoms_across_versions_and_across_files(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """THE PRECONDITION for every dedup claim below, asserted once here rather than assumed.

    On a corpus where no atom is ever shared, `Sigma chunks == |atoms|`, the ratio is 1.0, and
    every "the rebuild deduplicates" assertion passes while testing nothing. That is the
    false-success shape D7 names, so the sharing is established as a FACT of this fixture first:
    the same helper body appears in three different files and in several versions of one of them."""
    versions = ledger_versions(ledger)
    assert len(versions) >= 6, "fixture must hold a real multi-version history"

    seen: dict[str, set[tuple[str, str]]] = {}
    for path, blob in versions:
        source = _git(bench.sync.repo, "cat-file", "-p", blob)
        for ch in derive_code_chunks(path, source):
            seen.setdefault(atom_id(ch), set()).add((path, blob))

    # an atom shared ACROSS FILES (PD-1's cross-file dedup — the helper is byte-identical)
    cross_file = [cid for cid, occ in seen.items() if len({p for p, _ in occ}) >= 3]
    assert cross_file, "fixture must share an atom across at least three files"

    # an atom shared ACROSS VERSIONS of one file (the revert re-occupies its original atoms)
    a_versions = {b for p, b in versions if p == "a.py"}
    assert len(a_versions) == 2, "the revert means a.py has TWO distinct blobs, re-used three times"
    multi_version = [cid for cid, occ in seen.items()
                     if len({b for p, b in occ if p == "a.py"}) >= 2]
    assert multi_version, "fixture must share an atom across versions of one file"


def test_the_baseline_measures_the_factor_and_writes_nothing(
        bench: Bench, ledger: sqlite3.Connection, tmp_path: Path) -> None:
    """Item 1: the rebuild's target and cost, re-derived at the CURRENT cut, with no store written.

    Degenerate input: a pass that reports `|atoms| <= Sigma chunks` proves nothing — it holds at
    zero savings. So the MEASURED FACTOR is asserted (strictly above 1, and equal to the ratio of
    the two counts it reports), on a fixture whose sharing the test above established.

    "Writes nothing" is likewise asserted rather than trusted: the embedder would raise if called
    (it is counted), and the store, the membership relation and the ledger file are all compared
    before and after."""
    rows_before = bench.vectors.count()
    m_before = bench.memberships.count()
    ledger_path = tmp_path / "code_snapshots.sqlite"
    ledger_mtime = ledger_path.stat().st_mtime_ns
    ledger_size = ledger_path.stat().st_size

    base = measure_baseline(bench.sync, ledger)

    assert base.versions == len(ledger_versions(ledger))
    assert base.unreadable == 0
    assert base.chunks > 0 and base.atoms > 0
    assert base.atoms < base.chunks                        # necessary, and NOT sufficient
    assert base.ratio == pytest.approx(base.chunks / base.atoms)
    assert base.ratio > 1.0                                # the measured factor is the claim
    assert base.embeds_avoided == base.chunks - base.atoms

    # per lane, and the lanes are reported separately because they dedup differently
    assert set(base.per_layer) >= {LAYER_CODE_AST, LAYER_CODE_TEXT}
    assert sum(v.chunks for v in base.per_layer.values()) == base.chunks
    assert sum(v.atoms for v in base.per_layer.values()) == base.atoms

    # READ-ONLY, asserted on all four surfaces
    assert bench.embedder.embedded == [], "the baseline must never embed"
    assert bench.vectors.count() == rows_before
    assert bench.memberships.count() == m_before
    assert ledger_path.stat().st_mtime_ns == ledger_mtime
    assert ledger_path.stat().st_size == ledger_size


def test_the_baseline_reports_the_embedder_identity_it_can_and_cannot_see(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """Item 1's last column: is the carry-forward seed's geometry the live one?

    The degenerate answer is "yes" returned unconditionally. So the check is asserted to be
    STRUCTURED: `dim` is recoverable and is compared; `model` is NOT recorded on a pre-D1 row (the
    Arrow schema is shared with the prose lane and has no embedder column), and the count of rows
    carrying that status is reported rather than silently treated as a match."""
    bench.sync.sync()                                      # land HEAD so the plane is non-empty
    base = measure_baseline(bench.sync, ledger)
    check = base.embedder
    assert check is not None
    assert check.live == _EMB
    assert check.stored_dim == DIM                         # recoverable, and compared
    assert check.dim_match is True
    assert check.ledger_mismatched == 0
    assert check.matches is True

    # the falsifier: a dimension that contradicts the live config is NOT a match
    from ops.code_rebuild import EmbedderCheck
    mismatched = EmbedderCheck(live=_EMB, stored_dim=DIM + 1)
    assert mismatched.dim_match is False and mismatched.matches is False


# ── Item 2 — step 0: the sliced `commit_diffs` capture ───────────────────────────────────


def test_the_sliced_capture_is_idempotent_and_leaves_durable_progress(
        bench: Bench, ledger: sqlite3.Connection, repo: Path) -> None:
    """Item 2: the first successful capture, and R6's falsifier as a passing property.

    R6 names the failure as "a slice exceeding its budget WITHOUT leaving a checkpoint". The
    degenerate input is a budget so generous the slice never yields — that tests nothing about
    slicing — so the budget here is ZERO, forcing a yield at the first boundary, and the durable
    progress is then read back out of the marker table rather than out of a return value."""
    total = len(pending_commits(ledger))
    assert total >= 5, "fixture must hold enough commits for a slice to yield mid-history"

    first = capture_slice(ledger, repo, budget_s=0.0, batch=1)
    assert first.budget_spent is True and first.done is False
    assert first.captured >= 1, "a yielding slice must still make progress, never livelock"

    # THE R6 PROPERTY: the progress is durable, on disk, before the yield — not held in the token
    marked = ledger.execute("SELECT count(*) FROM _commit_diffs_captured").fetchone()[0]
    assert marked == first.captured
    assert len(pending_commits(ledger)) == total - first.captured

    while True:                                    # resume to completion, one slice at a time
        step = capture_slice(ledger, repo, budget_s=0.0, batch=2)
        if step.done:
            break
    assert pending_commits(ledger) == []
    assert ledger.execute("SELECT count(*) FROM _commit_diffs_captured").fetchone()[0] == total
    assert ledger.execute("SELECT count(*) FROM commit_diffs").fetchone()[0] > 0

    # idempotence: a re-run captures ZERO (the marker table, `:119-129`)
    again = capture_slice(ledger, repo, budget_s=30.0)
    assert again.captured == 0 and again.done is True


def test_pending_commits_reads_a_read_only_ledger_without_creating_its_schema(
        ledger: sqlite3.Connection, repo: Path, tmp_path: Path) -> None:
    """The dry-run's read must not write — found by the acceptance test, so it gets a ratchet.

    Degenerate input: asserting `pending_commits` works on a read-WRITE connection. It does, and it
    used to do so by calling `_ensure_schema` first — a `CREATE TABLE` that silently mutated the
    file a dry run promised to leave alone. On the LIVE ledger those tables have never existed, so
    this is the ordinary path, not a corner. The test therefore opens the ledger `mode=ro`, where
    the write cannot hide: it raises."""
    path = tmp_path / "code_snapshots.sqlite"
    # PRECONDITION: the marker table genuinely does NOT exist yet — the live ledger's own state
    assert ledger.execute(
        "SELECT 1 FROM sqlite_master WHERE name = '_commit_diffs_captured'").fetchone() is None

    ro = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        pending = pending_commits(ro)                  # must not raise: no schema is created
        assert pending, "an uncaptured ledger reports every commit pending"
        assert len(pending) == len(ro.execute("SELECT commit_sha FROM snapshots").fetchall())
    finally:
        ro.close()

    # ...and the file really was not written: the tables still do not exist
    assert ledger.execute(
        "SELECT 1 FROM sqlite_master WHERE name = '_commit_diffs_captured'").fetchone() is None

    # after a real capture, the same read reports the remainder — it is not simply "everything"
    capture_slice(ledger, repo, budget_s=30.0)
    assert pending_commits(ledger) == []


def test_the_captured_chains_preserve_a_revert_as_three_runs_two_edges(
        ledger: sqlite3.Connection, repo: Path) -> None:
    """Item 2 + Item 5: `[A, B, A]` survives, so the `:139` docstring's corrected wording is the
    behavior and not a wish.

    Degenerate input: a history with no revert. Every chain is then strictly increasing, and
    adjacent-collapse is indistinguishable from distinct-collapse — the exact confusion the old
    docstring licensed and the F4 dispute turns on. So the REVERT is asserted to exist in the
    chain first (a.py returns to a blob it already left), and only then is the shape read."""
    capture_slice(ledger, repo, budget_s=30.0)
    chains = supersession_chains(ledger)
    chain = chains["a.py"]

    # PRECONDITION: the chain genuinely REVISITS a blob, non-adjacently
    assert len(chain) == 3, "a.py: v0 -> v1 -> v0 is three RUNS"
    assert chain[0] == chain[2] != chain[1], "...and the third run re-occupies the first blob"
    assert len(set(chain)) == 2, "...over only TWO distinct blobs — which is what a revert IS"

    # the claim: adjacent-collapse keeps the revert; distinct-collapse would erase it
    assert len(chain) - 1 == 2, "|edges| = |runs| - 1"
    assert len(dict.fromkeys(chain)) == 2, "a DISTINCT collapse would report 2 runs / 1 edge"
    assert len(chain) != len(dict.fromkeys(chain)), "...so the two readings genuinely differ here"


# ── Item 3 — the carry-forward seed and the sliced, resumable walk ───────────────────────


def test_the_carry_forward_seed_lands_atoms_at_zero_embeds(bench: Bench,
                                                           ledger: sqlite3.Connection) -> None:
    """Item 3's economics: ~2/3 of the atom set enters by canonical RE-HASH of rows the old model
    already embedded, at zero embedder calls.

    Degenerate input: a store with no pre-D1 rows seeds nothing and "costs zero embeds" trivially.
    So a legacy-shaped store is built first and the recoverable set is asserted NON-EMPTY before
    the zero-embed claim is read."""
    legacy = _legacy_store(bench, ledger)
    targets = {atom_id(ch) for path, blob in ledger_versions(ledger)
               for ch in derive_code_chunks(path, _git(bench.sync.repo, "cat-file", "-p", blob))}

    seed_ids = carry_forward_candidates(legacy, targets=targets)
    # PRECONDITION: there is something to carry forward, and it is a real fraction of the target set
    assert seed_ids, "the legacy store must hold rows whose canonical body re-hashes to a target"
    assert len(seed_ids) < len(targets), "...but not all of them — L1 does not survive (D7)"
    assert {cid.split(":", 1)[0] for cid in seed_ids} == {LAYER_CODE_AST, LAYER_CODE_TEXT}

    # The seed reads and writes ONE store — which is the production shape, not a shortcut: D1
    # evolves the existing `chunks` table in place, so the legacy rows and the atom rows the seed
    # mints from them live side by side in the same table.
    memberships = MembershipStore(legacy.path.parent / "seeded.sqlite")
    atoms_before = legacy.atom_row_count()
    rows_before = legacy.count()
    assert atoms_before == 0, "PRECONDITION: no atom rows yet — the seed is what creates them"

    report = seed_carry_forward(legacy, memberships, _EMB, targets=seed_ids, stored_dim=DIM)
    assert report.refused_embedder_mismatch is False
    assert report.rows_written == len(seed_ids)
    assert report.atoms_recorded == len(seed_ids)
    assert report.embeds == 0

    # the seeded atoms are now PRESENT under the live identity, so a land reuses them
    assert memberships.known_atoms(seed_ids, _EMB) == seed_ids
    assert legacy.atom_row_count() == len(seed_ids)
    assert legacy.count() == rows_before + len(seed_ids), "APPEND-only: no legacy row was replaced"


def test_the_seed_refuses_outright_when_the_embedder_identity_disagrees(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """The embedder pin as a REFUSAL, not a warning (bp-152 §6, owner-confirmed).

    Degenerate input: a suite that only ever exercises one embedder cannot see this at all — the
    seed would happily copy vectors from another geometry into the one ANN space, and no downstream
    measurement could detect it. So a contradicting dimension is injected and the seed must do
    NOTHING: not fewer rows, none."""
    legacy = _legacy_store(bench, ledger)
    targets = {atom_id(ch) for path, blob in ledger_versions(ledger)
               for ch in derive_code_chunks(path, _git(bench.sync.repo, "cat-file", "-p", blob))}
    seed_ids = carry_forward_candidates(legacy, targets=targets)
    assert seed_ids, "PRECONDITION: there is a seed to refuse"

    memberships = MembershipStore(legacy.path.parent / "refused.sqlite")
    report = seed_carry_forward(legacy, memberships, _EMB, targets=seed_ids, stored_dim=DIM + 1)
    assert report.refused_embedder_mismatch is True
    assert report.rows_written == 0 and report.atoms_recorded == 0
    assert legacy.atom_row_count() == 0, "a PARTIAL seed would be the corruption"
    assert memberships.ledger_atom_ids() == set(), "...and nothing was recorded as reusable"


def test_killing_the_rebuild_mid_slice_and_resuming_lands_exactly_once(
        bench: Bench, ledger: sqlite3.Connection, repo: Path, tmp_path: Path) -> None:
    """Item 3's central property: sliced, checkpointed, RESUMABLE, with no double-landing.

    Degenerate input: a "resume" that re-runs from scratch into an empty store also produces a
    correct final state — it would prove nothing about resumption. So the run is genuinely
    interrupted (a zero budget forces a yield with real work already landed, asserted), resumed
    from its token, and the result compared against an INDEPENDENT single-shot rebuild of the same
    ledger: identical |V|, identical |M|, identical fibers, chunk for chunk.

    Fiber equality is why this holds — derivation is pure, so a re-landed version writes no row —
    which is also why the assertion is on the fibers themselves and not merely on the counts."""
    sliced = bench
    progress = rebuild_slice(sliced.sync, ledger, token=None, budget_s=0.0, slice_size=1)
    # PRECONDITION: the run really was interrupted with work already done
    assert progress.token is not None, "a zero budget must yield a resume token"
    assert progress.versions_landed >= 1, "...after landing something, so this is a real resume"
    assert progress.remaining > 0
    mid_m = sliced.memberships.count()
    assert mid_m > 0

    token: str | None = progress.token
    guard = 0
    while token is not None:
        guard += 1
        assert guard < 200, "the walk must terminate"
        step = rebuild_slice(sliced.sync, ledger, token=token, budget_s=0.0, slice_size=1)
        token = step.token
    assert sliced.memberships.count() > mid_m              # it genuinely continued

    # the independent control: one uninterrupted rebuild of the same ledger
    whole = _bench(repo, tmp_path, "whole")
    done = rebuild_slice(whole.sync, ledger, token=None, budget_s=3600.0)
    assert done.done is True

    assert sliced.memberships.count() == whole.memberships.count()
    assert sliced.vectors.atom_row_count() == whole.vectors.atom_row_count()
    assert sliced.memberships.fibers() == whole.memberships.fibers()
    for path, blob in whole.memberships.fibers():
        assert sliced.memberships.fiber(path, blob) == whole.memberships.fiber(path, blob)


def test_a_resumed_rebuild_re_lands_idempotently_even_with_a_lost_token(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """The token is an optimization, never the safety property (R6/D2 step 3).

    Degenerate input: asserting resumability only along the happy path, where the token always
    survives. The real crash loses it — so here the walk is re-run from scratch over an
    already-complete store, and nothing may move: no embed, no new occupancy, no new atom."""
    rebuild_slice(bench.sync, ledger, budget_s=3600.0)
    m_after, v_after = bench.memberships.count(), bench.vectors.atom_row_count()
    assert m_after > 0 and v_after > 0                     # PRECONDITION: something was landed
    embeds = len(bench.embedder.embedded)

    replay = rebuild_slice(bench.sync, ledger, token=None, budget_s=3600.0)
    assert replay.membership_rows == 0, "a re-land writes NO new occupancy"
    assert replay.atoms_embedded == 0, "...and embeds nothing"
    assert bench.memberships.count() == m_after
    assert bench.vectors.atom_row_count() == v_after
    assert len(bench.embedder.embedded) == embeds

    # an UNREADABLE token restarts the walk rather than failing it — same idempotent outcome
    garbage = rebuild_slice(bench.sync, ledger, token="{not json", budget_s=3600.0)
    assert garbage.membership_rows == 0 and garbage.atoms_embedded == 0
    assert bench.memberships.count() == m_after


def test_the_rebuilt_store_reproduces_the_baselines_measured_factor(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """§8(g): the rebuild lands the atom count Item 1 derived, against the duplicated model's count.

    Degenerate input, stated by the design itself: `|atoms| <= Sigma chunks` holds at zero savings.
    So the assertion is an EQUALITY on the factor — the standing `|M|/|V|` gauge must reproduce the
    baseline's ratio exactly, because `|M|` IS Sigma per-version chunks (one occupancy per chunk per
    version) and `|V|` IS the distinct atom count. That is the same number arrived at from two
    independent directions: derived-and-counted before the run, stored-and-queried after it."""
    base = measure_baseline(bench.sync, ledger)
    assert base.ratio > 1.0, "PRECONDITION: the fixture actually dedups (see the sharing test)"

    done = rebuild_slice(bench.sync, ledger, budget_s=3600.0)
    assert done.done is True

    gauges = frequency_gauges(bench.vectors, bench.memberships)
    assert gauges.occupancies == base.chunks, "|M| == Sigma per-version chunks"
    assert gauges.plane_atoms == base.atoms, "|V| == the distinct atom count"
    assert gauges.dedup_factor == pytest.approx(base.ratio)
    assert gauges.embeds_avoided == base.embeds_avoided

    # the embedder was called once per atom and never twice — the reuse is real, not incidental
    assert len(bench.embedder.embedded) == base.atoms
    assert len(set(bench.embedder.embedded)) == len(bench.embedder.embedded)

    # every ledger version has a fiber, INCLUDING the side-branch one that sits on no chain (F3)
    assert len(bench.memberships.fibers()) == len(ledger_versions(ledger))


def test_the_rebuild_lands_a_fiber_for_every_ledger_version_including_side_branch_ones(
        bench: Bench, ledger: sqlite3.Connection, repo: Path) -> None:
    """D4/F3: the version set is what the rebuild must cover — NOT the versions reachable along
    HEAD's first-parent line. A walk that followed the merge history would silently drop the
    intermediate blob a side branch produced, and that blob is a real member of M.

    Degenerate input: a linear history, where the two sets coincide and the distinction cannot
    bite. The fixture's two-commit side branch is asserted to have produced exactly that gap first.

    ⚑ Note what this does NOT assert. The design's F3 says "chain members are a strict subset of
    the version set", meaning `supersession_chains` misses side-branch versions. Measured against
    the shipped reader that is FALSE — chains are threaded over every SNAPSHOTTED commit, each
    diffed against its own first parent, so a side branch's own linear history is captured too
    (verified on the live ledger: 1,663 versions, 1,663 chain members, an empty difference both
    ways — issue filed). The claim that survives measurement, and the one the rebuild actually
    depends on, is this one: HEAD's first-parent line is a strict subset of the ledger."""
    capture_slice(ledger, repo, budget_s=30.0)
    versions = set(ledger_versions(ledger))

    # the versions visible along HEAD's FIRST-PARENT line alone (what a merge-history walk sees)
    first_parent: set[tuple[str, str]] = set()
    for sha in _git(repo, "rev-list", "--first-parent", "HEAD").split():
        for line in _git(repo, "ls-tree", "-r", sha).splitlines():
            meta, _, path = line.partition("\t")
            if path.endswith(".py"):
                first_parent.add((path, meta.split()[2]))

    # PRECONDITION: the side branch really did produce a version off that line
    off_line = versions - first_parent
    assert off_line, "fixture must hold a version absent from HEAD's first-parent line"
    assert first_parent < versions, "...so the first-parent view is a STRICT subset"

    rebuild_slice(bench.sync, ledger, budget_s=3600.0)
    landed = set(bench.memberships.fibers())
    assert landed == versions, "every ledger version landed a fiber"
    assert off_line <= landed, "...including the side-branch one"


# ── Item 6 — compaction and old-version cleanup (§3) ─────────────────────────────────────


def test_compaction_drops_versions_while_rows_and_search_are_unchanged(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """Item 6/§3: compaction is PHYSICAL — it removes no logical row and changes no answer.

    Degenerate input, named in the plan: a no-op compaction "changes nothing" and passes any test
    asserting only that rows and search results are unchanged. So the version count is asserted to
    have genuinely DROPPED, and the fixture is asserted to hold several dataset versions before
    that drop can mean anything. Both halves, or neither is evidence."""
    rebuild_slice(bench.sync, ledger, budget_s=3600.0)

    # PRECONDITION: many write batches happened, so there is version accumulation to compact
    before_versions = bench.vectors.dataset_versions()
    assert before_versions > 2, "fixture must accumulate dataset versions for a drop to be visible"

    query = FakeEmbedder().embed_query("def helper(value):")
    rows_before = bench.vectors.count()
    hits_before = [str(h["id"]) for h in bench.vectors.search(query, k=5)]
    atoms_before = bench.vectors.atom_row_count()
    assert hits_before, "PRECONDITION: search returns something to be preserved"

    report = bench.vectors.compact(older_than=__import__("datetime").timedelta(0))

    assert report.versions_dropped > 0, "the version count must actually FALL"
    assert report.versions_after < report.versions_before
    assert bench.vectors.dataset_versions() < before_versions

    assert report.rows_preserved is True                   # no logical row disappeared
    assert report.rows_before == report.rows_after == rows_before
    assert bench.vectors.count() == rows_before
    assert bench.vectors.atom_row_count() == atoms_before
    assert [str(h["id"]) for h in bench.vectors.search(query, k=5)] == hits_before

    # ...and the membership relation, which compaction never touches, is intact
    assert frequency_gauges(bench.vectors, bench.memberships).orphans == 0


def test_retiring_the_legacy_rows_supersedes_them_and_deletes_nothing(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """The rebuild lands the atom plane into the table holding the rows it replaces, so the old
    per-version rows must stop answering the default current-view search — by SUPERSESSION
    (keep-and-link, D2), never by deletion.

    Degenerate input: an empty legacy set makes "nothing was deleted" vacuous, so a populated
    legacy store is asserted first, and the retained-row count is asserted after."""
    legacy = _legacy_store(bench, ledger)
    total_before = legacy.count()
    legacy_current = len(legacy.project(["id"], where="source_path <> '' AND current = true"))
    assert legacy_current > 0, "PRECONDITION: there are current legacy rows to retire"

    flipped = retire_legacy_rows(legacy)
    assert flipped == legacy_current
    assert legacy.count() == total_before, "RETAINED — nothing was deleted (|V| cannot fall)"
    assert len(legacy.project(["id"], where="source_path <> '' AND current = true")) == 0

    assert retire_legacy_rows(legacy) == 0                 # idempotent: a second call is a no-op


# ── Item 7 — `palace code-rebuild`, the owner-visible verb ───────────────────────────────


def test_the_code_rebuild_verb_is_listed_and_dispatched() -> None:
    """Item 7: wiring IS the deliverable — the ON path must exist, not merely the code behind it.

    Degenerate input: asserting the `Launcher` method exists. That is the "flag-off is not done"
    failure exactly — a method nothing routes to is not a verb. So the USAGE line, the module
    docstring's verb list, and the `main()` dispatch are all read, and the dispatch is read from
    the SOURCE so a method that is never reached cannot pass."""
    import scripts.palace as palace

    assert "code-rebuild" in palace.USAGE
    assert "code-rebuild" in (palace.__doc__ or "")
    source = Path(palace.__file__).read_text(encoding="utf-8")
    assert 'if cmd == "code-rebuild":' in source
    assert "launcher.code_rebuild(dry_run=" in source

    from ops.lifecycle.launcher import Launcher
    assert callable(Launcher.code_rebuild)

    # the kind is registered as a handler on the daemon, or the enqueued job would never dispatch
    from scheduler.code_sync import CODE_REBUILD_KIND, code_rebuild_handler, enqueue_code_rebuild
    assert CODE_REBUILD_KIND == "code_rebuild"
    assert callable(code_rebuild_handler) and callable(enqueue_code_rebuild)
    launcher_src = Path(__file__).resolve().parents[2] / "ops" / "lifecycle" / "launcher.py"
    wiring = launcher_src.read_text(encoding="utf-8")
    assert "CODE_REBUILD_KIND: code_rebuild_handler(" in wiring


def test_the_verb_never_stops_the_daemon() -> None:
    """The invariant the design states outright: the rebuild is a queue citizen. A verb that
    stopped the daemon would satisfy every functional assertion above and violate D7's central
    operational claim, so the method's source is read for the calls it must not make."""
    import inspect

    from ops.lifecycle.launcher import Launcher
    source = inspect.getsource(Launcher.code_rebuild)
    for forbidden in ("self.stop(", "self.down(", "self.up(", "self.restart(", "self.deploy("):
        assert forbidden not in source, f"code-rebuild must never call {forbidden}"
    assert "enqueue_code_rebuild" in source, "...it ENQUEUES"


# ── the phase machine: one slice per dispatch, and the token that positions the next ─────


def test_the_phase_machine_walks_capture_then_seed_then_land_then_compact(
        bench: Bench, ledger: sqlite3.Connection) -> None:
    """The queue slice's shape (D7/S3): each dispatch runs ONE phase-slice and hands back the token
    that positions the next, so the rebuild never rides a single unbounded job — which is exactly
    how this lane wedged before.

    Degenerate input: a machine that reports the phases without doing them. So the OBSERVABLE
    effect of each phase is asserted as it passes: capture populates `commit_diffs`, seed/land fill
    the plane and the relation, compact reduces the dataset version count."""
    seen: list[str] = []
    token: str | None = None
    guard = 0
    while True:
        guard += 1
        assert guard < 300, "the phase machine must terminate"
        step = rebuild_step(bench.sync, ledger, token=token,
                            capture_budget_s=0.0, rebuild_budget_s=0.0,
                            capture_batch=1, slice_size=1)
        seen.append(step.phase)
        if step.done:
            break
        token = step.token
        assert token is not None
        assert json.loads(token)["phase"] in {PHASE_CAPTURE, PHASE_SEED, PHASE_LAND, PHASE_COMPACT}

    # every phase ran, in the D7/§3 order, and the final one ended the walk
    assert seen[0] == PHASE_CAPTURE
    assert seen[-1] == PHASE_COMPACT
    order = [p for i, p in enumerate(seen) if i == 0 or seen[i - 1] != p]
    assert order == [PHASE_CAPTURE, PHASE_SEED, PHASE_LAND, PHASE_COMPACT]
    # a zero budget with batch/slice 1 must have forced BOTH long phases to yield repeatedly —
    # otherwise the walk fitted in one dispatch and nothing about slicing has been exercised
    assert seen.count(PHASE_CAPTURE) > 1, "capture must yield mid-phase and resume"
    assert seen.count(PHASE_LAND) > 1, "the land walk must yield mid-phase and resume"

    # the observable effects, phase by phase
    assert pending_commits(ledger) == []
    assert ledger.execute("SELECT count(*) FROM commit_diffs").fetchone()[0] > 0
    base = measure_baseline(bench.sync, ledger)
    gauges = frequency_gauges(bench.vectors, bench.memberships)
    assert gauges.occupancies == base.chunks
    assert gauges.plane_atoms == base.atoms
    assert gauges.dedup_factor == pytest.approx(base.ratio)


# ── the canonical-body recovery the seed depends on ──────────────────────────────────────


def test_canonical_recovery_refuses_a_body_line_that_merely_looks_like_a_header() -> None:
    """A wrong strip is silent identity corruption — it mints an atom nothing can ever hit again.

    Degenerate input: a body whose first line does not begin with `#` at all. Any implementation
    handles that. The dangerous case is a body whose first line IS a comment, which is ordinary in
    this repo (`ops/code_lineage.py` opens with one), so the recovery is verified against the row's
    OWN `source_path` rather than against the shape of the line."""
    body = "def f():\n    return 1\n"
    header = "# pkg/mod.py:f(x)"
    assert canonical_body_of_stored(LAYER_CODE_AST, f"{header}\n{body}", "pkg/mod.py") == body

    # a real first-line comment, under a row whose path it does NOT name: refused, not stripped
    commented = "# ── Family 1 boundary ──\ndef f():\n    return 1\n"
    assert canonical_body_of_stored(LAYER_CODE_AST, commented, "pkg/mod.py") is None

    # L0b windows are headerless by construction, so the window IS its canonical body
    assert canonical_body_of_stored(LAYER_CODE_TEXT, commented, "pkg/mod.py") == commented

    # L1 never carries forward: its windows were cut over header-bearing prose (D7)
    assert canonical_body_of_stored("codedoc", f"# pkg/mod.py\n{body}", "pkg/mod.py") is None


# ── helpers ──────────────────────────────────────────────────────────────────────────────


def _legacy_store(bench: Bench, ledger: sqlite3.Connection) -> VectorStore:
    """A store shaped like the LIVE one: pre-D1 rows carrying `source_path`/`digest` and a
    header-bearing embed text, one per chunk per version — the duplicated model this replaces.

    Built by hand rather than by calling the old lander, because the old lander no longer exists:
    the point is to reproduce the ROWS the live store actually holds, so the carry-forward's
    canonical re-hash is exercised against real shapes."""
    from core.kernel.provenance import Provenance

    store = VectorStore(bench.vectors.path.parent / "legacy.lance", dim=DIM)
    embedder = FakeEmbedder()
    rows: list[dict[str, object]] = []
    for path, blob in ledger_versions(ledger):
        source = _git(bench.sync.repo, "cat-file", "-p", blob)
        for i, ch in enumerate(derive_code_chunks(path, source)):
            rows.append({
                "id": f"{path}:{ch.content_hash}", "digest": blob, "title": path,
                "source_path": path, "chunk_index": i, "provenance": Provenance.CODE.value,
                "text": ch.text, "layer": ch.layer, "qualname": ch.qualname,
                "line_start": ch.slot_line_start, "line_end": ch.slot_line_end,
                "current": True, "vector": embedder.embed_documents([ch.text])[0],
            })
    store.add(rows)
    return store
