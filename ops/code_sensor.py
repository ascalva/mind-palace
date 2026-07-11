"""The code sensor — a model-less pipeline agent over the repo instrument.

Proves the agent platform's "code acts" half with zero inference: an agent is its declared
tools, wired at build time, every act attested. This one holds six handles — the git
instrument (read-only), the snapshot ledger, the attestor, (bp-012) the OBSERVED-only
observation store + its handoff seam, and (bp-013) the Lane-1 reference-edge store —
and nothing else: no model, no embedder, no vector
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

Lane 1 (bp-013, B-c): the projection pass ALSO populates each observation's
`references_out` (validated code→corpus patterns) and mints typed doc↔code reference
edges — both directions — into the dedicated `ReferenceEdgeStore`
(`core/stores/reference_edges.py`), a store the balance math holds no handle to.
Extraction is mechanical (bp-011's measured-precision regexes verbatim); no model call
exists anywhere in this path.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.loader import Config
from core.attestation import Attestor
from core.sensing import CodeSensingHandoff
from core.stores.code_observations import CodeObservation, CodeObservationStore
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore
from ops.code_snapshot import (
    FileShape,
    _git,
    annotate_headers,
    backfill_docstrings,
    open_snapshot_db,
    snapshot_commit,
)

# ── Lane-1 reference extraction (B-c, bp-013 Item 7) — bp-011's VALIDATED patterns ONLY ──
# The V4 inventory (docs/build-plans/bp-011/inventory.json, `ranked_patterns_for_bp013`)
# measured per-(pattern, direction) precision on a stratified hand-check. Lane 1 is
# precision-first (a wrong deterministic edge is worse than a missing one; Lane 2 exists
# for fuzzy), so only the 100%-precision patterns are extracted:
#   KEPT:    note-citation (code→corpus, 4/4) · path-mention (code→corpus, 7/7)
#            · path-mention (corpus→code, 17/17)
#   DROPPED: wikilink (code→corpus, 0/5 — prose about [[...]] syntax, never a real link)
#            · symbol-mention (corpus→code, 1/5 — stdlib-shaped tokens, filenames-with-
#              dots, compound path.symbol needs its own pattern shape)
# The regexes are bp-011's probe patterns verbatim (docs/build-plans/bp-011/
# v4_reference_scan.py) — the measured precision belongs to THESE expressions; rewriting
# them would orphan the measurement. Targets are stored AS WRITTEN (no basename/proximity
# resolution — disambiguating a bare filename is consumer-side judgment, not Lane-1
# mechanics); a `:line` suffix on a corpus→code mention is stripped from the typed code
# endpoint (the endpoint is a path, not a path:line).
VALIDATED_PATTERNS = frozenset({
    ("code_to_corpus", "note-citation"),
    ("code_to_corpus", "path-mention"),
    ("corpus_to_code", "path-mention"),
})
_RE_NOTE_CITATION = re.compile(r"docs/(?:design-notes|findings|brainstorms)/[\w.\-]+\.md")
_RE_BACKTICK_PATH = re.compile(r"`([\w./\-]+\.(?:py|md|toml|yml|yaml|sh))(:\d+)?`")
_RE_PATH_MENTION = re.compile(r"`([\w./\-]+\.py)(:(\d+))?`")
# The corpus surfaces bp-011 scanned (corpus→code direction) — repo docs, not vault.
_CORPUS_DIRS = ("docs/design-notes", "docs/findings", "docs/brainstorms")


def extract_references(docstring: str, *, source_line: int) -> tuple[dict[str, Any], ...]:
    """φ_code's Lane-1 docstring pass (code→corpus): the §2.3 `references_out` elements
    `{type, target, source_line}`, validated patterns only, exact duplicates collapsed
    deterministically (first occurrence wins). `source_line` is the docstring owner's
    line — bp-011's probe convention (module = 1)."""
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for m in _RE_NOTE_CITATION.finditer(docstring):
        if ("note-citation", m.group(0)) not in seen:
            seen.add(("note-citation", m.group(0)))
            out.append({"type": "note-citation", "target": m.group(0),
                        "source_line": source_line})
    for m in _RE_BACKTICK_PATH.finditer(docstring):
        if ("path-mention", m.group(1)) not in seen:
            seen.add(("path-mention", m.group(1)))
            out.append({"type": "path-mention", "target": m.group(1),
                        "source_line": source_line})
    return tuple(out)


