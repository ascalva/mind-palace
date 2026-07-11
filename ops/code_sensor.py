"""The code sensor — a model-less pipeline agent over the repo instrument.

Proves the agent platform's "code acts" half with zero inference: an agent is its declared
tools, wired at build time, every act attested. This one holds five handles — the git
instrument (read-only), the snapshot ledger, the attestor, and (bp-012) the OBSERVED-only
observation store + its handoff seam — and nothing else: no model, no embedder, no vector
corpus, no network. It is the
same species as the vault watcher (`core/ingest/sync.py`), the deterministic-ingest agent
pattern, and deliberately NOT a factory-minted role: `PRE_DECLARED_MAX` holds no git or
store handle (§10), so instrument agents are wired by `build_*`, never minted.

Sensor framing (docs/brainstorms/code-as-sensor-stream.md): the repo is an instrument, the
commit stream is sensed data, `ops/code_snapshot.py` is the interpreter φ_code, the ledger
is the normalized ops-side record. CORRECTION (bp-012, ratified
docs/design-notes/code-observation-projection.md B-b): the stream is no longer
event-log-only — `sync()` now ALSO projects each newly-ingested commit into the observed
stratum, through the `CodeSensingHandoff` seam into the OBSERVED-only
`code_observations` store (symbol-grain, idempotent by (commit_sha, path, qualname),
attested `project_observations`). The LEDGER remains the ops-side record — build history,
reset-guarded; the OBSERVATIONS are corpus-side — the observed stratum, a reset target.
`sync()` keeps the watcher's rescan semantics: ledger-vs-history reconciliation, oldest
first, idempotent — a missed post-commit hook heals on the next invocation, and a no-op
sync is free. History backfill of observations is `backfill_observations()` — available,
deliberately NOT wired into sync (plan §11 parked decision: owner nod required).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from config.loader import Config
from core.attestation import Attestor
from core.sensing import CodeSensingHandoff
from core.stores.code_observations import CodeObservation, CodeObservationStore
from ops.code_snapshot import (
    FileShape,
    _git,
    annotate_headers,
    backfill_docstrings,
    open_snapshot_db,
    snapshot_commit,
)


@dataclass
class CodeSyncReport:
    ingested: int = 0
    ledger_total: int = 0
    shas: list[str] = field(default_factory=list)
    doc_coverage: float = 0.0     # documented symbols / total symbols in the ledger, [0, 1]
    projected: int = 0            # commits whose observation batch landed this sync (B-b)
    observation_rows: int = 0     # NEW observed-stratum rows this sync (0 on a re-run)

    def __str__(self) -> str:
        return (f"code-sensor sync: ingested={self.ingested} ledger_total={self.ledger_total} "
                f"doc_coverage={self.doc_coverage:.2%} projected={self.projected}")


@dataclass
class CodeSensor:
    """Tools are the wiring; the agent is the discipline over them."""

    repo: Path
    db: sqlite3.Connection
    # ingest attestation ("the code sensor ingested commit C under Constitution F") — the
    # sensed-stream analogue of the watcher's authored leaf. None = records-only ledger.
    attestor: Attestor | None = None
    # CONVENTIONS §Commits: main is the ingestion branch. Pinned by REF, not checkout —
    # a manual sync run from a feature branch still ingests main history only.
    branch: str = "main"
    # The B-b projection pair (both or neither): the OBSERVED-only store and the sensing
    # seam's code-stream sibling. None = ledger-only sensor (the pre-B-b behavior; existing
    # callers and tests degrade gracefully — no projection pass runs).
    observations: CodeObservationStore | None = None
    obs_handoff: CodeSensingHandoff | None = None

    def sync(self) -> CodeSyncReport:
        """Reconcile the ledger against the ingestion branch; snapshot + attest what's missing."""
        history = _git(self.repo, "rev-list", "--reverse", self.branch).splitlines()
        known = {s for (s,) in self.db.execute("SELECT commit_sha FROM snapshots")}
        report = CodeSyncReport()
        cache: dict[str, FileShape] = {}          # blob-shape cache shared across the pass
        for sha in history:
            if sha in known:
                continue
            snapshot_commit(self.db, self.repo, sha, _cache=cache)
            if self.attestor is not None:
                # input == output == the commit sha: git's own content address for the tree
                # state read and the snapshot written — the sensed-stream chain leaf.
                self.attestor.emit(agent_role="code_sensor", action="ingest_commit",
                                   input_hashes=[sha], output_hashes=[sha])
            report.ingested += 1
            report.shas.append(sha)
        # B-b projection pass: EXACTLY the newly-ingested commits (plan Item 5). NOT a
        # reconcile-all-history sweep — that would silently run the ~200-commit backfill on
        # the live daemon's first sync, against the plan §11 parked decision ("available,
        # not run"). History enters via backfill_observations(), on the owner's nod.
        if self.observations is not None and self.obs_handoff is not None:
            for sha in report.shas:
                report.observation_rows += self._project(sha)
                report.projected += 1
        annotate_headers(self.db, self.repo)   # heal pre-header rows (CONVENTIONS §Commits)
        backfill_docstrings(self.db, self.repo)  # heal pre-docstring-column rows (B-a)
        report.ledger_total = self.db.execute("SELECT count(*) FROM snapshots").fetchone()[0]
        total, documented = self.db.execute(
            "SELECT count(*), count(*) FILTER (WHERE docstring != '') FROM symbols"
        ).fetchone()
        report.doc_coverage = (documented / total) if total else 0.0
        return report

    def _observations_for(self, sha: str) -> list[CodeObservation]:
        """One commit's batch, from the snapshot walk's shapes already in the ledger (one
        parse per blob — φ_code stays the sole interpreter, §2.2): a module-grain row per
        file (the module docstring rides `files.docstring`) plus one row per def/class
        symbol, real docstrings verbatim (bp-011's column). `references_out` is emitted
        EMPTY by B-b — the deterministic reference extractor is Lane 1 (B-c / bp-013)."""
        out = [CodeObservation(commit_sha=sha, path=path, qualname="", kind="module",
                               signature="", docstring=doc)
               for (path, doc) in self.db.execute(
                   "SELECT path, docstring FROM files WHERE commit_sha=? ORDER BY path",
                   (sha,))]
        out.extend(CodeObservation(commit_sha=sha, path=path, qualname=qual, kind=kind,
                                   signature=sig, docstring=doc)
                   for (path, qual, kind, sig, doc) in self.db.execute(
                       "SELECT path, qualname, kind, signature, docstring FROM symbols "
                       "WHERE commit_sha=? ORDER BY path, qualname", (sha,)))
        return out

    def _project(self, sha: str) -> int:
        """Project one commit through the seam: emit the batch to the handoff, collect it
        back, land it in the OBSERVED-only store, attest. Idempotent: an already-projected
        sha is a no-op (no rows, no attestation), and collect() drains any batch a prior
        crash left in the handoff. Returns NEW rows landed."""
        assert self.observations is not None and self.obs_handoff is not None
        if self.observations.is_projected(sha):
            return 0
        content = self.obs_handoff.emit_batch(sha, self._observations_for(sha))
        added = self.observations.add_batch(self.obs_handoff.collect())
        self.observations.mark_projected(sha, content)
        if self.attestor is not None:
            # inputs=[commit sha], outputs=[batch content hash] (plan Q5). derived_from is
            # auto-linked by the attestor via producers_of: the ingest_commit attestation
            # for the same sha (output_hashes=[sha]) becomes this projection's parent.
            self.attestor.emit(agent_role="code_sensor", action="project_observations",
                               input_hashes=[sha], output_hashes=[content])
        return added

    def backfill_observations(self) -> int:
        """Project every ledger commit not yet projected — the HISTORY backfill (note
        PD-d). Available, deliberately NOT called by sync(): running it over the full
        ledger is the plan §11 parked decision (re-entry: one-batch timing journaled +
        owner nod). Idempotent via the projections table; returns commits projected."""
        if self.observations is None or self.obs_handoff is None:
            return 0
        done = 0
        for (sha,) in self.db.execute(
                "SELECT commit_sha FROM snapshots ORDER BY committed_at, commit_sha"):
            if not self.observations.is_projected(sha):
                self._project(sha)
                done += 1
        return done


def build_code_sensor(config: Config | None = None) -> CodeSensor:
    """Wire the agent's handles against the real repo, ledger, stores, and chain."""
    from config.loader import REPO_ROOT, get_config
    from core.attestation import build_attestor
    from core.stores.code_observations import open_code_observation_store

    cfg = config or get_config()
    return CodeSensor(
        repo=REPO_ROOT,
        db=open_snapshot_db(cfg.paths.data_dir / "code_snapshots.sqlite"),
        attestor=build_attestor(cfg),
        observations=open_code_observation_store(cfg),
        obs_handoff=CodeSensingHandoff(handoff=cfg.paths.data_dir / "code_sensing_handoff"),
    )
