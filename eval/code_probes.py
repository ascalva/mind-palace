"""The golden code-retrieval probe set (bp-093/CI-2; dn-code-ingest-pipeline §2.8 M-C3, §3 Q1).

A small, hand-authored set of "find the code that does X" queries with **known-answer paths** — the
honest retrieval-quality fixture the note calls for. It is deliberately NOT in `eval/golden/**` (the
frozen owner set, a foundation denylist): this is a builder-authored measurement fixture, versioned
here in ordinary code, re-checkable and free to grow.

Each probe pins a natural-language query to the repo path(s) whose code a human would call the
answer. Two disciplines keep the fixture honest:

  * **Known-answer paths are real files at HEAD.** `test_code_retrieval` asserts every
    `answer_paths` entry exists on disk, so a rename that orphans a probe fails the suite rather
    than silently degrading a future reading.
  * **Content-addressed.** `probe_set_hash()` fingerprints the set so a reading records exactly
    which probe fixture produced it (the CN-1 index discipline — a reading knows what it measured).

The probes are the *comparator substrate* for M-C3 (code-lane vs docstring-only baseline). They
carry no verdict and no scores — the harness (`eval/harness/code_retrieval.py`) computes those
against a seeded store. This module holds ZERO retrieval machinery and imports no store/embedder, so
it is a pure fixture importable anywhere.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeProbe:
    """One "find the code that does X" probe. `answer_paths` is the set of repo-relative paths whose
    code is a correct answer (usually one; a small set when the capability is legitimately split).
    `probe_id` is a short stable handle used in the reading table."""

    probe_id: str
    query: str
    answer_paths: frozenset[str]


# The golden set — 15 probes over confirmed-present HEAD paths (main-package + eval, never a test
# file). Queries are phrased as a user would ask them, not as the docstring reads, so the retrieval
# has real work to do rather than matching verbatim text.
PROBES: tuple[CodeProbe, ...] = (
    CodeProbe(
        "vectorstore",
        "where are embedded chunks stored and searched by nearest neighbour in LanceDB",
        frozenset({"core/stores/vectorstore.py"}),
    ),
    CodeProbe(
        "semantic-search",
        "provenance-aware semantic search over the thought graph, optionally grouped by source",
        frozenset({"core/ingest/index.py"}),
    ),
    CodeProbe(
        "code-embed-lane",
        "the lane that ingests source, docstrings and comments as three co-registered layers",
        frozenset({"core/ingest/code_corpus.py"}),
    ),
    CodeProbe(
        "sourceset",
        "group vector-search hits by their source object — a source is the set of its idea vectors",
        frozenset({"core/kernel/stores/sourceset.py"}),
    ),
    CodeProbe(
        "code-snapshot",
        "walk a python file's AST to snapshot its symbols, signatures and docstrings into a ledger",
        frozenset({"ops/code_snapshot.py"}),
    ),
    CodeProbe(
        "code-sensor",
        "the model-less sensor that extracts references from code to design notes and findings",
        frozenset({"ops/code_sensor.py"}),
    ),
    CodeProbe(
        "chunk-window",
        "split raw text into overlapping character windows for embedding",
        frozenset({"core/kernel/ingest/chunk.py"}),
    ),
    CodeProbe(
        "embedder",
        "the adapter that calls the qwen3 embedding model to vectorize documents and queries",
        frozenset({"core/ingest/embed.py"}),
    ),
    CodeProbe(
        "provenance",
        "the provenance classes and the mirror-readable firewall set that gates the self-model",
        frozenset({"core/kernel/provenance.py"}),
    ),
    CodeProbe(
        "code-sync",
        "the scheduler task that incrementally syncs changed code blobs into the vector store",
        frozenset({"scheduler/code_sync.py"}),
    ),
    CodeProbe(
        "note-ingest",
        "ingest a vault markdown note into the corpus — derive chunks, embed, index",
        frozenset({"core/kernel/ingest/pipeline.py"}),
    ),
    CodeProbe(
        "eval-store",
        "the append-only duckdb store of evaluation readings keyed by corpus, config and seed",
        frozenset({"eval/harness/store.py"}),
    ),
    CodeProbe(
        "golden-metrics",
        "compute recall-at-k and mean cosine distance for the frozen golden set",
        frozenset({"eval/metrics.py"}),
    ),
    CodeProbe(
        "reference-edges",
        "the store of reference edges between code and the doc corpus, including code-to-code",
        frozenset({"core/stores/reference_edges.py"}),
    ),
    CodeProbe(
        "note-centroids",
        "cluster embedded chunks into note centroids computed on read for the dreaming complex",
        frozenset({"core/dreaming/cluster.py"}),
    ),
)


def probe_set_hash(probes: tuple[CodeProbe, ...] = PROBES) -> str:
    """A content address for the probe fixture — sha256 over the sorted (id, query, sorted paths).
    A reading records this so it is unambiguous which fixture version produced it (CN-1). Stable
    under reordering; changes iff a probe's text or answer set changes."""
    h = hashlib.sha256()
    for p in sorted(probes, key=lambda p: p.probe_id):
        h.update(p.probe_id.encode("utf-8"))
        h.update(b"\0")
        h.update(p.query.encode("utf-8"))
        h.update(b"\0")
        for path in sorted(p.answer_paths):
            h.update(path.encode("utf-8"))
            h.update(b"\0")
        h.update(b"\x01")
    return h.hexdigest()


__all__ = ["CodeProbe", "PROBES", "probe_set_hash"]