@dataclass
class CodeSyncReport:
    ingested: int = 0
    ledger_total: int = 0
    shas: list[str] = field(default_factory=list)
    doc_coverage: float = 0.0     # documented symbols / total symbols in the ledger, [0, 1]
    projected: int = 0            # commits whose observation batch landed this sync (B-b)
    observation_rows: int = 0     # NEW observed-stratum rows this sync (0 on a re-run)
    reference_edges: int = 0      # NEW Lane-1 reference edges minted this sync (B-c)

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
    # The B-c Lane-1 store (bp-013): deterministic doc↔code reference edges, minted within
    # the projection pass. None = no edge minting (B-b behavior, graceful degrade). This
    # handle is the SENSOR's, never build_complex's — the balance math cannot reach it
    # (core/stores/reference_edges.py docstring; the isolation test pins it).
    reference_edges: ReferenceEdgeStore | None = None

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
                rows, edges = self._project(sha)
                report.observation_rows += rows
                report.reference_edges += edges
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
        symbol, real docstrings verbatim (bp-011's column). `references_out` is populated
        by the Lane-1 extractor (B-c / bp-013) — validated patterns only, source_line =
        the docstring owner's line (module = 1, bp-011's probe convention)."""
        out = [CodeObservation(commit_sha=sha, path=path, qualname="", kind="module",
                               signature="", docstring=doc,
                               references_out=extract_references(doc, source_line=1))
               for (path, doc) in self.db.execute(
                   "SELECT path, docstring FROM files WHERE commit_sha=? ORDER BY path",
                   (sha,))]
        out.extend(CodeObservation(commit_sha=sha, path=path, qualname=qual, kind=kind,
                                   signature=sig, docstring=doc,
                                   references_out=extract_references(doc, source_line=line))
                   for (path, qual, kind, sig, doc, line) in self.db.execute(
                       "SELECT path, qualname, kind, signature, docstring, lineno "
                       "FROM symbols WHERE commit_sha=? ORDER BY path, qualname", (sha,)))
        return out

    def _project(self, sha: str) -> tuple[int, int]:
        """Project one commit through the seam: emit the batch to the handoff, collect it
        back, land it in the OBSERVED-only store, mint the Lane-1 reference edges (B-c),
        attest. Idempotent: an already-projected sha is a no-op (no rows, no edges, no
        attestation), and collect() drains any batch a prior crash left in the handoff.
        Returns (NEW observation rows, NEW reference edges)."""
        assert self.observations is not None and self.obs_handoff is not None
        if self.observations.is_projected(sha):
            return 0, 0
        batch = self._observations_for(sha)
        content = self.obs_handoff.emit_batch(sha, batch)
        added = self.observations.add_batch(self.obs_handoff.collect())
        edges = self._mint_reference_edges(sha, batch)
        self.observations.mark_projected(sha, content)
        if self.attestor is not None:
            # inputs=[commit sha], outputs=[batch content hash] (plan Q5). derived_from is
            # auto-linked by the attestor via producers_of: the ingest_commit attestation
            # for the same sha (output_hashes=[sha]) becomes this projection's parent.
            # The Lane-1 edge minting is attested WITHIN this action (bp-013 Item 7 — no
            # new attestation kind): the batch hash covers `references_out` (code→corpus),
            # and the corpus→code half is deterministically re-derivable from the sha.
            self.attestor.emit(agent_role="code_sensor", action="project_observations",
                               input_hashes=[sha], output_hashes=[content])
        return added, edges

    def _mint_reference_edges(self, sha: str, batch: list[CodeObservation]) -> int:
        """Lane 1 (B-c): turn the batch's `references_out` (code→corpus) plus the commit's
        corpus-side path-mentions (corpus→code) into typed edges in the dedicated
        reference-edge store. Deterministic — no model anywhere in this path; validated
        patterns only (`VALIDATED_PATTERNS`); direction stored as extracted (Q3).
        Idempotent via the store's content identity AND `_project`'s projected-sha gate."""
        if self.reference_edges is None:
            return 0
        minted: list[ReferenceEdge] = []
        for o in batch:                                    # code→corpus: from references_out
            for ref in o.references_out:
                assert ("code_to_corpus", ref["type"]) in VALIDATED_PATTERNS
                minted.append(ReferenceEdge.mint(
                    direction="code_to_corpus", ref_type=str(ref["type"]), commit_sha=sha,
                    code_path=o.path, qualname=o.qualname, corpus_ref=str(ref["target"]),
                    corpus_kind="path", source_line=int(ref["source_line"])))
        minted.extend(self._corpus_reference_edges(sha))   # corpus→code: the md-side scan
        return self.reference_edges.add_batch(minted)

    def _corpus_reference_edges(self, sha: str) -> list[ReferenceEdge]:
        """The corpus→code direction (bp-011's highest-volume 100%-precision pattern):
        scan the commit's OWN tree state (`git show sha:path` — deterministic per §2.2,
        not the working tree) for backticked `*.py` path-mentions in the repo-doc corpus
        surfaces. Corpus endpoint = the note's repo-relative path (Q2 — these docs are not
        vault catalog content, so no digest exists to key by); code endpoint =
        (sha, mentioned path as written minus any `:line` suffix, qualname '')."""
        edges: list[ReferenceEdge] = []
        listed = _git(self.repo, "ls-tree", "-r", "--name-only", sha, "--", *_CORPUS_DIRS)
        for doc_path in listed.splitlines():
            if not doc_path.endswith(".md"):
                continue
            text = _git(self.repo, "show", f"{sha}:{doc_path}")
            for i, line in enumerate(text.splitlines(), start=1):
                for m in _RE_PATH_MENTION.finditer(line):
                    edges.append(ReferenceEdge.mint(
                        direction="corpus_to_code", ref_type="path-mention",
                        commit_sha=sha, code_path=m.group(1), qualname="",
                        corpus_ref=doc_path, corpus_kind="path", source_line=i))
        return edges

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
    from core.stores.reference_edges import open_reference_edge_store

    return CodeSensor(
        repo=REPO_ROOT,
        db=open_snapshot_db(cfg.paths.data_dir / "code_snapshots.sqlite"),
        attestor=build_attestor(cfg),
        observations=open_code_observation_store(cfg),
        obs_handoff=CodeSensingHandoff(handoff=cfg.paths.data_dir / "code_sensing_handoff"),
        reference_edges=open_reference_edge_store(cfg),
    )
