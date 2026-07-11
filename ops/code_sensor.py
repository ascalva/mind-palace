"""The code sensor — a model-less pipeline agent over the repo instrument.

Proves the agent platform's "code acts" half with zero inference: an agent is its declared
tools, wired at build time, every act attested. This one holds exactly three handles — the
git instrument (read-only), the snapshot ledger (its ONE designated store), and the
attestor — and nothing else: no model, no embedder, no corpus store, no network. It is the
same species as the vault watcher (`core/ingest/sync.py`), the deterministic-ingest agent
pattern, and deliberately NOT a factory-minted role: `PRE_DECLARED_MAX` holds no git or
store handle (§10), so instrument agents are wired by `build_*`, never minted.

Sensor framing (docs/brainstorms/code-as-sensor-stream.md): the repo is an instrument, the
commit stream is sensed data, `ops/code_snapshot.py` is the interpreter φ_code, the ledger
is the normalized store — event-log-only, outside the knowledge corpus. `sync()` is the
watcher's rescan semantics: ledger-vs-history reconciliation, oldest first, idempotent — a
missed post-commit hook heals on the next invocation, and a no-op sync is free.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from config.loader import Config
from core.attestation import Attestor
from ops.code_snapshot import FileShape, _git, annotate_headers, open_snapshot_db, snapshot_commit


@dataclass
class CodeSyncReport:
    ingested: int = 0
    ledger_total: int = 0
    shas: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"code-sensor sync: ingested={self.ingested} ledger_total={self.ledger_total}"


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
        annotate_headers(self.db, self.repo)   # heal pre-header rows (CONVENTIONS §Commits)
        report.ledger_total = self.db.execute("SELECT count(*) FROM snapshots").fetchone()[0]
        return report


def build_code_sensor(config: Config | None = None) -> CodeSensor:
    """Wire the agent's three tools against the real repo, ledger, and attestation chain."""
    from config.loader import REPO_ROOT, get_config
    from core.attestation import build_attestor

    cfg = config or get_config()
    return CodeSensor(
        repo=REPO_ROOT,
        db=open_snapshot_db(cfg.paths.data_dir / "code_snapshots.sqlite"),
        attestor=build_attestor(cfg),
    )
